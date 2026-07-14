# V15 → V16 Upgrade Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all custom code in the `lijish-up` and `stagging-deployment` branches compatible with Frappe/ERPNext/HRMS v16 before the upgrade is performed.

**Architecture:** Three phases — (1) pre-upgrade code fixes that can be applied now without v16 source, (2) test environment setup with v16 binaries, (3) source-diff verification tasks that require v16 source to complete. Phases 1 and 3 produce git commits; Phase 2 is infrastructure-only.

**Tech Stack:** Python 3.10 (current) / 3.14+ (target) · Frappe v15→v16 · ERPNext v15→v16 · HRMS v15→v16 · bench CLI · WSL2 Ubuntu 24.04

## Global Constraints

- All code changes go in source files only — never via `bench console`, SQL, or Frappe UI
- Every task ends with a `git commit` on the `lijish-up` branch
- Never call `frappe.db.commit()` inside document hooks (`before_save`, `after_save`, `on_submit`, `on_cancel`) in v16 — use `enqueue_after_commit=True` instead
- In v16: `frappe.cache` is a property, not a method — remove the `()` everywhere
- In v16: `frappe.in_test` replaces `frappe.flags.in_test`
- Bench path: `/home/ijish/frappe-bench` on Ubuntu-22.04 WSL instance
- Branch to commit to: `lijish-up`

---

## Phase 1 — Pre-Upgrade Code Fixes
> These tasks can be done right now without v16 source. All are one-file patches with known required changes.

---

### Task 1: Fix frappe.cache API in mft_license_api.py

**Files:**
- Modify: `apps/erpnext/erpnext/mft_license_api.py` (lines 18, 44, 52)

**Why:** In v16, `frappe.cache` is a module-level property, not a callable method. Calling `frappe.cache()` with parentheses raises `TypeError: 'RedisWrapper' object is not callable`. This breaks OTP login immediately after upgrade.

- [ ] **Step 1: Verify the three call sites**

```bash
grep -n "frappe\.cache()" /home/ijish/frappe-bench/apps/erpnext/erpnext/mft_license_api.py
```
Expected output:
```
18:	frappe.cache().set_value(cache_key, otp, expires_in_sec=600)
44:	stored_otp = frappe.cache().get_value(cache_key)
52:	frappe.cache().delete_value(cache_key)
```

- [ ] **Step 2: Apply the fix — remove all three `()`**

Edit `apps/erpnext/erpnext/mft_license_api.py`:

Line 18 — change:
```python
	frappe.cache().set_value(cache_key, otp, expires_in_sec=600)
```
to:
```python
	frappe.cache.set_value(cache_key, otp, expires_in_sec=600)
```

Line 44 — change:
```python
	stored_otp = frappe.cache().get_value(cache_key)
```
to:
```python
	stored_otp = frappe.cache.get_value(cache_key)
```

Line 52 — change:
```python
	frappe.cache().delete_value(cache_key)
```
to:
```python
	frappe.cache.delete_value(cache_key)
```

- [ ] **Step 3: Verify no remaining `frappe.cache()` calls**

```bash
grep -n "frappe\.cache()" /home/ijish/frappe-bench/apps/erpnext/erpnext/mft_license_api.py
```
Expected: no output (zero matches)

- [ ] **Step 4: Smoke-test syntax**

```bash
cd /home/ijish/frappe-bench && python3 -c "import ast; ast.parse(open('apps/erpnext/erpnext/mft_license_api.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /home/ijish/frappe-bench
git add apps/erpnext/erpnext/mft_license_api.py
git commit -m "fix(mft-license): frappe.cache() -> frappe.cache property for v16 compat"
```

---

### Task 2: Fix daterange import in leave_application.py

**Files:**
- Modify: `apps/hrms/hrms/hr/doctype/leave_application/leave_application.py` (line 23)

**Why:** `from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange` imports a private utility from an unrelated module. In v16, the supplier_scorecard module may be restructured or removed. The fix is to define `daterange` locally using Python's built-in `datetime.timedelta` — the logic is trivial (one-line generator).

