# Frappe Bench — Project Rules

## 1. All Frappe changes must be in JSON, never in the database

**Rule:** Any change to a DocType (fields, field_order, options, labels, layout) must be made by editing the app's JSON file and running `bench migrate`. Never use direct SQL, `frappe.db`, or the Python console to modify schema or layout data.

**Why:** Direct DB changes are wiped on the next `bench migrate` or fresh install. JSON changes in the app directory are version-controlled, shareable via git, and automatically re-applied on every migration.

### Correct flow for DocType field changes:
1. Edit the JSON — e.g. `apps/crm/crm/fcrm/doctype/crm_lead/crm_lead.json`
2. Run `bench --site mysite.local migrate`
3. Commit the JSON to git

### Correct flow for CRM Fields Layout (Data Fields, Side Panel, Quick Entry):
1. Make the change in the Frappe/CRM UI and save
2. Export fixtures: `bench --site mysite.local export-fixtures`
3. Commit the exported fixture JSON to git

### Never do this:
- `UPDATE \`tabCRM Fields Layout\` SET layout=...` (direct SQL)
- `frappe.get_doc(...).save()` from bench console for schema/layout changes
- Any Python script that patches the DB directly instead of going through JSON + migrate

---

## 2. API credentials must be stable across restarts

**Rule:** Do not regenerate Frappe API keys/secrets unnecessarily. Every time `bench serve` restarts, it does NOT reset keys — but `generate_keys` overwrites them. Only regenerate when explicitly needed and always update the `.env` on the backend server immediately after.

**Backend `.env` location:** `/var/www/html/frappe_backend_staging/.env` on the `185` server.

---

## 3. site_config.json must never be committed or merged

**Rule:** `sites/mysite.local/site_config.json` (and any `sites/*/site_config.json`) must never be committed to git, staged, or allowed to be overwritten by a merge. It is listed in `.gitignore` and must stay untracked.

**Why:** `site_config.json` contains the database name, DB password, and encryption key specific to each server. If it gets committed and merged, a pull on another server will overwrite that server's credentials, breaking the DB connection entirely (as happened when paul-update overwrote the local DB name from `_c059e81fe917cb98` to `_61803d1237a06352`).

### Rules:
- Never run `git add sites/` without explicitly excluding `site_config.json`
- Never commit `site_config.json` — even temporarily
- If a merge overwrites it, immediately restore from git history: `git show <pre-merge-commit>:sites/mysite.local/site_config.json > sites/mysite.local/site_config.json`
- Each server (local, staging, production) has its own `site_config.json` — they are intentionally different and must never be shared via git

### If site_config.json accidentally gets tracked:
```bash
git rm --cached sites/mysite.local/site_config.json
git commit -m "chore: untrack site_config.json"
```

---

## 4. This is part of the MFT multi-project system
**Full architecture, rules, and project overview are in the main CLAUDE.md:**
`C:\Users\Paul Sahaya Doss\Downloads\mft-landing-page\CLAUDE.md`

Read that file first for the full picture. All cross-project rules defined there apply here too.

### MFT-Specific Frappe Notes
- **Custom DocType:** `mft_license` — handles post-payment license generation
- **Key method:** `process_payment(stripe_session_id, name, org, email)`
  - Returns: `invoice_number`, `license_key`, `purchase_date`, `amount`
- **Triggered by:** Express backend after Stripe payment confirmed
- **Other integrations:** Helpdesk HD Tickets, Job Openings (HRMS), Career Inquiries, Job Applicants

### Project Locations (for cross-project edits)
| Project | Path |
|---|---|
| Frontend (Next.js) | `C:\Users\Paul Sahaya Doss\Downloads\mft-landing-page` |
| Backend (Express) | `C:\Users\Paul Sahaya Doss\Downloads\logs` |
| Work Progress Log | `workprogress.txt` (this bench root)
