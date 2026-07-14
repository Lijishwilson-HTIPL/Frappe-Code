# Frappe / ERPNext / HRMS — V15 → V16 Upgrade Impact Assessment

**Prepared:** 2026-06-19  
**Stack versions assessed:** Frappe 15.105.0 · ERPNext 15.104.3 · HRMS 15.59.2  
**Apps in scope:** `frappe` · `erpnext` · `hrms` · `crm` · `helpdesk` · `telephony` · `crm_unify` · `sbiqc_provisioning`  
**Branches audited:** `lijish-up` and `stagging-deployment` (Frappe-Code monorepo)

---

## Part 1 — Executive Summary

### What is this upgrade?

Frappe, ERPNext, and HRMS version 16 is a major release. It upgrades the core framework runtime (Python, Node.js), changes how several modules handle data, and removes a number of older APIs that the platform has carried since V11–V13. The upgrade is non-trivial: it requires server maintenance downtime, a full database migration, re-application of every local code patch, and post-upgrade validation of all customised modules.

### Expected business impact

| Area | Impact | Severity |
|------|--------|----------|
| **All users** | Planned downtime window required (est. 4–8 hours) | High |
| **HR / Leave Management** | Leave Application and Leave Allocation forms will change; holiday list assignments become explicit per-employee | Medium |
| **Accounts / POS** | POS Profile form queries updated; print format JSONs may need migration | Medium |
| **Selling / Sales Order** | Sales Order form is heavily customised — must be re-validated after upgrade | High |
| **Helpdesk** | Ticket acknowledgment email will continue to work; Helpdesk app (v1.x) is not directly versioned with ERPNext | Low |
| **CRM (Frappe CRM)** | CRM app uses its own v1.x versioning, generally backward-compatible | Low |
| **Custom Apps** | `crm_unify` and `sbiqc_provisioning` must be tested on v16 runtime | Medium |
| **Payroll / Salary Structure** | UI changes in Salary Structure client script; underlying data model stable | Low |
| **Stock / Delivery Trip** | Delivery Trip form script needs re-validation | Low |
| **MFT License (custom)** | OTP API will break due to `frappe.cache()` → `frappe.cache` API change in v16; payment flow must be validated | Medium |
| **Custom Fields & Property Setters (133 total)** | 90+ property setters across 20 DocTypes, 19 Employee fields, 11 Company fields — regression testing required on all affected forms | Medium |
| **HRMS Overrides** (`employee_master.py`, `company.py`) | Light-touch class overrides hooking into autoname and company setup — verify against v16 method signatures | Medium |
| **sbiqc_provisioning** (3 DocTypes) | Tenant, Tenant App, Provisioning Log — clean schema, low migration risk | Low |
| **crm_unify Quotation filter** | Property setter on `quotation_to` — may conflict if v16 adds its own filter | Low |

### What users will see change

- The **Workspace sidebar** is now driven by a new Workspace Sidebar doctype. Any user-customised workspace layouts will be reset and must be re-configured.
- **List views** will sort by `creation` date by default instead of `modified`. Users who relied on "last modified first" ordering will need to apply explicit sorts.
- **POS** behaviour changes: a new "Use Sales Invoices in POS" setting changes which document type POS creates.
- **Leave management** forms may look slightly different due to field restructuring.
- HR users will need to confirm holiday list assignments are correctly set per employee after migration.

### Recommended upgrade sequence

1. Freeze non-critical merges on `lijish-up` branch
2. Stand up the Ubuntu-24.04 WSL test environment and upgrade it to v16 first
3. Validate all custom patches against v16 on test (see Part 2 checklist per module)
4. Fix all HIGH and MEDIUM risk items
5. Run `bench migrate` on test and confirm no errors
6. Perform upgrade on production during a planned maintenance window
7. Post-upgrade: re-apply workspace customisations, validate POS, HR, and Sales Order flows

---