- [ ] **Step 1: Confirm the import and its single usage**

```bash
grep -n "daterange" /home/ijish/frappe-bench/apps/hrms/hrms/hr/doctype/leave_application/leave_application.py
```
Expected:
```
23:from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange
287:		for dt in daterange(getdate(self.from_date), getdate(self.to_date)):
```

- [ ] **Step 2: Replace the import with a local definition**

In `apps/hrms/hrms/hr/doctype/leave_application/leave_application.py`:

Remove line 23:
```python
from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange
```

The file already imports `import datetime` at line 4. Add the local function immediately before the class definitions (after all imports, before `class LeaveDayBlockedError`). The insertion point is before line 41 (`class LeaveDayBlockedError`):

```python
def daterange(start_date, end_date):
	"""Yield each date from start_date to end_date inclusive."""
	for n in range(int((end_date - start_date).days) + 1):
		yield start_date + datetime.timedelta(n)
```

- [ ] **Step 3: Verify syntax**

```bash
cd /home/ijish/frappe-bench && python3 -c "import ast; ast.parse(open('apps/hrms/hrms/hr/doctype/leave_application/leave_application.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Confirm no remaining external import of daterange**

```bash
grep -n "supplier_scorecard" /home/ijish/frappe-bench/apps/hrms/hrms/hr/doctype/leave_application/leave_application.py
```
Expected: no output

- [ ] **Step 5: Commit**

```bash
cd /home/ijish/frappe-bench
git add apps/hrms/hrms/hr/doctype/leave_application/leave_application.py
git commit -m "fix(leave-application): replace fragile supplier_scorecard daterange import with local impl"
```

---

### Task 3: Fix frappe.flags.in_test in sbiqc_provisioning

**Files:**
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py` (lines 69, 209, 370)

**Why:** In v16, `frappe.flags.in_test` is removed. The replacement is `frappe.in_test` (a direct attribute on the frappe module). These are used as `now=frappe.flags.in_test` in `frappe.enqueue()` calls — they make background jobs run synchronously during tests.

- [ ] **Step 1: Confirm all occurrences**

```bash
grep -n "frappe\.flags\.in_test" /home/ijish/frappe-bench/apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py
```
Expected:
```
69:			now=frappe.flags.in_test,
209:		now=frappe.flags.in_test,
370:		now=frappe.flags.in_test,
```

- [ ] **Step 2: Replace all three occurrences**

In `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py`:

Change all three instances of:
```python
			now=frappe.flags.in_test,
```
to:
```python
			now=frappe.in_test,
```

(Use replace_all=true since all three are identical.)

- [ ] **Step 3: Verify no remaining frappe.flags.in_test in the file**

```bash
grep -n "frappe\.flags\.in_test" /home/ijish/frappe-bench/apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py
```
Expected: no output

- [ ] **Step 4: Check entire codebase for any other occurrences in our custom apps**

```bash
grep -rn "frappe\.flags\.in_test" \
  /home/ijish/frappe-bench/apps/erpnext/erpnext/mft_license_api.py \
  /home/ijish/frappe-bench/apps/erpnext/erpnext/accounts/doctype/mft_license/ \
  /home/ijish/frappe-bench/apps/crm_unify/ \
  /home/ijish/frappe-bench/apps/helpdesk/helpdesk/overrides/ \
  2>/dev/null || echo "none found"
```
Expected: `none found` (or a list of files to fix — fix any that appear)

- [ ] **Step 5: Syntax check**

```bash
cd /home/ijish/frappe-bench && python3 -c "import ast; ast.parse(open('apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
cd /home/ijish/frappe-bench
git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py
git commit -m "fix(sbiqc): frappe.flags.in_test -> frappe.in_test for v16 compat"
```

---

### Task 4: Fix frappe.db.commit() in on_submit hook (sbiqc_provisioning)

**Files:**
- Modify: `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py` (line 62)

