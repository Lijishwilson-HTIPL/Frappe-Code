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