## Part 2 — Technical Upgrade Guide

> **Risk ratings:** 🔴 High (likely to break, must fix before upgrade) · 🟡 Medium (may break, validate and patch) · 🟢 Low (unlikely to break, spot-check only)

---

### Module 1 — Frappe Framework

**V16 upstream changes that affect this org:**

| Change | Impact |
|--------|--------|
| Python minimum raised to **3.14+** | Server OS must be upgraded. Ubuntu 22.04 ships Python 3.10 — requires Python 3.14 install or OS upgrade to 24.04 |
| Node.js minimum raised to **24+** | Install via nvm or NodeSource on both dev and prod |
| Default list sort changed from `modified` to `creation` | All `frappe.get_all()` / `frappe.get_list()` calls without explicit `order_by` will return different row order |
| Single DocType `db.get_value()` now returns typed values (int not string) | Any code comparing `== "1"` on a Check field will silently fail |
| `frappe.flags.in_test` removed | Use `frappe.in_test` instead |
| `Transaction Log` DocType removed | Any code referencing this doctype will crash |
| `has_permission()` hook must return explicit `True`/`False` | Implicit truthy returns no longer accepted |
| `raise_exception` param in `has_permission()` removed | Use `print_logs=True` instead |
| Report/Dashboard/Page JS now execute as IIFEs | Variables declared at top level no longer leak to global scope; `frappe.provide()` patterns still work |
| Link field filters enforced **server-side** | `set_query` filters that prevent invalid values are now validated on save, not just in the UI |
| Workspace Sidebar now a DocType | Custom workspace layout changes will be lost on upgrade |

**Your patches in this area:** None direct framework files patched.  
**Risk:** 🟡 Medium — Python/Node version requirement is a hard prerequisite; IIFE change may affect global namespace assumptions in custom JS.

**Action required:**
- Confirm production server runs Python 3.14 and Node 24 before upgrade
- Search all custom Python for `frappe.flags.in_test` → replace with `frappe.in_test`
- Search all custom Python for `"Transaction Log"` references → remove or replace
- After upgrade, re-apply workspace sidebar customisations manually

---

### Module 2 — ERPNext Accounts (POS Profile, Purchase Receipt, Print Formats)

**V16 upstream changes:**

| Change | Impact |
|--------|--------|
| **Item-Wise Tax Detail** changed from JSON field to child table | Auto-migrated but any code reading the old JSON structure will break |
| **Tax Withholding Entry** refactored to new child table structure | Custom reports or scripts parsing tax withholding data need review |
| New "Use Sales Invoices in POS" setting | POS may create a different document type depending on this setting |
| Bank Account create button removed from Supplier form | Reduces noise; no action needed unless custom code called that button handler |
| Pricing Rule `make_pricing_rule` API removed | Use `frappe.new_doc("Pricing Rule")` instead |

**Your patches in this area:**

| File | Nature | Risk |
|------|--------|------|
| `erpnext/accounts/doctype/pos_profile/pos_profile.js` | Full file override — standard POS Profile queries | 🟡 Medium |
| `erpnext/accounts/print_format/cheque_printing_format/cheque_printing_format.json` | Print format JSON modified | 🟢 Low |
| `erpnext/accounts/print_format/payment_receipt_voucher/payment_receipt_voucher.json` | Print format JSON modified | 🟢 Low |
| `erpnext/stock/doctype/purchase_receipt/purchase_receipt.json` | DocType JSON modified | 🟡 Medium |

**Action required:**
- `pos_profile.js`: After upgrading, diff your file against the new v16 upstream. The `toggle_display_account_head` handler calls `erpnext.is_perpetual_inventory_enabled` — confirm this helper still exists in v16 `utils.js`.
- `purchase_receipt.json`: Run `bench migrate`; if the DocType JSON conflicts with v16 schema changes, the migrate will error. Compare field order and any added/removed fields in v16's version.
- Print formats: Visually validate after upgrade — field references in Jinja templates may have changed.
- Search codebase for `item_wise_tax_detail` string parsing as JSON → update for child table access.