**Why:** In v16, calling `frappe.db.commit()` inside a document hook (`on_submit`) raises an error because Frappe wraps the entire submit operation in a transaction. The commit must not be called mid-transaction. The fix: remove the explicit commit and use `enqueue_after_commit=True` on the background job — this tells Frappe to enqueue the worker only after the outer transaction has committed, which guarantees the status update is visible to the worker.

- [ ] **Step 1: Read the on_submit method to understand the full context**

Read lines 59–75 of `apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py`.

The method looks like:
```python
def on_submit(self):
    self.db_set("status", "Provisioning")
    frappe.db.commit()

    frappe.enqueue(
        "sbiqc_provisioning.provisioner.engine.provision_tenant",
        tenant_name=self.name,
        queue="long",
        timeout=1800,
        now=frappe.in_test,
    )
```

- [ ] **Step 2: Apply the fix**

Change `on_submit` to remove `frappe.db.commit()` and add `enqueue_after_commit=True`:

```python
def on_submit(self):
    self.db_set("status", "Provisioning")

    frappe.enqueue(
        "sbiqc_provisioning.provisioner.engine.provision_tenant",
        tenant_name=self.name,
        queue="long",
        timeout=1800,
        now=frappe.in_test,
        enqueue_after_commit=True,
    )
```

Note: `db_set()` writes directly to the DB column without a full document save. It does not require an explicit commit — the outer Frappe transaction will commit it when `on_submit` returns. `enqueue_after_commit=True` ensures the worker starts only after that commit lands.

- [ ] **Step 3: Verify syntax**

```bash
cd /home/ijish/frappe-bench && python3 -c "import ast; ast.parse(open('apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Audit remaining frappe.db.commit() calls in tenant.py and engine.py**

The `provisioner/engine.py` and `provisioning_log.py` commits are all inside `@frappe.whitelist` functions or background worker functions — **not** inside document hooks. These are allowed in v16. Confirm this is true:

```bash
grep -n "def on_submit\|def on_cancel\|def before_save\|def after_save\|def validate\|frappe\.db\.commit" \
  /home/ijish/frappe-bench/apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py | head -30
```

Verify that no other hook method (lines before any `frappe.db.commit()`) is a document lifecycle hook. If any additional `frappe.db.commit()` inside a hook is found, apply the same `enqueue_after_commit=True` treatment or move the commit to a `@frappe.whitelist` function.

- [ ] **Step 5: Commit**

```bash
cd /home/ijish/frappe-bench
git add apps/sbiqc_provisioning/sbiqc_provisioning/sbiqc_provisioning/doctype/tenant/tenant.py
git commit -m "fix(sbiqc): remove db.commit() from on_submit hook, use enqueue_after_commit=True"
```

---

## Phase 2 — Test Environment Upgrade
> SysAdmin tasks. No code changes. Required before Phase 3 tasks can be completed.

---

### Task 5: Upgrade Ubuntu-24.04 WSL test bench to v16

**Files:** None (infrastructure only)

**Why:** Many Phase 3 verification tasks require running `bench migrate`, loading the actual v16 source, and validating real behaviour. The Ubuntu-22.04 instance stays on v15 for production. The Ubuntu-24.04 instance (offset ports: web 8001, DB 3307, redis 13001/11001) is the test environment.

- [ ] **Step 1: On Ubuntu 24.04 WSL, verify Python and Node versions**

```bash
wsl -d Ubuntu-24.04 -- bash -c "python3 --version && node --version"
```
Required: Python ≥ 3.14, Node ≥ 24. If not met:

```bash
# Install Python 3.14 (Ubuntu 24.04 may have 3.12 — use deadsnakes PPA)
wsl -d Ubuntu-24.04 -- bash -c "
  sudo add-apt-repository ppa:deadsnakes/ppa -y &&
  sudo apt-get update &&
  sudo apt-get install -y python3.14 python3.14-venv python3.14-dev
"

