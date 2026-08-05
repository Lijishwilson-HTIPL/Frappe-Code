# Mercury ERP (Frappe Bench) — Change & Deployment Log

Internal tracking of everything pushed to GitHub and the features shipped, so we
can roll back cleanly if a future change goes wrong.

- **Repository:** https://github.com/hephzibahtechnologies/Frappe-Code
- **Primary branch:** `paul-update` (our working branch, also on the remote)
- **Other branches of interest:** `DMS` (project-module customisation), `staging-deployment`, `main`
- **Deprecated remote:** `origin` = `Lijishwilson-HTIPL/Frappe-Code` — do **not** push there. Use remote `hephzibah`.
- **Local working copy:** `\\wsl.localhost\Ubuntu-22.04\home\paul\frappe-bench` (a real git repo, unlike the xellabs ZIP)
- **Platform:** ERPNext v16 / Frappe v16 · **Demo site:** `mysite.local` · login `Administrator`
- **Author rule:** Paul Sahaya Doss is the sole commit author — never add a Claude/Anthropic co-author trailer.
- Related but different: `CHANGELOG_DRAFT.md` (repo root) is a repo-wide feature log by
  date/branch with no commit IDs. **This** file is the Mercury project log with commit IDs
  and rollback targets.

---

## Current state

**Latest push:** `015e556ae` — "proj module ui defects fixed + task module dynamic
delivered status dropdown added" (2026-08-05)

**Local-only (NOT yet pushed):** nothing. `paul-update` is 0 ahead / 0 behind
`hephzibah/paul-update`.

**Rollback targets (newest first):**

| Tag / commit | What it is |
|---|---|
| `38932a7b4` — tag **`pre-staging-merge`** | last state before the `staging-deployment` merge |
| `3c8dd4878` — tag **`pre-dms-merge`** | last state before the `DMS` merge |
| `b5583b40d` (2026-07-22) | Mercury baseline, before any Mercury work |

**Phase status:** Phase 1 = COMPLETE (all 8 stages, config-only; only custom code is the
~3-line QR jinja helper in `apps/mercury/mercury/utils.py`). Management feedback item #1
delivered. Phase 2 (Shipment Acknowledgement DocType + QR portal) not started.

---

## Push history (newest first)

| # | Commit | Date | Pushed | Summary |
|---|--------|------|--------|---------|
| 9 | `015e556ae` | 2026-08-05 | yes | proj module UI defects fixed + Task "Delivered" status, gated per company |
| 8 | `80be0a9a2` | 2026-08-05 | yes | docs: rewrite the Mercury handoff block for the next session |
| 7 | `03a8a49b5` | 2026-08-05 | yes | merge: `staging-deployment` (DMS versioning/metrics, SBIQC login redesign, prod deploy job) |
| 6 | `38932a7b4` | 2026-08-05 | yes | docs: protect the Project/desk UI fixes from being lost in a merge — tag `pre-staging-merge` |
| 5 | `01ea91644` | 2026-08-04 | yes | merge: `DMS` — sidebar relabel + Summary tab stat tile styling |
| 4 | `c23b650eb` | 2026-08-04 | yes | merge: DMS project-module UI updates (sidebar relabel + status-accented stat tiles) |
| 3 | `3c8dd4878` | 2026-08-04 | yes | mercury: rename QI template `Mercury Steel Casting QC.` → without trailing period |
| 2 | `a609a8cef` | 2026-08-04 | yes | mercury: per-component QR shipping labels + logo, export phase-1 fixtures |
| 1 | `03c7f0d68` | 2026-08-03 | yes | mercury thin app phase 1 — configurable 8 stages |
| 0 | `b5583b40d` | 2026-07-22 | yes | (baseline before our Mercury work) merge staging-deployment into the branch |

---

### `5cbb13884` … `7f7776ce1` — Project module + desk form-shell UI fixes (2026-08-04/05) · PUSHED
17 commits fixing UI defects on the Project Summary tab and the desk form shell:
collapsible Tasks/Defects accordions (Defects closed on every login), a single
scrollbar instead of three, a genuinely pinned page head, a pinned tab bar with no gap
above it, and the right form sidebar no longer clipped at the viewport edge.

**Documented separately in [`PROJECT_UI_CHANGES.md`](PROJECT_UI_CHANGES.md)** — that file
is the re-apply guide, because `project.js` is an **erpnext core file** that a future
pull/merge can clobber. It records the root cause of each defect (most trace to
`hrms/layout_global.css` and `quality_dms.css` overriding core layout with
`!important`), the verification checklist, and the exact cherry-pick commands.