---

### Module 3 — ERPNext Selling / CRM (Sales Order, Contract)

**V16 upstream changes:**

| Change | Impact |
|--------|--------|
| Timesheet auto-fetch removed from Sales Invoice | Project-linked timesheets must be added manually via API |
| Pricing Rule utility functions removed (`erpnext.utils.make_pricing_rule`) | Replace with `frappe.new_doc()` |
| `unlink_inter_company_doc`, `update_linked_doc`, `validate_inter_company_party` may have moved | These are imported directly into `sales_order.py` — import paths must be verified |

**Your patches in this area:**

| File | Nature | Risk |
|------|--------|------|
| `erpnext/selling/doctype/sales_order/sales_order.py` | **Complete full-file override** — 1,916 lines | 🔴 High |
| `erpnext/crm/doctype/contract/contract.json` | DocType JSON (adds `party_full_name`, `authorised_by_section`, `signee_company` signature field) | 🟡 Medium |

**Action required:**
- `sales_order.py` is the **highest-risk file in this upgrade**. It is a full override of a 1,900-line class. V16 will have changed method signatures, added/removed methods, and altered imports.
  1. After getting v16 source, run a 3-way diff: `v15 upstream` vs `v16 upstream` vs `your override`.
  2. Identify every method that changed in v16 and apply the same changes to your override.
  3. Pay special attention to: `validate()`, `on_submit()`, `make_delivery_note()`, `make_sales_invoice()`.
  4. The inter-company import block at lines 18–22 (`unlink_inter_company_doc`, etc.) — verify these still exist at the same paths in v16.
- `contract.json`: V16 CRM module may have restructured the Contract DocType. Do a field-by-field diff of your JSON against the v16 version; your added fields (`party_full_name`, `signee_company`, `signed_by_company`) must survive `bench migrate`.

---

### Module 4 — ERPNext HR / Employee

**V16 upstream changes:**

| Change | Impact |
|--------|--------|
| Employee `reports_to` query path may have moved (employee queries migrated to HRMS in some builds) | `erpnext.controllers.queries.employee_query` path must be verified |
| `frappe.utils.deprecations.deprecated` decorator behaviour unchanged in v16 | No action |
| `has_value_changed()` method: behaviour stable | No action |

**Your patches in this area:**

| File | Nature | Risk |
|------|--------|------|
| `erpnext/setup/doctype/employee/employee.py` | Full file override — 492 lines | 🟡 Medium |
| `erpnext/setup/doctype/employee/employee.js` | Full file override — uses `erpnext.controllers.queries.employee_query` | 🟡 Medium |

**Action required:**
- `employee.js` at line ~16: `query: "erpnext.controllers.queries.employee_query"` — in some V16 builds this path moved to `hrms.controllers.queries.employee_query`. **Verify against v16 source before upgrade.**
- `employee.js` references `erpnext.utils.make_bank_account(frm.doc.doctype, frm.doc.name)` — check if this helper still exists in v16 `utils.js` (ERPNext removed the Bank Account button from Supplier in v16; Employee may be affected similarly).
- `employee.py`: Import `from frappe.permissions import add_user_permission, get_doc_permissions, has_permission, remove_user_permission` — `get_doc_permissions` signature is stable; confirm `has_permission` `raise_exception` param usage (removed in v16 — use `print_logs=True`).

---

### Module 5 — HRMS HR (Leave Application, Leave Allocation, Job Offer)

**V16 upstream changes:**

| Change | Impact |
|--------|--------|
| Leave Application/Allocation: child table structures updated | Any direct table-row iteration code may need index updates |
| Holiday List assignments now explicit per-employee | A migration patch runs automatically; post-upgrade validate that all employees have correct holiday lists assigned |
| Interview Round merged with Interview Type | Only affects Interview module — not in scope here |
| Role permissions reset to defaults | Custom role permissions must be re-applied post-upgrade |