# Install Node 24 via nvm
wsl -d Ubuntu-24.04 -- bash -c "
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash &&
  source ~/.bashrc &&
  nvm install 24 && nvm use 24 && nvm alias default 24
"
```

- [ ] **Step 2: Take a full backup of the test site before upgrade**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench backup --with-files --site mysite.local
"
```

- [ ] **Step 3: Pull v16 branches for all core apps**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench get-app --branch version-16 frappe &&
  bench get-app --branch version-16 erpnext &&
  bench get-app --branch version-16 hrms
"
```

- [ ] **Step 4: Rebuild assets and run migrate**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench build &&
  bench --site mysite.local migrate
"
```
Expected: migration completes without Python exceptions. If errors appear, record them — they inform Phase 3 tasks.

- [ ] **Step 5: Restart bench and verify the site loads**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench restart &&
  sleep 5 &&
  curl -s -o /dev/null -w '%{http_code}' http://mysite.local:8001
"
```
Expected: `200` or `302`

---

## Phase 3 — v16 Source Verification Diffs
> These tasks require the v16 source to be available in the test bench (Task 5 complete). They verify that our full-file overrides are compatible with v16 method signatures and import paths.

---

### Task 6: Verify employee_query path in employee.js and leave_allocation.js

**Files:**
- Modify if needed: `apps/erpnext/erpnext/setup/doctype/employee/employee.js`
- Modify if needed: `apps/hrms/hrms/hr/doctype/leave_allocation/leave_allocation.js`

**Why:** Our files use `query: "erpnext.controllers.queries.employee_query"`. In some v16 HRMS builds, this path moved to `hrms.controllers.queries.employee_query`. Using the wrong path returns no results in the `reports_to` / employee fields.

- [ ] **Step 1: Check if the function exists in v16 ERPNext**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  grep -r 'def employee_query' /home/ijish/frappe-bench/apps/erpnext/erpnext/controllers/queries.py 2>/dev/null && echo 'found in erpnext' || echo 'NOT in erpnext'
"
```

- [ ] **Step 2: Check if it exists in v16 HRMS instead**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  grep -r 'def employee_query' /home/ijish/frappe-bench/apps/hrms/ 2>/dev/null && echo 'found in hrms' || echo 'NOT in hrms'
"
```

- [ ] **Step 3a: If only in hrms — update both JS files**

In `apps/erpnext/erpnext/setup/doctype/employee/employee.js`, change:
```javascript
query: "erpnext.controllers.queries.employee_query",
```
to:
```javascript
query: "hrms.controllers.queries.employee_query",
```

Apply the same change in `apps/hrms/hrms/hr/doctype/leave_allocation/leave_allocation.js`.

- [ ] **Step 3b: If in both (re-exported) — leave unchanged**

If ERPNext v16 re-exports `employee_query` from HRMS, the existing path works. No change needed.

- [ ] **Step 4: Verify erpnext.utils.make_bank_account in v16**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  grep -r 'make_bank_account' /home/ijish/frappe-bench/apps/erpnext/erpnext/public/js/utils.js 2>/dev/null | head -5 || echo 'NOT FOUND'
"
```
If not found, the `make_bank_account` button in `employee.js` will silently not work. Locate the new equivalent:
```bash
wsl -d Ubuntu-24.04 -- bash -c "grep -r 'make_bank_account\|bank_account' /home/ijish/frappe-bench/apps/erpnext/erpnext/public/js/ 2>/dev/null | grep 'function\|frappe.utils' | head -10"
```
Update the call site in `employee.js` to the new location if moved.

- [ ] **Step 5: Commit any changes made**

```bash
cd /home/ijish/frappe-bench
git add apps/erpnext/erpnext/setup/doctype/employee/employee.js
git add apps/hrms/hrms/hr/doctype/leave_allocation/leave_allocation.js
git commit -m "fix(employee): update employee_query path for v16 compat" \
  || echo "No changes needed — paths unchanged in v16"
```

---

### Task 7: 3-Way Diff sales_order.py Against v16

