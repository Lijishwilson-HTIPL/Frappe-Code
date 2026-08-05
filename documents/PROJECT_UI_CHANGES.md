# Project / Desk UI Changes — Re-apply Guide

**ACTION ITEM.** These changes fix UI defects in the Project module and the desk form
shell. One of the two files is an **ERPNext core file**, so pulling or merging newer
code (e.g. from `DMS`, `staging-deployment`, upstream ERPNext) can overwrite it. After
any such pull, work through the **Verification checklist** below and re-apply anything
that regressed.

- **Branch:** `paul-update` (remote `hephzibah`)
- **Date of this work:** 2026-08-04 → 2026-08-05
- **Related:** `documents/CHANGELOG.md` (full commit-by-commit log)

---

## 1. What was changed, and how exposed each file is

| File | Owner | Risk on `git pull` / merge |
|---|---|---|
| `apps/erpnext/erpnext/projects/doctype/project/project.js` | **erpnext core** | 🔴 **HIGH** — a newer erpnext or a branch that also edited this file will conflict or silently replace our accordion work |
| `apps/mercury/mercury/public/css/mercury_desk.css` | mercury (ours) | 🟢 low — nobody else touches our app |
| `apps/mercury/mercury/hooks.py` (`app_include_css`) | mercury (ours) | 🟢 low |

> The desk CSS deliberately lives in **our** app as additive overrides. **No frappe,
> erpnext or hrms CSS file is patched.** Commenting out the single `app_include_css`
> line in `mercury/hooks.py` reverts every desk-shell change at once.

---

## 2. Change A — Collapsible Tasks / Defects on the Project Summary tab

**File:** `apps/erpnext/erpnext/projects/doctype/project/project.js`
**Function:** `show_task_defect_summary_tab`

**Why:** the Mercury demo must not show a "Defects" panel — the term is DMS/SBIQC
vocabulary and the count is always 0 on a manufacturing project. Made collapsible
rather than hidden, so the DMS team keeps it.

What it does:

- Both **Tasks** and **Defects** render as accordions. Header = chevron + icon + title
  + **count badge** + `View All …` button; the whole header row toggles.
- Panel animates with `grid-template-rows: 0fr → 1fr` (no hardcoded `max-height`).
- Keyboard accessible: `role="button"`, `tabindex="0"`, `aria-expanded`,
  `aria-controls`, Enter/Space. Honours `prefers-reduced-motion`.
- `View All …` stays on the header row and its click is `stopPropagation`'d, so opening
  the list does not also toggle the section.
- Both buttons share `min-width: 132px` with centred text, so `View All Tasks` and
  `View All Defects` line up on **both** edges.
- Theme variables only (`--fg-hover-color`, `--control-bg`, `--text-muted`,
  `--primary`) — correct in dark mode.

**State rules (this is the fiddly part — three attempts before it was right):**

| Event | Defects |
|---|---|
| Log in | **closed** (`DEFAULT_COLLAPSED = { Tasks: false, Defects: true }`) |
| User opens it | open |
| Reload / navigate away and back | stays open |
| User closes it | stays closed |
| **Log out → log in** | **closed again** |

Implemented as `sessionStorage`, with the key namespaced by **`frappe.csrf_token`**:

```js
const session_id = frappe.csrf_token || frappe.session?.user || "nosession";
const collapse_key = (title) => `project_summary_collapsed::${session_id}::${title}`;
```

⚠️ **Do not "simplify" this**, and specifically do not switch it to:
- `localStorage` — outlives the session entirely; Defects stays open for days.
- plain `sessionStorage` — survives logout → login in the **same tab**.
- the **`sid` cookie** — `frappe/auth.py:394` sets `sid` with `httponly=True`, so JS can
  **never** read it. The key silently degrades to a constant and behaves like plain
  `sessionStorage`. This looks correct and is not.

`frappe.csrf_token` is exposed to JS in `frappe/www/desk.html:56` and is reissued per
session, which is what makes logout→login reset the default.

---

## 3. Change B — Desk form-shell UI fixes

