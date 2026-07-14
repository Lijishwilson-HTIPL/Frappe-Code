# SBIQ Provisioner v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the SBIQ Provisioner dashboard with a sidebar-navigation layout (5 sections), 3-step new-tenant wizard, post-provisioning app updates, Frappe-theme-aware CSS, and install it on mysite.local as the dev control plane.

**Architecture:** The `sbiqc_provisioning` Frappe app is installed on `mysite.local` only. The Page `sbiqc-provisioning` is rebuilt as a sidebar shell with five swappable content sections rendered in pure JS. All backend APIs live in `tenant.py` as `@frappe.whitelist()` functions. The engine gains a new `provision_update()` function for post-provisioning app installs.

**Tech Stack:** Frappe v15, Python 3.10, MariaDB, RQ (Redis Queue), plain JS (no frameworks), Frappe CSS variables for theming.

**App path:** `apps/sbiqc_provisioning/sbiqc_provisioning/`  
**All paths below are relative to the bench root** `~/frappe-bench/` unless stated otherwise.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.json` | Modify | Add `currency`, `timezone` fields |
| `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py` | Modify | Fix injection bug; add `get_bench_health`, `get_provisioning_report`, `update_tenant_apps`, `cancel_queued_job` |
| `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.js` | Delete | Replaced by page JS |
| `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.html` | Rewrite | Sidebar shell HTML only |
| `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.js` | Rewrite | Full dashboard controller |
| `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.css` | Create | All CSS using Frappe variables only |
| `apps/sbiqc_provisioning/sbiqc_provisioning/hooks.py` | Modify | Include page CSS |
| `apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/engine.py` | Modify | Add `provision_update()` |
| `apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/seeder.py` | Modify | Accept currency/timezone; create admin user |

---

## Task 1: Fix command injection bug in `delete_tenant`

**Files:**
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py`

- [ ] **Step 1: Open the file and locate the bug**

  Open `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py`.  
  Find the `delete_tenant` function (around line 150). It contains:
  ```python
  subprocess.run(
      f"bench drop-site {site_name} --db-root-password {db_root_password} --no-backup",
      shell=True, cwd=bench_path,
      capture_output=True, text=True, timeout=120,
  )
  ```

- [ ] **Step 2: Replace with safe argv list form**

  Replace that `subprocess.run` call with:
  ```python
  subprocess.run(
      ["bench", "drop-site", site_name,
       "--db-root-password", db_root_password, "--no-backup"],
      shell=False, cwd=bench_path,
      capture_output=True, text=True, timeout=120,
  )
  ```

- [ ] **Step 3: Commit**

  ```bash
  cd ~/frappe-bench
  git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py
  git commit -m "fix(provisioner): remove shell=True command injection in delete_tenant"
  ```

---

## Task 2: Add `currency` and `timezone` fields to Tenant DocType

**Files:**
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.json`

- [ ] **Step 1: Add fields to `field_order`**

  In `tenant.json`, find `"field_order"` array. Insert `"currency"` and `"timezone"` after `"plan"`:
  ```json
  "field_order": [
    "subdomain",
    "client_name",
    "plan",
    "currency",
    "timezone",
    "admin_email",
    ...
  ]
  ```

- [ ] **Step 2: Add field definitions to `fields` array**

  In the `"fields"` array, after the `plan` field object, insert:
  ```json
  {
    "fieldname": "currency",
    "fieldtype": "Select",
    "label": "Currency",
    "options": "INR\nUSD\nEUR\nGBP",
    "default": "INR",
    "in_list_view": 0
  },
  {
    "fieldname": "timezone",
    "fieldtype": "Select",
    "label": "Timezone",
    "options": "Asia/Kolkata\nUTC\nAmerica/New_York\nEurope/London\nAsia/Dubai",
    "default": "Asia/Kolkata",
    "in_list_view": 0
  },
  ```

- [ ] **Step 3: Update `modified` timestamp**

  Change `"modified"` in `tenant.json` to `"2026-06-12 12:00:00.000000"`.

- [ ] **Step 4: Run migration**

  ```bash
  cd ~/frappe-bench
  bench --site mysite.local migrate
  ```
  Expected: migration runs without errors, no output about missing columns.

- [ ] **Step 5: Verify fields exist**

  ```bash
  bench --site mysite.local execute frappe.db.get_value \
    --args "['DocType','Tenant','name']"
  ```
  Then open `mysite.local:8000/app/tenant/new-tenant-1` and confirm Currency and Timezone dropdowns appear.

- [ ] **Step 6: Commit**

  ```bash
  git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.json
  git commit -m "feat(tenant): add currency and timezone fields"
  ```

---

## Task 3: Update `seeder.py` — currency, timezone, admin user creation

**Files:**
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/seeder.py`

- [ ] **Step 1: Update `seed_tenant` signature and setup_data**

  Replace the entire `seed_tenant` function with:
  ```python
  def seed_tenant(site_name, client_name, plan="Starter", currency="INR", timezone="Asia/Kolkata", admin_email=None):
      bench_path = frappe.utils.get_bench_path()
      bench_cmd = shutil.which("bench") or "bench"

      setup_data = {
          "app_name": client_name,
          "company_name": client_name,
          "company_abbr": _abbreviate(client_name),
          "currency": currency,
          "timezone": timezone,
          "country": "India",
      }

      for key, val in setup_data.items():
          _run(
              [bench_cmd, "--site", site_name, "set-config", key, str(val)],
              cwd=bench_path,
          )

      _set_site_branding(site_name, client_name, bench_path)

      if admin_email:
          _create_admin_user(site_name, admin_email, bench_path)
  ```

- [ ] **Step 2: Add `_create_admin_user` function**

  Add this function after `_set_site_branding`:
  ```python
  def _create_admin_user(site_name, admin_email, bench_path):
      """Create a System Manager user on the tenant site with the given email."""
      import json as _json
      safe_site = _json.dumps(site_name)
      safe_email = _json.dumps(admin_email)
      script = (
          "import frappe;"
          f"frappe.init(site={safe_site});"
          "frappe.connect();"
          f"em={safe_email};"
          "u=frappe.db.exists('User',em);"
          "( None if u else ("
          "  frappe.get_doc({"
          "    'doctype':'User','email':em,'first_name':'Admin',"
          "    'send_welcome_email':0,'user_type':'System User'"
          "  }).insert(ignore_permissions=True),"
          f"  frappe.get_doc('User',em).add_roles('System Manager')"
          ") );"
          "frappe.db.commit();frappe.destroy()"
      )
      python = os.path.join(bench_path, "env", "bin", "python")
      _run(
          [python, "-c", script],
          cwd=os.path.join(bench_path, "sites"),
      )
  ```

- [ ] **Step 3: Update `engine.py` to pass new seeder args**

  Open `apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/engine.py`.  
  Find the `seed_tenant` call (around line 83) and replace:
  ```python
  seed_tenant(
      site_name=site_name,
      client_name=tenant.client_name,
      plan=tenant.plan,
  )
  ```
  With:
  ```python
  seed_tenant(
      site_name=site_name,
      client_name=tenant.client_name,
      plan=tenant.plan,
      currency=getattr(tenant, "currency", "INR") or "INR",
      timezone=getattr(tenant, "timezone", "Asia/Kolkata") or "Asia/Kolkata",
      admin_email=getattr(tenant, "admin_email", None) or None,
  )
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/seeder.py \
          apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/engine.py
  git commit -m "feat(seeder): pass currency/timezone from tenant; create admin user"
  ```

---

## Task 4: Add `provision_update()` to engine.py

**Files:**
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/engine.py`

- [ ] **Step 1: Add the function at the end of `engine.py`**

  Append to `apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/engine.py`:
  ```python
  def provision_update(tenant_name, apps_to_add):
      """Install additional apps on an already-Active tenant site."""
      frappe.init(site=frappe.local.site)
      frappe.connect()

      tenant = frappe.get_doc("Tenant", tenant_name)
      bench_path = frappe.utils.get_bench_path()
      site_name = tenant.site_name

      log_name = create_log(tenant_name, site_name)
      _update_status(tenant, "Provisioning")
      update_log_step(log_name, "Starting app update", 5)

      try:
          _clear_stale_locks(site_name, bench_path)
          already_installed = _get_installed_apps(site_name, bench_path)
          to_install = [a for a in apps_to_add if a not in already_installed]

          if not to_install:
              update_log_step(log_name, "All requested apps already installed", 80)
          else:
              for i, app in enumerate(to_install):
                  pct = 10 + int((i + 1) / len(to_install) * 60)
                  update_log_step(log_name, f"Installing {app}", pct)
                  _install_app(site_name, app, bench_path)

          update_log_step(log_name, "Running migrations", 80)
          _run(["bench", "--site", site_name, "migrate"], cwd=bench_path, timeout=300)

          update_log_step(log_name, "Clearing cache", 92)
          _run(["bench", "--site", site_name, "clear-cache"], cwd=bench_path)

          # Append new apps to Tenant.apps_to_install child table
          tenant.reload()
          existing_apps = {row.app_name for row in tenant.apps_to_install}
          for app in to_install:
              if app not in existing_apps:
                  frappe.db.insert({
                      "doctype": "Tenant App",
                      "parent": tenant.name,
                      "parenttype": "Tenant",
                      "parentfield": "apps_to_install",
                      "app_name": app,
                  })
          frappe.db.commit()

          _update_status(tenant, "Active")
          complete_log(log_name)

      except Exception:
          import traceback as _tb
          tb = _tb.format_exc()
          _update_status(tenant, "Error")
          tenant.reload()
          tenant.db_set("error_log", tb[:10000])
          frappe.db.commit()
          frappe.log_error(title=f"App update failed: {tenant_name}", message=tb)
          complete_log(log_name, failed=True, error=tb)
          raise
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add apps/sbiqc_provisioning/sbiqc_provisioning/provisioner/engine.py
  git commit -m "feat(engine): add provision_update for post-provisioning app installs"
  ```

---

## Task 5: Add new API functions to `tenant.py`

**Files:**
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py`

- [ ] **Step 1: Add required imports at the top of `tenant.py`**

  After the existing imports, ensure these are present:
  ```python
  import json
  import shutil
  ```

- [ ] **Step 2: Add `update_tenant_apps` whitelist function**

  Append to `tenant.py`:
  ```python
  @frappe.whitelist()
  def update_tenant_apps(tenant_name, new_apps):
      """Queue a provision_update job to install additional apps on an Active tenant."""
      frappe.only_for("System Manager")
      if isinstance(new_apps, str):
          new_apps = json.loads(new_apps)
      frappe.enqueue(
          "sbiqc_provisioning.provisioner.engine.provision_update",
          tenant_name=tenant_name,
          apps_to_add=new_apps,
          queue="long",
          timeout=1800,
          now=frappe.flags.in_test,
      )
      return {"status": "queued", "apps": new_apps}
  ```

