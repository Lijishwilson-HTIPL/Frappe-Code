# Docker Setup — Hephzibah Technologies Frappe Bench

## Prerequisites
- Docker Desktop installed and running
- Docker Compose v2+
- Internet connection (pulls repo and images on first build)

---

## First-Time Setup

### 1. Build and start all services

```bash
docker compose up -d --build
```

> First build takes **15–20 minutes** — it clones `Lijishwilson-HTIPL/Frappe-Code` (branch `Lijish-up`) and installs all apps. Subsequent starts are fast.

---

### 2. Create the site and install apps

```bash
docker compose exec frappe bash
```

Inside the container:

```bash
bench new-site mysite.local \
  --mariadb-root-password root \
  --admin-password admin \
  --db-host db

bench --site mysite.local install-app erpnext
bench --site mysite.local install-app hrms
bench --site mysite.local install-app crm
bench --site mysite.local install-app helpdesk

bench --site mysite.local migrate
bench build --app erpnext --app hrms --app crm --app helpdesk

bench --site mysite.local set-config host_name "http://localhost:8000"
exit
```

---

### 3. Open in browser

```
http://localhost:8000
Username: Administrator
Password: admin
```

---

## Deploying Updates

When new changes are pushed to `Lijish-up`, rebuild and restart:

```bash
# Rebuild the image with latest code
docker compose up -d --build

# Run inside the container to apply schema and asset changes
docker compose exec frappe bash -c "
  bench --site mysite.local migrate &&
  bench build --app erpnext --app hrms --app crm --app helpdesk
"
```

> No `git submodule update` needed — all apps are plain directories in the repo.

---

## Stop / Restart

```bash
docker compose down          # stop containers (data preserved)
docker compose up -d         # start again
docker compose down -v       # stop AND wipe all data (fresh start)
```

---

## Useful Commands Inside the Container

```bash
docker compose exec frappe bash   # open a shell

# Then inside:
bench --site mysite.local list-apps
bench --site mysite.local clear-cache
bench --site mysite.local backup
bench --site mysite.local console
tail -f logs/worker.error.log
```

---

## Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| `frappe` | 8000 (web), 9000 (socketio) | Frappe/ERPNext app server |
| `db` | internal | MariaDB 10.6 |
| `redis-cache` | internal | Page and doctype cache |
| `redis-queue` | internal | Background job queue (auto-email, etc.) |
| `redis-socketio` | internal | Realtime events |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Build fails on `yarn install` | Run `docker compose build --no-cache` |
| Site not found after container restart | Volume `frappe_sites` is persisted — run `bench --site mysite.local migrate` if schema changed |
| Auto-email not sending | Configure outgoing email in Frappe → Email Settings inside the container |
| Logo not showing after update | Run `bench build --app <appname>` inside container, then hard-refresh browser |
| MariaDB connection refused | Wait for `db` healthcheck to pass — check with `docker compose ps` |
| `bench: command not found` in container | Run as the `frappe` user: `docker compose exec --user frappe frappe bash` |