**File:** `apps/mercury/mercury/public/css/mercury_desk.css`, loaded via
`hooks.app_include_css = "/assets/mercury/css/mercury_desk.css?v=13"`.

> Bump the `?v=` when editing the file (same convention as `hrms ?v=31`,
> `quality_dms ?v=13`) or browsers serve a stale copy.

Each fix, and the **root cause** it works around — these are the notes worth keeping,
because none of these defects originate in our code:

| # | Symptom | Root cause | Our override |
|---|---|---|---|
| 1 | **Two vertical scrollbars** on a form | `main.scss:37` `.main-section { height:100vh; overflow:scroll }` **and** `form_sidebar.scss:274` `.layout-side-section { height: calc(100vh - head); overflow-y:auto; position:sticky }` — two independent scroll containers | sidebar returned to normal page flow |
| 2 | **A third scrollbar** on `.form-sidebar.overlay-sidebar` | **hrms** `layout_global.css:137` forces `overflow-y: auto !important` + `scrollbar-gutter: stable !important` on `.form-sidebar` itself (so overriding the parent does nothing) | matching `!important` override; mercury CSS loads **after** hrms |
| 3 | **Outer window scrollbar** | nothing in frappe sets `overflow` on `html`/`body`, so the document scrolls too | `html, body { overflow: hidden }` — `.main-section` is already a full-viewport scroller |
| 4 | Scrollbars kept **coming back** one by one | any app can set `overflow` on a shell element | blanket suppression inside `.page-container`; `.main-section` sits **outside** it so its bar survives as the single visible one (slimmed to 8px) |
| 5 | **Page head scrolled out of view** | **quality_dms** `quality_dms.css:862` `body.dms-theme .page-head { position: relative }` outranks core's `position: sticky` on specificity (0,2,1 vs 0,1,0). Overriding only `top` does nothing — **`position` must be re-asserted** | `position: sticky !important; top: 0; z-index: 20` |
| 6 | **Tab bar not sticky** until first scroll | `form.scss:484` gives `.form-tabs-list` `position: sticky` with **no `top`**, so sticky is inert until `form/layout.js:538` adds `.form-tabs-sticky-up/-down` on first scroll | pinned unconditionally |
| 7 | Tab bar sticky **captured by an ancestor** | `position: sticky` resolves against the nearest ancestor with a **scrolling box**, and `overflow: hidden` counts (e.g. `page.scss:105` `.layout-main-section.frappe-card`) | `overflow: visible` cleared along `.layout-main-section` → `.form-tab-content` |
| 8 | **Empty band above the tabs** | two separate causes: (a) the card's own **top inset** — quality_dms padding on `.layout-main-section` + margin on `.layout-main-section-wrapper`; (b) a positive `top` offset, since the bar's sticky container **already starts below the head** | top padding/margin zeroed on form routes; tab bar `top: 0`, **not** `var(--page-head-height)` |
| 9 | **Right sidebar clipped** at the viewport edge | `form_sidebar.scss:281` `.form-sidebar { width: var(--form-sidebar-width) }` = **277px**, inside a column **hrms** forces to **250px** (`layout_global.css:126`) → 27px overflow, cut by `.main-section`'s `overflow-x: hidden`. Padding the column cannot fix a fixed-width child | `.form-sidebar { width:100%; max-width:100%; min-width:0; box-sizing:border-box }` + 16px right inset on the column |

**Known trade-offs (deliberate):**
- The form sidebar is **no longer sticky/pinned** — it scrolls with the page. That is the
  price of a single scrollbar; you cannot have both.
- Scrollbars inside `.page-container` are hidden, so nested areas scroll without an
  indicator. Scrolling behaviour itself is unchanged everywhere.
- `document.documentElement.scrollTop` stays `0`, which no-ops frappe's scroll-away
  header handlers (`ui/page.js:69`, `form/layout.js:560`) — harmless, since we pin the
  head anyway.

---

## 4. Verification checklist (run after any pull/merge)

Open `/app/project/PROJ-0001` and hard-reload (**Ctrl+Shift+R** — the CSS is
cache-busted by `?v=`, `project.js` needs `bench clear-cache` + hard reload):