- [ ] **Step 3: Add `get_bench_health` whitelist function**

  Append to `tenant.py`:
  ```python
  @frappe.whitelist()
  def get_bench_health():
      """Return health status of bench services."""
      import redis as _redis
      frappe.only_for("System Manager")
      bench_path = frappe.utils.get_bench_path()
      checks = []

      # Redis Cache
      try:
          _redis.Redis.from_url(frappe.conf.get("redis_cache", "redis://127.0.0.1:13000")).ping()
          checks.append({"name": "Redis Cache", "status": "ok"})
      except Exception as e:
          checks.append({"name": "Redis Cache", "status": "error", "detail": str(e)})

      # Redis Queue
      try:
          _redis.Redis.from_url(frappe.conf.get("redis_queue", "redis://127.0.0.1:11000")).ping()
          checks.append({"name": "Redis Queue", "status": "ok"})
      except Exception as e:
          checks.append({"name": "Redis Queue", "status": "error", "detail": str(e)})

      # MariaDB
      try:
          frappe.db.sql("SELECT 1")
          checks.append({"name": "MariaDB", "status": "ok"})
      except Exception as e:
          checks.append({"name": "MariaDB", "status": "error", "detail": str(e)})

      # Long Worker
      try:
          import rq as _rq
          conn = _redis.Redis.from_url(frappe.conf.get("redis_queue", "redis://127.0.0.1:11000"))
          q = _rq.Queue("long", connection=conn)
          workers = _rq.Worker.all(connection=conn)
          long_workers = [w for w in workers if any(q.name in str(qq) for qq in w.queues)]
          if long_workers:
              checks.append({"name": "Long Worker", "status": "ok", "detail": f"{len(long_workers)} worker(s)"})
          else:
              checks.append({"name": "Long Worker", "status": "warn", "detail": "No long queue worker found"})
      except Exception as e:
          checks.append({"name": "Long Worker", "status": "error", "detail": str(e)})

      # Disk Free
      try:
          free_bytes = shutil.disk_usage(bench_path).free
          free_gb = round(free_bytes / (1024 ** 3), 1)
          status = "ok" if free_gb >= 5 else "warn"
          checks.append({"name": "Disk Free", "status": status, "detail": f"{free_gb} GB"})
      except Exception as e:
          checks.append({"name": "Disk Free", "status": "error", "detail": str(e)})

      # Sites on bench
      try:
          sites_dir = os.path.join(bench_path, "sites")
          site_count = sum(
              1 for d in os.listdir(sites_dir)
              if os.path.isfile(os.path.join(sites_dir, d, "site_config.json"))
          )
          checks.append({"name": "Sites on Bench", "status": "ok", "detail": f"{site_count} site(s)"})
      except Exception as e:
          checks.append({"name": "Sites on Bench", "status": "error", "detail": str(e)})

      # Bench Apps
      try:
          apps_file = os.path.join(bench_path, "sites", "apps.txt")
          with open(apps_file) as f:
              apps = [l.strip() for l in f if l.strip()]
          checks.append({"name": "Bench Apps", "status": "ok", "detail": ", ".join(apps)})
      except Exception as e:
          checks.append({"name": "Bench Apps", "status": "error", "detail": str(e)})

      overall = "error" if any(c["status"] == "error" for c in checks) else \
                "warn"  if any(c["status"] == "warn"  for c in checks) else "ok"
      return {"checks": checks, "overall": overall}
  ```

- [ ] **Step 4: Add `get_provisioning_report` whitelist function**

  Append to `tenant.py`:
  ```python
  @frappe.whitelist()
  def get_provisioning_report():
      """Return provisioning analytics for the Reports section."""
      frappe.only_for("System Manager")

      # Monthly counts — last 6 months
      monthly = frappe.db.sql("""
          SELECT DATE_FORMAT(creation, '%Y-%m') AS month, COUNT(*) AS count
          FROM `tabProvisioning Log`
          WHERE status = 'Completed'
            AND creation >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
          GROUP BY month
          ORDER BY month
      """, as_dict=True)

      # Plan breakdown
      plans = frappe.db.sql("""
          SELECT plan, COUNT(*) AS count
          FROM `tabTenant`
          WHERE status != 'Terminated'
          GROUP BY plan
      """, as_dict=True)

      # Average duration in minutes
      avg_dur = frappe.db.sql("""
          SELECT AVG(TIMESTAMPDIFF(SECOND, started_at, completed_at)) AS avg_seconds
          FROM `tabProvisioning Log`
          WHERE status = 'Completed' AND started_at IS NOT NULL AND completed_at IS NOT NULL
      """, as_dict=True)
      avg_minutes = round((avg_dur[0].avg_seconds or 0) / 60, 1) if avg_dur else 0

      # Top 5 apps
      top_apps = frappe.db.sql("""
          SELECT app_name, COUNT(*) AS count
          FROM `tabTenant App`
          GROUP BY app_name
          ORDER BY count DESC
          LIMIT 5
      """, as_dict=True)

      return {
          "monthly": monthly,
          "plans": plans,
          "avg_provision_minutes": avg_minutes,
          "top_apps": top_apps,
      }
  ```

- [ ] **Step 5: Add `cancel_queued_job` whitelist function**

  Append to `tenant.py`:
  ```python
  @frappe.whitelist()
  def cancel_queued_job(log_name):
      """Cancel a Queued provisioning job before it starts."""
      frappe.only_for("System Manager")
      log = frappe.get_doc("Provisioning Log", log_name)
      if log.status != "Queued":
          return {"status": "error", "message": "Job is not in Queued state"}
      # Mark log cancelled
      log.db_set("status", "Failed")
      log.db_set("current_step", "Cancelled by user")
      log.db_set("completed_at", frappe.utils.now())
      # Cancel the Tenant status back to Pending
      tenant = frappe.get_doc("Tenant", log.tenant)
      if tenant.status == "Provisioning":
          tenant.db_set("status", "Pending")
      frappe.db.commit()
      return {"status": "ok"}
  ```

- [ ] **Step 6: Update `get_provisioning_stats` to support pagination**

  Find the existing `get_provisioning_stats` function. Change the `recent_tenants` query to accept `offset` and `limit`:
  ```python
  @frappe.whitelist()
  def get_provisioning_stats(offset=0, limit=20):
      """Return tenant counts by status for the dashboard."""
      offset = int(offset)
      limit = int(limit)
      stats = frappe.db.sql("""
          SELECT status, COUNT(*) as count
          FROM `tabTenant`
          GROUP BY status
      """, as_dict=True)

      result = {
          "total": 0,
          "Pending": 0, "Provisioning": 0, "Active": 0,
          "Error": 0, "Suspended": 0, "Terminated": 0,
      }
      for row in stats:
          result[row.status] = row["count"]
          result["total"] += row["count"]

      result["recent_logs"] = frappe.get_all(
          "Provisioning Log",
          fields=["name", "tenant", "site_name", "status", "current_step",
                  "progress", "started_at", "completed_at"],
          order_by="creation desc",
          limit_page_length=10,
      )

      result["recent_tenants"] = frappe.get_all(
          "Tenant",
          fields=["name", "subdomain", "client_name", "site_name", "status",
                  "plan", "provisioned_at", "admin_email"],
          order_by="creation desc",
          limit_page_length=limit,
          limit_start=offset,
      )

      for t in result["recent_tenants"]:
          t["db_name"] = ""
          if t.get("site_name"):
              cfg_path = os.path.join(
                  frappe.utils.get_bench_path(), "sites", t["site_name"], "site_config.json"
              )
              if os.path.exists(cfg_path):
                  try:
                      with open(cfg_path) as f:
                          cfg = json.load(f)
                      t["db_name"] = cfg.get("db_name", "")
                  except Exception:
                      pass

      return result
  ```

- [ ] **Step 7: Commit**

  ```bash
  git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py
  git commit -m "feat(tenant): add update_tenant_apps, get_bench_health, get_provisioning_report, cancel_queued_job; paginate get_provisioning_stats"
  ```

---

## Task 6: Build the dashboard CSS

**Files:**
- Create: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.css`
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/hooks.py`