**Files:**
- Modify: `apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py` (1,916 lines)

**Why:** This is a full-file override of a 1,900-line class. Any method that changed signature, was added, or was removed in v16 must be reconciled. The inter-company import block (lines 18–22) is the most likely single point of failure.

- [ ] **Step 1: Export v15 upstream, v16 upstream, and our override to temp files**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  SO_PATH='erpnext/selling/doctype/sales_order/sales_order.py'
  APPDIR='/home/ijish/frappe-bench/apps/erpnext'

  # v15 upstream (last upstream commit before our customisation)
  git -C \$APPDIR show origin/version-15:\$SO_PATH > /tmp/so_v15_upstream.py

  # v16 upstream
  git -C \$APPDIR show origin/version-16:\$SO_PATH > /tmp/so_v16_upstream.py

  # Our override (working tree)
  cp \$APPDIR/\$SO_PATH /tmp/so_our_override.py

  echo 'Files exported'
  wc -l /tmp/so_v15_upstream.py /tmp/so_v16_upstream.py /tmp/so_our_override.py
"
```

- [ ] **Step 2: Run the 3-way diff — what changed in v16 vs v15**

```bash
wsl -d Ubuntu-24.04 -- bash -c "diff /tmp/so_v15_upstream.py /tmp/so_v16_upstream.py > /tmp/so_v15_to_v16.diff && echo 'Diff saved' && wc -l /tmp/so_v15_to_v16.diff"
```

- [ ] **Step 3: Extract method-level changes only**

```bash
wsl -d Ubuntu-24.04 -- bash -c "grep '^[-+].*def ' /tmp/so_v15_to_v16.diff"
```
This shows every method that was added (`+def`) or removed (`-def`) in v16. For each changed method, apply the same change to our override.

- [ ] **Step 4: Verify the inter-company imports still exist in v16**

```bash
wsl -d Ubuntu-24.04 -- bash -c "python3 -c \"
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_inter_company_details
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
print('core imports OK')
\" 2>&1"
```

Check the three specific imports from lines 18–22 of our override:
```bash
wsl -d Ubuntu-24.04 -- bash -c "
  grep -n 'unlink_inter_company_doc\|update_linked_doc\|validate_inter_company_party' \
    /home/ijish/frappe-bench/apps/erpnext/erpnext/controllers/accounts_controller.py \
    /home/ijish/frappe-bench/apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py \
    2>/dev/null | head -10
"
```
If not found at their current import paths, locate the new path:
```bash
wsl -d Ubuntu-24.04 -- bash -c "grep -r 'def unlink_inter_company_doc\|def update_linked_doc\|def validate_inter_company_party' /home/ijish/frappe-bench/apps/erpnext/ 2>/dev/null"
```
Update the import block in our `sales_order.py` accordingly.

- [ ] **Step 5: Apply each v16 method change to our override**

For each method listed in Step 3:
- If the method is in our override: apply the equivalent v16 changes manually
- If the method is new in v16: add it to our override after the corresponding method
- If the method was removed in v16 (and we have it): check if we call it anywhere; if safe to remove, remove it

- [ ] **Step 6: Verify syntax**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  python3 -c \"import ast; ast.parse(open('/home/ijish/frappe-bench/apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py').read()); print('OK')\"
"
```
Expected: `OK`

