<div align="center">

# Hephzibah Technologies — Frappe Bench

**Production Frappe / ERPNext v15 bench — single-repo, all apps tracked directly**

[![Frappe](https://img.shields.io/badge/Frappe-v15-blue?style=flat-square&logo=python)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15-orange?style=flat-square)](https://erpnext.com)
[![HRMS](https://img.shields.io/badge/HRMS-HR-green?style=flat-square)](https://github.com/Lijishwilson-HTIPL/Frappe-Code)
[![CRM](https://img.shields.io/badge/CRM-SBIQ-purple?style=flat-square)](https://github.com/Lijishwilson-HTIPL/Frappe-Code)
[![Helpdesk](https://img.shields.io/badge/Helpdesk-v1.17-blue?style=flat-square)](https://github.com/Lijishwilson-HTIPL/Frappe-Code)

**Repo:** `Lijishwilson-HTIPL/Frappe-Code` · **Branch:** `Lijish-up`

</div>

---

## What's Inside

| App | Folder | Purpose |
|-----|--------|---------|
| Frappe | `apps/frappe` | Core framework (v15) |
| ERP | `apps/erpnext` | ERP — renamed "ERP", custom logo, Career Inquiry DocType |
| HR | `apps/hrms` | HR module — renamed "HR", custom HRv2 logo, Job Applicant extensions |
| SBIQ CRM | `apps/crm` | CRM — SBIQ workspace, Leads Journey, status flow, auto-email on lead |
| Helpdesk | `apps/helpdesk` | Support tickets — Ticket Journey, Ticket Data Tab, custom logo |

> All apps are **plain tracked directories** in this repo — no git submodules. A `git pull` gets everything in one shot.

---

## Key Customisations

### ERP
- App renamed from "ERPNext" to **"ERP"** with custom blue logo
- Career Inquiry DocType — tracks every website job application
- `job_applicant_ref` links speculative applications to HRMS Job Applicant records

### HR
- App renamed from "Frappe HR" to **"HR"** with custom HRv2 logo
- Job Applicant extended with: `role_applying_for`, `years_of_experience`, `linkedin_profile_url`, `portfolio_site`, `how_did_you_hear`, `other_source`

### SBIQ CRM
- Workspace renamed to **SBIQ CRM**
- **Leads Journey** — sidebar page with backend API, dashboard component, qualified count excludes converted leads
- **Status flow** — enforced one-step progression (New → Contacted → Nurture → Qualified → Converted; Unqualified/Junk always available)
- **Lead Data tab** — renamed from "Data" for clarity
- **Export filter** — time range (Today, Last 7/30 Days, This Month, etc.) with dynamic record count
- **Auto-email on lead creation** — when a lead comes in via the website inquiry form (has `website_message` + `email`), a professional follow-up email is automatically sent via `frappe.enqueue` → `send_inquiry_followup()`
- **Royal Purple website theme** fixture

### Helpdesk
- Custom Helpdesk logo
- **Ticket Journey** — `TicketJourney.vue` visualises ticket stage progression
- **Ticket Data Tab** — `TicketDataTab.vue` consolidates ticket detail fields

### Website Integration
- Website discovery call form → Node.js backend → Frappe CRM Lead creation
- Auto-email triggered from `crm_lead.py` `after_insert` — no website backend changes needed

---

## Prerequisites

Install on the server before cloning:

| Dependency | Minimum Version |
|-----------|----------------|
| Python | 3.10+ |
| Node.js | 18+ (20 recommended) |
| npm | 8+ |
| MariaDB | 10.6+ |
| Redis | 6+ |
| git | any recent |
| wkhtmltopdf | 0.12.6+ |

```bash
sudo apt update && sudo apt install -y \
  git python3 python3-pip python3-venv \
  nodejs npm redis-server \
  mariadb-server mariadb-client \
  libssl-dev libffi-dev libjpeg-dev \
  libxrender1 libxext6 wkhtmltopdf

pip3 install frappe-bench
```

---

## First-Time Setup (Fresh Server)

### 1. Clone the repo

```bash
git clone -b Lijish-up https://github.com/Lijishwilson-HTIPL/Frappe-Code.git frappe-bench
cd frappe-bench
```

> No `--recurse-submodules` needed — all apps are plain directories.

---

### 2. Set up Python environment

```bash
bench setup env

bench pip install -e apps/frappe
bench pip install -e apps/erpnext
bench pip install -e apps/hrms
bench pip install -e apps/crm
bench pip install -e apps/helpdesk
```

---

### 3. Configure MariaDB

```bash
sudo mysql_secure_installation
```

Add to `/etc/mysql/mariadb.conf.d/50-server.cnf`:

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

### 4. Create a new site

```bash
bench new-site mysite.local \
  --db-root-password <mariadb-root-password> \
  --admin-password  <your-admin-password>
```

---

### 5. Install apps on the site

```bash
bench --site mysite.local install-app erpnext
bench --site mysite.local install-app hrms
bench --site mysite.local install-app crm
bench --site mysite.local install-app helpdesk
```

---

### 6. Run migrations & build assets

```bash
bench --site mysite.local migrate
bench build --app erpnext --app hrms --app crm --app helpdesk
```

---

### 7. Start the server

```bash
# Development
bench start
```

Open **http://localhost:8000**

**Production:**
```bash
sudo bench setup production <linux-username>
sudo supervisorctl restart all
```

---

## Deploying Updates (Existing Server)

This is the standard deploy sequence every time changes are pushed:

```bash
# 1. Pull latest — gets ALL app code in one pull (no submodule commands needed)
git pull origin Lijish-up

# 2. Apply DocType schema changes
bench --site mysite.local migrate

# 3. Rebuild frontend assets (always run after logo/JS/Vue changes)
bench build --app erpnext --app hrms --app crm --app helpdesk

# 4. Restart services
bench restart
```

> No `git submodule update` needed — apps are plain directories. `git pull` is all you need.

---

## Starting & Stopping

```bash
# Start (development)
bench start

# Stop
Ctrl + C

# Production restart
sudo supervisorctl restart all
```

---

## Useful Admin Commands

| Task | Command |
|------|---------|
| Clear cache | `bench --site mysite.local clear-cache` |
| Backup database | `bench --site mysite.local backup` |
| Open Python console | `bench --site mysite.local console` |
| Run migrations | `bench --site mysite.local migrate` |
| Rebuild all assets | `bench build` |
| Rebuild single app assets | `bench build --app <appname>` |
| Export fixtures | `bench --site mysite.local export-fixtures` |
| List installed apps | `bench --site mysite.local list-apps` |
| View scheduler logs | `tail -f logs/scheduler.log` |
| View error logs | `tail -f logs/worker.error.log` |

---

## Environment / Site Config

`sites/mysite.local/site_config.json` is **never committed** (contains DB credentials). Created automatically by `bench new-site`. To add mail settings:

```json
{
  "db_name": "...",
  "db_password": "...",
  "encryption_key": "...",
  "mail_login": "contact@hephzibahtech.in",
  "mail_password": "...",
  "mail_server": "smtp.example.com",
  "mail_port": 587,
  "use_ssl": 1
}
```

**Website backend `.env`** (`/var/www/html/frappe_backend_staging/.env`):
```env
FRAPPE_URL=http://localhost:8000
FRAPPE_API_KEY=<api-key-from-frappe>
FRAPPE_API_SECRET=<api-secret-from-frappe>
```

To generate API keys: Frappe Desk → Avatar → **My Profile** → **API Access** → **Generate Keys**

> Never regenerate keys unless explicitly needed — always update the website backend `.env` immediately after.

---

## Developer Rules

See [`CLAUDE.md`](./CLAUDE.md) for the full rules. Key points:

1. **All DocType changes go in JSON files** — never edit the database directly
2. After editing a DocType in the Frappe UI, always export:
   ```bash
   bench --site mysite.local export-fixtures   # for CRM layout/fixture changes
   bench --site mysite.local migrate           # after editing JSON files directly
   ```
3. Commit the JSON, then push to `Lijish-up`
4. **Never push directly to `main`**
5. **Always push to** `git push target Lijish-up` (remote: `Lijishwilson-HTIPL/Frappe-Code`)

---

## Repository Structure

```
frappe-bench/
├── apps/
│   ├── frappe/           # Core framework
│   ├── erpnext/          # ERP — custom logo, Career Inquiry DocType
│   ├── hrms/             # HR — custom logo, Job Applicant extensions
│   ├── crm/              # SBIQ CRM — Leads Journey, auto-email, SBIQ workspace
│   └── helpdesk/         # Helpdesk — Ticket Journey, Ticket Data Tab
├── sites/
│   └── mysite.local/     # Site data, uploads (not fully committed)
├── .claude/agents/       # AI agent pipeline (team-lead, developer, tester, release-manager)
├── CLAUDE.md             # Developer rules
├── CHANGELOG_DRAFT.md    # Release changelog
└── README.md
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `bench: command not found` | Add `~/.local/bin` to `$PATH` or use `~/.local/bin/bench` |
| Redis connection refused | `redis-server --port 13000 --daemonize yes` (cache) · `redis-server --port 11000 --daemonize yes` (queue) |
| `ModuleNotFoundError` for an app | `bench pip install -e apps/<appname>` |
| Migrate fails — lock error | `rm -f sites/mysite.local/locks/*.lock` then retry |
| Site not found in browser | `bench --site mysite.local set-config host_name http://localhost:8000` |
| MariaDB access denied | Check `sites/mysite.local/site_config.json` for correct `db_password` |
| Logo not updating after pull | Run `bench build --app <appname>` then hard-refresh browser (Ctrl+Shift+R) |
| Auto-email not sending | Check outgoing email account is configured in Frappe → Email Settings and `enable_outgoing` is checked |
| Assets out of date after deploy | Always run `bench build` after every pull |

---

<div align="center">

Maintained by **Hephzibah Technologies** · [hephzibahtech.in](https://hephzibahtech.in)

</div>
