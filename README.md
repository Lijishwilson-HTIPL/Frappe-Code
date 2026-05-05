# Hephzibah Technologies — Frappe Bench

This repository contains the full Frappe/ERPNext bench for Hephzibah Technologies, including customisations to ERPNext and HRMS that power the public website's Careers module.

---

## What's Inside

| App | Source | Purpose |
|-----|--------|---------|
| `frappe` | frappe/frappe v15 | Framework |
| `erpnext` | corporaterulers/erpnext | ERP + Career Inquiry DocType |
| `hrms` | corporaterulers/hrms | HR module with native Job Applicant career fields |
| `crm` | frappe/crm | CRM module |

### Key customisations
- **Career Inquiry** (`erpnext/setup/doctype/career_inquiry`) — tracks every website application; gains a `job_applicant_ref` Link field so role-specific submissions link back to the Job Applicant record.
- **Job Applicant** (`hrms`) — extended with native Career Inquiry fields: `role_applying_for`, `years_of_experience`, `linkedin_profile_url`, `portfolio_site`, `how_did_you_hear`, `other_source`.

---

## Prerequisites

Install these on the server before cloning.

| Dependency | Required version |
|-----------|-----------------|
| Python | 3.10+ |
| Node.js | 18+ (20 recommended) |
| npm | 8+ |
| MariaDB | 10.6+ |
| Redis | 6+ |
| git | any recent |

**Ubuntu/Debian one-liner for system packages:**
```bash
sudo apt update && sudo apt install -y git python3 python3-pip python3-venv \
  nodejs npm redis-server mariadb-server mariadb-client \
  libssl-dev libffi-dev libjpeg-dev libxrender1 libxext6 wkhtmltopdf
```

**Install bench CLI:**
```bash
pip3 install frappe-bench
```

---

## First-time Setup (fresh server)

### 1. Clone the repo with submodules

```bash
git clone --recurse-submodules https://github.com/Lijishwilson-HTIPL/Frappe-Code.git frappe-bench
cd frappe-bench
```

### 2. Set up the Python environment

```bash
bench setup env

bench pip install -e apps/frappe
bench pip install -e apps/erpnext
bench pip install -e apps/hrms
bench pip install -e apps/crm
```

### 3. Configure MariaDB

```bash
sudo mysql_secure_installation   # follow prompts, set root password
```

Add this to `/etc/mysql/my.cnf` (or `/etc/mysql/mariadb.conf.d/50-server.cnf`):

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

```bash
sudo systemctl restart mariadb
```

### 4. Create a new site

```bash
bench new-site mysite.local \
  --db-root-password <mariadb-root-password> \
  --admin-password <your-admin-password>
```

### 5. Install all apps on the site

```bash
bench --site mysite.local install-app erpnext
bench --site mysite.local install-app hrms
bench --site mysite.local install-app crm
```

### 6. Run migrations

```bash
bench --site mysite.local migrate
```

### 7. Start the development server

```bash
bench start
```

Access the site at: **http://mysite.local:8000** (or **http://localhost:8000**)

---

## Updating an Existing Bench

When changes are pushed to this repo, pull them down and migrate:

```bash
# Pull latest + update all submodules
git pull
git submodule update --init --recursive

# Apply schema changes to the database
bench --site mysite.local migrate

# Restart services to pick up Python changes
bench restart
```

> **Never skip `git submodule update`** — the app code lives inside the submodule directories. A plain `git pull` only updates the pointer, not the actual files.

---

## Starting & Stopping

```bash
# Start all services (web, workers, redis, scheduler)
bench start

# Stop
Ctrl+C

# Production (supervisor-managed)
sudo bench setup production <your-linux-user>
sudo supervisorctl restart all
```

---

## Useful Commands

```bash
# Open the Frappe console (Python REPL with site context)
bench --site mysite.local console

# Clear cache
bench --site mysite.local clear-cache

# Run a specific patch
bench --site mysite.local run-patch <patch.path>

# View scheduler logs
bench --site mysite.local scheduler-log

# Backup the site database
bench --site mysite.local backup

# Export a DocType to JSON after making UI changes (see rules.md)
bench --site mysite.local export-doc "DocType" "<DocType Name>"
```

---

## Environment Variables

Set these in `sites/mysite.local/site_config.json` (created by `bench new-site`, never committed):

```json
{
  "db_name": "...",
  "db_password": "...",
  "encryption_key": "...",
  "mail_login": "...",
  "mail_password": "...",
  "mail_server": "...",
  "mail_port": 587,
  "use_ssl": 1
}
```

---

## Website Backend Integration

The website (`C:\Users\Lijish\Desktop\Website`) connects to this bench via REST API.

Set the following in the website backend `.env`:

```env
FRAPPE_URL=http://localhost:8000
FRAPPE_API_KEY=<api-key-from-frappe>
FRAPPE_API_SECRET=<api-secret-from-frappe>
```

To generate an API key: Frappe desk → **User** → **API Access** → Generate Keys.

---

## Developer Rules

See [`rules.md`](./rules.md) — all developers must read this before making DocType changes.

The most important rule: **always export a DocType to JSON after changing it in the UI**, otherwise the change lives only in the database and will be lost on the next server deploy.

```bash
bench --site mysite.local export-doc "DocType" "<Name>"
git add apps/<app>/path/to/doctype/<name>.json
git commit -m "..."
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `bench: command not found` | Run `~/.local/bin/bench` or add `~/.local/bin` to `$PATH` |
| Redis connection refused | `redis-server --port 13000 --daemonize yes` (cache) and `redis-server --port 11000 --daemonize yes` (queue) |
| `ModuleNotFoundError` for an app | Run `bench pip install -e apps/<app>` |
| Migrate fails with lock error | `rm -f sites/mysite.local/locks/*.lock` then retry |
| Site not found | `bench --site mysite.local set-config host_name http://localhost:8000` |
| MariaDB `Access denied` | Check `sites/mysite.local/site_config.json` for correct `db_password` |