- [ ] **Step 7: Run Sales Order functional test on the test bench**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench --site mysite.local run-tests --app erpnext --module erpnext.selling.doctype.sales_order.test_sales_order 2>&1 | tail -20
"
```
Expected: All tests pass (or fail for the same reasons as on v15 — no regressions).

- [ ] **Step 8: Commit**

```bash
cd /home/ijish/frappe-bench
git add apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py
git commit -m "fix(sales-order): reconcile sales_order.py override with v16 upstream changes"
```

---

### Task 8: Verify pos_profile.js helper and purchase_receipt.json schema

**Files:**
- Modify if needed: `apps/erpnext/erpnext/accounts/doctype/pos_profile/pos_profile.js`
- Modify if needed: `apps/erpnext/erpnext/stock/doctype/purchase_receipt/purchase_receipt.json`

- [ ] **Step 1: Check if is_perpetual_inventory_enabled still exists in v16**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  grep -r 'is_perpetual_inventory_enabled' /home/ijish/frappe-bench/apps/erpnext/erpnext/public/js/utils.js 2>/dev/null | head -5 || echo 'NOT FOUND'
"
```
If not found, locate the replacement:
```bash
wsl -d Ubuntu-24.04 -- bash -c "grep -r 'perpetual_inventory\|is_perpetual' /home/ijish/frappe-bench/apps/erpnext/erpnext/public/js/ 2>/dev/null | grep -v '.pyc' | head -10"
```
Update the call in `pos_profile.js` to the new location.

- [ ] **Step 2: Validate purchase_receipt.json against v16 schema**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  RECFILE='/home/ijish/frappe-bench/apps/erpnext/erpnext/stock/doctype/purchase_receipt/purchase_receipt.json'
  python3 -c \"
import json
with open('\$RECFILE') as f:
    d = json.load(f)
print('Fields:', len(d.get('fields', [])))
print('Field names:', [f['fieldname'] for f in d.get('fields', []) if 'fieldname' in f][:10])
\"
"
```

Then diff our fields against the v16 upstream:
```bash
wsl -d Ubuntu-24.04 -- bash -c "
  git -C /home/ijish/frappe-bench/apps/erpnext show origin/version-16:erpnext/stock/doctype/purchase_receipt/purchase_receipt.json \
  | python3 -c \"import json,sys; d=json.load(sys.stdin); print([f['fieldname'] for f in d.get('fields',[]) if 'fieldname' in f])\"
"
```
Compare the field lists. If v16 added/removed any field that our JSON also touches, merge accordingly.

- [ ] **Step 3: Commit any changes**

```bash
cd /home/ijish/frappe-bench
git add apps/erpnext/erpnext/accounts/doctype/pos_profile/pos_profile.js
git add apps/erpnext/erpnext/stock/doctype/purchase_receipt/purchase_receipt.json
git commit -m "fix(accounts,stock): pos_profile and purchase_receipt v16 compat" \
  || echo "No changes needed"
```

---

### Task 9: Verify mft_license.py get_payment_entry import path

**Files:**
- Modify if needed: `apps/erpnext/erpnext/accounts/doctype/mft_license/mft_license.py`

- [ ] **Step 1: Check if get_payment_entry still exists at the same path in v16**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  grep -n 'def get_payment_entry' /home/ijish/frappe-bench/apps/erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.py 2>/dev/null | head -3 || echo 'NOT FOUND at original path'
"
```

- [ ] **Step 2: If not found, locate it**

```bash
wsl -d Ubuntu-24.04 -- bash -c "grep -rn 'def get_payment_entry' /home/ijish/frappe-bench/apps/erpnext/ 2>/dev/null"
```

- [ ] **Step 3: If path changed, update all three import sites in mft_license.py**

Find the 3 import lines:
```bash
grep -n "get_payment_entry" /home/ijish/frappe-bench/apps/erpnext/erpnext/accounts/doctype/mft_license/mft_license.py
```

Update the import path at each site from old to new. The import typically looks like:
```python
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
```

- [ ] **Step 4: Syntax check**

```bash
wsl -d Ubuntu-24.04 -- bash -c "python3 -c \"import ast; ast.parse(open('/home/ijish/frappe-bench/apps/erpnext/erpnext/accounts/doctype/mft_license/mft_license.py').read()); print('OK')\""
```

- [ ] **Step 5: Commit any changes**

```bash
cd /home/ijish/frappe-bench
git add apps/erpnext/erpnext/accounts/doctype/mft_license/mft_license.py
git commit -m "fix(mft-license): update get_payment_entry import path for v16" \
  || echo "No changes needed — path unchanged"
```

---

### Task 10: Verify HRMS override method signatures

