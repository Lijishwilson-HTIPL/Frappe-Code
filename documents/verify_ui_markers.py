"""Post-merge verification: the protected UI markers from CLAUDE.md must all survive."""

import re

BENCH = "/home/paul/frappe-bench/"
PROJECT_JS = BENCH + "apps/erpnext/erpnext/projects/doctype/project/project.js"
MERCURY_CSS = BENCH + "apps/mercury/mercury/public/css/mercury_desk.css"
MERCURY_JS = BENCH + "apps/mercury/mercury/public/js/mercury_desk.js"
HOOKS = BENCH + "apps/mercury/mercury/hooks.py"

js = open(PROJECT_JS, encoding="utf-8").read()
css = open(MERCURY_CSS, encoding="utf-8").read()
mjs = open(MERCURY_JS, encoding="utf-8").read()
hooks = open(HOOKS, encoding="utf-8").read()

CHECKS = [
    ("project.js", js, "DEFAULT_COLLAPSED = { Tasks: false, Defects: true }"),
    ("project.js", js, "frappe.csrf_token"),
    ("project.js", js, "collapse_key"),
    ("project.js", js, "show_task_defect_summary_tab"),
    ("project.js", js, ".summary-accordion"),
    ("project.js", js, "summary-accordion-header"),
    ("project.js", js, "summary-accordion-panel"),
    ("project.js", js, "summary-count-badge"),
    ("project.js", js, "summary-view-all"),
    ("project.js", js, "PROTECTED"),
    ("mercury_desk.css", css, "PROTECTED"),
    # % Progress list header: fieldname/Bootstrap class collision (see the CSS block).
    ("mercury_desk.css", css, ".list-row-head .list-row-col.progress"),
    # Breadcrumb retarget: home icon -> workspace, workspace crumb -> list.
    ("mercury_desk.js", mjs, "PROTECTED"),
    ("mercury_desk.js", mjs, "mercury.breadcrumbs.CRUMB_TARGETS"),
    ("mercury_desk.js", mjs, "mercury.breadcrumbs.retarget"),
    # Core misspells this class; "fixing" the selector silently breaks the lookup.
    ("mercury_desk.js", mjs, "a.worksapce-breadcrumb"),
    ("hooks.py", hooks, "app_include_css"),
    ("hooks.py", hooks, "app_include_js"),
    ("hooks.py", hooks, "mercury_desk.js"),
    ("hooks.py", hooks, "mercury.task_status.validate"),
]

fails = 0
for fname, blob, needle in CHECKS:
    ok = needle in blob
    if not ok:
        fails += 1
    print(f"  {'OK  ' if ok else 'FAIL'}  {fname:<18} {needle}")

# The two handlers must both be bound on the accordion header.
for evt in ("click", "keydown"):
    ok = re.search(rf"{evt}[^\n]*summary-accordion-header|summary-accordion-header[^\n]*{evt}", js)
    if not ok:
        # handlers may be bound on separate lines; fall back to a windowed search
        ok = any(
            evt in chunk
            for chunk in re.findall(r".{0,200}summary-accordion-header.{0,200}", js, re.S)
        )
    if not ok:
        fails += 1
    print(f"  {'OK  ' if ok else 'FAIL'}  project.js         {evt} handler on .summary-accordion-header")

# Forbidden regressions. NOTE: a bare "localStorage" substring is NOT a failure -
# the file legitimately contains it in the warning comments AND in a deliberate
# localStorage.removeItem() that clears the stale flag left by the first
# implementation. Only a READ or WRITE of the collapsed state is wrong.
FORBIDDEN = [
    (r"localStorage\.(getItem|setItem)", "localStorage read/write outlives the session"),
    (r"cookie\.match\(/sid", "sid is httponly - JS can never read it"),
    (r"sessionStorage\.(getItem|setItem)\(\s*[\"'`]project_summary",
     "sessionStorage key not built from csrf_token survives logout->login"),
]
for pattern, why in FORBIDDEN:
    hit = re.search(pattern, js)
    if hit:
        fails += 1
    print(f"  {'FAIL' if hit else 'OK  '}  project.js         no {pattern}  ({why})")

# app_include_js must stay COMMENTED-OUT nowhere: an uncommented hook is required,
# or the breadcrumb override never loads and the fix silently disappears.
hook_live = re.search(r"^app_include_js\s*=", hooks, re.M)
if not hook_live:
    fails += 1
print(f"  {'OK  ' if hook_live else 'FAIL'}  hooks.py           app_include_js is uncommented")

# Positive check: the state must be read AND written through collapse_key().
for op in ("getItem", "setItem"):
    ok = re.search(rf"sessionStorage\.{op}\(\s*collapse_key\(", js)
    if not ok:
        fails += 1
    print(f"  {'OK  ' if ok else 'FAIL'}  project.js         sessionStorage.{op}(collapse_key(...))")

print(f"\n{'ALL CHECKS PASSED' if not fails else str(fails) + ' CHECK(S) FAILED'}")
