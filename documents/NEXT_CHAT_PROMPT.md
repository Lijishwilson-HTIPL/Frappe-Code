
# START HERE — next chat prompt (paste this whole block)

You are taking over the Mercury / SBIQC ERPNext v16 work from Paul Sahaya Doss.

## Read these first, in this order

1. `CLAUDE.md` — v16-only rule, the PROTECTED UI FIXES section, and the
   DocType-changes-go-to-fixtures rule.
2. `workprogress_mercury.txt` — read section **[20] first**, then [19]. [20] is
   the current front of the work.
3. `documents/CHANGELOG.md` — the top entry (`a50434f20`) is where we are now.
4. `documents/alex_questions_delivery_ack.md` — the questions sent to Alex.

## Where things stand

The Alex demo (2026-08-13, job 1105VS10 / Evapco PO 536POR22825) went well, and
all of that work plus the 2026-08-18/20 white-labelling round is **merged to
`staging-deployment` and live on QA**. Latest merge: PR **#31** = `5e806ed82`.

`paul-update` and `staging-deployment` are level. Git is fully closed out —
nothing pending, nothing half-merged.

**Merging is not deploying, and merging is not building.** `build.yml` runs on
push to `staging-deployment` and only builds an image; `deploy-staging.yml` is
`workflow_dispatch` only and does **no** rebuild. See the two process rules
below — both were learned the hard way this round.

## Where the last session ended — 2026-08-20

The sidebar-icon defect is **DONE, deployed and verified on QA.** It grew into a
full SBIQC white-labelling round. Read `workprogress_mercury.txt` **§21** for the
whole thing — it is the front of the work now, ahead of §20.

`paul-update` and `staging-deployment` are level (PR #31 = `5e806ed82`).
Nothing is pending, nothing is half-merged.

Shipped: the 10 Projects sidebar icons; the desk grid flattened out of erpnext's
single ERPNext tile (24 real icons); favicon / page loader / login logo / window
title on the HTIPL mark; "Frappe Support" → **SBIQC Support** → docs.sbiqc.com;
the About dialog white-labelled with app icons mapped and branch names
suppressed; login-page scrollbars gone; Accounting converted from Folder to
Link; Mercury2 deleted; mercury + sbiqc_provisioning released as **1.0.0**.

**Read §21's "FIVE TRAPS" before touching any desktop icon.** Each cost real
time. The short version: `logo_url` is a plain URL and must NOT be fixed by
repointing a record's `app` (migrate's orphan sweep deletes standard icons that
way — it destroyed three); the `/desk` grid renders a per-user `Desktop Layout`
JSON snapshot, not the Desktop Icon table; never sync `label` into that snapshot;
a Folder can never display an icon; and a record's `name` is not its `label`.

**Two process rules that came out of this round, both non-negotiable:**

- **Confirm commits are on the remote before asking anyone to deploy.** For most
  of 2026-08-18 the work existed only in the working tree and the local DB, so
  the desk looked finished while the repo held nothing. PR #28 was handed over in
  that state and deployed exactly what it contained. The admin team did nothing
  wrong. Commit as you go.
- **Merge → wait for "Build & Push Images" → then Deploy to Staging.** The deploy
  does no rebuild. Deploying early runs the hooks and writes new asset paths into
  the DB while the image lacks the files — broken is worse than unchanged. If two
  PRs merge close together, deploy by explicit commit SHA, not `latest-staging`.

## Still open from that round (none urgent, none to start unasked)

- `quality_dms` and `telephony` still report `0.0.1`. quality_dms is the Quality
  Team's (James) and telephony is Frappe Technologies' vendored app — **ask**.
- SBIQC / SBIQC HR / SBIQC Provisioning are still letter tiles in the **flyout
  only** (the grid is fine). They are `icon_type = App` and their `app` field
  feeds `check_app_permission()`, so repointing it would break permissions.
- `home.png` and `htipl_logo.png` are byte-identical — Home has no artwork of
  its own.
- The About footer now reads Hephzibah Technologies. LICENSE files and source
  copyright headers in frappe/erpnext are untouched, which is where GPLv3 §5
  requires the notice — worth a legal nod before customer release.

## THE ACTUAL NEXT TASK — ask Paul for the rest of Alex's suggestions

Everything above was a detour. The real front of the work is still §20: the
customer delivery acknowledgement, which is **scoped but not built**, and gated
on **"whose phone does the scanning?"** — Paul is asking Alex. If it is
third-party freight (his bet, and mine), the app cannot live on the driver's
device and that changes the whole build. **Do not start building until that
answer lands.**

Alex gave a batch of suggestions after the demo and Paul has handed over only
the first. **Ask for the rest — do not infer them.** A previous brief cost three
sessions of guessing before it was finally handed over; that is not being
repeated.

Recommended pacing already agreed: build the **online** path first and demo it,
because it is most of the value and it reuses the Stage 6 QR labels. Offline
follows, since the answer above could still send us to the paper fallback.

## Standing rules — these are not negotiable

- **Paul Sahaya Doss is the SOLE author.** Never add a Claude/Anthropic
  co-author trailer to any commit.
- **Never push to `staging-deployment` without asking.** Raising a PR is fine
  when he asks for one; merging it is his call.
- **Never read or print `~/.git-credentials`.**
- **Never patch frappe / erpnext / hrms core.** Overrides live in
  `apps/mercury/`. The one existing exception (`is_subcontracted` restored to
  `sales_order.json`) is a bug fix, is documented, and is not a precedent.
- `mercury_desk.css` must stay **LAST** in `app_include_css`, and bump its `?v=`
  whenever it is edited.
- Any DocType or config change must be exported to fixtures and committed. The
  JSON is the source of truth, not the database.
- **Do not fix things unprompted.** Ask first.

## Verification after any merge — run all four

```bash
python3 documents/verify_ui_markers.py     # must print ALL CHECKS PASSED (28/28)
bench --site mysite.local migrate
bench --site mysite.local execute frappe.get_hooks --kwargs "{'hook':'app_include_css'}"
#   -> mercury_desk.css must be the LAST entry
```

Then check by eye: the **Projects workspace** (Light Aurora cards) and the
**Sales Order form** (RTM stepper). Those are the two places James's DMS theme
and our CSS land on the same elements, and a forced workspace reimport is
exactly how the aurora would silently revert.

## Environment gotchas

- The bench is in WSL; the shell bridge mangles `$(...)`, heredocs and loops.
  **Write a script file to `/tmp` and run it** — do not inline complex shell.
- `python` does not exist; use `python3`.
- `gh` is not installed and `sudo` is unavailable, so **PRs cannot be opened
  from the CLI** — produce the compare URL and a PR body for Paul to paste.

## Known open items (none are urgent, none are yours to start unasked)

- The rest of Alex's suggestions — **ask for them.**
- Assignee backfill on staging/QA. Assignee is now mandatory on Task, so
  existing tasks there will fail validation the moment anyone edits one. Only
  the local bench was backfilled.
- Freight-box split for the packing slip — blocked, needs Alex's `1105VS10-PL3`
  box breakdown.
- Remap incoming QI to the ITP hold points — agreed with Paul, not built.
- Customer Inspection Notice (QCF 10.409) — parked as Phase 2.
- Nine unapplied quality_dms drift findings — James's call, not ours.