**Files:**
- Modify if needed: `apps/hrms/hrms/overrides/employee_master.py`
- Modify if needed: `apps/hrms/hrms/overrides/company.py`

- [ ] **Step 1: Check Employee base class autoname signature in v16 HRMS**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  grep -n 'def autoname\|def validate_onboarding_process\|def publish_update\|def update_job_applicant' \
    /home/ijish/frappe-bench/apps/hrms/hrms/hr/doctype/employee/employee.py 2>/dev/null
"
```
Compare with our override's method signatures in `hrms/overrides/employee_master.py`. If the base class no longer has a method we're overriding, it's safe — our override takes over. If the base class added a mandatory parameter to a method we override, add the same parameter.

- [ ] **Step 2: Verify get_account_currency import in company.py**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  python3 -c 'from erpnext.accounts.utils import get_account_currency; print(\"OK\")' 2>&1
"
```
If this fails:
```bash
wsl -d Ubuntu-24.04 -- bash -c "grep -rn 'def get_account_currency' /home/ijish/frappe-bench/apps/erpnext/ 2>/dev/null"
```
Update the import in `apps/hrms/hrms/overrides/company.py` to the new path.

- [ ] **Step 3: Syntax checks**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  python3 -c \"import ast
for f in ['apps/hrms/hrms/overrides/employee_master.py','apps/hrms/hrms/overrides/company.py']:
    ast.parse(open('/home/ijish/frappe-bench/'+f).read())
    print(f,'OK')
\"
"
```

- [ ] **Step 4: Commit any changes**

```bash
cd /home/ijish/frappe-bench
git add apps/hrms/hrms/overrides/employee_master.py apps/hrms/hrms/overrides/company.py
git commit -m "fix(hrms-overrides): align employee_master and company overrides with v16 signatures" \
  || echo "No changes needed"
```

---

## Phase 4 — Migration & Smoke Tests
> Run after all Phase 1–3 tasks are committed. These verify end-to-end functionality.

---

### Task 11: Run bench migrate and validate custom fields

**Files:** None (validation only)

- [ ] **Step 1: Run bench migrate on the test bench**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench --site mysite.local migrate 2>&1 | tee /tmp/migrate_v16.log | tail -30
"
```
Expected: ends with `migrate: success`. If errors appear, read `/tmp/migrate_v16.log` and fix the causing file.

- [ ] **Step 2: Verify custom fields are reapplied on Employee**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench --site mysite.local execute frappe.client.get_list --kwargs \"{\\\"doctype\\\": \\\"Custom Field\\\", \\\"filters\\\": [[\\\"dt\\\", \\\"=\\\", \\\"Employee\\\"]], \\\"fields\\\": [\\\"name\\\", \\\"fieldname\\\"], \\\"limit\\\": 30}\" 2>&1
"
```
Expected: 19 Custom Field records for Employee (leave_approver, expense_approver, ifsc_code, etc.)

- [ ] **Step 3: Verify custom fields on Project and Task**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench --site mysite.local execute frappe.db.get_all --kwargs \"{\\\"doctype\\\": \\\"Custom Field\\\", \\\"filters\\\": [[\\\"dt\\\", \\\"in\\\", [\\\"Project\\\",\\\"Task\\\"]]], \\\"fields\\\": [\\\"dt\\\",\\\"fieldname\\\",\\\"fieldtype\\\"]}\" 2>&1
"
```
Expected: 5 Project fields (total_project_budget, total_estimated_cost, budget_variance + breaks) and 11 Task fields.

- [ ] **Step 4: Verify Construction Task Item and Construction Task Vendor tables exist**

```bash
wsl -d Ubuntu-24.04 -- bash -c "
  cd /home/ijish/frappe-bench &&
  bench --site mysite.local execute frappe.db.table_exists --args \"Construction Task Item\" 2>&1
  bench --site mysite.local execute frappe.db.table_exists --args \"Construction Task Vendor\" 2>&1
"
```
Expected: `True` for both

