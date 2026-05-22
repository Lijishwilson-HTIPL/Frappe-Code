# Session Compact Summary — 2026-05-22

## Agent Pipeline Created
Location: `/home/ijish/frappe-bench/.claude/agents/`
4 agents: `team-lead.md` → `developer.md` → `tester.md` → `release-manager.md`
Also zipped at: `frappe-bench/agents.zip`

**Flow:** Team Lead receives requirement → delegates to Developer → Tester validates → Release Manager commits & pushes to GitHub.
**Rule:** All changes in JSON/Python/JS files only. No direct DB writes. No pushes to `main`.

---

## Changes Collected (NOT YET PROMOTED — waiting for "promote it")

### 1. HR App — Logo & Rename
- `apps/hrms/hrms/hooks.py`
  - `app_title`: `"Frappe HR"` → `"HR"`
  - `add_to_apps_screen` title: `"Frappe HR"` → `"HR"`
  - logo: `frappe-hr-logo.svg` → `HRv2.png`
- `apps/hrms/hrms/public/images/HRv2.png` — new custom logo (copied from `C:\Users\Lijish\Downloads\HRv2.png`)
- Run `bench build --app hrms` after promoting.

### 2. ERP App — Logo & Rename (already committed in submodule, not pushed)
- `apps/erpnext/erpnext/hooks.py` — `app_title`: `"ERPNext"` → `"ERP"`, logo → `erpnext-logo-blue.png`
- `apps/erpnext/erpnext/public/images/erpnext-logo-blue.png` — custom logo
- Submodule remote: `Lijishwilson-HTIPL/erpnext.git`, branch: `version-15`
- Key commits: `b6d1b0889d` (rename + logo), `16eeabc726` (logo update)

### 3. Helpdesk App — Logo
- `apps/helpdesk/helpdesk/hooks.py`
  - logo: `favicon.svg` → `Helpdesk.png`
- `apps/helpdesk/helpdesk/public/images/Helpdesk.png` — new custom logo (copied from `C:\Users\Lijish\Downloads\Helpdesk.png`)
- Run `bench build --app helpdesk` after promoting.

### 4. CRM Submodule — 15 Unpushed Commits
Remote: `hephzibahtechnologies/frappe-demo.git` (origin/main), branch: `main`
All 15 commits already committed locally, none pushed. Key changes:
- `a4f64a22` — Royal Purple website theme fixture
- `dec1334e` — Lead Data tab rename, stage conditional rendering (New→Converted), export time range filter, dynamic record count, status flow restriction
- `73418a7f` — CRM Lead DocType field updates
- `10ed5cc4` → `59d890ae` → `74f7311f` → `74a137b2` — Leads Journey full implementation (backend API, sidebar page, dashboard component, chart type)
- `35e08c20` — Renamed workspace → SBIQ CRM
- `70eeab1b` — Removed hardcoded Desk from Apps menu
- `f74fe8b6`, `3f44da81`, `5e9e7b07` — Custom CRM logo
- `a7ef9633`, `f7135e94` — CRM lead updates, workspace & component sync

### 5. CRM Lead — Auto Email on Website Inquiry (new code)
- `apps/crm/crm/fcrm/doctype/crm_lead/crm_lead.py`
  - Added `send_inquiry_followup(lead_name)` — top-level function (not a class method)
  - Triggered from `after_insert` via `frappe.enqueue` when lead has `website_message` + `email`
  - Sends email automatically using `frappe.sendmail` with `now=True`
  - Email template (professional, formal):
    - Subject: `Discussion Call Scheduled — {primary_interest} | Hephzibah Technologies`
    - Body pulls dynamically: `first_name`, `organization`, `industry`, `job_title`, `primary_interest`, `website_message`, `preferred_contact`
    - Tone: "Thank you for reaching out… We understand you are looking for support with [interest]… As per the preferred time shared by your team, we have scheduled the discussion call accordingly…"
  - Sender: default outgoing email account or `contact@hephzibahtech.in`

### 6. Helpdesk — Ticket Data Tab (already committed in parent repo)
- Commit `17ec60d6e` in parent repo includes:
  - `TicketDataTab.vue` — "Ticket Data" tab in ticket view
  - `TicketJourney.vue` — journey sidebar panel
  - Status flow, ticket fields

---

## Submodule Status Summary

| App | Type | Status | Remote |
|-----|------|--------|--------|
| CRM | Submodule | 15 commits ahead, NOT pushed | `hephzibahtechnologies/frappe-demo.git` |
| ERP | Submodule | commits ahead on `version-15`, NOT pushed | `Lijishwilson-HTIPL/erpnext.git` |
| HRMS | Tracked files | hooks.py modified, HRv2.png untracked | parent repo |
| Helpdesk | Tracked files | hooks.py modified, Helpdesk.png untracked | parent repo |

---

## Files Pending Staging & Commit (parent repo — `Lijish-up` branch)

```
M  apps/hrms/hrms/hooks.py
?? apps/hrms/hrms/public/images/HRv2.png
M  apps/helpdesk/helpdesk/hooks.py
?? apps/helpdesk/helpdesk/public/images/Helpdesk.png
M  apps/crm/crm/fcrm/doctype/crm_lead/crm_lead.py   (in CRM submodule)
```

---

## Discovery Call Flow (Website → CRM)
- Website: `C:\Users\Lijish\Desktop\Website`
- Form fields sent to Frappe CRM: `first_name`, `last_name`, `email`, `mobile_no`, `organization`, `job_title` (role), `industry` (orgType), `website_message` (message), `primary_interest` (interest), `preferred_contact`, `how_found_us` (referral)
- Backend: `frappeCrmClient.createEmailDraft` in `Backend/src/utils/frappeCrmClient.js` — creates draft Communication in Frappe with `send_email: 0` (stays as draft, do NOT change)
- Auto-email is handled by `crm_lead.py` `after_insert` → `send_inquiry_followup()` via Frappe queue

---

## Key Rules (from CLAUDE.md)
- All DocType/layout changes → JSON files + `bench migrate`. Never direct DB/SQL.
- CRM Fields Layout → UI save → `bench --site mysite.local export-fixtures` → commit JSON.
- API keys: do NOT regenerate unless explicitly requested.
- Never push to `main` directly.

---

## Pending Action
User has not yet said "promote it". All changes above are staged in conversation only.
When user says "promote it":
1. Commit HRMS hooks.py + HRv2.png to parent repo
2. Commit Helpdesk hooks.py + Helpdesk.png to parent repo
3. Commit crm_lead.py change to CRM submodule
4. Push CRM submodule to `hephzibahtechnologies/frappe-demo.git` main
5. Push ERP submodule to `Lijishwilson-HTIPL/erpnext.git` version-15
6. Update parent repo submodule pointers
7. Push parent repo `Lijish-up` branch
