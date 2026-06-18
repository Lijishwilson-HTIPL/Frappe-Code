# SBIQ Provisioner v2 — Design Spec
**Date:** 2026-06-12  
**Status:** Approved  
**Scope:** Full rebuild of the sbiqc_provisioning dashboard + engine enhancements, installed on mysite.local as the dev control plane.

---

## 1. Goals

1. Install `sbiqc_provisioning` on `mysite.local` so developers provision client sites (`client.localhost`, `acme.localhost`, etc.) from the dev environment.
2. Replace the existing tab-based dashboard page with a sidebar-navigation layout (5 sections).
3. Theme via Frappe's native theme switcher (SBIQ Core, Frappe Light, Timeless Night) — CSS variables only, no hardcoded colours.
4. New Tenant creation via a 3-step wizard inside the dashboard.
5. Post-provisioning app updates: add more apps to an already-Active tenant.
6. Five sidebar sections: Tenants, Queue, Health, Reports, Errors.
7. Fix known bugs: command injection in `delete_tenant`, hardcoded seeder values, `serve_default_site` misconfiguration.

---

## 2. Architecture

### 2.1 Control Plane

`mysite.local` is the control plane site. `sbiqc_provisioning` is installed on it and only it. Client sites (`*.localhost`) are provisioned by the engine and live on the same bench — they do **not** have `sbiqc_provisioning` installed.

```
Browser → mysite.local:8000/app/sbiqc-provisioning
              │
              ▼
         sbiqc_provisioning Page
              │
              ├── frappe.enqueue → long worker
              │         │
              │         ▼
              │    engine.provision_tenant(tenant_name)
              │    engine.provision_update(tenant_name, new_apps)  [NEW]
              │         │
              │         ├── bench new-site client.localhost
              │         ├── bench install-app …
              │         ├── seeder.seed_tenant(…)
              │         └── /etc/hosts + Windows hosts update
              │
              └── Provisioning Log (progress tracking)
```

### 2.2 Multi-site Routing Fix

`sites/common_site_config.json` must have:
```json
"serve_default_site": false
```
Frappe routes requests by the `Host` header. With this set, an unknown hostname returns a 404 instead of accidentally serving another site. **Never set `default_site` in this file** (see CLAUDE.md §3b).

### 2.3 Installation Steps (one-time)

```bash
bench --site mysite.local install-app sbiqc_provisioning
bench --site mysite.local migrate
bench build --app sbiqc_provisioning
bench restart
```

---

## 3. Dashboard Shell

### 3.1 Layout

```
┌─────────────┬────────────────────────────────────────────┐
│  SIDEBAR    │  TOPBAR (section title + context actions)  │
│  ─────────  ├────────────────────────────────────────────┤
│  Tenants ◀  │  KPI strip (4 stat cards)                  │
│  Queue  [N] │  ────────────────────────────────────────  │
│  Health     │  Toolbar (search + filter chips)           │
│  Reports    │  ────────────────────────────────────────  │
│  Errors [N] │  Content panel (swaps per nav item)        │
│             │                                            │
│  ─────────  │                                            │
│  ● Local Dev│                                            │
└─────────────┴────────────────────────────────────────────┘
```

- Sidebar width: 170px, fixed.
- Content panel: `flex: 1`, scrollable.
- Active nav item: left border in `var(--primary)`, background `color-mix(in srgb, var(--primary) 12%, transparent)`.
- Badge count on Queue and Errors nav items — live-updated from `get_provisioning_stats()`.
- Bottom chip shows "Local Dev" (`is_production: false`) or "Production" (`is_production: true`).

### 3.2 Theme

All colours use **Frappe native CSS variables** only:

| Variable | Usage |
|---|---|
| `var(--bg-color)` | Page and sidebar background |
| `var(--card-bg)` | Table rows, KPI cards, form panels |
| `var(--border-color)` | All borders |
| `var(--text-color)` | Primary text |
| `var(--text-muted)` | Secondary/metadata text |
| `var(--primary)` | Active nav, buttons, badges |
| `var(--sidebar-select-color)` | Sidebar active item background (fallback: primary 12%) |

No `!important` overrides, no hardcoded hex values. Works with SBIQ Core, Frappe Light, Timeless Night, Automatic, and any future theme automatically.

---

## 4. Section: Tenants

### 4.1 Table Columns

| Column | Content |
|---|---|
| Tenant | Client name (bold) + subdomain + time-ago |
| Site | Clickable link if Active, muted text otherwise + DB name below |
| Plan | Colour-coded pill (Starter grey, Standard indigo, Enterprise violet) |
| Status | Colour-coded badge |
| Actions | Context-aware icon buttons (see below) |