- [ ] **Step 1: Create the CSS file**

  Create `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.css` with the following content. Every value uses a Frappe CSS variable — no hardcoded hex:

  ```css
  /* ── Layout ── */
  .sbiqc-app {
    display: flex;
    height: calc(100vh - 60px);
    background: var(--bg-color);
    overflow: hidden;
  }

  /* ── Sidebar ── */
  .sbiqc-sidebar {
    width: 170px;
    flex-shrink: 0;
    background: var(--card-bg);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 14px 0;
  }
  .sbiqc-sidebar-logo {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 14px 14px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 10px;
  }
  .sbiqc-sidebar-logo svg { color: var(--primary); }
  .sbiqc-logo-text { font-size: 13px; font-weight: 700; color: var(--text-color); }
  .sbiqc-logo-sub  { font-size: 10px; color: var(--text-muted); }

  .sbiqc-nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    font-size: 12px;
    color: var(--text-muted);
    cursor: pointer;
    border-left: 2px solid transparent;
    user-select: none;
  }
  .sbiqc-nav-item:hover { background: var(--sidebar-select-color, color-mix(in srgb, var(--primary) 8%, transparent)); }
  .sbiqc-nav-item.active {
    color: var(--primary);
    background: var(--sidebar-select-color, color-mix(in srgb, var(--primary) 12%, transparent));
    border-left-color: var(--primary);
    font-weight: 600;
  }
  .sbiqc-nav-icon { width: 16px; text-align: center; font-size: 13px; }
  .sbiqc-nav-badge {
    margin-left: auto;
    background: var(--red-avatar-bg, #ef4444);
    color: #fff;
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 8px;
    font-weight: 700;
    display: none;
  }
  .sbiqc-nav-badge.show { display: inline-block; }
  .sbiqc-nav-badge.blue { background: var(--blue-avatar-bg, #3b82f6); }

  .sbiqc-sidebar-bottom {
    margin-top: auto;
    padding: 10px 14px 0;
    border-top: 1px solid var(--border-color);
  }
  .sbiqc-env-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: color-mix(in srgb, var(--primary) 12%, transparent);
    color: var(--primary);
    font-size: 9px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: .5px;
  }

  /* ── Main ── */
  .sbiqc-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg-color);
  }
  .sbiqc-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 18px;
    background: var(--card-bg);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
  }
  .sbiqc-topbar-title { font-size: 15px; font-weight: 700; color: var(--text-color); }
  .sbiqc-topbar-actions { display: flex; gap: 8px; align-items: center; }

  /* ── Buttons ── */
  .sbiqc-btn-primary {
    background: var(--primary);
    color: #fff;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 5px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .sbiqc-btn-icon {
    background: color-mix(in srgb, var(--primary) 12%, transparent);
    color: var(--primary);
    border: none;
    border-radius: 5px;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    cursor: pointer;
  }
  .sbiqc-btn-icon.sbiqc-spin { animation: sbiqc-rotate .7s linear infinite; }
  @keyframes sbiqc-rotate { to { transform: rotate(360deg); } }

  /* ── KPI Strip ── */
  .sbiqc-kpi-row {
    display: flex;
    gap: 10px;
    padding: 12px 18px;
    background: var(--bg-color);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
  }
  .sbiqc-kpi {
    flex: 1;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 7px;
    padding: 10px 12px;
    cursor: pointer;
    border-top: 2px solid var(--kpi-c);
    transition: box-shadow .15s;
  }
  .sbiqc-kpi:hover { box-shadow: 0 2px 8px color-mix(in srgb, var(--kpi-c) 20%, transparent); }
  .sbiqc-kpi-val   { font-size: 22px; font-weight: 800; color: var(--kpi-c); line-height: 1; }
  .sbiqc-kpi-label { font-size: 10px; color: var(--text-muted); margin-top: 3px; }

  /* ── Toolbar ── */
  .sbiqc-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 18px;
    background: var(--bg-color);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
    flex-wrap: wrap;
  }
  .sbiqc-search-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 5px;
    padding: 5px 10px;
    color: var(--text-muted);
    flex: 1;
    max-width: 240px;
  }
  .sbiqc-search-wrap input {
    border: none;
    background: transparent;
    outline: none;
    font-size: 12px;
    color: var(--text-color);
    width: 100%;
  }
  .sbiqc-chip {
    font-size: 10px;
    padding: 4px 10px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    color: var(--text-muted);
    cursor: pointer;
  }
  .sbiqc-chip.active {
    background: color-mix(in srgb, var(--primary) 12%, transparent);
    color: var(--primary);
    border-color: var(--primary);
    font-weight: 600;
  }

  /* ── Content Panel ── */
  .sbiqc-panel { flex: 1; overflow-y: auto; padding: 16px 18px; }
  .sbiqc-panel-hidden { display: none; }

  /* ── Table ── */
  .sbiqc-table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; }
  .sbiqc-table th {
    padding: 9px 12px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: var(--text-muted);
    background: var(--bg-color);
    border-bottom: 1px solid var(--border-color);
    text-align: left;
  }
  .sbiqc-table td {
    padding: 9px 12px;
    font-size: 12px;
    color: var(--text-color);
    border-bottom: 1px solid var(--border-color);
  }
  .sbiqc-table tr:hover td { background: color-mix(in srgb, var(--primary) 4%, var(--card-bg)); }
  .sbiqc-table tr:last-child td { border-bottom: none; }
  .sbiqc-tenant-name { font-weight: 600; }
  .sbiqc-tenant-sub  { font-size: 10px; color: var(--text-muted); }

  /* ── Badges & Pills ── */
  .sbiqc-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 8px;
    background: color-mix(in srgb, var(--bc) 15%, transparent);
    color: var(--bc);
  }
  .sbiqc-pill {
    display: inline-block;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 4px;
    background: color-mix(in srgb, var(--pc) 15%, transparent);
    color: var(--pc);
    font-weight: 600;
  }

  /* ── Row Action Buttons ── */
  .sbiqc-actions { display: flex; gap: 4px; align-items: center; }
  .sbiqc-act {
    width: 24px; height: 24px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--card-bg);
    color: var(--text-muted);
    font-size: 11px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    title: attr(title);
  }
  .sbiqc-act:hover           { border-color: var(--primary); color: var(--primary); }
  .sbiqc-act.danger:hover    { border-color: var(--red-avatar-bg, #ef4444); color: var(--red-avatar-bg, #ef4444); }
  .sbiqc-act.retry           { color: var(--blue-avatar-bg, #3b82f6); }
  .sbiqc-act.open            { color: var(--green-avatar-bg, #10b981); }

  /* ── Load More ── */
  .sbiqc-load-more {
    text-align: center;
    padding: 12px;
    color: var(--primary);
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
  }

  /* ── Empty State ── */
  .sbiqc-empty { text-align: center; padding: 48px 20px; color: var(--text-muted); }
  .sbiqc-empty svg { opacity: .4; margin-bottom: 12px; }
  .sbiqc-empty-h { font-weight: 600; font-size: 14px; margin-bottom: 6px; color: var(--text-color); }

  /* ── Wizard ── */
  .sbiqc-wizard { max-width: 580px; }
  .sbiqc-wizard-steps { display: flex; gap: 8px; margin-bottom: 6px; }
  .sbiqc-wstep { flex: 1; height: 3px; border-radius: 2px; background: var(--border-color); }
  .sbiqc-wstep.done   { background: var(--primary); }
  .sbiqc-wstep.active { background: var(--primary); opacity: .6; }
  .sbiqc-wizard-step-labels {
    display: flex; justify-content: space-between;
    font-size: 10px; color: var(--text-muted); margin-bottom: 20px;
  }
  .sbiqc-wizard-step-labels span.active { color: var(--primary); font-weight: 600; }
  .sbiqc-wizard-title { font-size: 15px; font-weight: 700; color: var(--text-color); margin-bottom: 16px; }
  .sbiqc-field { margin-bottom: 14px; }
  .sbiqc-field label { display: block; font-size: 11px; color: var(--text-muted); margin-bottom: 4px; font-weight: 500; }
  .sbiqc-field input,
  .sbiqc-field select {
    width: 100%;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 12px;
    color: var(--text-color);
    outline: none;
  }
  .sbiqc-field input:focus,
  .sbiqc-field select:focus { border-color: var(--primary); }
  .sbiqc-field .sbiqc-hint { font-size: 10px; color: var(--text-muted); margin-top: 3px; }
  .sbiqc-field .sbiqc-preview { color: var(--primary); font-weight: 600; }
  .sbiqc-field-error { border-color: var(--red-avatar-bg, #ef4444) !important; }
  .sbiqc-field-msg   { font-size: 10px; color: var(--red-avatar-bg, #ef4444); margin-top: 3px; }

  /* App toggles — Step 2 */
  .sbiqc-app-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }
  .sbiqc-app-card {
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 10px;
    cursor: pointer;
    background: var(--card-bg);
    font-size: 12px;
    color: var(--text-color);
    display: flex;
    align-items: center;
    gap: 8px;
    user-select: none;
  }
  .sbiqc-app-card.selected { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 10%, var(--card-bg)); color: var(--primary); }
  .sbiqc-app-card.locked   { opacity: .6; cursor: not-allowed; }
  .sbiqc-app-card .check   { font-size: 14px; }

  /* Wizard footer */
  .sbiqc-wizard-foot { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
  .sbiqc-btn-secondary {
    background: transparent;
    color: var(--text-muted);
    border: 1px solid var(--border-color);
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 12px;
    cursor: pointer;
  }

  /* ── Queue Jobs ── */
  .sbiqc-job {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 7px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }
  .sbiqc-job-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
  .sbiqc-job-id   { font-weight: 600; font-size: 12px; color: var(--primary); text-decoration: none; }
  .sbiqc-job-site { font-size: 11px; color: var(--text-muted); margin-right: auto; }
  .sbiqc-job-step { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
  .sbiqc-job-ts   { font-size: 10px; color: var(--text-muted); margin-top: 4px; }
  .sbiqc-bar      { height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden; }
  .sbiqc-bar-fill { height: 4px; background: var(--primary); border-radius: 2px; transition: width .5s; }

  /* ── Health Grid ── */
  .sbiqc-health-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
  .sbiqc-health-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-left: 3px solid var(--hc);
    border-radius: 7px;
    padding: 12px 14px;
  }
  .sbiqc-health-name   { font-size: 12px; font-weight: 600; color: var(--text-color); margin-bottom: 4px; }
  .sbiqc-health-status { font-size: 11px; color: var(--hc); font-weight: 700; }
  .sbiqc-health-detail { font-size: 10px; color: var(--text-muted); margin-top: 2px; }

  /* ── Reports ── */
  .sbiqc-report-section { margin-bottom: 24px; }
  .sbiqc-report-title { font-size: 13px; font-weight: 700; color: var(--text-color); margin-bottom: 12px; }
  .sbiqc-bar-chart { display: flex; flex-direction: column; gap: 6px; }
  .sbiqc-bar-row { display: flex; align-items: center; gap: 8px; }
  .sbiqc-bar-label { font-size: 11px; color: var(--text-muted); width: 60px; text-align: right; }
  .sbiqc-bar-track { flex: 1; background: var(--border-color); border-radius: 3px; height: 18px; }
  .sbiqc-bar-seg { height: 18px; background: var(--primary); border-radius: 3px; display: flex; align-items: center; padding: 0 6px; }
  .sbiqc-bar-seg-val { font-size: 10px; color: #fff; font-weight: 700; }

  /* ── Slideout (Add Apps) ── */
  .sbiqc-slideout-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,.3); z-index: 1000; display: none;
  }
  .sbiqc-slideout-panel {
    position: fixed; right: 0; top: 0; bottom: 0; width: 320px;
    background: var(--card-bg);
    border-left: 1px solid var(--border-color);
    z-index: 1001;
    display: flex; flex-direction: column;
    transform: translateX(100%);
    transition: transform .25s ease;
  }
  .sbiqc-slideout-panel.open { transform: translateX(0); }
  .sbiqc-slideout-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 16px;
    border-bottom: 1px solid var(--border-color);
  }
  .sbiqc-slideout-title { font-size: 14px; font-weight: 700; color: var(--text-color); }
  .sbiqc-slideout-body { flex: 1; overflow-y: auto; padding: 14px 16px; }
  .sbiqc-slideout-foot { padding: 12px 16px; border-top: 1px solid var(--border-color); }

  /* ── Errors Section ── */
  .sbiqc-error-row {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-left: 3px solid var(--red-avatar-bg, #ef4444);
    border-radius: 7px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }
  .sbiqc-error-traceback {
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 10px;
    font-size: 10px;
    font-family: monospace;
    color: var(--text-muted);
    white-space: pre-wrap;
    max-height: 200px;
    overflow-y: auto;
    margin-top: 8px;
    display: none;
  }
  .sbiqc-error-traceback.open { display: block; }

  /* ── Site link ── */
  .sbiqc-site-link { color: var(--primary); font-size: 11px; text-decoration: none; }
  .sbiqc-site-link:hover { text-decoration: underline; }
  .sbiqc-muted { color: var(--text-muted); font-size: 11px; }
  .sbiqc-db-name { font-size: 10px; color: var(--text-muted); margin-top: 2px; }
  .sbiqc-db-name code { font-family: monospace; }
  ```