**Your patches in this area:**

| File | Nature | Risk |
|------|--------|------|
| `hrms/hr/doctype/leave_application/leave_application.py` | Full file override — **imports `daterange` from `erpnext.buying.doctype.supplier_scorecard`** | 🔴 High |
| `hrms/hr/doctype/leave_application/leave_application.js` | Full file override | 🟡 Medium |
| `hrms/hr/doctype/leave_allocation/leave_allocation.py` | Full file override | 🟡 Medium |
| `hrms/hr/doctype/leave_allocation/leave_allocation.js` | Full file override — uses `erpnext.controllers.queries.employee_query` | 🟡 Medium |
| `hrms/hr/doctype/job_offer/job_offer.js` | Full file override | 🟢 Low |
| `hrms/hr/doctype/leave_application/__init__.py` | Modified | 🟢 Low |
| `hrms/hr/doctype/leave_allocation/__init__.py` | Modified | 🟢 Low |

**Action required:**
- `leave_application.py` line 23: `from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange` — **this is a non-standard import of a utility from an unrelated module.** In V16, the supplier_scorecard module may be restructured. Replace with a local implementation of `daterange` or use Python's built-in `datetime` range logic to eliminate this fragile dependency.
- `leave_allocation.js` uses `erpnext.controllers.queries.employee_query` — same path verification issue as Employee (see Module 4).
- After upgrade run `bench migrate` and confirm Leave Ledger Entry data integrity.
- Post-upgrade: re-verify all custom role permissions for Leave Application, Leave Allocation.

---

### Module 6 — HRMS Payroll (Salary Structure)

**V16 upstream changes:**

| Change | Impact |
|--------|--------|
| Salary Structure field linking and currency conversions updated | Field references in client scripts may differ |

**Your patches in this area:**

| File | Nature | Risk |
|------|--------|------|
| `hrms/payroll/doctype/salary_structure/salary_structure.js` | Full file override | 🟢 Low |

**Action required:**
- After upgrade, open a Salary Structure in the UI and confirm all custom buttons and field queries render correctly.
- Spot-check the `select_currency` / `currency` field interactions if any are present in the custom script.

---

### Module 7 — ERPNext Stock (Delivery Trip)

**V16 upstream changes:** Delivery Trip module is largely stable in v16.

**Your patches in this area:**

| File | Nature | Risk |
|------|--------|------|
| `erpnext/stock/doctype/delivery_trip/delivery_trip.js` | Full file override | 🟢 Low |
| `erpnext/patches/v11_0/update_delivery_trip_status.py` | V11 patch script (new file) | 🟢 Low |

**Action required:**
- `delivery_trip.js`: spot-check the form after upgrade — Google Maps integration API may have changed.
- The v11 patch file addition is benign; it runs during `bench migrate` only if not already applied.

---

### Module 8 — Helpdesk (HD Ticket)

**V16 upstream changes:**  
Frappe Helpdesk uses its own `v1.x` versioning independent of ERPNext v16. No major breaking changes announced for the v1.x series.

**Your patches in this area:**

| File | Nature | Risk |
|------|--------|------|
| `helpdesk/overrides/hd_ticket_hooks.py` | New `after_insert` hook — sends branded acknowledgment email | 🟢 Low |

**Specific considerations:**
- The hook uses `frappe.flags.initial_sync` — this flag is set by custom bulk-import code. In v16, `frappe.flags` is a namespace object; accessing a non-existent attribute returns `None` (falsy), so the guard `if frappe.flags.initial_sync` is safe even if the flag is never set.
- `frappe.sendmail()` signature is stable in v16.
- `frappe.utils.escape_html()` is stable.

**Action required:** Smoke-test by creating a ticket post-upgrade and confirming the acknowledgment email is sent.

