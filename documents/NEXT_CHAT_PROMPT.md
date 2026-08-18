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

The Alex demo (2026-08-13, job 1105VS10 / Evapco PO 536POR22825) went well.
All of that work is **merged to `staging-deployment`** (PR #26, then PR back
round again). `paul-update` is 2 commits ahead of staging and fast-forwards.

Git is fully closed out. Nothing is pending, nothing is half-merged.

**Merging is not deploying.** `deploy-staging.yml` is `workflow_dispatch` only,
so the staging *site* still runs an older build until someone runs the workflow
from the Actions tab by hand.

## What is actually next

Alex gave a batch of suggestions after the demo. **Paul has handed over only the
first one.** Do not go looking for the rest and do not infer them — **ask Paul
for the remaining suggestions.** A previous brief cost three sessions of guessing
before it was finally handed over; that is not being repeated.

The first suggestion is scoped but **not built**: a customer delivery
acknowledgement — minimal, per-item scanning, working at remote sites with no
connectivity. Section [20] has the full design, and the answer that gates it is
**"whose phone does the scanning?"** — Paul is asking Alex. If it is third-party
freight (his bet, and mine), the app cannot live on the driver's device, and
that changes the whole build. **Do not start building until that answer lands.**

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