### 4.2 Action Buttons Per Row

| Status | Buttons |
|---|---|
| Active | ↗ Open Site · ⏸ Suspend · ⊕ Add Apps · 🗑 Delete |
| Provisioning | ≡ View Log |
| Error | ↺ Retry · 🗑 Delete |
| Suspended | ▶ Resume · 🗑 Delete |
| Pending | 🗑 Delete |

### 4.3 Pagination

`get_provisioning_stats()` gains `offset` (default 0) and `limit` (default 20) parameters. Dashboard shows a "Load More" button when the returned list equals `limit`. No full-page reload — appends rows to the existing table.

### 4.4 Filter Chips

All · Active · Running · Pending · Suspended · Error (was missing Suspended)

### 4.5 Auto-refresh

Every 15 seconds when `Provisioning > 0 OR Pending > 0` (current behaviour, keep).

---

## 5. Section: New Tenant (3-Step Wizard)

Clicking "+ New Tenant" replaces the main content panel with the wizard. The sidebar remains visible. Cancel returns to the Tenants list.

### Step 1 — Identity

| Field | Validation |
|---|---|
| Subdomain | `^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$`, live preview shows `subdomain.localhost` |
| Client Name | Required |
| Admin Email | Email format, used to create admin user on tenant site |
| Plan | Select: Starter / Standard / Enterprise |
| Currency | Select: INR (default) / USD / EUR / GBP |
| Timezone | Select: Asia/Kolkata (default) + common options |

### Step 2 — Apps

- Loads `get_installable_apps()` dynamically.
- Visual toggle cards (checked = install).
- ERPNext pre-checked and locked (cannot uncheck).
- No install time estimates in v2 — future enhancement.

### Step 3 — Confirm

- Summary of all Step 1 + Step 2 selections.
- "Provision →" button: saves Tenant doc via `frappe.call`, submits it, redirects to Tenants list.
- New tenant row appears immediately in "Pending" state, transitions to "Provisioning" on next refresh.

### New DocType Fields

Add to `Tenant` DocType JSON:

```json
{ "fieldname": "currency", "fieldtype": "Select", "label": "Currency",
  "options": "INR\nUSD\nEUR\nGBP", "default": "INR" },
{ "fieldname": "timezone", "fieldtype": "Select", "label": "Timezone",
  "options": "Asia/Kolkata\nUTC\nAmerica/New_York\nEurope/London\nAsia/Dubai",
  "default": "Asia/Kolkata" }
```

Both fields passed to `seeder.seed_tenant()` instead of the current hardcoded values.

---

## 6. Section: Add Apps (Post-Provisioning)

### 6.1 UI Flow

1. Click ⊕ on an Active tenant row → slideout opens from the right.
2. Slideout shows two groups:
   - **Installed** (greyed out, checkmark shown) — from `bench list-apps` on the tenant site.
   - **Available** (selectable toggles) — from `get_installable_apps()` minus installed.
3. "Install Selected" button triggers `provision_update`.

### 6.2 New Engine Function

New function `provision_update(tenant_name, apps_to_add)` in `engine.py`:

```
1. Fetch Tenant doc
2. Create Provisioning Log
3. Clear stale locks
4. For each app in apps_to_add:
     - Skip if already installed
     - bench install-app <app> on tenant site
     - Update Provisioning Log step + progress
5. bench --site <site> migrate  (to apply new app migrations)
6. bench --site <site> clear-cache
7. Update Tenant.apps_to_install child table with new apps
8. Complete Provisioning Log
```

New whitelisted API endpoint `update_tenant_apps(tenant_name, new_apps)` that enqueues `provision_update` on the long queue.

---

## 7. Section: Queue

Enhancements to existing Queue tab (now sidebar section):

- **Live progress bars**: `frappe.realtime.on("progress", handler)` wires Frappe's realtime events to update the progress bar width without a full list reload.
- **Elapsed time**: Running jobs show `started_at → now` in human-readable form.
- **Cancel button** for Queued (not yet Running) jobs: calls `frappe.call` to `cancel_queued_job(log_name)`. The server side calls `frappe.get_doc("RQ Job").cancel()` — Frappe stores RQ job references in `tabRQ Job`; look up by `status="queued"` and matching log reference, then cancel. If the job has already started, the button is disabled (status flips to Running).

---

## 8. Section: Health

### 8.1 New API

New whitelisted function `get_bench_health()` in `tenant.py`:

| Check | Implementation |
|---|---|
| Redis Cache | `redis.Redis.from_url(frappe.conf.redis_cache).ping()` |
| Redis Queue | `redis.Redis.from_url(frappe.conf.redis_queue).ping()` |
| MariaDB | `frappe.db.sql("SELECT 1")` — OK if no exception |
| Long Worker | `rq.Queue("long", connection=...).count` + check worker count |
| Disk Free | `shutil.disk_usage(bench_path).free` — warn if < 5 GB |
| Sites on Bench | Count dirs in `sites/` with `site_config.json` |
| Bench Apps | Read `sites/apps.txt` |

Returns `{"checks": [...], "overall": "ok"|"warn"|"error"}`.

### 8.2 UI

- Grid of check cards: green (OK), amber (warn), red (error).
- Overall status in topbar.
- Auto-refreshes every 30 seconds.
- No action buttons — read-only diagnostic view.

---

## 9. Section: Reports

### 9.1 New API

New whitelisted function `get_provisioning_report()` in `tenant.py`:

- Monthly provisioning counts (last 6 months) — from Provisioning Log `creation`.
- Breakdown by plan — from Tenant `plan` field.
- Average provisioning duration — `completed_at - started_at` for Completed logs.
- Top 5 apps installed — frequency count from `Tenant App` child table.

### 9.2 UI

- CSS bar chart for monthly counts (no external library — pure div widths as percentages).
- Plan breakdown as horizontal stacked bar.
- Duration and top-apps as simple stat cards.
- "Export CSV" button calls `frappe.call` and triggers file download.

---

## 10. Section: Errors

- Filtered tenant list: `status = "Error"` only.
- Each row shows tenant name, site, last error step (from latest Provisioning Log `current_step`), time of failure.
- "▶ View Traceback" expands an inline code block with `error_traceback` from the Provisioning Log.
- "↺ Retry" re-submits provisioning via `on_submit` equivalent call.
- Badge count on sidebar nav item matches `get_provisioning_stats().Error`.

---

## 11. Bug Fixes

### 11.1 Command Injection in `delete_tenant` (Critical)

**File:** `sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py:165`

Replace:
```python
subprocess.run(
    f"bench drop-site {site_name} --db-root-password {db_root_password} --no-backup",
    shell=True, ...
)
```
With:
```python
subprocess.run(
    ["bench", "drop-site", site_name,
     "--db-root-password", db_root_password, "--no-backup"],
    shell=False, ...
)
```

### 11.2 Seeder — Use Tenant Fields

`seeder.seed_tenant()` signature changes to:
```python
def seed_tenant(site_name, client_name, plan, currency="INR", timezone="Asia/Kolkata"):
```
Engine passes `tenant.currency` and `tenant.timezone` instead of hardcoded values.

### 11.3 Seeder — Create Admin User

After branding, if `admin_email` is set on the Tenant doc, run a Python script in the tenant site context:
```python
script = (
    "import frappe;"
    f"frappe.init(site={safe_site});"
    "frappe.connect();"
    "if not frappe.db.exists('User', {safe_email}):"
    "  u = frappe.new_doc('User');"
    "  u.email = {safe_email}; u.first_name = 'Admin'; u.send_welcome_email = 0;"
    "  u.add_roles('System Manager'); u.save(ignore_permissions=True);"
    "frappe.db.commit(); frappe.destroy()"
)
```
Executed via `python -c script` in the bench env (same pattern as `_set_site_branding` in `seeder.py`). Skipped if `admin_email` is blank.

### 11.4 Multi-site Routing

`sites/common_site_config.json`:
```json
"serve_default_site": false
```

---

## 12. Files Changed / Created

| File | Change |
|---|---|
| `sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.json` | Add `currency`, `timezone` fields |
| `sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py` | Fix `delete_tenant` injection; add `get_bench_health`, `get_provisioning_report`, `update_tenant_apps` |
| `sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.js` | Remove (replaced by dashboard page JS) |
| `sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.html` | Rebuild as sidebar shell |
| `sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.js` | Full rewrite: SBIQCProvisioning class with 5 sections, wizard, add-apps slideout, realtime |
| `sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.css` | New: CSS-variable-only styles for sidebar layout |
| `sbiqc_provisioning/sbiqc_provisioning/hooks.py` | Add CSS include for new page CSS |
| `sbiqc_provisioning/provisioner/engine.py` | Add `provision_update()` function |
| `sbiqc_provisioning/provisioner/seeder.py` | Accept `currency`, `timezone`; create admin user |
| `sites/common_site_config.json` | `serve_default_site: false` — **not committed** (machine-specific) |

---

## 13. Out of Scope (v2)

- Production Nginx routing (`_setup_production_routing` remains stub).
- Email notifications on provision complete/fail.
- Role-based access beyond System Manager.
- Multi-bench support.