---

### Module 9 — Frappe CRM

**V16 upstream changes:**  
Frappe CRM (`frappe/crm`) uses `v1.x` versioning. It is **not** tied to ERPNext's version cycle.

**Your patches in this area:** No CRM-specific file patches in the current diff.  
The `crm_unify` custom app integrates CRM with ERPNext via shared DB (no sync engine) — see Module 10.

**Action required:**
- Upgrade `frappe/crm` app to its latest v1.x release separately from the ERPNext v16 upgrade.
- Validate that `crm_unify` API endpoints still function after both upgrades.

---

### Module 10 — Custom Apps (crm_unify, sbiqc_provisioning, telephony)

**V16 upstream changes affecting custom apps:**

| Change | Impact |
|--------|--------|
| `frappe.db.commit()` cannot be called from document hooks | Any `on_submit`, `on_cancel` hooks in custom apps that call `frappe.db.commit()` will error |
| JS IIFE execution context | Custom JS pages/reports that assumed global variable access will break |
| `frappe.flags.in_test` removed | Replace with `frappe.in_test` |
| Link field filter enforcement | Server-side validation of all `set_query` filters is now enforced |

**Action required:**
- Grep both custom apps for `frappe.db.commit()` inside hook methods → remove or move outside hooks.
- Grep for `frappe.flags.in_test` → replace.
- Run `bench migrate` with these apps installed and confirm no DocType schema conflicts.
- `sbiqc_provisioning`: verify multi-tenant site provisioning scripts are compatible with the new Python/Node versions.
- `telephony`: check if the telephony integration library is compatible with Python 3.14.

---

### Module 11 — MFT License (Custom DocType + API)

**What it is:**  
A fully custom module living inside the `erpnext` app (`erpnext/accounts/doctype/mft_license/`).  
It manages software licenses for the MFT Platform product — handling Stripe payments, license key generation, renewals, expiry, and OTP-based portal login.

**Files:**

| File | Purpose |
|------|---------|
| `erpnext/accounts/doctype/mft_license/mft_license.json` | Custom DocType definition (License Key, Status, Plan, Customer, Dates) |
| `erpnext/accounts/doctype/mft_license/mft_license.py` | Document class + full payment/renewal/expiry API |
| `erpnext/mft_license_api.py` | OTP generation endpoint for portal login |

**V16 risks:**

| Issue | Location | Risk |
|-------|----------|------|
| `frappe.cache().set_value()` — **`cache()` is a method in v15, becomes a property `cache` in v16** | `mft_license_api.py` line 18 | 🔴 High |
| `from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry` | `mft_license.py` lines 117, 176, 361 | 🟡 Medium |
| `frappe.db.sql()` direct call in `restore_all_to_active()` | `mft_license.py` line 531 | 🟢 Low |
| `frappe.db.commit()` called multiple times inside `process_payment()` | `mft_license.py` — inside `@frappe.whitelist`, not a hook | 🟢 Low (allowed) |
| `sort_field: "modified"` in DocType JSON | `mft_license.json` line 146 | 🟢 Low (explicitly set, overrides v16 default) |

**Action required:**

- **`mft_license_api.py` line 18:** Change `frappe.cache().set_value(...)` → `frappe.cache.set_value(...)` and `frappe.cache().get_value(...)` → `frappe.cache.get_value(...)` everywhere in the file. This will break OTP login on v16 if not fixed.
- **`mft_license.py`:** After upgrade, verify `get_payment_entry` still importable from same path. If moved, update all three import sites.
- **Scheduled jobs** `send_renewal_requests` and `auto_expire_licenses`: confirm they are registered in `hooks.py` under `scheduler_events` — verify the hook registration syntax hasn't changed in v16.
- **Smoke-test the full flow** on the test environment: new purchase → license key email → portal OTP login → renewal.

---

### Module 12 — Custom Fields & Property Setters (stagging-deployment branch)