- [ ] **Step 2: Register CSS in hooks.py**

  Open `apps/sbiqc_provisioning/sbiqc_provisioning/hooks.py`.  
  The existing line:
  ```python
  app_include_css = "/assets/sbiqc_provisioning/css/sbiqc_provisioning.css"
  ```
  Change to a list so both files load:
  ```python
  app_include_css = [
      "/assets/sbiqc_provisioning/css/sbiqc_provisioning.css",
      "/assets/sbiqc_provisioning/css/sbiqc_provisioning.css",
  ]
  ```

  > **Note:** Frappe serves page CSS automatically when the page module path matches. The CSS file in the page folder (`page/sbiqc_provisioning/sbiqc_provisioning.css`) is served automatically by Frappe's asset pipeline for that page — no hooks entry needed for it. The `app_include_css` entry above is only needed if you want it globally. Since this CSS is page-specific, you can skip the hooks change and rely on Frappe's auto-serving. Verify after build which approach works — if the CSS loads from the page path without hooks, revert hooks.py.

- [ ] **Step 3: Commit**

  ```bash
  git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.css \
          apps/sbiqc_provisioning/sbiqc_provisioning/hooks.py
  git commit -m "feat(dashboard): add CSS-variable-only sidebar stylesheet"
  ```

---

## Task 7: Rewrite the dashboard HTML shell

**Files:**
- Rewrite: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.html`

- [ ] **Step 1: Replace entire file content**

  ```html
  <div class="sbiqc-app">

    <!-- Sidebar -->
    <div class="sbiqc-sidebar">
      <div class="sbiqc-sidebar-logo">
        <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
          <rect x="2" y="3" width="24" height="9" rx="3" fill="currentColor" opacity=".9"/>
          <rect x="2" y="16" width="24" height="9" rx="3" fill="currentColor" opacity=".5"/>
          <circle cx="7" cy="7.5" r="1.5" fill="#fff"/>
          <circle cx="7" cy="20.5" r="1.5" fill="#fff"/>
        </svg>
        <div>
          <div class="sbiqc-logo-text">Provisioner</div>
          <div class="sbiqc-logo-sub">mysite.local</div>
        </div>
      </div>

      <div class="sbiqc-nav-item active" data-section="tenants">
        <span class="sbiqc-nav-icon">&#9646;</span> Tenants
      </div>
      <div class="sbiqc-nav-item" data-section="queue">
        <span class="sbiqc-nav-icon">&#9889;</span> Queue
        <span class="sbiqc-nav-badge blue sbiqc-badge-queue"></span>
      </div>
      <div class="sbiqc-nav-item" data-section="health">
        <span class="sbiqc-nav-icon">&#10003;</span> Health
      </div>
      <div class="sbiqc-nav-item" data-section="reports">
        <span class="sbiqc-nav-icon">&#9636;</span> Reports
      </div>
      <div class="sbiqc-nav-item" data-section="errors">
        <span class="sbiqc-nav-icon">&#9888;</span> Errors
        <span class="sbiqc-nav-badge sbiqc-badge-errors"></span>
      </div>

      <div class="sbiqc-sidebar-bottom">
        <span class="sbiqc-env-chip sbiqc-env-label">&#9679; Local Dev</span>
      </div>
    </div>

    <!-- Main Area -->
    <div class="sbiqc-main">

      <!-- Topbar -->
      <div class="sbiqc-topbar">
        <span class="sbiqc-topbar-title sbiqc-section-title">Tenants</span>
        <div class="sbiqc-topbar-actions">
          <button class="sbiqc-btn-icon sbiqc-btn-refresh" title="{{ __('Refresh') }}">&#8635;</button>
          <button class="sbiqc-btn-primary sbiqc-btn-new-tenant">+ {{ __('New Tenant') }}</button>
        </div>
      </div>

      <!-- KPI Strip (shown for Tenants section only) -->
      <div class="sbiqc-kpi-row sbiqc-kpi-strip"></div>

      <!-- Toolbar (shown for Tenants + Errors) -->
      <div class="sbiqc-toolbar sbiqc-toolbar-area">
        <div class="sbiqc-search-wrap">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input type="text" class="sbiqc-search-input" placeholder="{{ __('Search tenants…') }}"/>
        </div>
        <div class="sbiqc-chips">
          <button class="sbiqc-chip active" data-status="">{{ __('All') }}</button>
          <button class="sbiqc-chip" data-status="Active">{{ __('Active') }}</button>
          <button class="sbiqc-chip" data-status="Provisioning">{{ __('Running') }}</button>
          <button class="sbiqc-chip" data-status="Pending">{{ __('Pending') }}</button>
          <button class="sbiqc-chip" data-status="Suspended">{{ __('Suspended') }}</button>
          <button class="sbiqc-chip" data-status="Error">{{ __('Errors') }}</button>
        </div>
      </div>

      <!-- Content Panels -->
      <div class="sbiqc-panel sbiqc-panel-tenants" id="sbiqc-panel-tenants"></div>
      <div class="sbiqc-panel sbiqc-panel-hidden" id="sbiqc-panel-queue"></div>
      <div class="sbiqc-panel sbiqc-panel-hidden" id="sbiqc-panel-health"></div>
      <div class="sbiqc-panel sbiqc-panel-hidden" id="sbiqc-panel-reports"></div>
      <div class="sbiqc-panel sbiqc-panel-hidden" id="sbiqc-panel-errors"></div>

    </div>

    <!-- Add Apps Slideout -->
    <div class="sbiqc-slideout-backdrop" id="sbiqc-backdrop"></div>
    <div class="sbiqc-slideout-panel" id="sbiqc-slideout">
      <div class="sbiqc-slideout-head">
        <span class="sbiqc-slideout-title" id="sbiqc-slideout-title">Add Apps</span>
        <button class="sbiqc-btn-icon sbiqc-slideout-close">&#10005;</button>
      </div>
      <div class="sbiqc-slideout-body" id="sbiqc-slideout-body"></div>
      <div class="sbiqc-slideout-foot" id="sbiqc-slideout-foot"></div>
    </div>

  </div>
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.html
  git commit -m "feat(dashboard): rebuild HTML as sidebar shell"
  ```

---

## Task 8: Rewrite the dashboard JavaScript — core + Tenants section

**Files:**
- Rewrite: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.js`