Only `apps/erpnext/.../project/project.js` is at risk; the desk CSS lives in the mercury
app as additive overrides and no frappe/erpnext/hrms file is patched.
Rollback-before-this: `3db8740fd`

## Features by commit

### `015e556ae` — Task "Delivered" status, gated per company (2026-08-05) · PUSHED
- **Why:** management asked for a `Delivered` status on Task, but only for the Mercury
  work — not for the DMS/SBIQC projects that share this Task doctype.
- **The constraint:** Frappe `Select` options are **DocType metadata**, so an option
  cannot be offered to only some records. There is no per-record variant in v16. The
  option is therefore added DocType-wide and scoped by two separate mechanisms:

  | Layer | Record / file | What it does |
  |---|---|---|
  | Option | Property Setter `Task-status-options` | appends `Delivered` between `Completed` and `Cancelled` |
  | Gate (config) | Custom Field `Company.allow_delivered_task_status` | the opt-in checkbox — ticked on **Mercury** only |
  | Scope (UI) | Client Script `Mercury - Delivered Task Status` | removes the option from the dropdown when the company hasn't opted in |
  | Scope (real) | `mercury/task_status.py` via `doc_events` | **rejects the write** — this is the actual control |

- **The Client Script is cosmetic; the `validate` hook is the enforcement.** A REST call,
  a Data Import or `frappe.db.set_value` never runs client JS. Both are required — the
  script alone is not a permission boundary. A warning to that effect is in the script
  header so nobody deletes the hook as redundant.
- **Gated on a checkbox, not a company name.** `Company` is a Link field, so its value is
  always the exact record name and `company == "Mercury"` would work today — but it would
  also match a future *"Mercury Freight Ltd"*, and enabling a second company would mean a
  code change instead of a click. Case-insensitive matching was considered and rejected
  for the same reason: link values cannot vary in case.
- **Known trade-off:** the checkbox **value** lives on the Company record, which is master
  data and *not* a fixture. On a fresh machine the field imports **unticked**, so
  `Delivered` stays hidden on Mercury tasks until someone ticks it. Either document the
  step or add an `after_migrate` hook — not yet decided.
- **Latent issue, not currently reachable:** `set_tasks_as_overdue`
  (`erpnext/hooks.py`, `daily_maintenance`) flips any task **not** in
  `("Cancelled", "Completed")` with a past `exp_end_date` to `Overdue` — which would
  silently un-deliver a Delivered task. Every PROJ-0001 task has `exp_end_date = None`,
  so it cannot fire today. **If end dates are ever added, this must be handled** (override
  `update_status` from the mercury app; do not patch erpnext core).
- Also cosmetic: `task_list.js` has a hardcoded status→colour map with no `Delivered`
  key, so the list-view indicator renders without a colour.
- Fixtures exported (`.claude/rules.md`): `custom_field.json`, `property_setter.json`,
  `client_script.json`, all filtered by `module = Mercury`.
- **Verified:** `Delivered` saves on a Mercury task; blocked with a validation error on a
  *Hephzibah Technologies India* task. Both tests rolled back — PROJ-0001 untouched at
  78.57%.
- Rollback-before-this: `80be0a9a2`

### `<pending>` — collapsible Tasks/Defects sections on the Project Summary tab (2026-08-04) · PUSHED in `015e556ae` and earlier
- **Why:** the Mercury demo shouldn't show a "Defects" panel (DMS/SBIQC terminology,
  always 0 for a manufacturing project). Rather than hard-hide it, both sections on the
  Project Summary tab are now **accordions**, so it can be folded away for the demo and
  unfolded again after.
- Header (chevron + icon + title + **count badge** + View All) is clickable; panel uses
  the `grid-template-rows: 0fr → 1fr` trick so it animates to natural height without a
  hardcoded max-height. Keyboard accessible (`role=button`, `tabindex=0`,
  `aria-expanded`, `aria-controls`, Enter/Space), and honours
  `prefers-reduced-motion`.
- **Default is EXPANDED** and the collapsed state is stored per section in
  `localStorage` (`project_summary_collapsed::<title>`). Deliberate: this file is shared
  with the DMS/SBIQC project module, so nobody else's view changes until they collapse it
  themselves — and Paul collapses Defects once and it stays collapsed for the demo.
