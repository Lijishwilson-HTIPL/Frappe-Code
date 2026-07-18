#!/bin/bash
# Startup script for the Frappe container.
#
# Fixes the recurring blank-page problem: the base image idles (tail -f /dev/null)
# and never starts the web server, and the built JS assets live inside the
# container filesystem (not a volume) so they are wiped whenever the container is
# recreated. This script rebuilds assets when missing and starts the full stack.
set -e
cd /home/frappe/frappe-bench

echo "[docker-start] Waiting for database..."
until bench --site "${FRAPPE_SITE_NAME:-mysite.local}" execute frappe.ping >/dev/null 2>&1; do
    sleep 3
done

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