- [ ] **Step 1: Write the full JS file**

  Replace the entire file with:

  ```javascript
  /* globals frappe, __ */
  frappe.pages["sbiqc-provisioning"].on_page_load = function (wrapper) {
      var page = frappe.ui.make_app_page({
          parent: wrapper,
          title: "SBIQ Provisioning",
          single_column: true,
      });
      $(wrapper).find(".page-head").addClass("hide");
      page.main.html(frappe.render_template("sbiqc_provisioning"));
      wrapper.__sbiqc = new SBIQCProvisioning(wrapper);
  };

  frappe.pages["sbiqc-provisioning"].on_page_show = function (wrapper) {
      if (wrapper.__sbiqc) wrapper.__sbiqc.on_show();
  };

  class SBIQCProvisioning {
      constructor(wrapper) {
          this.$w        = $(wrapper);
          this.data      = null;
          this.section   = "tenants";
          this.filter    = "";
          this.search    = "";
          this.offset    = 0;
          this.limit     = 20;
          this.loading   = false;
          this._timer    = null;
          this._health_timer = null;
          this._slide_tenant = null;
          this._all_apps = [];
          this._installed_apps = {};

          this._is_production = false;
          frappe.call({
              method: "frappe.client.get_single_value",
              args: { doctype: "System Settings", field: "app_name" },
              callback: () => {
                  var is_prod = frappe.boot && frappe.boot.conf && frappe.boot.conf.is_production;
                  this._is_production = !!is_prod;
                  this.$w.find(".sbiqc-env-label").text(
                      (is_prod ? "● Production" : "● Local Dev")
                  );
              }
          });

          this._bind();
          this.load_stats();
          this._auto_refresh();
          this._wire_realtime();
      }

      on_show() { this.load_stats(); }

      /* ─── Navigation ─── */
      _bind() {
          var self = this;

          // Nav items
          this.$w.on("click", ".sbiqc-nav-item", function () {
              var sec = $(this).data("section");
              self._go(sec);
          });

          // Refresh button
          this.$w.on("click", ".sbiqc-btn-refresh", function () {
              var $b = $(this);
              $b.addClass("sbiqc-spin");
              self.load_stats(function () {
                  setTimeout(function () { $b.removeClass("sbiqc-spin"); }, 500);
              });
          });

          // New Tenant
          this.$w.on("click", ".sbiqc-btn-new-tenant", function () {
              self._wizard_show();
          });

          // Filter chips
          this.$w.on("click", ".sbiqc-chip", function () {
              var s = $(this).data("status") || "";
              self.filter = s;
              self.$w.find(".sbiqc-chip").removeClass("active");
              $(this).addClass("active");
              self.offset = 0;
              self._render_tenants();
          });

          // Search
          this.$w.on("input", ".sbiqc-search-input", function () {
              self.search = $(this).val().toLowerCase().trim();
              self._render_tenants();
          });

          // Row click → form
          this.$w.on("click", ".sbiqc-trow", function (e) {
              if ($(e.target).closest("button,a").length) return;
              frappe.set_route("Form", "Tenant", $(this).data("name"));
          });

          // Row actions
          this.$w.on("click", ".sbiqc-act-open",    function (e) { e.stopPropagation(); window.open("http://" + $(this).data("site") + ":8000", "_blank"); });
          this.$w.on("click", ".sbiqc-act-suspend",  function (e) { e.stopPropagation(); self._suspend($(this).data("name")); });
          this.$w.on("click", ".sbiqc-act-resume",   function (e) { e.stopPropagation(); self._resume($(this).data("name")); });
          this.$w.on("click", ".sbiqc-act-retry",    function (e) { e.stopPropagation(); self._retry($(this).data("name")); });
          this.$w.on("click", ".sbiqc-act-addapps",  function (e) { e.stopPropagation(); self._addapps_open($(this).data("name")); });
          this.$w.on("click", ".sbiqc-act-delete",   function (e) { e.stopPropagation(); self._delete($(this).data("name")); });
          this.$w.on("click", ".sbiqc-act-viewlog",  function (e) { e.stopPropagation(); frappe.set_route("List", "Provisioning Log", { tenant: $(this).data("name") }); });
          this.$w.on("click", ".sbiqc-act-cancel",   function (e) { e.stopPropagation(); self._cancel_job($(this).data("log")); });

          // Load More
          this.$w.on("click", ".sbiqc-load-more", function () { self._load_more(); });

          // Errors section expand traceback
          this.$w.on("click", ".sbiqc-err-expand", function () {
              $(this).closest(".sbiqc-error-row").find(".sbiqc-error-traceback").toggleClass("open");
          });

          // Errors retry
          this.$w.on("click", ".sbiqc-err-retry", function () { self._retry($(this).data("name")); });

          // Slideout close
          this.$w.on("click", "#sbiqc-backdrop, .sbiqc-slideout-close", function () { self._slideout_close(); });

          // Slideout Install Selected
          this.$w.on("click", ".sbiqc-install-selected", function () { self._addapps_submit(); });
      }

      _go(section) {
          this.section = section;
          var titles = { tenants: __("Tenants"), queue: __("Queue"), health: __("Health"), reports: __("Reports"), errors: __("Errors") };
          this.$w.find(".sbiqc-section-title").text(titles[section] || section);
          this.$w.find(".sbiqc-nav-item").removeClass("active");
          this.$w.find('.sbiqc-nav-item[data-section="' + section + '"]').addClass("active");
          this.$w.find(".sbiqc-panel").addClass("sbiqc-panel-hidden");
          this.$w.find("#sbiqc-panel-" + section).removeClass("sbiqc-panel-hidden");

          // Show/hide KPI strip and toolbar for relevant sections
          var show_kpi     = (section === "tenants");
          var show_toolbar = (section === "tenants");
          this.$w.find(".sbiqc-kpi-strip").toggle(show_kpi);
          this.$w.find(".sbiqc-toolbar-area").toggle(show_toolbar);

          // Show/hide New Tenant button
          this.$w.find(".sbiqc-btn-new-tenant").toggle(section === "tenants");

          // Section-specific loads
          if (section === "tenants") { this._render_tenants(); }
          if (section === "queue")   { this._render_queue(); }
          if (section === "health")  { this._load_health(); }
          if (section === "reports") { this._load_reports(); }
          if (section === "errors")  { this._render_errors(); }
      }

      /* ─── Data loading ─── */
      load_stats(cb) {
          var self = this;
          if (this.loading) return;
          this.loading = true;
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_provisioning_stats",
              args: { offset: 0, limit: this.limit },
              callback: function (r) {
                  self.loading = false;
                  if (r.message) {
                      self.data = r.message;
                      self.offset = self.limit;
                      self._render_kpis();
                      self._update_badges();
                      if (self.section === "tenants") self._render_tenants();
                      if (self.section === "queue")   self._render_queue();
                      if (self.section === "errors")  self._render_errors();
                  }
                  if (cb) cb();
              },
              error: function () { self.loading = false; if (cb) cb(); }
          });
      }

      _auto_refresh() {
          var self = this;
          this._timer = setInterval(function () {
              if (self.data && (self.data.Provisioning > 0 || self.data.Pending > 0)) {
                  self.load_stats();
              }
          }, 15000);
      }

      _wire_realtime() {
          var self = this;
          frappe.realtime.on("progress", function (data) {
              if (!data || !data.title) return;
              // Update progress bar in queue panel for matching job
              var $bar = self.$w.find('.sbiqc-bar-fill[data-site="' + data.title + '"]');
              if ($bar.length && data.percent) {
                  $bar.css("width", data.percent + "%");
              }
          });
      }

      /* ─── KPIs ─── */
      _render_kpis() {
          var d = this.data || {};
          var kpis = [
              { key: "total",        label: __("Total"),       val: d.total || 0,        color: "var(--primary)" },
              { key: "Active",       label: __("Active"),      val: d.Active || 0,       color: "#10b981" },
              { key: "Provisioning", label: __("Running"),     val: d.Provisioning || 0, color: "#3b82f6" },
              { key: "Error",        label: __("Errors"),      val: d.Error || 0,        color: "#ef4444" },
          ];
          var h = "";
          for (var i = 0; i < kpis.length; i++) {
              var k = kpis[i];
              h += '<div class="sbiqc-kpi" style="--kpi-c:' + k.color + ';" data-filter="' + k.key + '">';
              h += '<div class="sbiqc-kpi-val">' + k.val + '</div>';
              h += '<div class="sbiqc-kpi-label">' + k.label + '</div>';
              h += '</div>';
          }
          this.$w.find(".sbiqc-kpi-strip").html(h);
      }

      _update_badges() {
          var d = this.data || {};
          var q_count = (d.Provisioning || 0) + (d.Pending || 0);
          var e_count = d.Error || 0;
          var $qb = this.$w.find(".sbiqc-badge-queue");
          var $eb = this.$w.find(".sbiqc-badge-errors");
          if (q_count > 0) { $qb.text(q_count).addClass("show"); } else { $qb.text("").removeClass("show"); }
          if (e_count > 0) { $eb.text(e_count).addClass("show"); } else { $eb.text("").removeClass("show"); }
      }

      /* ─── Tenants Table ─── */
      _render_tenants() {
          var self = this;
          var $panel = this.$w.find("#sbiqc-panel-tenants");
          var tenants = (this.data && this.data.recent_tenants) || [];

          if (this.filter && this.filter !== "total") {
              tenants = tenants.filter(function (t) { return t.status === self.filter; });
          }
          if (this.search) {
              var s = this.search;
              tenants = tenants.filter(function (t) {
                  return ((t.client_name || "") + " " + (t.subdomain || "") + " " + (t.site_name || "")).toLowerCase().indexOf(s) !== -1;
              });
          }

          if (!tenants.length) {
              $panel.html(this._empty("No tenants found", "Create your first tenant to begin provisioning."));
              return;
          }

          var h = '<table class="sbiqc-table"><thead><tr>';
          h += '<th>' + __("Tenant") + '</th><th>' + __("Site / DB") + '</th><th>' + __("Plan") + '</th><th>' + __("Status") + '</th><th></th>';
          h += '</tr></thead><tbody>';

          for (var i = 0; i < tenants.length; i++) {
              var t = tenants[i];
              h += '<tr class="sbiqc-trow" data-name="' + t.name + '">';
              h += '<td><div class="sbiqc-tenant-name">' + frappe.utils.escape_html(t.client_name || t.subdomain) + '</div>';
              h += '<div class="sbiqc-tenant-sub">' + frappe.utils.escape_html(t.subdomain) + (t.provisioned_at ? " · " + frappe.datetime.prettyDate(t.provisioned_at) : "") + '</div></td>';

              var site_h = "";
              if (t.status === "Active" && t.site_name) {
                  site_h = '<a class="sbiqc-site-link" href="http://' + t.site_name + ':8000" target="_blank">' + t.site_name + ' &#8599;</a>';
              } else {
                  site_h = '<span class="sbiqc-muted">' + (t.site_name || "—") + '</span>';
              }
              if (t.db_name) {
                  site_h += '<div class="sbiqc-db-name"><code>' + t.db_name + '</code></div>';
              }
              h += '<td>' + site_h + '</td>';
              h += '<td>' + this._plan_pill(t.plan) + '</td>';
              h += '<td>' + this._badge(t.status) + '</td>';
              h += '<td>' + this._row_actions(t) + '</td>';
              h += '</tr>';
          }
          h += '</tbody></table>';

          if (tenants.length === this.limit) {
              h += '<div class="sbiqc-load-more">' + __("Load more") + ' &#8595;</div>';
          }

          $panel.html(h);
      }

      _load_more() {
          var self = this;
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_provisioning_stats",
              args: { offset: this.offset, limit: this.limit },
              callback: function (r) {
                  if (!r.message) return;
                  var more = r.message.recent_tenants || [];
                  self.data.recent_tenants = (self.data.recent_tenants || []).concat(more);
                  self.offset += self.limit;
                  self._render_tenants();
              }
          });
      }

      _row_actions(t) {
          var h = '<div class="sbiqc-actions">';
          if (t.status === "Active") {
              h += '<button class="sbiqc-act sbiqc-act-open open" data-site="' + t.site_name + '" title="' + __("Open site") + '">&#8599;</button>';
              h += '<button class="sbiqc-act sbiqc-act-suspend" data-name="' + t.name + '" title="' + __("Suspend") + '">&#9646;&#9646;</button>';
              h += '<button class="sbiqc-act sbiqc-act-addapps" data-name="' + t.name + '" title="' + __("Add Apps") + '">&#8853;</button>';
              h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + t.name + '" title="' + __("Delete") + '">&#128465;</button>';
          } else if (t.status === "Provisioning") {
              h += '<button class="sbiqc-act sbiqc-act-viewlog" data-name="' + t.name + '" title="' + __("View log") + '">&#9776;</button>';
          } else if (t.status === "Error") {
              h += '<button class="sbiqc-act retry sbiqc-act-retry" data-name="' + t.name + '" title="' + __("Retry") + '">&#8635;</button>';
              h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + t.name + '" title="' + __("Delete") + '">&#128465;</button>';
          } else if (t.status === "Suspended") {
              h += '<button class="sbiqc-act open sbiqc-act-resume" data-name="' + t.name + '" title="' + __("Resume") + '">&#9654;</button>';
              h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + t.name + '" title="' + __("Delete") + '">&#128465;</button>';
          } else if (t.status === "Pending") {
              h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + t.name + '" title="' + __("Delete") + '">&#128465;</button>';
          }
          h += '</div>';
          return h;
      }

      /* ─── Tenant Actions ─── */
      _suspend(name) {
          frappe.confirm(__("Suspend tenant {0}? Their site will become inaccessible.", [name]), function () {
              frappe.db.set_value("Tenant", name, "status", "Suspended").then(function () {
                  frappe.show_alert({ message: __("Tenant suspended"), indicator: "orange" });
              });
          });
      }

      _resume(name) {
          frappe.db.set_value("Tenant", name, "status", "Active").then(function () {
              frappe.show_alert({ message: __("Tenant resumed"), indicator: "green" });
          });
      }

      _retry(name) {
          var self = this;
          frappe.confirm(__("Re-queue provisioning for {0}?", [name]), function () {
              frappe.call({
                  method: "frappe.client.get",
                  args: { doctype: "Tenant", name: name },
                  callback: function (r) {
                      if (r.message && r.message.docstatus === 1) {
                          frappe.call({
                              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.retry_provisioning",
                              args: { tenant_name: name },
                              callback: function () {
                                  frappe.show_alert({ message: __("Provisioning re-queued"), indicator: "blue" });
                                  self.load_stats();
                              }
                          });
                      }
                  }
              });
          });
      }

      _delete(name) {
          var self = this;
          frappe.confirm(
              __("Permanently delete tenant {0} and drop its database? This cannot be undone.", [name]),
              function () {
                  frappe.call({
                      method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.delete_tenant",
                      args: { tenant_name: name },
                      callback: function (r) {
                          if (r.message && r.message.status === "ok") {
                              frappe.show_alert({ message: __("Tenant deleted"), indicator: "green" });
                              self.load_stats();
                          }
                      }
                  });
              }
          );
      }

      _cancel_job(log_name) {
          var self = this;
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.cancel_queued_job",
              args: { log_name: log_name },
              callback: function () {
                  frappe.show_alert({ message: __("Job cancelled"), indicator: "orange" });
                  self.load_stats();
              }
          });
      }

      /* ─── Queue Section ─── */
      _render_queue() {
          var $p = this.$w.find("#sbiqc-panel-queue");
          var logs = (this.data && this.data.recent_logs) || [];
          if (!logs.length) {
              $p.html(this._empty("Queue is clear", "Jobs appear here during tenant provisioning."));
              return;
          }
          var h = "";
          for (var i = 0; i < logs.length; i++) {
              var l = logs[i];
              var pct = l.progress || 0;
              var is_queued = l.status === "Queued";
              var is_running = l.status === "Running";
              h += '<div class="sbiqc-job">';
              h += '<div class="sbiqc-job-top">';
              h += '<a class="sbiqc-job-id" href="/app/provisioning-log/' + l.name + '">' + l.name + '</a>';
              h += '<span class="sbiqc-job-site">' + frappe.utils.escape_html(l.site_name || l.tenant) + '</span>';
              h += this._log_badge(l.status);
              if (is_queued) {
                  h += '<button class="sbiqc-btn-secondary sbiqc-act-cancel" data-log="' + l.name + '" style="font-size:10px;padding:2px 8px;">' + __("Cancel") + '</button>';
              }
              h += '</div>';
              if (l.current_step) {
                  h += '<div class="sbiqc-job-step">' + frappe.utils.escape_html(l.current_step) + '</div>';
              }
              if (is_running || is_queued) {
                  h += '<div class="sbiqc-bar"><div class="sbiqc-bar-fill" data-site="' + (l.site_name || "") + '" style="width:' + pct + '%;"></div></div>';
              } else if (l.status === "Completed") {
                  h += '<div class="sbiqc-bar"><div class="sbiqc-bar-fill" style="width:100%;background:var(--green-avatar-bg,#10b981);"></div></div>';
              }
              var ts = l.completed_at || l.started_at;
              if (ts) h += '<div class="sbiqc-job-ts">' + frappe.datetime.prettyDate(ts) + '</div>';
              h += '</div>';
          }
          $p.html(h);
      }

      /* ─── Health Section ─── */
      _load_health() {
          var self = this;
          var $p = this.$w.find("#sbiqc-panel-health");
          $p.html('<div class="sbiqc-empty"><p>Loading health checks...</p></div>');
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_bench_health",
              callback: function (r) {
                  if (!r.message) return;
                  self._render_health(r.message);
              }
          });
          // Auto-refresh health every 30s
          clearInterval(this._health_timer);
          this._health_timer = setInterval(function () {
              if (self.section === "health") self._load_health();
          }, 30000);
      }

      _render_health(data) {
          var $p = this.$w.find("#sbiqc-panel-health");
          var color_map = { ok: "var(--green-avatar-bg,#10b981)", warn: "var(--yellow-avatar-bg,#f59e0b)", error: "var(--red-avatar-bg,#ef4444)" };
          var overall_color = color_map[data.overall] || color_map.ok;
          var h = '<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">';
          h += '<span style="font-size:14px;font-weight:700;color:' + overall_color + ';">&#9679; ' + (data.overall === "ok" ? __("All systems operational") : data.overall === "warn" ? __("Degraded") : __("Service error")) + '</span>';
          h += '</div>';
          h += '<div class="sbiqc-health-grid">';
          (data.checks || []).forEach(function (c) {
              var hc = color_map[c.status] || color_map.ok;
              h += '<div class="sbiqc-health-card" style="--hc:' + hc + ';">';
              h += '<div class="sbiqc-health-name">' + frappe.utils.escape_html(c.name) + '</div>';
              h += '<div class="sbiqc-health-status">' + c.status.toUpperCase() + '</div>';
              if (c.detail) h += '<div class="sbiqc-health-detail">' + frappe.utils.escape_html(c.detail) + '</div>';
              h += '</div>';
          });
          h += '</div>';
          $p.html(h);
      }

      /* ─── Reports Section ─── */
      _load_reports() {
          var self = this;
          var $p = this.$w.find("#sbiqc-panel-reports");
          $p.html('<div class="sbiqc-empty"><p>Loading reports...</p></div>');
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_provisioning_report",
              callback: function (r) {
                  if (!r.message) return;
                  self._render_reports(r.message);
              }
          });
      }

      _render_reports(data) {
          var $p = this.$w.find("#sbiqc-panel-reports");
          var h = "";

          // Stat cards row
          h += '<div style="display:flex;gap:12px;margin-bottom:24px;">';
          h += '<div class="sbiqc-kpi" style="--kpi-c:var(--primary);"><div class="sbiqc-kpi-val">' + (data.avg_provision_minutes || 0) + 'm</div><div class="sbiqc-kpi-label">' + __("Avg Provision Time") + '</div></div>';
          var total_active = 0;
          (data.plans || []).forEach(function (p) { total_active += (p.count || 0); });
          h += '<div class="sbiqc-kpi" style="--kpi-c:#10b981;"><div class="sbiqc-kpi-val">' + total_active + '</div><div class="sbiqc-kpi-label">' + __("Total Tenants") + '</div></div>';
          h += '</div>';

          // Monthly bar chart
          h += '<div class="sbiqc-report-section">';
          h += '<div class="sbiqc-report-title">' + __("Provisioning by Month") + '</div>';
          var monthly = data.monthly || [];
          var max_monthly = Math.max.apply(null, monthly.map(function (m) { return m.count; }).concat([1]));
          h += '<div class="sbiqc-bar-chart">';
          monthly.forEach(function (m) {
              var pct = Math.round((m.count / max_monthly) * 100);
              h += '<div class="sbiqc-bar-row">';
              h += '<span class="sbiqc-bar-label">' + (m.month || "") + '</span>';
              h += '<div class="sbiqc-bar-track"><div class="sbiqc-bar-seg" style="width:' + pct + '%;">';
              h += '<span class="sbiqc-bar-seg-val">' + m.count + '</span></div></div>';
              h += '</div>';
          });
          h += '</div></div>';

          // Plan breakdown
          h += '<div class="sbiqc-report-section">';
          h += '<div class="sbiqc-report-title">' + __("Tenants by Plan") + '</div>';
          var plan_colors = { Starter: "#6b7280", Standard: "#6366f1", Enterprise: "#7c3aed" };
          var max_plan = Math.max.apply(null, (data.plans || []).map(function (p) { return p.count; }).concat([1]));
          h += '<div class="sbiqc-bar-chart">';
          (data.plans || []).forEach(function (p) {
              var pct = Math.round((p.count / max_plan) * 100);
              var col = plan_colors[p.plan] || "var(--primary)";
              h += '<div class="sbiqc-bar-row">';
              h += '<span class="sbiqc-bar-label">' + (p.plan || "—") + '</span>';
              h += '<div class="sbiqc-bar-track"><div class="sbiqc-bar-seg" style="width:' + pct + '%;background:' + col + ';">';
              h += '<span class="sbiqc-bar-seg-val">' + p.count + '</span></div></div>';
              h += '</div>';
          });
          h += '</div></div>';

          // Top apps
          h += '<div class="sbiqc-report-section">';
          h += '<div class="sbiqc-report-title">' + __("Top Apps Installed") + '</div>';
          (data.top_apps || []).forEach(function (a) {
              h += '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border-color);font-size:12px;color:var(--text-color);">';
              h += '<span>' + frappe.utils.escape_html(a.app_name) + '</span><span style="color:var(--primary);font-weight:700;">' + a.count + '</span>';
              h += '</div>';
          });
          h += '</div>';

          $p.html(h);
      }

      /* ─── Errors Section ─── */
      _render_errors() {
          var $p = this.$w.find("#sbiqc-panel-errors");
          var tenants = (this.data && this.data.recent_tenants || []).filter(function (t) { return t.status === "Error"; });
          if (!tenants.length) {
              $p.html(this._empty("No errors", "All tenants are healthy."));
              return;
          }
          var h = "";
          tenants.forEach(function (t) {
              h += '<div class="sbiqc-error-row">';
              h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">';
              h += '<span style="font-weight:700;font-size:13px;color:var(--text-color);">' + frappe.utils.escape_html(t.client_name || t.subdomain) + '</span>';
              h += '<span class="sbiqc-muted">' + (t.site_name || "") + '</span>';
              h += '<span style="margin-left:auto;display:flex;gap:6px;">';
              h += '<button class="sbiqc-act retry sbiqc-err-retry" data-name="' + t.name + '" title="' + __("Retry") + '">&#8635; ' + __("Retry") + '</button>';
              h += '<button class="sbiqc-act sbiqc-err-expand" title="' + __("View traceback") + '">&#9660; ' + __("Traceback") + '</button>';
              h += '</span></div>';
              if (t.error_log) {
                  h += '<div class="sbiqc-error-traceback">' + frappe.utils.escape_html((t.error_log || "").substring(0, 5000)) + '</div>';
              }
              h += '</div>';
          });
          $p.html(h);
      }

      /* ─── 3-Step Wizard ─── */
      _wizard_show() {
          var self = this;
          this._wizard_step = 1;
          this._wizard_data = { subdomain: "", client_name: "", admin_email: "", plan: "Standard", currency: "INR", timezone: "Asia/Kolkata", apps: [] };
          // Load apps list
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_installable_apps",
              callback: function (r) {
                  self._all_apps = r.message || [];
                  self._wizard_data.apps = ["erpnext"];
                  self._wizard_render();
              }
          });
          // Show wizard panel (replace tenants panel content)
          this.$w.find(".sbiqc-kpi-strip").hide();
          this.$w.find(".sbiqc-toolbar-area").hide();
          this.$w.find(".sbiqc-btn-new-tenant").hide();
          this.$w.find(".sbiqc-btn-refresh").hide();
          this.$w.find("#sbiqc-panel-tenants").html(this._wizard_html_loading());
      }

      _wizard_html_loading() {
          return '<div class="sbiqc-wizard"><p style="color:var(--text-muted);font-size:12px;">' + __("Loading apps list...") + '</p></div>';
      }

      _wizard_render() {
          var self = this;
          var step = this._wizard_step;
          var d    = this._wizard_data;
          var steps_h = '<div class="sbiqc-wizard-steps">';
          for (var i = 1; i <= 3; i++) {
              var cls = i < step ? "done" : (i === step ? "active" : "");
              steps_h += '<div class="sbiqc-wstep ' + cls + '"></div>';
          }
          steps_h += '</div>';
          steps_h += '<div class="sbiqc-wizard-step-labels">';
          steps_h += '<span class="' + (step === 1 ? "active" : "") + '">' + __("1. Identity") + '</span>';
          steps_h += '<span class="' + (step === 2 ? "active" : "") + '">' + __("2. Apps") + '</span>';
          steps_h += '<span class="' + (step === 3 ? "active" : "") + '">' + __("3. Confirm") + '</span>';
          steps_h += '</div>';

          var body_h = "";
          if (step === 1) { body_h = this._wizard_step1_html(d); }
          if (step === 2) { body_h = this._wizard_step2_html(d); }
          if (step === 3) { body_h = this._wizard_step3_html(d); }

          var foot_h = '<div class="sbiqc-wizard-foot">';
          foot_h += '<button class="sbiqc-btn-secondary sbiqc-wiz-cancel">' + __("Cancel") + '</button>';
          if (step > 1) foot_h += '<button class="sbiqc-btn-secondary sbiqc-wiz-back">' + __("← Back") + '</button>';
          if (step < 3) foot_h += '<button class="sbiqc-btn-primary sbiqc-wiz-next">' + __("Next →") + '</button>';
          if (step === 3) foot_h += '<button class="sbiqc-btn-primary sbiqc-wiz-submit">&#9654; ' + __("Provision") + '</button>';
          foot_h += '</div>';

          var html = '<div class="sbiqc-wizard">' + steps_h + '<div class="sbiqc-wizard-title">' + ["", __("Identity"), __("Choose Apps"), __("Confirm & Provision")][step] + '</div>' + body_h + foot_h + '</div>';
          this.$w.find("#sbiqc-panel-tenants").html(html);

          // Bind wizard buttons
          this.$w.find(".sbiqc-wiz-cancel").off("click").on("click", function () { self._wizard_cancel(); });
          this.$w.find(".sbiqc-wiz-back").off("click").on("click", function ()   { self._wizard_step--; self._wizard_render(); });
          this.$w.find(".sbiqc-wiz-next").off("click").on("click", function ()   { self._wizard_next(); });
          this.$w.find(".sbiqc-wiz-submit").off("click").on("click", function () { self._wizard_submit(); });

          // Live subdomain preview
          this.$w.find("#wiz-subdomain").off("input").on("input", function () {
              var val = $(this).val().toLowerCase().replace(/[^a-z0-9-]/g, "");
              $(this).val(val);
              self.$w.find(".sbiqc-preview").text(val ? val + ".localhost" : "");
          });

          // App toggle
          this.$w.on("click", ".sbiqc-app-card:not(.locked)", function () {
              $(this).toggleClass("selected");
              var app = $(this).data("app");
              var idx = self._wizard_data.apps.indexOf(app);
              if ($(this).hasClass("selected")) {
                  if (idx === -1) self._wizard_data.apps.push(app);
              } else {
                  if (idx !== -1) self._wizard_data.apps.splice(idx, 1);
              }
              $(this).find(".check").text($(this).hasClass("selected") ? "✓" : "○");
          });
      }

      _wizard_step1_html(d) {
          return (
              '<div class="sbiqc-field"><label>' + __("Subdomain") + ' *</label>' +
              '<input id="wiz-subdomain" value="' + frappe.utils.escape_html(d.subdomain) + '" placeholder="e.g. acme-corp" />' +
              '<div class="sbiqc-hint">' + __("Site will be at:") + ' <span class="sbiqc-preview">' + (d.subdomain ? d.subdomain + ".localhost" : "") + '</span></div></div>' +
              '<div class="sbiqc-field"><label>' + __("Client Name") + ' *</label><input id="wiz-client" value="' + frappe.utils.escape_html(d.client_name) + '" placeholder="Acme Corporation" /></div>' +
              '<div class="sbiqc-field"><label>' + __("Admin Email") + '</label><input id="wiz-email" type="email" value="' + frappe.utils.escape_html(d.admin_email) + '" placeholder="admin@client.com" /></div>' +
              '<div class="sbiqc-field"><label>' + __("Plan") + '</label><select id="wiz-plan"><option ' + (d.plan==="Starter"?"selected":"") + '>Starter</option><option ' + (d.plan==="Standard"?"selected":"") + '>Standard</option><option ' + (d.plan==="Enterprise"?"selected":"") + '>Enterprise</option></select></div>' +
              '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
              '<div class="sbiqc-field"><label>' + __("Currency") + '</label><select id="wiz-currency"><option ' + (d.currency==="INR"?"selected":"") + '>INR</option><option ' + (d.currency==="USD"?"selected":"") + '>USD</option><option ' + (d.currency==="EUR"?"selected":"") + '>EUR</option><option ' + (d.currency==="GBP"?"selected":"") + '>GBP</option></select></div>' +
              '<div class="sbiqc-field"><label>' + __("Timezone") + '</label><select id="wiz-tz"><option ' + (d.timezone==="Asia/Kolkata"?"selected":"") + '>Asia/Kolkata</option><option ' + (d.timezone==="UTC"?"selected":"") + '>UTC</option><option ' + (d.timezone==="America/New_York"?"selected":"") + '>America/New_York</option><option ' + (d.timezone==="Europe/London"?"selected":"") + '>Europe/London</option><option ' + (d.timezone==="Asia/Dubai"?"selected":"") + '>Asia/Dubai</option></select></div>' +
              '</div>'
          );
      }

      _wizard_step2_html(d) {
          var h = '<div class="sbiqc-app-grid">';
          var apps = this._all_apps;
          if (!apps.length) return '<p style="color:var(--text-muted)">' + __("No apps available") + '</p>';
          for (var i = 0; i < apps.length; i++) {
              var app = apps[i];
              var is_locked   = (app === "erpnext");
              var is_selected = (d.apps.indexOf(app) !== -1);
              var cls = "sbiqc-app-card" + (is_selected ? " selected" : "") + (is_locked ? " locked" : "");
              h += '<div class="' + cls + '" data-app="' + app + '">';
              h += '<span class="check">' + (is_selected ? "✓" : "○") + '</span>';
              h += frappe.utils.escape_html(app);
              h += '</div>';
          }
          h += '</div>';
          return h;
      }

      _wizard_step3_html(d) {
          var h = '<div style="background:var(--bg-color);border:1px solid var(--border-color);border-radius:8px;padding:16px;">';
          var rows = [
              [__("Subdomain"), d.subdomain + ".localhost"],
              [__("Client Name"), d.client_name],
              [__("Admin Email"), d.admin_email || "—"],
              [__("Plan"), d.plan],
              [__("Currency"), d.currency],
              [__("Timezone"), d.timezone],
              [__("Apps"), d.apps.join(", ")],
          ];
          rows.forEach(function (r) {
              h += '<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border-color);font-size:12px;">';
              h += '<span style="color:var(--text-muted);">' + r[0] + '</span>';
              h += '<span style="color:var(--text-color);font-weight:600;">' + frappe.utils.escape_html(r[1]) + '</span>';
              h += '</div>';
          });
          h += '</div>';
          return h;
      }

      _wizard_next() {
          var d = this._wizard_data;
          if (this._wizard_step === 1) {
              d.subdomain    = (this.$w.find("#wiz-subdomain").val() || "").trim().toLowerCase();
              d.client_name  = (this.$w.find("#wiz-client").val() || "").trim();
              d.admin_email  = (this.$w.find("#wiz-email").val() || "").trim();
              d.plan         = this.$w.find("#wiz-plan").val();
              d.currency     = this.$w.find("#wiz-currency").val();
              d.timezone     = this.$w.find("#wiz-tz").val();
              if (!d.subdomain || !d.client_name) {
                  frappe.show_alert({ message: __("Subdomain and Client Name are required"), indicator: "red" });
                  return;
              }
              if (!/^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$/.test(d.subdomain)) {
                  frappe.show_alert({ message: __("Invalid subdomain format"), indicator: "red" });
                  return;
              }
          }
          this._wizard_step++;
          this._wizard_render();
      }

      _wizard_cancel() {
          this._wizard_step = 0;
          this.$w.find(".sbiqc-kpi-strip").show();
          this.$w.find(".sbiqc-toolbar-area").show();
          this.$w.find(".sbiqc-btn-new-tenant").show();
          this.$w.find(".sbiqc-btn-refresh").show();
          this._render_tenants();
      }

      _wizard_submit() {
          var self = this;
          var d    = this._wizard_data;
          // Build apps_to_install rows
          var apps_rows = d.apps.map(function (a) { return { app_name: a }; });
          frappe.call({
              method: "frappe.client.insert",
              args: {
                  doc: {
                      doctype: "Tenant",
                      subdomain: d.subdomain,
                      client_name: d.client_name,
                      admin_email: d.admin_email,
                      plan: d.plan,
                      currency: d.currency,
                      timezone: d.timezone,
                      apps_to_install: apps_rows,
                  }
              },
              callback: function (r) {
                  if (!r.exc && r.message) {
                      // Submit the doc to trigger on_submit provisioning
                      frappe.call({
                          method: "frappe.client.submit",
                          args: { doc: r.message },
                          callback: function () {
                              frappe.show_alert({ message: __("Provisioning queued for {0}", [d.subdomain + ".localhost"]), indicator: "blue" });
                              self._wizard_cancel();
                              self.load_stats();
                          }
                      });
                  }
              }
          });
      }

      /* ─── Add Apps Slideout ─── */
      _addapps_open(tenant_name) {
          var self = this;
          this._slide_tenant = tenant_name;
          var t = (this.data && this.data.recent_tenants || []).find(function (x) { return x.name === tenant_name; });
          this.$w.find("#sbiqc-slideout-title").text(__("Add Apps — {0}", [t ? t.client_name : tenant_name]));
          this.$w.find("#sbiqc-slideout-body").html('<p style="color:var(--text-muted);font-size:12px;">' + __("Loading...") + '</p>');

          // Get installed apps for this site
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_installable_apps",
              callback: function (r) {
                  var all_apps = r.message || [];
                  // Get installed via child table
                  frappe.call({
                      method: "frappe.client.get",
                      args: { doctype: "Tenant", name: tenant_name },
                      callback: function (tr) {
                          var installed = new Set((tr.message && tr.message.apps_to_install || []).map(function (a) { return a.app_name; }));
                          self._render_addapps_slideout(all_apps, installed);
                      }
                  });
              }
          });

          this.$w.find("#sbiqc-backdrop").show();
          setTimeout(function () { self.$w.find("#sbiqc-slideout").addClass("open"); }, 10);
      }

      _render_addapps_slideout(all_apps, installed) {
          var h = "";
          if (installed.size) {
              h += '<p style="font-size:11px;color:var(--text-muted);margin-bottom:8px;font-weight:600;">' + __("Already installed") + '</p>';
              installed.forEach(function (a) {
                  h += '<div class="sbiqc-app-card locked selected" style="margin-bottom:6px;"><span class="check">✓</span>' + frappe.utils.escape_html(a) + '</div>';
              });
          }
          var available = all_apps.filter(function (a) { return !installed.has(a); });
          if (available.length) {
              h += '<p style="font-size:11px;color:var(--text-muted);margin:12px 0 8px;font-weight:600;">' + __("Available to install") + '</p>';
              available.forEach(function (a) {
                  h += '<div class="sbiqc-app-card sbiqc-addapp-toggle" data-app="' + a + '" style="margin-bottom:6px;"><span class="check">○</span>' + frappe.utils.escape_html(a) + '</div>';
              });
          }
          if (!available.length) {
              h += '<p style="color:var(--text-muted);font-size:12px;margin-top:8px;">' + __("All available apps are already installed.") + '</p>';
          }
          this.$w.find("#sbiqc-slideout-body").html(h);
          this.$w.find("#sbiqc-slideout-foot").html(
              available.length
                  ? '<button class="sbiqc-btn-primary sbiqc-install-selected" style="width:100%;">' + __("Install Selected") + '</button>'
                  : ''
          );

          // Toggle selection
          this.$w.on("click", ".sbiqc-addapp-toggle", function () {
              $(this).toggleClass("selected");
              $(this).find(".check").text($(this).hasClass("selected") ? "✓" : "○");
          });
      }

      _addapps_submit() {
          var self = this;
          var selected = [];
          this.$w.find(".sbiqc-addapp-toggle.selected").each(function () {
              selected.push($(this).data("app"));
          });
          if (!selected.length) {
              frappe.show_alert({ message: __("Select at least one app"), indicator: "orange" });
              return;
          }
          frappe.call({
              method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.update_tenant_apps",
              args: { tenant_name: this._slide_tenant, new_apps: JSON.stringify(selected) },
              callback: function (r) {
                  if (r.message && r.message.status === "queued") {
                      frappe.show_alert({ message: __("App installation queued"), indicator: "blue" });
                      self._slideout_close();
                      self.load_stats();
                  }
              }
          });
      }

      _slideout_close() {
          this.$w.find("#sbiqc-slideout").removeClass("open");
          this.$w.find("#sbiqc-backdrop").hide();
          this._slide_tenant = null;
      }

      /* ─── Helpers ─── */
      _badge(status) {
          var colors = { Active: "#10b981", Provisioning: "#3b82f6", Pending: "#f59e0b", Error: "#ef4444", Suspended: "#6b7280", Terminated: "#6b7280" };
          var c = colors[status] || "#6b7280";
          return '<span class="sbiqc-badge" style="--bc:' + c + ';">' + (status || "—") + '</span>';
      }
      _log_badge(status) {
          var colors = { Completed: "#10b981", Running: "#3b82f6", Queued: "#f59e0b", Failed: "#ef4444" };
          var c = colors[status] || "#6b7280";
          return '<span class="sbiqc-badge" style="--bc:' + c + ';">' + (status || "—") + '</span>';
      }
      _plan_pill(plan) {
          var colors = { Starter: "#6b7280", Standard: "#6366f1", Enterprise: "#7c3aed" };
          var c = colors[plan] || "#6b7280";
          return '<span class="sbiqc-pill" style="--pc:' + c + ';">' + (plan || "—") + '</span>';
      }
      _empty(h, p) {
          return '<div class="sbiqc-empty"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="6" cy="6" r="1"/><circle cx="6" cy="18" r="1"/></svg><p class="sbiqc-empty-h">' + h + '</p><p>' + p + '</p></div>';
      }
  }
  ```

