#!/bin/bash
# Startup script for the Frappe container.
#
# Fixes the recurring blank-page problem: the base image idles (tail -f /dev/null)
# and never starts the web server, and the built JS assets live inside the
# container filesystem (not a volume) so they are wiped whenever the container is
# recreated. This script rebuilds assets when missing and starts the full stack.
set -e
cd /home/frappe/frappe-bench

# The checked-in sites/common_site_config.json carries host-dev values (Redis on
# 127.0.0.1, no db_host). Overwrite with the Docker-network settings every start,
# same as the image's original CMD did before docker-compose.override.yml swapped
# it for this script.
python3 -c "
import json, os
cfg_path = 'sites/common_site_config.json'
cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
cfg.update({
  'redis_cache':    'redis://' + os.environ.get('REDIS_CACHE',    'redis-cache:6379'),
  'redis_queue':    'redis://' + os.environ.get('REDIS_QUEUE',    'redis-queue:6379'),
  'redis_socketio': 'redis://' + os.environ.get('REDIS_SOCKETIO', 'redis-socketio:6379'),
  'db_host': os.environ.get('DB_HOST', 'db'),
  'db_port': int(os.environ.get('DB_PORT', 3306)),
})
json.dump(cfg, open(cfg_path, 'w'), indent=1)
"

echo "[docker-start] Waiting for database..."
SITE="${FRAPPE_SITE_NAME:-mysite.local}"
until bench --site "$SITE" execute frappe.ping >/dev/null 2>&1; do
    sleep 3
done

# PDF generation (training certificates, print formats) runs wkhtmltopdf inside
# this container. It fetches page assets over HTTP via get_url(); without a
# reachable host_name that resolves to the internal web server, the fetch fails
# and (with unpatched wkhtmltopdf) the whole PDF errors out. Point host_name at
# the internal address the container can actually reach.
bench --site "$SITE" set-config host_name "http://localhost:8000" >/dev/null 2>&1 || true

# Rebuild frontend assets if the dist bundles are missing (lost on recreate).
if [ -z "$(ls -A apps/frappe/frappe/public/dist/js 2>/dev/null)" ]; then
    echo "[docker-start] Frontend assets missing - running bench build (this can take a few minutes)..."
    bench build
else
    echo "[docker-start] Frontend assets present - skipping build."
fi

# The bundled Procfile has no 'web' process, so bench start never serves the site.
# Prepend a web entry (idempotent) so bench start brings up gunicorn/serve too.
if ! grep -q '^web:' Procfile; then
    echo "[docker-start] Adding missing 'web' entry to Procfile."
    printf 'web: bench serve --port 8000\n\n%s' "$(cat Procfile)" > Procfile.tmp
    mv Procfile.tmp Procfile
fi

echo "[docker-start] Starting Frappe stack (web + socketio + worker + schedule + watch)..."
exec bench start
