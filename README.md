<div align="center">

# 🏗️ Hephzibah Technologies — Frappe Bench

**Production-grade Frappe / ERPNext v15 bench powering the Hephzibah Technologies platform**

[![Frappe](https://img.shields.io/badge/Frappe-v15-blue?style=flat-square&logo=python)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15-orange?style=flat-square)](https://erpnext.com)
[![HRMS](https://img.shields.io/badge/HRMS-corporaterulers-green?style=flat-square)](https://github.com/corporaterulers/hrms)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square&logo=python)](https://python.org)
[![MariaDB](https://img.shields.io/badge/MariaDB-10.6+-brown?style=flat-square&logo=mariadb)](https://mariadb.org)

</div>

---

## 📦 What's Inside

| App | Fork / Source | Purpose |
|-----|--------------|---------|
| `frappe` | corporaterulers/frappe | Core framework |
| `erpnext` | corporaterulers/erpnext | ERP + **Career Inquiry** DocType |
| `hrms` | corporaterulers/hrms | HR module with native Job Applicant career fields |
| `crm` | frappe/crm | CRM module |

### ✨ Key Customisations

- **Career Inquiry** — tracks every website job application; `job_applicant_ref` Link field connects speculative and role-specific applications back to HRMS Job Applicant records.
- **Job Applicant** — extended with native career fields: `role_applying_for`, `years_of_experience`, `linkedin_profile_url`, `portfolio_site`, `how_did_you_hear`, `other_source`.
- **Website Integration** — the public careers page reads live Job Opening records (title, HTML description, salary range gated by `publish_salary_range`), and form submissions create both a Job Applicant and a Career Inquiry atomically.

---

## 🖥️ Prerequisites

> Install the following on the server **before** cloning.

| Dependency | Minimum Version |
|-----------|----------------|
| Python | 3.10+ |
| Node.js | 18+ (20 recommended) |
| npm | 8+ |
| MariaDB | 10.6+ |
| Redis | 6+ |
| git | any recent |
| wkhtmltopdf | 0.12.6+ |

**Ubuntu / Debian — install everything in one shot:**

```bash
sudo apt update && sudo apt install -y \
  git python3 python3-pip python3-venv \
  nodejs npm redis-server \
  mariadb-server mariadb-client \
  libssl-dev libffi-dev libjpeg-dev \
  libxrender1 libxext6 wkhtmltopdf
```

**Install the Bench CLI:**

```bash
pip3 install frappe-bench
```

---

## 🚀 First-Time Setup (Fresh Server)

### Step 1 — Clone with submodules

```bash
git clone --recurse-submodules https://github.com/Lijishwilson-HTIPL/Frappe-Code.git frappe-bench
cd frappe-bench
```

> ⚠️ The `--recurse-submodules` flag is **required**. Without it the `apps/` directories will be empty.

---

### Step 2 — Set up the Python environment

```bash
bench setup env

bench pip install -e apps/frappe
bench pip install -e apps/erpnext
bench pip install -e apps/hrms
bench pip install -e apps/crm
```

---

### Step 3 — Configure MariaDB

```bash
sudo mysql_secure_installation   # follow the prompts, set a root password
```

Append the following to `/etc/mysql/mariadb.conf.d/50-server.cnf`:

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server            = utf8mb4
collation-server                = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

```bash
sudo systemctl restart mariadb
```

---

### Step 4 — Create a new site

```bash
bench new-site mysite.local \
  --db-root-password <mariadb-root-password> \
  --admin-password  <your-admin-password>
```

---

### Step 5 — Install apps on the site

```bash
bench --site mysite.local install-app erpnext
bench --site mysite.local install-app hrms
bench --site mysite.local install-app crm
```

---

### Step 6 — Run migrations

```bash
bench --site mysite.local migrate
```

---

### Step 7 — Start the development server

```bash
bench start
```

🌐 Open **http://localhost:8000** in your browser.

---

## 🔄 Updating an Existing Bench

When changes are pushed to this repo, pull and migrate:

```bash
# 1. Pull latest commits AND update all submodule code
git pull
git submodule update --init --recursive

# 2. Apply schema changes to the database
bench --site mysite.local migrate

# 3. Restart all services
bench restart
```

> 🔴 **Never skip `git submodule update`.**
> A plain `git pull` only moves the submodule pointer — the actual app code inside `apps/` stays at the old commit until you run the submodule update.

---

## ▶️ Starting & Stopping

```bash
# Development — starts web, workers, Redis and scheduler together
bench start

# Stop
Ctrl + C
```

**Production (supervisor-managed):**

```bash
sudo bench setup production <your-linux-username>
sudo supervisorctl restart all
```

---

## 🛠️ Useful Commands

| Task | Command |
|------|---------|
| Open Python console | `bench --site mysite.local console` |
| Clear cache | `bench --site mysite.local clear-cache` |
| Backup database | `bench --site mysite.local backup` |
| Export DocType to JSON | `bench --site mysite.local export-doc "DocType" "<Name>"` |
| View scheduler logs | `bench --site mysite.local scheduler-log` |
| Run a specific patch | `bench --site mysite.local run-patch <patch.path>` |
| Rebuild assets | `bench build` |

---

## 🔑 Environment / Site Config

`sites/mysite.local/site_config.json` is **never committed** (it contains DB credentials and encryption keys). It is created automatically by `bench new-site`. To add mail settings, edit it directly:

```json
{
  "db_name": "...",
  "db_password": "...",
  "encryption_key": "...",
  "mail_login": "your@email.com",
  "mail_password": "...",
  "mail_server": "smtp.example.com",
  "mail_port": 587,
  "use_ssl": 1
}
```

---

## 🌐 Website Backend Integration

The Hephzibah Technologies website (`Website/Backend`) connects to this bench via the Frappe REST API.

Set the following in the website backend `.env`:

```env
FRAPPE_URL=http://localhost:8000
FRAPPE_API_KEY=<api-key-from-frappe>
FRAPPE_API_SECRET=<api-secret-from-frappe>
```

**To generate API keys:**
Frappe Desk → top-right avatar → **My Profile** → **API Access** → **Generate Keys**

---

## 📐 Developer Rules

> See [`rules.md`](./rules.md) — read before making any DocType changes.

**The golden rule:** always export a DocType to JSON after editing it in the Frappe UI. Changes made only in the UI live in the database and will be **lost** on the next server deploy.

```bash
# After editing a DocType in the desk UI:
bench --site mysite.local export-doc "DocType" "<Name>"

# Then commit the updated JSON:
git add apps/<app>/path/to/doctype/<name>.json
git commit -m "feat: update <DocType> — <what changed>"
git push
```

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `bench: command not found` | Use `~/.local/bin/bench` or add `~/.local/bin` to `$PATH` |
| Redis connection refused | `redis-server --port 13000 --daemonize yes` (cache) and `redis-server --port 11000 --daemonize yes` (queue) |
| `ModuleNotFoundError` for an app | `bench pip install -e apps/<app>` |
| Migrate fails — lock error | `rm -f sites/mysite.local/locks/*.lock` then retry |
| Site not found in browser | `bench --site mysite.local set-config host_name http://localhost:8000` |
| MariaDB `Access denied` | Check `sites/mysite.local/site_config.json` for correct `db_password` |
| Submodule directory is empty | `git submodule update --init --recursive` |
| Python venv broken after copy | `bench setup env` then re-install all apps with `bench pip install -e` |

---

## 📁 Repository Structure

```
frappe-bench/
├── apps/
│   ├── frappe/          # Core framework (submodule)
│   ├── erpnext/         # ERP + Career Inquiry (submodule — corporaterulers fork)
│   ├── hrms/            # HR module (submodule — corporaterulers fork)
│   └── crm/             # CRM module (submodule)
├── sites/
│   └── mysite.local/    # Site data, uploads, private files (not fully committed)
├── config/              # Procfile, Redis configs
├── rules.md             # Developer DocType change rules
└── README.md
```

---

<div align="center">

Maintained by **Hephzibah Technologies** · [hephzibahtech.in](https://hephzibahtech.in)

</div>