- [ ] **Step 2: Add `retry_provisioning` whitelist to `tenant.py`** (referenced in JS `_retry`)

  Append to `tenant.py`:
  ```python
  @frappe.whitelist()
  def retry_provisioning(tenant_name):
      """Re-queue a failed provisioning job."""
      frappe.only_for("System Manager")
      tenant = frappe.get_doc("Tenant", tenant_name)
      if tenant.docstatus != 1:
          frappe.throw("Tenant must be submitted before retrying.")
      tenant.db_set("status", "Provisioning")
      frappe.db.commit()
      frappe.enqueue(
          "sbiqc_provisioning.provisioner.engine.provision_tenant",
          tenant_name=tenant_name,
          queue="long",
          timeout=1800,
          now=frappe.flags.in_test,
      )
      return {"status": "queued"}
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/page/sbiqc_provisioning/sbiqc_provisioning.js \
          apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py
  git commit -m "feat(dashboard): full JS rewrite — sidebar nav, wizard, add-apps, queue, health, reports, errors"
  ```

---

## Task 9: Delete the old `tenant.js`

**Files:**
- Delete: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.js`

- [ ] **Step 1: Remove the file**

  ```bash
  cd ~/frappe-bench
  git rm apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.js
  git commit -m "chore(tenant): remove old tenant.js (replaced by page JS)"
  ```

---

## Task 10: Build assets and install on mysite.local

- [ ] **Step 1: Build the app assets**

  ```bash
  cd ~/frappe-bench
  bench build --app sbiqc_provisioning
  ```
  Expected: Build completes without errors. CSS and JS files appear under `sites/assets/sbiqc_provisioning/`.

- [ ] **Step 2: Install app on mysite.local**

  ```bash
  bench --site mysite.local install-app sbiqc_provisioning
  ```
  Expected output: `Installing sbiqc_provisioning...` followed by success message. If already installed: `App sbiqc_provisioning already installed`.

- [ ] **Step 3: Migrate**

  ```bash
  bench --site mysite.local migrate
  ```
  Expected: Runs DocType migrations including `currency` and `timezone` columns. No errors.

- [ ] **Step 4: Fix multi-site routing**

  Edit `sites/common_site_config.json` (do NOT commit this file — it is machine-specific):
  ```json
  {
    "serve_default_site": false,
    ...
  }
  ```
  Change `"serve_default_site": true` to `false`.

- [ ] **Step 5: Restart bench**

  ```bash
  bench restart
  ```

- [ ] **Step 6: Verify the page loads**

  Open `http://mysite.local:8000/app/sbiqc-provisioning` in the browser.  
  Expected: Sidebar with 5 nav items visible. Tenants section shows KPI strip. No JS console errors.

