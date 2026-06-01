# Frappe Bench — Project Rules

## 0. On Every Session Start — Read Rules & Update Memory

**When you open this project (after a pull or fresh clone), you MUST:**

1. Read `CLAUDE.md` (this file) — all rules apply immediately
2. Read `deployment-comment.md` — deployment flow, .env rules, Redis fix, push rules
3. Update your memory with anything new or changed since the last session

**Why:** The team shares rules through git. A `git pull` may bring new rules. If you don't read and save them to memory, you will repeat mistakes the team has already documented and solved.

### What to save to memory after reading:
- Any new rules added to `CLAUDE.md` or `deployment-comment.md`
- Any known gaps or fixes documented (Redis paths, site_config.json protection, .env rules)
- The push rule: **never push to GitHub unless explicitly told "promote it"**

---

## 0b. On Every Task — Run Agents First

**When any feature, fix, or change request is given, the agent pipeline runs first — always.**

```
Team Lead → Developer → Tester → Compliance Checker → Release Manager
```

1. **Never implement directly** — always delegate to the `team-lead` agent first
2. Team Lead breaks it down and sends to `developer`
3. Developer implements → `tester` validates → `compliance-checker` approves → `release-manager` commits
4. Only after the full pipeline passes does the change get promoted

**Why:** Direct edits skip testing and compliance. This is healthcare software — every change must go through the pipeline so nothing ships untested or non-compliant.

**Agents are in:** `.claude/agents/` — `team-lead.md`, `developer.md`, `tester.md`, `compliance-checker.md`, `release-manager.md`

---

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

## 3. site_config.json must never be committed, merged, or lost

**Rule:** `sites/mysite.local/site_config.json` must never be committed to git, staged, or overwritten by a merge. It is gitignored and must stay untracked on every machine.

**Why:** This file contains the DB name, DB password, and encryption key specific to each server. If it gets overwritten or lost during a merge/stash, Frappe shows "mysite.local does not exist" and the entire bench stops working. This actually happened on 2026-06-01 after merging Lijish-up — site_config.json went missing and had to be restored from an old git commit.

### Rules:
- Never run `git add sites/` — always add files explicitly by path
- Never commit `site_config.json` — even temporarily
- Before any git merge or stash operation, verify the file exists: `cat sites/mysite.local/site_config.json`
- Each server (local, staging, production) has its own `site_config.json` — they are intentionally different and must never be shared via git

### If site_config.json goes missing, restore from git history:
```bash
git show 25b22572f:sites/mysite.local/site_config.json > sites/mysite.local/site_config.json
```
Local site_config.json values (as of 2026-06-01):
- `db_name`: `_61803d1237a06352`
- `db_password`: `mysite123`
- `encryption_key`: `O9zVFd86kAIajafOvsDGHWQAkZQsvBD3CQXm9dkTeLY=`

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
