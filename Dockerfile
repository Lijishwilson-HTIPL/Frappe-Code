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

# Install Node 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

# Install bench CLI
RUN pip install frappe-bench

# Create bench user
RUN useradd -m -s /bin/bash frappe
WORKDIR /home/frappe
USER frappe

# Clone Frappe-Code — single repo, all apps included (no submodules)
RUN git clone \
    --branch Lijish-up \
    --depth 1 \
    https://github.com/Lijishwilson-HTIPL/Frappe-Code.git \
    frappe-bench

WORKDIR /home/frappe/frappe-bench

# Set up Python virtualenv and install all apps
RUN bench setup env && \
    env/bin/pip install -e apps/frappe && \
    env/bin/pip install -e apps/erpnext && \
    env/bin/pip install -e apps/crm && \
    env/bin/pip install -e apps/hrms && \
    env/bin/pip install -e apps/helpdesk

# Install frontend dependencies for all apps
RUN cd apps/frappe   && yarn install --frozen-lockfile && cd ../.. && \
    cd apps/erpnext  && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/crm      && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/hrms     && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/helpdesk && yarn install --frozen-lockfile 2>/dev/null || true && cd ../..

# Regenerate Procfile and Redis configs with correct container paths
# (the repo's Procfile has hardcoded local machine paths — this overwrites them)
RUN bench setup procfile && bench setup redis

EXPOSE 8000 9000

CMD ["bench", "start"]