- [ ] **Step 7: Verify theme switching works**

  In Frappe, click the top-right Help menu → Toggle Theme → switch between Frappe Light / Timeless Night / SBIQ Core.  
  Expected: Dashboard colours update immediately with no hardcoded colours bleeding through.

- [ ] **Step 8: Commit any config changes that ARE safe to commit**

  Only commit app files — never `common_site_config.json`, `Procfile`, or `config/redis_*.conf`:
  ```bash
  git status
  # Confirm only sbiqc_provisioning app files are staged
  git add apps/sbiqc_provisioning/
  git commit -m "chore(provisioner): post-install verification — all sections live on mysite.local"
  ```

---

## Task 11: Smoke test all 5 sections

- [ ] **Step 1: Test New Tenant wizard end-to-end**

  1. Click "+ New Tenant".
  2. Step 1: Enter subdomain `smoke-test`, client name `Smoke Test Co`, plan `Starter`. Verify live preview shows `smoke-test.localhost`. Click Next.
  3. Step 2: Select `erpnext` (pre-checked). Click Next.
  4. Step 3: Confirm summary shows correct values. Click Provision.
  5. Expected: Alert "Provisioning queued for smoke-test.localhost". Tenant row appears in list with status `Provisioning`.

- [ ] **Step 2: Test Queue section**

  1. Click "Queue" in sidebar.
  2. Expected: PROV-XXXX job card visible with progress bar and current step updating.
  3. If job is still Queued: Cancel button visible; click Cancel → job card shows Failed, tenant reverts to Pending.

