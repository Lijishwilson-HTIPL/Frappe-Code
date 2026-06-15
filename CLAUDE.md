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

## 0c. Self-Learning — Update Rules on Every New Discovery

**Every mistake, correction, failed command, or new pattern must be recorded here immediately — before the task is reported as done.**

This is how the rulebook grows. If it is not written down, the same mistake will happen again in a future session.

### Triggers — update CLAUDE.md when ANY of these happen

| Trigger | Example |
|---|---|
| User corrects you | "no, don't do that", "wrong approach", "stop doing X" |
| A command fails and you find a workaround | `node` not on PATH during migrate |
| You make the same mistake twice | Forgetting to bump `modified` in JSON |
| A new pattern proves reliably better | `get_list` over `get_all` for permission enforcement |
| A tool or API behaves unexpectedly | Edit tool fails if file was not Read first |
| A protected file is almost committed | Procfile, site_config.json, uichange*.css |
| An assumption about environment turns out wrong | Wrong WSL distro, wrong bench path |

### Entry format — add under the relevant section or create a new one

```
**[Short title] — [YYYY-MM-DD]:**
- Root cause: [why it happened]
- Fix: [what resolves it]
- Rule: [one sentence — what to do or never do going forward]
```

### Where to write

- **CLAUDE.md** — for technical rules, environment facts, and command patterns. Shared via git; applies on every machine.
- **Memory** (`C:\Users\Hilton\.claude\projects\...\memory\`) — for behavioral feedback, user preferences, and personal guidance. Applies only to this assistant instance.
- **Both** — when a mistake is both a technical gotcha (CLAUDE.md) and a behavioral correction (memory `feedback` type).

### Mandatory end-of-task checklist

Before reporting a task complete, answer each of these:
1. Did anything fail that needed a workaround? → Document the workaround here
2. Was I corrected by the user during this task? → Add it as a rule
3. Did I discover a new "always" or "never" pattern? → Add it
4. Did a command need a specific path or flag that is not obvious? → Record it in the environment facts below

---

### Environment facts (update whenever a new fact is discovered)

These were all learned the hard way — do not re-discover them:

**WSL / shell:**
- Always use `wsl -d Ubuntu-22.04 -e bash -lc '...'` via PowerShell — the Bash tool connects to the wrong WSL distro and cannot see the repo
- Use single quotes for the entire `bash -lc` argument in PowerShell so PS does not expand `$HOME`, `$PATH`, or other variables inside the string
- `$HOME` inside a PowerShell double-quoted string becomes empty — always single-quote the whole arg

**bench / migrate:**
- `bench` is at `~/.local/bin/bench` — use `bench --site mysite.local migrate` from `/home/hilton/frappe-bench`
- `../env/bin/python -m frappe.utils.bench_helper` does NOT work — it errors with `apps.txt Not Found`; always use the `bench` CLI directly
- `bench migrate` calls `Popen("node", ...)` for Website Theme compilation — node must be on PATH. Prefix with `export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"` before running migrate in a bash -lc call
- After editing any DocType JSON or Workspace JSON, the `"modified"` timestamp **must be bumped** to a future value or `bench migrate` silently skips syncing that document

**Frappe API:**
- Use `frappe.get_list` (not `frappe.get_all`) whenever the current user's permissions must be enforced — `get_all` bypasses permission checks
- Use `frappe.db.rollback()` at the end of any test/E2E script to leave the DB clean — never leave test data behind
- `doc.save()` triggers hooks, validation, and Version records — `frappe.db.set_value` bypasses all of these; prefer `doc.save()` for business logic changes

**File editing tools:**
- Always `Read` a file at least once before calling `Edit` on it — Edit will error if the file has not been read in this session
- Always `Read` a file before calling `Write` on it even if it is new or empty — Write will error otherwise
- `frappe.db.insert` on a doc dict bypasses validation hooks — use `frappe.get_doc(dict).db_insert()` or `frappe.get_doc(dict).insert()` instead

**`bench start` Redis crash — "Can't chdir to config/pids":**
- Root cause: `config/pids/` is gitignored as a directory, so it disappears after every clone/pull
- Fix: `.gitignore` must ignore only `config/pids/*.pid` (not the whole directory); a `config/pids/.gitkeep` must be committed so git tracks the directory
- Rule: if `bench start` crashes immediately with "Can't chdir to config/pids", run `mkdir -p config/pids` — then commit `.gitkeep` + `.gitignore` fix so it doesn't recur

**PowerShell ↔ WSL file paths:**
- All UNC paths to WSL files use `\\wsl.localhost\Ubuntu-22.04\home\hilton\frappe-bench\...`
- Never use `git add sites/` — always add files explicitly by path to avoid staging site_config.json

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

## 3b. Machine-specific config files must never be committed

**Rule:** Never stage or commit these files — they contain machine-specific paths and will break other developers' environments:
- `Procfile`
- `config/redis_cache.conf`
- `config/redis_queue.conf`
- `config/redis_cache.acl`
- `config/redis_queue.acl`

**Why:** These files embed the local Linux username (e.g. `/home/ijish/`) in paths. Committing them overwrites another machine's working paths and causes Redis/bench to fail on startup.

**After editing these files locally:** do NOT run `git add Procfile` or `git add config/redis_*.conf`. Always add files explicitly by path and skip these.

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

## 4. DocType Export Rule — JSON is the Source of Truth

**Any time a DocType is created or modified, export it to JSON immediately.**

The database is not the source of truth — the JSON file is. Changes saved only to the DB:
- Will not survive a fresh `bench restore`
- Will not appear in `git diff`
- Will not apply on another machine via `bench migrate`

### Export workflow

```bash
# Export a single DocType
bench --site mysite.local export-doc "DocType" "<DocType Name>"

# Export all fixtures for an app
bench --site mysite.local export-fixtures --app <app_name>

# Confirm what changed
git diff apps/
```

### Checklist before every commit
- [ ] Every modified DocType has been exported to JSON
- [ ] `git diff` shows only intentional JSON changes
- [ ] No DocType was changed only in the database without a JSON update

### Custom Fields and Property Setters

Custom Fields/Property Setters added via **Customize Form** also live in the database. Export them as fixtures by adding to `hooks.py`:

```python
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Your Module"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Your Module"]]},
]
```

### Backup mysite.local

```bash
bench --site mysite.local backup --with-files
# Saved to: ~/frappe-bench/sites/mysite.local/private/backups/
```

---

## 5. Frappe HR Theme & CSS Rules

### Use CSS variables — never hardcode colors

```css
--primary            /* Primary brand color */
--text-color         /* Main text */
--bg-color           /* Page background */
--card-bg            /* Card/widget background */
--border-color       /* Borders */
--navbar-bg          /* Navbar background */
--input-bg           /* Form inputs */
```

### Specificity hierarchy

```css
/* Try low first */
.btn-primary { color: red; }
/* Escalate only if needed */
body[data-theme="light"] .btn-primary { color: red !important; }
```

### Always provide dark + light mode variants

```css
body[data-theme="light"] .my-element { background: var(--bg-color); }
body[data-theme="dark"]  .my-element { background: var(--bg-color); }
```

### Where to place custom CSS

- **Recommended:** `Setup > Website > Website Theme` → Custom CSS field
- **App-level:** `apps/your_app/your_app/public/css/custom.css` + include in `hooks.py`
- **Never:** edit core Frappe files

### After every CSS change

```bash
bench --site mysite.local clear-cache
bench build --app hrms      # or whichever app
bench restart
```
Browser: hard-refresh with `Ctrl+Shift+R`

### Wrap all custom CSS fixes with comments

```css
/* FIX: [Description] - [Date] */
.selector { property: value; }
/* END FIX */
```

### Common glitch fixes

**Primary color not applying to buttons:**
```css
:root { --primary: #YOUR_COLOR; --btn-primary-bg: #YOUR_COLOR; }
.btn-primary { background: var(--primary) !important; background-image: none !important; }
```

**Form tabs misaligned:**
```css
.form-tabs-list { display: flex !important; overflow-x: auto; border-bottom: 1px solid var(--border-color); }
```

**Modals behind sidebar:**
```css
.modal-backdrop { z-index: 1040 !important; }
.modal          { z-index: 1050 !important; }
```

---

## 7. HRMS Theme Switcher Rules (uichange1–9)

**Files (local-only, gitignored):**
- `apps/hrms/hrms/public/css/uichange1–9.css` — one file per theme
- `apps/hrms/hrms/public/js/theme_switcher.js` — registers all 9 themes

**These files must NEVER be committed.** They are in `.gitignore` via `uichange*.css` glob. To restore them after a `git rm --cached` or fresh clone, run:
```bash
git checkout <commit-hash> -- apps/hrms/hrms/public/css/uichange1.css ... uichange9.css apps/hrms/hrms/public/js/theme_switcher.js
git rm --cached apps/hrms/hrms/public/css/uichange*.css apps/hrms/hrms/public/js/theme_switcher.js
```
The commit with all 9 themes is: `3db603798^` (parent of "chore: gitignore uichange1-9 themes and theme_switcher.js"). Restore with:
```bash
git show 3db603798^:apps/hrms/hrms/public/js/theme_switcher.js > apps/hrms/hrms/public/js/theme_switcher.js
```

### Backup & Restore (Windows zip — primary method)

**Backup location:** `C:\Users\Hilton\hrms-themes.zip` (last updated 2026-06-08)

Contains all 10 files with folder structure preserved:
```
css/uichange1.css … css/uichange9.css
js/theme_switcher.js
```

**To restore after a `git pull` wipes the files**, run in PowerShell:
```powershell
$zip  = "C:\Users\Hilton\hrms-themes.zip"
$dest = "\\wsl.localhost\Ubuntu-22.04\home\hilton\frappe-bench\apps\hrms\hrms\public"
Expand-Archive -Path $zip -DestinationPath $dest -Force
```

**To update the zip after editing any theme file**, say "update theme backup" — Claude will re-zip automatically. Or run:
```powershell
$src   = "\\wsl.localhost\Ubuntu-22.04\home\hilton\frappe-bench\apps\hrms\hrms\public"
$tmp   = "$env:TEMP\hrms-themes"
New-Item -ItemType Directory -Force "$tmp\css","$tmp\js" | Out-Null
Copy-Item "$src\css\uichange*.css" "$tmp\css\"
Copy-Item "$src\js\theme_switcher.js" "$tmp\js\"
Compress-Archive -Path "$tmp\*" -DestinationPath "C:\Users\Hilton\hrms-themes.zip" -Force
Remove-Item $tmp -Recurse -Force
```

### Known CSS bugs and fixes (2026-06-05)

**Bug 1 — Field text invisible in themes 5–9:**
- Root cause: `-webkit-text-fill-color: transparent` from gradient page-title CSS leaks into `.frappe-control span` via CSS inheritance.
- Fix: add `-webkit-text-fill-color` explicitly on ALL `.frappe-control` input/value selectors at the END of each theme file.

**Bug 2 — Theme 7 & 9 (dark): transparent field wrapper backgrounds:**
- Root cause: broad `background-color: transparent` rules on `span` expose the dark body behind field wrappers.
- Fix: lock `.frappe-control .control-input, .control-input-wrapper, .awesomplete, .input-area` to `background: rgba(255,255,255,0.06)`.

**Bug 3 — Theme 9 workspace link text invisible (DEFINITIVE FIX via JS 2026-06-05):**
- Root cause chain: (1) original theme injects `html body *{color:#EDE9FE!important}` as body `<style>`. (2) CSS overrides partially work but workspace section cards render inside `.form-section` context. (3) Our own form-restore step (`form-section * { color:#EDE9FE }`) then makes those link items light on white = invisible. No CSS `!important` chain can break this circular override.
- **Definitive fix:** JavaScript `element.style.setProperty('color', value, 'important')` — inline `!important` beats ALL CSS rules (highest priority in author origin).
- `theme_switcher.js` now has `hrms.theme._fix_t9()` which directly sets inline `!important` color on all DOM elements. It: (a) sets all main content to dark `#2E1065`, (b) restores dark-bg contexts (shortcut boxes, forms, lists, modals) to light, (c) fixes sidebar/navbar/icon letters.
- The fix is re-run on `$(document).on("page-change")` (SPA navigation) and via `MutationObserver` on `.layout-main-section` (lazy-loaded content).
- **Rule: When CSS specificity battles fail for a Frappe custom theme, use JS `el.style.setProperty('color', val, 'important')`. This is the only approach that definitively wins over all CSS including Frappe's dynamically injected styles.**

**Bug 4 — Theme 5: list-view column headers invisible (fixed 2026-06-05):**
- Root cause 1: `--subtle-fg` not set in `:root` → Frappe core picks whatever the current value is (can be dark in certain modes), making the header row background dark.
- Root cause 2: the global `span, div { color: #111827 !important }` rule in Theme 5 explicitly overrides the *inherited* teal color from `.list-row-head .list-row-col` on child spans. Explicit beats inherited even with `!important`.
- Fix applied in `uichange5.css`:
  1. Add `--subtle-fg: #CCFBF1 !important` to `:root` so Frappe's core header-row background variable is always light teal.
  2. Add explicit background on `.list-row-head, .list-row.list-row-head { background: #CCFBF1 !important }`.
  3. Add `.list-row-head span, .list-row-head div, .list-row-head .list-row-col *` selector with `color: #0D9488 !important; -webkit-text-fill-color: #0D9488 !important` to beat the global element selector.
- **Pattern:** Whenever a theme uses a broad `div, span { color: X !important }` global rule, every list/datatable header fix must target the child elements (`*`) directly — relying on inheritance from the parent row selector is NOT enough.
- **Same fix applied to Theme 6** (uichange6.css) — identical root cause, uses `--subtle-fg: #E0F2FE` and `color: #0369A1`.

**Bug 5 — Theme 7: white backgrounds on module/workspace pages (fixed 2026-06-05):**
- Root cause: glassmorphism cards use `rgba(255,255,255,0.035)` as background. This looks dark on `#0D0B1E`, but appears near-white when ANY ancestor container has a white background. The missing ancestor was `.layout-main-section-wrapper` and inner module page wrappers (`.modules-page`, `.workspace-section`, `.standard-page-container`, `.frappe-list-area`).
- Fix: added all missing page-level ancestors to the dark background rule set in uichange7.css (alongside the existing `.frappe-desk, .desk-body, .page-wrapper` block).
- **Rule:** For glassmorphism dark themes, EVERY ancestor of a glass card (all the way up to `body`) must explicitly have a dark background. A single white ancestor anywhere in the DOM tree makes all descendant glass cards appear white.

**Bug 4 — Sidebar selected module letter invisible:**
- Root cause: Frappe renders module icons as `<div class="app-icon" style="background-color:[module-color]"><span class="inner">A</span></div>`. The `.inner` letter inherits our sidebar `color: #7C6FAA` (muted violet), which doesn't contrast against the module's colored background (e.g. orange for Accounting). Result: letter invisible.
- Fix: `html[data-hrms-theme="uichange9"] .app-icon .inner { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }` — always white for the module letter regardless of background.
- Also fix SVG icons inside `.app-icon` with `fill: #FFFFFF; stroke: #FFFFFF`.
- **Rule:** Always explicitly set `.app-icon .inner` to `#FFFFFF` in any custom Frappe theme that overrides sidebar text color.

**Bug 6 — Themes 7 & 9: Task list / board view text not clearly visible (fixed 2026-06-08):**
- Root cause: List row sub-elements (`.list-subject`, `.level-item`, `.dt-cell` and their children) lacked explicit `-webkit-text-fill-color` overrides. Two cascading problems: (1) Theme 9's STEP 1 nuclear rule sets `color: #2E1065; -webkit-text-fill-color: #2E1065` globally, and STEP 6's `.frappe-list *` restore rule doesn't cover all render paths (task board, grouped lists, toolbar area). (2) Theme 7 broad rules set `color: #E2E8F0` but not `-webkit-text-fill-color`; if any Frappe-default or prior theme CSS set `-webkit-text-fill-color` on a parent element, browser uses that value instead of `color`, making text invisible.
- Fix (uichange9.css — STEP 11): Added `html[data-hrms-theme="uichange9"] .list-row *, .list-row-container *, .list-subject *, .level-item *, .dt-cell *, .dt-row *, .list-toolbar-wrapper *, .filter-area *, .standard-filter-section *` → `color: #EDE9FE; -webkit-text-fill-color: #EDE9FE`. Column headers restored to `#C4B5FD`. Kanban/board cards to `#EDE9FE`.
- Fix (uichange7.css — end of file): Same selectors (no html prefix needed — Theme 7 applies via injected `<link>` not a body attribute) → `color: #E2E8F0; -webkit-text-fill-color: #E2E8F0`. Column headers to `#A78BFA`. Kanban cards to `#E2E8F0`.
- **Rule:** When adding a list/board view to a custom Frappe theme, ALWAYS set BOTH `color` AND `-webkit-text-fill-color` on `.list-row *`, `.list-subject *`, `.level-item *`, `.dt-cell *`. Setting only `color` is not enough — `-webkit-text-fill-color` from any ancestor or prior stylesheet overrides `color` silently.

---

## 6. This is part of the MFT multi-project system
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

---

## 8. Frappe/ERPNext Development Patterns (learned 2026-06-11)

Patterns discovered during the Projects module review and enhancement session. Apply everywhere in this bench.

---

### 8a. DocType JSON — `field_order` must exactly match `fields`

**Rule:** The `field_order` array and the `fields` array must contain the exact same fieldnames — same count, no extras, no missing entries.

**Why:** Frappe silently skips rendering any field in `field_order` that has no matching entry in `fields`. Conversely, a field in `fields` with no entry in `field_order` is placed at the end randomly. After every field add/remove, verify both arrays are in sync.

```bash
# Quick count check (should print same number twice)
python3 -c "
import json, sys
d = json.load(open('path/to/doctype.json'))
fo = set(d['field_order']); ff = set(f['fieldname'] for f in d['fields'])
print('field_order:', len(fo), '  fields:', len(ff))
print('in field_order but not fields:', fo - ff)
print('in fields but not field_order:', ff - fo)
"
```

---

### 8b. Script Report — always 4 files

Every Script Report needs exactly these 4 files in `report/<report_name>/`:

| File | Purpose |
|---|---|
| `report_name.json` | Report DocType record — sets `report_type`, `ref_doctype`, `roles` |
| `report_name.py` | `execute(filters)` function — returns `(columns, data)` |
| `report_name.js` | `frappe.query_reports["Report Name"] = { filters: [...] }` |
| `__init__.py` | Empty — required for Python module discovery |

Missing any one of these causes the report to silently 404 or fail to load filters.

**`report_name.json` minimum fields:**
```json
{
  "report_type": "Script Report",
  "ref_doctype": "DocType Name",
  "is_standard": "Yes",
  "module": "Module Name",
  "roles": [{"role": "Projects User"}]
}
```

After creating, register in the Workspace JSON (`links` array + `shortcuts` array + `content` blob).

---

### 8c. Workspace JSON — `content` blob must stay in sync with `shortcuts`/`links`

**Rule:** The `content` field in Workspace JSON is a **serialised JSON string** (not an array). It is a separate copy of the layout grid. Any shortcut added to `shortcuts` must also get a `{"id": "...", "type": "shortcut", "data": {"shortcut_name": "..."}}` entry in `content`. Any link removed from `shortcuts` must also be removed from `content`.

**Why:** Frappe renders the workspace from `content`, not from `shortcuts`/`links` directly. A shortcut in `shortcuts` but missing from `content` is invisible on the workspace page. A stale entry in `content` pointing to a deleted shortcut throws a render error.

**After any workspace edit:** Search the `content` string for the affected shortcut name to confirm both sides match.

---

### 8d. Patch workflow — cleaning up DB-only custom fields

When a DocType field is added to the JSON but was previously created as a DB-only Custom Field (e.g. via Customize Form), a patch must delete the duplicate Custom Field record before migrate tries to create the real column.

**File location:** `apps/erpnext/erpnext/patches/vXX_Y/descriptive_name.py`

```python
import frappe

def execute():
    for name in ["DocType-fieldname1", "DocType-fieldname2"]:
        frappe.delete_doc("Custom Field", name, ignore_missing=True, force=1)
```

**Register at the END of `apps/erpnext/erpnext/patches.txt`:**
```
erpnext.patches.vXX_Y.descriptive_name
```

**Rule:** Never register a patch in the middle of `patches.txt` — patches run in order; inserting in the middle can cause them to be skipped on sites that already ran later patches.

---

### 8e. `@frappe.whitelist()` — required on every Python function called from JS

Any Python function invoked via `frappe.call(...)` from the browser **must** have the `@frappe.whitelist()` decorator. Without it, Frappe returns a 403 `PermissionError`.

```python
@frappe.whitelist()
def my_function(arg1, arg2):
    ...
```

Also applies to functions registered as `doc_events` hooks that can be triggered remotely. Check every new `@frappe.whitelist()` function also has `doc.check_permission("write")` when it mutates data.

---

### 8f. `frappe.sendmail` — never use `now=True` for user-facing emails

```python
# WRONG — blocks the request thread, can timeout on slow mail servers
frappe.sendmail(recipients=[...], subject="...", message="...", now=True)

# CORRECT — queued and sent by the background worker
frappe.sendmail(recipients=[...], subject="...", message="...")
```

**Rule:** Omit `now=True` in all user-facing flows. Only use `now=True` in migration patches or CLI scripts where there is no background worker.

---

### 8g. Dead code audit before cleanup — check DB counts first

Before removing a feature or module, check whether it has any live data:

```python
# In frappe console or a temp script
for dt in ["Project Update", "Activity Cost", "Sprint", "Project Template"]:
    print(dt, frappe.db.count(dt))
```

**Rule:** A feature with 0 records is safe to hide from the workspace. A feature with records — even 1 — must not have its DocType deleted without a data migration plan.

---

### 8h. Assignment sync — always update both `_assign` and child table together

This codebase uses a dual assignment system on Task:
- `_assign` — Frappe-native JSON field, used by the bell icon, `frappe.get_list` assignee filter, and all built-in assignment flows
- `task_assignees` — custom child table (Task Assignee), used by legacy board and reporting

**Rule:** Whenever a task is (re)assigned, always sync both:
1. `doc.set("task_assignees", [...])` + `doc.save()` for the child table
2. `clear_assignments(...)` + `add_assignment(...)` from `frappe.desk.form.assign_to` for `_assign`

Never update only one side — the board will show one assignee while the Task form shows another.

**Priority:** `_assign` is the source of truth for reads. When reading assignees, prefer parsing `_assign` JSON first; fall back to `task_assignees` only if `_assign` is empty.

---

### 8i. NestedSet DocTypes (`is_tree: 1`) — key rules

- The `lft` / `rgt` / `old_parent` fields are auto-managed by Frappe's NestedSet manager — never write to them manually
- Set `"nsm_parent_field": "parent_task"` (or equivalent) in the DocType JSON
- In `before_delete`: check `frappe.db.get_value("Task", {"parent_task": self.name})` and throw if children exist — Frappe does NOT block group deletion automatically
- Group tasks (`is_group = 1`) should block direct status changes; status should roll up from children

---

### 8j. E2E / integration test pattern for this bench

Write test as a standalone Python script, pipe into the frappe console, roll back at the end:

```bash
# Write script to /tmp (not inside the bench)
# Always end with frappe.db.rollback() — never leave test data behind

wsl -d Ubuntu-22.04 -e bash -lc '
export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"
cd /home/hilton/frappe-bench
../env/bin/python -m frappe.utils.bench_helper frappe --site mysite.local console < /tmp/test_script.py
'
```

**Do not use `frappe.db.commit()` anywhere in a test script.** If a test accidentally commits, you must restore from the last backup at `sites/mysite.local/private/backups/`.