- Styled with frappe theme variables (`--fg-hover-color`, `--control-bg`, `--text-muted`,
  `--primary`) rather than fixed hex, so it is correct in dark mode.
- `View All` sits inside the clickable header, so its click is `stopPropagation`'d —
  otherwise opening the list would also toggle the section.
- File: `apps/erpnext/erpnext/projects/doctype/project/project.js`
  (`show_task_defect_summary_tab`). Doctype client script — no `bench build` needed,
  just `bench clear-cache` + hard reload.
Rollback-before-this: `3db8740fd`

### `<pending>` — Outgoing QIs for the whole kit + Stage 6 guide rewrite (2026-08-04) · PUSHED
- **Unblocked `MAT-DN-2026-00003` for submission.** All 4 kit items carry *Inspection
  Required before Delivery*, and erpnext (`stock_controller.py:1463`) requires a
  **submitted QI on every row** (`Delivery Note Item.quality_inspection`), not one per
  shipment. Created + submitted 4 Outgoing QIs against the DN:
  `MAT-QA-2026-00003` pump (sample 1), `-00004` BFV-8 (2), `-00005` LG-01 (1),
  `-00006` EJ-8 (3) — all Accepted, each linked on its row.
  Verified by running `submit()` inside a transaction and rolling back:
  **submits cleanly, DN left in draft on purpose** (Packing Slips need a draft DN).
- **New QC template "Mercury Accessory Final QC"** (Visual / Surface Finish, Dimensional /
  Flange Fit, Marking / Tag Present) — the pump's leak/performance/paint checks don't
  apply to a valve or gauge. One shared template rather than three per-item ones.
- **Closed a reproducibility gap:** template rows link to **Quality Inspection Parameter**
  records that were in no fixture, so a fresh `bench migrate` would have failed the
  template import with `LinkValidationError`. Added a `Quality Inspection Parameter`
  fixture (9 records), listed **before** the template entry since fixtures import in
  hooks order.
- **Stage 6 of `web docs/mercury_phase1_stepbystep_guide.txt` rewritten** for the
  per-unit-QR flow so it can be practised from scratch: revised 6a–6e, new 6f
  (Packing Slip → submit), a "what changed from v1" section, and the new gotchas
  (td-img width override, serial naming-series conflict, QI Parameter links,
  exact-match non-numeric readings, wkhtmltopdf/PATH). Guide 643 → 776 lines.
Rollback-before-this: `733f94aba`