- [ ] **Step 3: Test Health section**

  1. Click "Health" in sidebar.
  2. Expected: 7 check cards visible. Redis Cache, Redis Queue, MariaDB, Long Worker all green. Disk Free shows GB count.

- [ ] **Step 4: Test Reports section**

  1. Click "Reports" in sidebar.
  2. Expected: Monthly bar chart (may be empty if no completed provisions yet). Plan breakdown shows current tenants. Top Apps list visible.

- [ ] **Step 5: Test Errors section**

  1. If no error tenants: manually set one tenant's status to `Error` via bench console:
     ```bash
     bench --site mysite.local execute frappe.db.set_value --args "['Tenant','<name>','status','Error']"
     ```
  2. Click "Errors" in sidebar.
  3. Expected: Error row visible with Retry button. Click "▼ Traceback" to expand error log.

- [ ] **Step 6: Test Add Apps on an Active tenant**

  1. Once `smoke-test` is Active: click ⊕ (Add Apps) on its row.
  2. Slideout opens showing `erpnext` as installed (greyed). Select another available app.
  3. Click "Install Selected".
  4. Expected: Alert "App installation queued". Queue section shows new job.

---

## Self-Review Checklist

After implementing all tasks, verify:

- [ ] `delete_tenant` uses list-form `subprocess.run` (no `shell=True`)
- [ ] `tenant.json` has `currency` and `timezone` fields with defaults
- [ ] `seeder.py` passes currency/timezone from Tenant; creates admin user if email set
- [ ] `provision_update` in engine.py runs install → migrate → clear-cache → updates child table
- [ ] All 5 API functions are `@frappe.whitelist()` and call `frappe.only_for("System Manager")`
- [ ] CSS has zero hardcoded hex values — only `var(--*)` Frappe variables
- [ ] Dashboard sidebar has 5 nav items; badges on Queue and Errors update from stats
- [ ] Wizard validates subdomain regex before proceeding to Step 2
- [ ] `serve_default_site` is `false` in `common_site_config.json` (not committed)
- [ ] `tenant.js` has been deleted
- [ ] All 5 sections render without JS console errors
