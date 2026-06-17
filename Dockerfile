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
    --branch stagging-deployment \
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
    env/bin/pip install -e apps/helpdesk && \
    env/bin/pip install -e apps/telephony && \
    env/bin/pip install -e apps/sbiqc_provisioning

# Install frontend dependencies for all apps
RUN cd apps/frappe   && yarn install --frozen-lockfile && cd ../.. && \
    cd apps/erpnext  && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/crm      && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/hrms     && yarn install --frozen-lockfile 2>/dev/null || true && cd ../.. && \
    cd apps/helpdesk && yarn install --frozen-lockfile 2>/dev/null || true && cd ../..

# Build frontend assets — compiles Vue/JS bundles for CRM, Helpdesk, etc.
RUN bench build --app frappe --app erpnext --app crm --app hrms --app helpdesk --app telephony || true

# Regenerate Procfile with correct container paths; strip local redis entries
# (Redis runs in separate containers — no redis-server binary needed here)
RUN echo y | bench setup procfile && sed -i '/^redis_/d' Procfile

EXPOSE 8000 9000

# At startup: write Redis + DB config directly into common_site_config.json, then start bench.
# Using python instead of 'bench set-config' because bench requires a TTY / interactive context
# and is not reliably in PATH during Docker CMD execution.
CMD python3 -c " \
import json, os; \
cfg_path = 'sites/common_site_config.json'; \
cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}; \
cfg.update({ \
  'redis_cache':    'redis://' + os.environ.get('REDIS_CACHE',    'redis-cache:6379'), \
  'redis_queue':    'redis://' + os.environ.get('REDIS_QUEUE',    'redis-queue:6379'), \
  'redis_socketio': 'redis://' + os.environ.get('REDIS_SOCKETIO', 'redis-socketio:6379'), \
  'db_host': os.environ.get('DB_HOST', 'db'), \
  'db_port': int(os.environ.get('DB_PORT', 3306)), \
}); \
json.dump(cfg, open(cfg_path, 'w'), indent=1) \
" && bench start
