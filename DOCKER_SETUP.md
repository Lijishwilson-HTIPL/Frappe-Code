# Running with Docker

## Prerequisites
- Docker Desktop installed
- Docker Compose v2+

## Steps

### 1. Build and start
```bash
docker compose up -d --build
```
> First build takes ~10–15 minutes (downloads Frappe, ERPNext, CRM, HRMS).

### 2. Create a new site
```bash
docker compose exec frappe bash
# Inside the container:
bench new-site mysite.local \
  --mariadb-root-password root \
  --admin-password admin \
  --db-host db
bench --site mysite.local install-app erpnext
bench --site mysite.local install-app crm
bench --site mysite.local install-app hrms
bench --site mysite.local set-config host_name "http://localhost:8000"
```

### 3. Open in browser
```
http://localhost:8000
Username: Administrator
Password: admin
```

## Stop / restart
```bash
docker compose down       # stop
docker compose up -d      # start again (data is preserved in volumes)
docker compose down -v    # ⚠ stop AND delete all data
```