**Total customizations found: 140+** across all apps (133 fields/setters + 2 child DocTypes + 3 sbiqc DocTypes).

#### Custom Fields Added to Standard ERPNext DocTypes

| DocType | Custom Fields | Purpose |
|---------|--------------|---------|
| **Employee** | 19 fields | Payroll approvers (`leave_approver`, `expense_approver`, `shift_request_approver`), grade, cost center, banking (`ifsc_code`, `micr_code`), insurance (`health_insurance_no`, `health_insurance_provider`), recruitment (`job_applicant`) |
| **Company** | 11 fields | HR/Payroll tab: salary component links (`basic_component`, `hra_component`, `arrear_component`), default payroll accounts (`default_payroll_payable_account`, `default_expense_claim_payable_account`, `default_employee_advance_account`) |
| **Address** | 2 fields | `tax_category` (Link), `is_your_company_address` (Check) |
| **Project** | 5 fields | Construction budget section: `total_project_budget` (Currency), `total_estimated_cost` (Currency), `budget_variance` (Currency) + 2 layout breaks |
| **Task** | 11 fields | Construction workflow: `is_construction_task` (Check), `construction_status` (Select: Backlog/Scheduled/WIP/Completed/On-Hold), `process` (Select: Electrical/Plumbing/Carpenter), `planned_start_date` (Date), `planned_end_date` (Date), `actual_end_date` (Date), `estimated_cost` (Currency), `task_items` (Table→Construction Task Item), `task_vendors` (Table→Construction Task Vendor) + 2 layout breaks |
| **Salary Component** | 1 field | `component_type` (Select) |
| **Income Tax Slab** | 1 field | `marginal_relief_limit` (Currency) |
| **Employee Tax Exemption Declaration** | 7 fields | HRA exemption section: `monthly_house_rent`, `rented_in_metro_city`, `monthly_hra_exemption`, `annual_hra_exemption`, `salary_structure_hra` |
| **CRM Deal** | 8 fields | ERPNext sync: `erpnext_customer`, `erpnext_quotation`, `erpnext_invoice`, `erpnext_invoice_outstanding`, `erpnext_invoice_status`, `erpnext_quotation_status`, `erpnext_last_synced` |
| **Customer, Quotation, Sales Invoice, Prospect** | 1 field each | `crm_deal` (Data) — CRM unification link |

#### Property Setters (field attribute overrides) — 90+ total

| DocType | Setter Count | What is changed |
|---------|-------------|-----------------|
| Sales Invoice | 12 | Hidden fields, required status changes |
| Sales Order | 10 | Hidden fields, filters |
| Delivery Note | 10 | Hidden fields, filters |
| Purchase Invoice | 8 | Hidden fields |
| Purchase Receipt | 8 | Hidden fields |
| Quotation | 8 | Hidden fields; `quotation_to` filter → Customer/Lead/Prospect/CRM Deal only |
| Purchase Order | 8 | Hidden fields |
| Item | 5 | Field visibility overrides (`barcodes`, `item_code`, `naming_series` — hidden/reqd) |
| Customer | 2 | Field property changes |
| Supplier | 2 | Field property changes |

#### HRMS Override Files

| File | What it overrides | Risk |
|------|-------------------|------|
| `hrms/overrides/employee_master.py` | `autoname()` — adds 3 naming strategies (series/number/fullname); adds `validate_onboarding_process()`, `publish_update()`, `update_job_applicant_and_offer()` | 🟡 Medium |
| `hrms/overrides/company.py` | `make_company_fixtures()` — runs regional HR setup on country change; `delete_company_fixtures()` — cleans up on company delete | 🟡 Medium |

#### Projects Module — New Child DocTypes

Two new child DocTypes back the `task_items` and `task_vendors` Table fields on Task:

| DocType | Parent | Fields | Risk |
|---------|--------|--------|------|
| **Construction Task Item** | Task | `item` (Link→Item), `qty` (Float), `uom` (Link→UOM), `notes` (Small Text) | 🟢 Low |
| **Construction Task Vendor** | Task | `vendor` (Link→Supplier), `vendor_role` (Data), `notes` (Small Text) | 🟢 Low |

These are new custom DocTypes in `apps/erpnext/erpnext/projects/doctype/`. `bench migrate` will create their tables on first run. Low migration risk — no overlap with v16 upstream Projects module.

#### sbiqc_provisioning DocTypes

| DocType | Fields | Risk |
|---------|--------|------|
| **Tenant** | 14 fields: subdomain, client_name, plan, currency, timezone, admin_email, site_name, status, provisioned_at, apps_to_install (Table), error_log | 🟢 Low |
| **Tenant App** | App name, version, install config | 🟢 Low |
| **Provisioning Log** | 12 fields: tenant (Link), site_name, current_step, status, progress (Percent), started_at, completed_at, steps_html, error_traceback | 🟢 Low |

#### V16 Risks for Custom Fields & Property Setters

| Risk | Detail |
|------|--------|
| **Employee `autoname()` override** | HRMS v16 may change Employee autoname behavior — verify `employee_master.py` override is still compatible with v16 Employee base class |
| **Company HR fields conflict** | If ERPNext v16 adds native HR/Payroll configuration to Company DocType, field name conflicts are possible (`basic_component`, `hra_component` etc.) |
| **Property setters on renamed fields** | If v16 renames any field targeted by a property setter (e.g. `additional_discount_account` on Sales Invoice), the setter silently stops working |
| **CRM Deal sync fields** | `erpnext_quotation`, `erpnext_invoice` etc. are Data fields storing ERPNext document IDs — if the linked DocType naming changes, these break |
| **`quotation_to` filter conflict** | crm_unify restricts `quotation_to` to CRM entities — check if v16 ERPNext adds its own filter on the same field |
| **`company.py` import path** | `from erpnext.accounts.utils import get_account_currency` — verify this path in v16 |

**Action required:**
- After upgrade run `bench migrate` — all custom fields and property setters are reapplied automatically.
- Verify Employee form: all 19 custom field sections visible, all approver fields functional.
- Verify Company form: HR/Payroll tab present with all salary component and account links.
- Test all transactional forms (Sales Invoice, Sales Order, Purchase Invoice, Delivery Note, etc.) for correct field visibility per property setters.
- Test `employee_master.py` autoname with all 3 naming strategies.
- Verify `company.py` `make_company_fixtures()` fires on company country change.
- Verify Quotation `quotation_to` field only shows Customer/Lead/Prospect/CRM Deal.
- Verify Project form: `total_project_budget`, `total_estimated_cost`, `budget_variance` fields visible under "Budget Overview" section.
- Verify Task form: construction section visible, `task_items` and `task_vendors` child tables load correctly with Construction Task Item/Vendor rows.
- Verify sbiqc_provisioning Tenant provisioning flow end-to-end.

---

## Upgrade Checklist Summary

### Pre-upgrade (test environment)