- [ ] **Step 5: Commit any last-minute fixes, update the risk matrix in the spec**

```bash
cd /home/ijish/frappe-bench
# Update the Risk Matrix Status column in docs/superpowers/specs/2026-06-19-v15-to-v16-upgrade-impact.md
# Change all "Pending" entries that have been addressed to "Done"
git add docs/superpowers/specs/2026-06-19-v15-to-v16-upgrade-impact.md
git commit -m "docs: update upgrade impact risk matrix — mark fixed items Done" || echo "No doc changes"
```

---

### Task 12: Full Smoke Test Suite

**Files:** None (UI/functional testing)

Run each test manually on the test bench (http://mysite.local:8001). Open browser dev console — any JS errors are a failure.

- [ ] **Smoke 1: MFT OTP Login**
  1. Navigate to the MFT portal login page
  2. Enter a valid license email address
  3. Confirm OTP email is sent (check sent emails or mail log)
  4. Enter the OTP — confirm license details page loads
  5. **Pass criterion:** No `TypeError: frappe.cache is not callable` in server error log

- [ ] **Smoke 2: Leave Application**
  1. Create a new Leave Application for an active employee
  2. Set leave type, from/to dates spanning a weekend
  3. Save → Submit
  4. **Pass criterion:** Half-day count and date iteration work correctly; no import errors in traceback

- [ ] **Smoke 3: Sales Order**
  1. Create a new Sales Order
  2. Add one item, set delivery date
  3. Save → Submit
  4. Make Delivery Note from Sales Order
  5. **Pass criterion:** No inter-company import errors; DN created successfully

- [ ] **Smoke 4: Employee form**
  1. Open an existing Employee record
  2. Confirm `reports_to` field shows the employee search popup
  3. Confirm custom fields (leave_approver, banking fields) are visible
  4. **Pass criterion:** No JS console errors; all 19 custom fields render

- [ ] **Smoke 5: Helpdesk ticket acknowledgment**
  1. Create a new Helpdesk ticket
  2. Check the site's outgoing email log
  3. **Pass criterion:** Branded acknowledgment email sent within 30 seconds

- [ ] **Smoke 6: Tenant provisioning (sbiqc)**
  1. Create a new Tenant record
  2. Fill subdomain, plan, admin_email
  3. Submit the Tenant document
  4. **Pass criterion:** Status changes to "Provisioning" with no hook error; background job enqueues

- [ ] **Smoke 7: Project/Task construction fields**
  1. Open a Project → confirm "Budget Overview" section with 3 currency fields
  2. Open a Task → confirm "Construction Details" section; add a row to task_items table and task_vendors table
  3. **Pass criterion:** Child table rows save and reload correctly

---

## Risk Matrix — Status Tracking

| File / Component | Risk | Status |
|-----------------|------|--------|
| `mft_license_api.py` — `frappe.cache()` API | 🔴 High | Task 1 |
| `leave_application.py` — `daterange` import | 🔴 High | Task 2 |
| `tenant.py` — `frappe.flags.in_test` (×3) | 🟡 Medium | Task 3 |
| `tenant.py` — `frappe.db.commit()` in on_submit | 🟡 Medium | Task 4 |
| Python 3.14 / Node 24 infra | 🔴 High | Task 5 (SysAdmin) |
| `employee.js` + `leave_allocation.js` — `employee_query` path | 🟡 Medium | Task 6 |
| `sales_order.py` — 3-way diff | 🔴 High | Task 7 |
| `pos_profile.js` — `is_perpetual_inventory_enabled` | 🟡 Medium | Task 8 |
| `purchase_receipt.json` — schema conflict | 🟡 Medium | Task 8 |
| `mft_license.py` — `get_payment_entry` import | 🟡 Medium | Task 9 |
| `employee_master.py` + `company.py` — HRMS overrides | 🟡 Medium | Task 10 |
| `bench migrate` + custom fields validation | 🟡 Medium | Task 11 |
| Full smoke test suite | — | Task 12 |
