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

# Install Node 18 (Frappe requires it)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

# Install bench CLI
RUN pip install frappe-bench

# Create bench user
RUN useradd -m -s /bin/bash frappe
WORKDIR /home/frappe
USER frappe

# Init bench with Frappe v15
RUN bench init \
    --frappe-branch version-15 \
    --python python3 \
    frappe-bench

WORKDIR /home/frappe/frappe-bench

# ERPNext — official v15
RUN bench get-app erpnext \
    https://github.com/frappe/erpnext.git \
    --branch version-15

# CRM — Hephzibah custom build (your updates)
RUN bench get-app crm \
    https://github.com/hephzibahtechnologies/frappe-demo.git \
    --branch main

# HRMS — CorporateRulers custom build (your updates)
RUN bench get-app hrms \
    https://github.com/corporaterulers/hrms.git \
    --branch master

EXPOSE 8000 9000

CMD ["bench", "start"]