### `c23b650eb` — merge DMS project-module UI updates (2026-08-04) · PUSHED
- Merged `hephzibah/DMS` into `paul-update` with `--no-ff` (explicit, revertable merge point).
- Only **2 commits** were actually new — DMS's heavy project rework was already in our
  branch (merge base `65e41eb82`, which includes `90f263546` "rebuild overview home page,
  rename Issue to Defect, brand as SBIQC"):
  - `00f1bcd84` style(project): Summary tab stat cards → status-accented tiles
  - `85d9baa17` rename(dms): relabel sidebar sections/links
- Files touched: `apps/erpnext/erpnext/projects/doctype/project/project.js`,
  `apps/quality_dms/quality_dms/workspace_sidebar/dms.json`. **Zero conflicts.**
- Verified `git diff pre-dms-merge HEAD -- apps/mercury workprogress_mercury.txt .gitignore`
  was **empty** — no Mercury work altered.
- ⚠ **Watch:** `project.js` is the Project doctype client script that Mercury Stage 4 and
  the Stage 8 Monthly Progress Report rely on. Changes are cosmetic but SBIQC/DMS-branded
  ("Defect" instead of "Issue") and will show on `PROJ-0001` in the Mercury demo.
Rollback-before-this: `3c8dd4878` (= tag `pre-dms-merge`)

### `3c8dd4878` — rename QI template, drop trailing period (2026-08-04)
- `Mercury Steel Casting QC.` → `Mercury Steel Casting QC` via `frappe.rename_doc`, so the
  submitted Quality Inspection `MAT-QA-2026-00001` was relinked automatically (verified: 0
  stale references).
- Re-exported `fixtures/quality_inspection_template.json`.
Rollback-before-this: `a609a8cef`

### `a609a8cef` — per-component QR labels + Mercury logo + fixtures (2026-08-04)
**Management feedback #1:** one QR for the whole bundle meant the customer could not
confirm each loose component. Every physical unit now gets its own label and QR.

- **Kit changed:** dropped `BOLT-M16` / `NUT-M16` from the shipment (Item records still
  exist, just not in the kit); added 3 serial-tracked accessories so every unit has a
  unique identity — `BFV-8` 8" Butterfly Valve ×2, `LG-01` Level Gauge ×1,
  `EJ-8` 8" Expansion Joint ×3, plus `MERCURY-001` pump ×1 = **7 units**.
- **Print Format "Mercury Shipping Label" rewritten:** page 1 = shipment manifest
  (`Label 1/7…7/7`, serial, "Unit 2 of 3"); then **one full label page per unit** with the
  serial in large mono, `LABEL n OF 7`, and its **own QR**.
- **QR payload now per-unit and Phase-2 ready:**
  `{site}/shipment-ack?dn=<DN>&item=<code>&sr=<serial>` (was `doc.name`, i.e. identical on
  every label). Verified all 7 payloads distinct.
- **Logo** added to all 8 headers, stored as a **file** in the app
  (`apps/mercury/mercury/public/images/mercury_logo.png` + `.svg`), served via the existing
  `sites/assets/mercury` symlink. Size is one jinja var: `logo_w = 106`.
- **Fixtures exported** (per `.claude/rules.md`) — enabled the 3 commented hooks and ran
  `bench --site mysite.local export-fixtures --app mercury`: both print formats, the
  30/40/30 Payment Terms Template, and both QI Templates now live in git instead of only
  in the local DB. This cleared export debt carried since 2026-07-29.
- `.gitignore`: added `.env` (machine-local honcho PATH injection for wkhtmltopdf).
Rollback-before-this: `03c7f0d68`

### `03c7f0d68` — Mercury thin app, Phase 1, 8 configurable stages (2026-08-03)
- Thin `mercury` app as a config container (fixtures in git; JSON = source of truth).
- "Mercury" Workspace + Workspace Sidebar + Desktop Icon navigation.
- Stage 2 workflow "Mercury RTM Approval" on Sales Order + its states/actions, exported.
- Stages 1–8 built config-only; the only custom code is the ~3-line QR jinja helper
  (`mercury.utils.qr_base64`) registered via `hooks.jinja`.
Rollback-before-this: `b5583b40d`

---

## Gotchas worth not re-learning

- **Print format images:** frappe injects a legacy hack
  `body:last-child .print-format td img { width:100% !important }`. An image inside a `<td>`
  therefore ignores any inline width, making the **desk preview and the PDF disagree**.
  Fix: wrap the `<img>` in a fixed-width `<div>` and give the img `width:100%`.
- **Logo sizing:** never hardcode both width and height (stretches the image). Set width
  only, `height:auto`. Also crop transparent padding first — a logo that is mostly padding
  gets "sized by its padding".
- **Serial naming series:** if `tabSeries` has no counter row for a prefix but serials
  already exist, auto-generation throws "naming series conflict". Supply serials explicitly
  (`use_serial_batch_fields=1` + `serial_no`) and sync `tabSeries`.
- **Packing Slip** can only be attached to a **draft** Delivery Note.
- **wkhtmltopdf:** must be **0.12.x with patched qt**. Frappe calls it by bare name with no
  site_config override, so it must be on the PATH of the bench processes. Installed
  without root at `~/opt/wkhtmltox`; PATH injected via `~/frappe-bench/.env` (honcho reads
  it on `bench start`). **`bench restart` does not pick this up — fully restart
  `bench start`.** Both are machine-local and NOT in git.

---

## How to roll back

This repo is a real clone, so rollbacks happen here directly.

Undo the DMS merge but keep everything else (safest — history preserved):

```
git revert -m 1 c23b650eb
```

Move the branch back to the last known-good commit (local only, nothing pushed yet):

```
git reset --hard pre-dms-merge      # = 3c8dd4878
```

If a bad commit was already pushed, prefer a revert over a force-push, since this branch
is shared:

```
git revert <bad-commit-id>
git push hephzibah paul-update
```

Force-push only if you are certain nobody else has the branch:

```
git push --force-with-lease hephzibah paul-update
```

> After any rollback that changes DocType/config JSON, run
> `bench --site mysite.local migrate` so the database matches the fixtures again.

---

## Log new entries here as we push

<!--
Template:
### <commit-id> — <short title> (<date>)
- what changed / features
Rollback-before-this: <previous commit-id>
-->