- [ ] **Exactly one** vertical scrollbar, at the right edge of the content area
- [ ] Right sidebar card fully visible — right border and `+` icons not clipped
- [ ] Sidebar and main column start at the **same** vertical level
- [ ] Page head (breadcrumb, title, %, Actions/View/Save) **stays visible** when scrolled to the bottom
- [ ] Tab bar (Summary / Costing / …) pinned flush under the head, **no gap above it**
- [ ] Summary tab: **Tasks expanded, Defects collapsed** on a fresh login
- [ ] Open Defects → reload → still open; log out → log in → **closed**
- [ ] `View All Tasks` / `View All Defects` same width, aligned on both edges
- [ ] Clicking `View All …` opens the filtered list and does **not** collapse the section
- [ ] Dark mode still correct

---

## 5. How to re-apply

Commits, oldest → newest (all on `paul-update`):

```
5cbb13884  feat(project): collapsible Tasks/Defects accordions
d74991fa8  fix(project): View All inside panel; Defects starts collapsed
cd19e49fb  fix(project): View All back on the header row
21d71941e  fix(project): session-scoped state + aligned View All buttons
633c72c47  fix(desk): single scrollbar; sidebar aligned with main section
0766a7cae  fix(desk): pin page head + form tab bar
7ae5208b8  fix: outer scrollbar; scope accordion state to the session
690560584  fix: stop document scrolling; key accordion state to csrf token
4b9e7b704  fix(desk): remove form sidebar scrollbar forced by hrms
aa1d696f0  fix(desk): one scrollbar only; make the tab bar actually pin
7d834c91c  fix(desk): drop tab bar top offset
5dbad4a58  fix(desk): page head was never sticky (quality_dms overrides position)
5fc37465a  fix(desk): stop sticking the tab bar
298ff8112  fix(desk): tab bar sticky under head; remove card top inset
09f8e4572  fix(desk): tab bar sticky with top:0
05046772c  fix(desk): right sidebar clipped at viewport edge
7f7776ce1  fix(desk): sidebar card carries its own fixed width
```

**If only `project.js` was clobbered** (the likely case) — take our version of that one
file, then re-check the accordion items in the checklist:

```
git checkout 7f7776ce1 -- apps/erpnext/erpnext/projects/doctype/project/project.js
bench --site mysite.local clear-cache
```

**If a merge conflicts on `project.js`**, keep **both** sides: the accordion markup
lives entirely inside `show_task_defect_summary_tab`, so incoming changes elsewhere in
the file can be accepted as-is. Re-check that `DEFAULT_COLLAPSED`, `collapse_key`
(csrf-namespaced) and the `.summary-accordion-header` click/keydown handlers all
survived.

**The mercury app files should never conflict.** If the desk shell looks wrong, first
confirm the stylesheet is still being served and the hook is registered:

```
curl -s -o /dev/null -w "%{http_code}\n" http://mysite.local:8000/assets/mercury/css/mercury_desk.css
bench --site mysite.local console
>>> frappe.get_hooks("app_include_css")   # mercury_desk.css must be LAST in the list
```

Load order matters: mercury must come **after** `hrms` and `quality_dms`, otherwise the
`!important` overrides for the sidebar scrollbar and the page head lose.

---

## 6. Notes for whoever owns the DMS/HRMS side

Three of the nine defects above are caused by **our own apps**, not frappe, and would be
better fixed at source than worked around in mercury:

1. `hrms/public/css/layout_global.css:137` — `overflow-y: auto !important` on
   `.form-sidebar` creates a second scrollbar on every form.
2. `quality_dms/public/css/quality_dms.css:862` — `position: relative` on `.page-head`
   breaks core's sticky header desk-wide. DMS only needs a containing block for its
   `::after` accent rule, and `position: sticky` provides one just as well.
3. `hrms` forcing the sidebar column to 250px while frappe sizes the card inside it to
   `--form-sidebar-width` (277px) guarantees a 27px overflow on every form.
