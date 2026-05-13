FROM python:3.11-slim-bookworm

# System dependencies
RUN apt-get update && apt-get install -y \
    git curl wget gnupg2 \
    mariadb-client \
    redis-tools \
    wkhtmltopdf \
    libssl-dev libffi-dev \
    libmariadb-dev gcc g++ \
    xvfb xfonts-75dpi xfonts-base \
    && rm -rf /var/lib/apt/lists/*

# Install Node 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

# Install bench CLI
RUN pip install frappe-bench

# Create bench user
RUN useradd -m -s /bin/bash frappe
WORKDIR /home/frappe
USER frappe

# Clone Frappe-Code with all submodules (your full bench)
RUN git clone \
    --branch liji-overall-update \
    --recurse-submodules \
    https://github.com/Lijishwilson-HTIPL/Frappe-Code.git \
    frappe-bench

WORKDIR /home/frappe/frappe-bench

# Install Python dependencies for all apps
RUN pip install -e apps/frappe && \
    pip install -e apps/erpnext && \
    pip install -e apps/crm && \
    pip install -e apps/hrms

# Build frontend assets
RUN cd apps/frappe && yarn install --frozen-lockfile && cd ../.. && \
    cd apps/erpnext && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/crm && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/hrms && yarn install --frozen-lockfile 2>/dev/null || true && cd ../..

EXPOSE 8000 9000

CMD ["bench", "start"]