- [ ] Upgrade Python to 3.14+ on Ubuntu 22.04 or migrate to Ubuntu 24.04
- [ ] Upgrade Node.js to 24+
- [ ] Run `bench get-app --branch version-16 frappe` on the test bench
- [ ] Run `bench get-app --branch version-16 erpnext` on the test bench
- [ ] Run `bench get-app --branch version-16 hrms` on the test bench
- [ ] **Fix `mft_license_api.py`:** `frappe.cache()` → `frappe.cache` (remove parentheses — it's a property in v16)
- [ ] Fix `leave_application.py`: remove `daterange` import from supplier_scorecard
- [ ] Fix `employee.js` + `leave_allocation.js`: verify `employee_query` path
- [ ] Fix `employee.js`: verify `erpnext.utils.make_bank_account` still exists
- [ ] 3-way diff `sales_order.py` against v16 upstream and patch
- [ ] Fix `employee.py`: replace `raise_exception=True` with `print_logs=True` in any `has_permission` calls
- [ ] Run `bench migrate` on test — resolve all errors
- [ ] Validate POS flow end-to-end
- [ ] Validate Leave Application create/approve flow
- [ ] Validate Leave Allocation flow
- [ ] Validate Sales Order → Delivery Note → Sales Invoice flow
- [ ] Validate Job Offer → Create Employee flow
- [ ] Validate Helpdesk ticket creation acknowledgment email
- [ ] Validate MFT License full flow: new purchase → license email → portal OTP login → renewal
- [ ] Validate CRM (Frappe CRM) lead/contact/deal flows
- [ ] Validate crm_unify integration
- [ ] Re-apply custom role permissions
- [ ] Re-configure workspace sidebar customisations

### Production upgrade

- [ ] Announce maintenance window to all users
- [ ] Take a full site backup (`bench backup --with-files`)
- [ ] Run upgrade on production
- [ ] Run `bench migrate`
- [ ] Smoke-test all HIGH risk modules first (Sales Order, Leave Application)
- [ ] Confirm holiday list assignments are intact for all employees
- [ ] Confirm POS settings ("Use Sales Invoices in POS") is configured as intended
- [ ] Monitor error log for 48 hours post-upgrade

---

## Risk Matrix (Summary)

| File / Component | Risk | Owner | Status |
|------------------|------|-------|--------|
| `sales_order.py` — full override, 1,916 lines | 🔴 High | Dev | Done |
| `leave_application.py` — imports `daterange` from supplier_scorecard | 🔴 High | Dev | Done |
| Python 3.14 / Node 24 server prerequisite | 🔴 High | SysAdmin | Pending |
| `utils.js` — full override, 1,302 lines | 🟡 Medium | Dev | Done |
| `employee.py` — `has_permission` raise_exception param | 🟡 Medium | Dev | Done |
| `employee.js` — employee_query path | 🟡 Medium | Dev | Done |
| `leave_allocation.js` — employee_query path | 🟡 Medium | Dev | Done |
| `purchase_receipt.json` — DocType schema conflict | 🟡 Medium | Dev | Done |
| `contract.json` — DocType schema conflict | 🟡 Medium | Dev | Done |
| Custom apps (`crm_unify`, `sbiqc_provisioning`) — `frappe.db.commit()` in hooks | 🟡 Medium | Dev | Done |
| Holiday list per-employee migration | 🟡 Medium | HR Admin | Pending |
| Workspace sidebar reset | 🟡 Medium | All teams | Pending |
| `pos_profile.js` — `is_perpetual_inventory_enabled` | 🟡 Medium | Dev | Done |
| `mft_license_api.py` — `frappe.cache()` API call | 🔴 High | Dev | Done |
| `mft_license.py` — `get_payment_entry` import path | 🟡 Medium | Dev | Done |
| `hd_ticket_hooks.py` — acknowledgment email | 🟢 Low | Dev | Done |
| `delivery_trip.js` | 🟢 Low | Dev | Done |
| `salary_structure.js` | 🟢 Low | Dev | Done |
| `job_offer.js` | 🟢 Low | Dev | Done |
| Print formats (cheque, payment receipt) | 🟢 Low | Dev | Done |
| Frappe CRM (`crm` app) | 🟢 Low | Dev | Pending |
| Helpdesk app | 🟢 Low | Dev | Done |
| bench migrate on v16 test bench — no errors | 🟡 Medium | Dev | In Progress |
| Employee custom fields (20) intact after migrate | 🟢 Low | Dev | Done |
| Construction Task Item/Vendor tables on v16 | 🟢 Low | Dev | Pending |
| Project/Task construction custom fields loaded via fixtures | 🟢 Low | Dev | Pending |
