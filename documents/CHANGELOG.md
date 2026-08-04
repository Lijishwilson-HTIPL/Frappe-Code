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

**Latest push:** `3c8dd4878` — "mercury: rename QI template … without trailing period" (2026-08-04)

**Local-only (NOT yet pushed):** `c23b650eb` (DMS merge) and this changelog.

**Last known-good rollback target:** `3c8dd4878` — also tagged **`pre-dms-merge`**
(last state that is pushed *and* pre-DMS-merge).
**Mercury baseline (before any Mercury work):** `b5583b40d` (2026-07-22)

**Phase status:** Phase 1 = COMPLETE (all 8 stages, config-only; only custom code is the
~3-line QR jinja helper in `apps/mercury/mercury/utils.py`). Management feedback item #1
delivered. Phase 2 (Shipment Acknowledgement DocType + QR portal) not started.

---

## Push history (newest first)

| # | Commit | Date | Pushed | Summary |
|---|--------|------|--------|---------|
| 4 | `c23b650eb` | 2026-08-04 | **no** | merge: DMS project-module UI updates (sidebar relabel + status-accented stat tiles) |
| 3 | `3c8dd4878` | 2026-08-04 | yes | mercury: rename QI template `Mercury Steel Casting QC.` → without trailing period |
| 2 | `a609a8cef` | 2026-08-04 | yes | mercury: per-component QR shipping labels + logo, export phase-1 fixtures |
| 1 | `03c7f0d68` | 2026-08-03 | yes | mercury thin app phase 1 — configurable 8 stages |
| 0 | `b5583b40d` | 2026-07-22 | yes | (baseline before our Mercury work) merge staging-deployment into the branch |

---

## Features by commit

### `c23b650eb` — merge DMS project-module UI updates (2026-08-04) · NOT PUSHED
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
