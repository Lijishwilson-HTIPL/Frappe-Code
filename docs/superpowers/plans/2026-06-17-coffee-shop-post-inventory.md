# Coffee Shop Post-Inventory — Implementation Plan (Phases 2–6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Phases 2–6 of the Namibian Coffee Roasters system — drink recipe BOMs, POS with automatic ingredient deduction, multi-branch support, a 5-tier smart sourcing hierarchy, and a manager reporting dashboard.

**Architecture:** All data lives in standard ERPNext DocTypes. Two Server Scripts drive automation: one fires on POS Invoice submit (deducts ingredients via BOM), one extends the Phase 1 low-stock alert with a 5-tier sourcing cascade (internal transfers → external POs). Six Script Reports and a custom Workspace complete the manager dashboard. No new DocTypes needed.

**Tech Stack:** ERPNext v15, Frappe Server Scripts (Python), ERPNext Stock module (BOM, POS Profile, POS Invoice, Stock Entry, Purchase Order, Bin, Warehouse), Frappe Script Reports, Frappe Workspace

---

## File Structure

| What | Path | Phase |
|---|---|---|
| POS deduction Server Script | DB only — `Settings → Server Script` | 3 |
| Extended sourcing Server Script | DB — update `Low Stock Alert - Coffee Shop` | 5 |
| Report: Stock Levels by Branch | `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/` (4 files) | 6 |
| Report: Daily Sales by Branch | `apps/erpnext/erpnext/stock/report/daily_sales_by_branch/` (4 files) | 6 |
| Report: Top Selling Drinks | `apps/erpnext/erpnext/stock/report/top_selling_drinks/` (4 files) | 6 |
| Report: Ingredient Cost vs Revenue | `apps/erpnext/erpnext/stock/report/ingredient_cost_vs_revenue/` (4 files) | 6 |
| Report: Waste & Loss Tracker | `apps/erpnext/erpnext/stock/report/waste_and_loss_tracker/` (4 files) | 6 |
| Report: Sourcing History | `apps/erpnext/erpnext/stock/report/sourcing_history/` (4 files) | 6 |
| hooks.py (fixtures update) | `apps/erpnext/erpnext/hooks.py` | 3, 5, 6 |
| fixtures server_script.json | `apps/erpnext/erpnext/fixtures/server_script.json` | 3, 5 |
| E2E test: POS deduction | `/tmp/test_pos_deduction.py` (not committed) | 3 |
| E2E test: Sourcing hierarchy | `/tmp/test_sourcing_hierarchy.py` (not committed) | 5 |

---

## Phase 2 — Bill of Materials

### Task 1: Create BOMs for all drinks in the ERPNext UI

**Files:** None — BOMs are created via ERPNext UI and stored in DB.

- [ ] **Step 1: Enable Manufacturing module**

Navigate to `Setup → Settings → System Settings`. Confirm `Manufacturing` is in the enabled modules list. If not, check it and Save.

- [ ] **Step 2: Open BOM list**

In the top search bar type `BOM` and open **BOM** under Manufacturing.

- [ ] **Step 3: Create BOM for Espresso**

Click **New**. Fill in:

| Field | Value |
|---|---|
| Item | `Espresso` |
| Quantity | `1` |
| UOM | `Cup` |
| Is Default | ✓ |
| Is Active | ✓ |
| Company | *(your company)* |

In the **Items** table add two rows:

| Item Code | Qty | UOM |
|---|---|---|
| `COFFEE-BEANS-ARABICA` | `0.018` | `Kg` |
| `CUPS-PAPER-8OZ` | `1` | `Nos` |

Click **Save**, then **Submit**.

- [ ] **Step 4: Create BOM for Latte**

Click **New**:

| Field | Value |
|---|---|
| Item | `Latte` |
| Quantity | `1` |
| UOM | `Cup` |
| Is Default | ✓ |
| Is Active | ✓ |

Items table:

| Item Code | Qty | UOM |
|---|---|---|
| `COFFEE-BEANS-ARABICA` | `0.018` | `Kg` |
| `MILK-FULL-CREAM` | `0.2` | `Litre` |
| `CUPS-PAPER-8OZ` | `1` | `Nos` |

Save → Submit.

- [ ] **Step 5: Verify BOMs**

In the BOM list, filter by `Is Default = Yes`. Both Espresso and Latte should appear with status `Active`.

Run this to confirm via console:

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local execute frappe.db.get_all --args "\"BOM\"" --kwargs "{\"filters\":{\"is_default\":1,\"is_active\":1},\"fields\":[\"name\",\"item\",\"docstatus\"]}"'
```

Expected: both BOMs listed with `docstatus: 1`.

- [ ] **Step 6: Commit**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && git add apps/erpnext/ && git commit -m "feat(coffee-bom): add Phase 2 BOM note — BOMs created in DB via UI"'
```

---

## Phase 3 — Point of Sale + Auto Ingredient Deduction

### Task 2: Create POS Profile for Branch 1

**Files:** None — POS Profile created via ERPNext UI.

- [ ] **Step 1: Open POS Profile**

Navigate to `Retail → POS Profile → New`.

- [ ] **Step 2: Fill in POS Profile**

| Field | Value |
|---|---|
| POS Profile Name | `Coffee Shop - Branch 1` |
| Company | *(your company)* |
| Warehouse | `Coffee Shop - Main - [Abbr]` *(the warehouse from Phase 1)* |
| Write Off Account | *(leave default)* |
| Apply Discount On | `Grand Total` |

In the **Payment Methods** table add two rows:

| Mode of Payment | Default |
|---|---|
| `Cash` | ✓ |
| `Card` | ☐ |

Click **Save**.

- [ ] **Step 3: Verify POS Profile**

Open `Retail → POS Profile`. The new profile should appear. Click it and confirm the warehouse is correctly set.

---

### Task 3: Create the POS Auto-Deduction Server Script

**Files:**
- Create (DB): `POS Auto Deduction - Coffee Shop` Server Script via `Settings → Server Script`
- Modify: `apps/erpnext/erpnext/hooks.py`

- [ ] **Step 1: Read hooks.py**

```powershell
Get-Content "\\wsl.localhost\Ubuntu-22.04\home\hilton\frappe-bench\apps\erpnext\erpnext\hooks.py"
```

- [ ] **Step 2: Open Server Script list and create new script**

Navigate to `Settings → Server Script → New`. Fill in the header:

| Field | Value |
|---|---|
| Name | `POS Auto Deduction - Coffee Shop` |
| Script Type | `DocType Event` |
| Reference DocType | `POS Invoice` |
| DocType Event | `On Submit` |
| Enabled | ✓ |

- [ ] **Step 3: Paste the script**

In the **Script** field paste exactly:

```python
# Determine the warehouse for this POS session
warehouse = doc.set_warehouse
if not warehouse:
    warehouse = frappe.db.get_value("POS Profile", doc.pos_profile, "warehouse")

if not warehouse:
    frappe.log_error(
        "No warehouse found for POS Invoice {0}".format(doc.name),
        "POS Auto Deduction - No Warehouse"
    )
    return

for item in doc.items:
    item_code = item.item_code
    qty_sold = item.qty

    # Find the submitted default BOM for this item
    bom_name = frappe.db.get_value("BOM", {
        "item": item_code,
        "is_default": 1,
        "is_active": 1,
        "docstatus": 1
    }, "name")

    if not bom_name:
        continue  # No BOM — packaged/non-manufactured item, skip

    # Get raw material rows from the BOM
    bom_items = frappe.db.get_all("BOM Item", {
        "parent": bom_name,
        "parenttype": "BOM"
    }, ["item_code", "qty", "stock_uom"])

    if not bom_items:
        continue

    se_items = []

    # Consumption rows: raw materials out
    for bom_item in bom_items:
        se_items.append({
            "item_code": bom_item.item_code,
            "qty": bom_item.qty * qty_sold,
            "uom": bom_item.stock_uom,
            "s_warehouse": warehouse
        })

    # Production row: finished drink in
    se_items.append({
        "item_code": item_code,
        "qty": qty_sold,
        "uom": item.stock_uom or item.uom,
        "t_warehouse": warehouse
    })

    try:
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Manufacture",
            "company": doc.company,
            "bom_no": bom_name,
            "fg_completed_qty": qty_sold,
            "remarks": "Auto-created from POS Invoice {0}".format(doc.name),
            "items": se_items
        })
        se.insert(ignore_permissions=True)
        se.submit()
    except Exception as e:
        frappe.log_error(
            "POS deduction failed for {0} on invoice {1}: {2}".format(
                item_code, doc.name, str(e)
            ),
            "POS Auto Deduction Error"
        )
```

Click **Save**.

- [ ] **Step 4: Add the new script to the fixtures filter in hooks.py**

Read `apps/erpnext/erpnext/hooks.py`. Update the `fixtures` list so the filter covers both scripts:

```python
# Namibian Coffee Roasters — fixtures for version control
fixtures = [
    {"dt": "Server Script", "filters": [["name", "like", "%Coffee Shop%"]]},
    {"dt": "Role", "filters": [["role_name", "=", "Namibian Coffee Roasters Manager"]]},
]
```

- [ ] **Step 5: Export and commit**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local export-fixtures --app erpnext'
```

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && git add apps/erpnext/erpnext/hooks.py apps/erpnext/erpnext/fixtures/server_script.json && git commit -m "feat(coffee-pos): add POS auto-deduction server script"'
```

---

### Task 4: End-to-End Test — POS Invoice triggers ingredient deduction

**Files:**
- Create: `/tmp/test_pos_deduction.py` (not committed)

- [ ] **Step 1: Check opening stock before the test**

```powershell
$script = @'
import frappe

item_code = "COFFEE-BEANS-ARABICA"
warehouse_name = "Coffee Shop - Main"
warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name}, "name")
qty_before = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
print("Coffee Beans qty before:", qty_before)
frappe.db.rollback()
'@
$script | Out-File -FilePath "\\wsl.localhost\Ubuntu-22.04\tmp\test_pos_deduction.py" -Encoding utf8
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ../env/bin/python -m frappe.utils.bench_helper frappe --site mysite.local console < /tmp/test_pos_deduction.py'
```

Note the qty shown — expect a number above the reorder level (5 Kg).

- [ ] **Step 2: Submit a POS Invoice via the UI for 1 Latte**

Open `Retail → Point of Sale`. Select profile `Coffee Shop - Branch 1`. Add item `Latte` qty `1`. Select payment method `Cash`, enter amount. Click **Submit**.

- [ ] **Step 3: Verify ingredients were deducted**

```powershell
$script = @'
import frappe

warehouse_name = "Coffee Shop - Main"
warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name}, "name")

for item_code, expected_deduction in [("COFFEE-BEANS-ARABICA", 0.018), ("MILK-FULL-CREAM", 0.2), ("CUPS-PAPER-8OZ", 1)]:
    qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
    print("{0}: {1} (deducted {2})".format(item_code, qty, expected_deduction))

# Check Stock Entry was created
se_list = frappe.db.get_all("Stock Entry", {
    "stock_entry_type": "Manufacture",
    "remarks": ["like", "Auto-created from POS Invoice%"]
}, ["name", "remarks", "creation"], order_by="creation desc", limit=3)
print("Recent manufacture stock entries:", se_list)

frappe.db.rollback()
'@
$script | Out-File -FilePath "\\wsl.localhost\Ubuntu-22.04\tmp\test_pos_deduction.py" -Encoding utf8
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ../env/bin/python -m frappe.utils.bench_helper frappe --site mysite.local console < /tmp/test_pos_deduction.py'
```

Expected: coffee beans reduced by 0.018, milk by 0.2, cups by 1. One Stock Entry of type Manufacture linked to the POS Invoice in remarks.

- [ ] **Step 4: Verify no deduction for an item with no BOM**

Add `Coffee Filters` (Equipment & Consumables — no BOM) to a new POS Invoice and submit. Verify no Stock Entry of type Manufacture was created for it and its stock was NOT changed by the script (only by the POS Invoice's own mechanism).

---

## Phase 4 — Multi-Branch

### Task 5: Create second branch warehouse and POS Profile

**Files:** None — UI configuration.

- [ ] **Step 1: Create Branch 2 Warehouse**

Navigate to `Stock → Warehouse → New`:

| Field | Value |
|---|---|
| Warehouse Name | `Coffee Shop - Branch 2` |
| Warehouse Type | `Stores` |
| Company | *(your company)* |

Save. Note the full name (e.g. `Coffee Shop - Branch 2 - NCR`).

- [ ] **Step 2: Create Head Office Warehouse**

Navigate to `Stock → Warehouse → New`:

| Field | Value |
|---|---|
| Warehouse Name | `Head Office` |
| Warehouse Type | `Stores` |
| Company | *(your company)* |

Save. Note the full name (e.g. `Head Office - NCR`).

- [ ] **Step 3: Create external source Warehouses**

Repeat the same warehouse creation steps for each:

| Warehouse Name | Warehouse Type |
|---|---|
| `Wholesale Store` | `Transit` |
| `Supermarket` | `Transit` |
| `Small Shop` | `Transit` |

- [ ] **Step 4: Set reorder levels for Branch 2**

Navigate to `Stock → Item → Coffee Beans - Arabica`. Open the **Reorder Levels** tab. Add a row for Branch 2:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| `Coffee Shop - Branch 2 - [Abbr]` | `5` | `20` | `Kg` |

Repeat for all 9 items on both Branch 2 and Head Office warehouses (use same levels as Branch 1 from Phase 1 plan).

- [ ] **Step 5: Create POS Profile for Branch 2**

Navigate to `Retail → POS Profile → New`:

| Field | Value |
|---|---|
| POS Profile Name | `Coffee Shop - Branch 2` |
| Company | *(your company)* |
| Warehouse | `Coffee Shop - Branch 2 - [Abbr]` |

Payment Methods: Cash + Card (same as Branch 1).

Save.

- [ ] **Step 6: Add opening stock to Branch 2 and Head Office**

Navigate to `Stock → Stock Reconciliation → New`. Set Purpose = `Opening Stock`. Add all 9 items for `Coffee Shop - Branch 2 - [Abbr]` at above-reorder quantities (same as Phase 1 Task 6). Submit.

Repeat for `Head Office - [Abbr]` using higher quantities (e.g. 3× reorder qty — Head Office holds central buffer stock).

- [ ] **Step 7: Create Suppliers for external sources**

Navigate to `Buying → Supplier → New`. Create three suppliers:

| Supplier Name | Supplier Type |
|---|---|
| `Wholesale Store` | `Company` |
| `Supermarket` | `Company` |
| `Small Shop` | `Individual` |

Save each.

- [ ] **Step 8: Commit**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && git add apps/erpnext/ && git commit -m "feat(coffee-branch): Phase 4 multi-branch setup note"'
```

---

## Phase 5 — Smart Sourcing Hierarchy

### Task 6: Replace the Low Stock Alert script with the 5-tier sourcing version

**Files:**
- Modify (DB): `Low Stock Alert - Coffee Shop` Server Script
- Modify: `apps/erpnext/erpnext/fixtures/server_script.json` (via export)

- [ ] **Step 1: Open the existing script**

Navigate to `Settings → Server Script → Low Stock Alert - Coffee Shop`. Click **Edit**.

- [ ] **Step 2: Replace the entire script body with the sourcing version**

Select all content in the Script field and replace with:

```python
item_code = doc.item_code
warehouse = doc.warehouse

actual_qty = frappe.db.get_value("Bin",
    {"item_code": item_code, "warehouse": warehouse},
    "actual_qty") or 0

reorder_level = frappe.db.get_value("Item Reorder",
    {"parent": item_code, "warehouse": warehouse},
    "warehouse_reorder_level") or 0

reorder_qty = frappe.db.get_value("Item Reorder",
    {"parent": item_code, "warehouse": warehouse},
    "warehouse_reorder_qty") or 10

if actual_qty >= reorder_level or reorder_level == 0:
    return

recent = frappe.db.exists("Notification Log", {
    "document_type": "Item",
    "document_name": item_code,
    "creation": [">", frappe.utils.add_days(frappe.utils.now(), -1)]
})
if recent:
    return

recipients = frappe.db.sql("""
    SELECT u.email, u.name
    FROM `tabUser` u
    JOIN `tabHas Role` hr ON hr.parent = u.name
    WHERE hr.role = 'Namibian Coffee Roasters Manager'
      AND u.enabled = 1
      AND u.email IS NOT NULL
      AND u.email != ''
""", as_dict=True)

if not recipients:
    return

item_name = frappe.db.get_value("Item", item_code, "item_name")
uom = frappe.db.get_value("Item", item_code, "stock_uom")
company = frappe.db.get_value("Warehouse", warehouse, "company")


def notify(action_message):
    subject = "Low Stock Alert - {0}".format(item_name)
    message = (
        "{0} at {1} has dropped to {2} {3}. "
        "Reorder level is {4} {3}. {5}".format(
            item_name, warehouse, actual_qty, uom, reorder_level, action_message
        )
    )
    for user in recipients:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": subject,
            "email_content": message,
            "for_user": user.get("name"),
            "document_type": "Item",
            "document_name": item_code,
            "type": "Alert"
        }).insert(ignore_permissions=True)
        frappe.sendmail(
            recipients=[user.get("email")],
            subject=subject,
            message=message
        )


def get_qty(wh):
    return frappe.db.get_value("Bin",
        {"item_code": item_code, "warehouse": wh},
        "actual_qty") or 0


def get_wh_reorder_level(wh):
    return frappe.db.get_value("Item Reorder",
        {"parent": item_code, "warehouse": wh},
        "warehouse_reorder_level") or 0


def create_transfer(source_wh, dest_wh, qty):
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "company": company,
        "remarks": "Auto-transfer: low stock at {0}".format(dest_wh),
        "items": [{
            "item_code": item_code,
            "qty": qty,
            "uom": uom,
            "s_warehouse": source_wh,
            "t_warehouse": dest_wh
        }]
    })
    se.insert(ignore_permissions=True)
    return se.name


def create_po(supplier_name, qty, dest_wh):
    supplier = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
    if not supplier:
        return None
    po = frappe.get_doc({
        "doctype": "Purchase Order",
        "supplier": supplier,
        "company": company,
        "schedule_date": frappe.utils.add_days(frappe.utils.today(), 3),
        "items": [{
            "item_code": item_code,
            "qty": qty,
            "warehouse": dest_wh,
            "schedule_date": frappe.utils.add_days(frappe.utils.today(), 3),
            "uom": uom
        }]
    })
    po.insert(ignore_permissions=True)
    return po.name


# STEP 1 — Head Office
head_office_wh = frappe.db.get_value("Warehouse",
    {"warehouse_name": "Head Office", "company": company, "disabled": 0}, "name")

if head_office_wh:
    ho_qty = get_qty(head_office_wh)
    ho_reorder = get_wh_reorder_level(head_office_wh)
    if ho_qty > (ho_reorder * 1.5) and ho_qty >= reorder_qty:
        create_transfer(head_office_wh, warehouse, reorder_qty)
        notify("Stock transferred from Head Office - no purchase needed.")
        return

# STEP 2 — Other Coffee Shop branches
branch_whs = frappe.db.get_all("Warehouse", {
    "warehouse_name": ["like", "Coffee Shop%"],
    "company": company,
    "disabled": 0
}, ["name"])

for branch_dict in branch_whs:
    branch_wh = branch_dict.name
    if branch_wh == warehouse:
        continue
    branch_qty = get_qty(branch_wh)
    branch_reorder = get_wh_reorder_level(branch_wh)
    if branch_qty > (branch_reorder * 1.5) and branch_qty >= reorder_qty:
        create_transfer(branch_wh, warehouse, reorder_qty)
        notify("Stock transferred from {0} - no purchase needed.".format(branch_wh))
        return

# STEPS 3–5 — External suppliers in priority order
external_sources = [
    ("Wholesale Store", "Draft PO raised to Wholesale Store."),
    ("Supermarket", "Wholesale unavailable - Draft PO raised to Supermarket."),
    ("Small Shop", "EMERGENCY: Draft PO raised to Small Shop - review urgently."),
]

for supplier_name, message in external_sources:
    po_name = create_po(supplier_name, reorder_qty, warehouse)
    if po_name:
        notify(message)
        return

notify("WARNING: No sourcing option found. Manual restocking required immediately.")
```

Click **Save**.

---

### Task 7: Test the 5-tier sourcing hierarchy

**Files:**
- Create: `/tmp/test_sourcing_hierarchy.py` (not committed)

- [ ] **Step 1: Write the test script**

```powershell
$script = @'
import frappe

item_code = "COFFEE-BEANS-ARABICA"
company = frappe.db.get_value("Warehouse", {"warehouse_name": "Coffee Shop - Main"}, "company")

# Show current state of all relevant warehouses
whs = frappe.db.get_all("Warehouse", {
    "company": company,
    "warehouse_name": ["in", ["Coffee Shop - Main", "Head Office", "Coffee Shop - Branch 2"]]
}, ["name", "warehouse_name"])

print("=== Current stock across warehouses ===")
for wh in whs:
    qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh.name}, "actual_qty") or 0
    reorder = frappe.db.get_value("Item Reorder", {"parent": item_code, "warehouse": wh.name}, "warehouse_reorder_level") or 0
    print("{0}: qty={1}, reorder_level={2}, surplus_threshold={3}".format(
        wh.warehouse_name, qty, reorder, reorder * 1.5))

# Check recent notification logs and POs
print("\n=== Recent Notification Logs for this item ===")
logs = frappe.db.get_all("Notification Log", {
    "document_type": "Item",
    "document_name": item_code
}, ["subject", "email_content", "creation"], order_by="creation desc", limit=5)
for log in logs:
    print(" -", log.subject, "|", log.email_content[:100])

print("\n=== Recent Purchase Orders for this item ===")
pos = frappe.db.sql("""
    SELECT po.name, po.supplier, poi.item_code, poi.qty
    FROM `tabPurchase Order` po
    JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
    WHERE poi.item_code = %s
    ORDER BY po.creation DESC LIMIT 5
""", item_code, as_dict=True)
for po in pos:
    print(" -", po.name, "|", po.supplier, "|", po.qty)

frappe.db.rollback()
'@
$script | Out-File -FilePath "\\wsl.localhost\Ubuntu-22.04\tmp\test_sourcing_hierarchy.py" -Encoding utf8
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ../env/bin/python -m frappe.utils.bench_helper frappe --site mysite.local console < /tmp/test_sourcing_hierarchy.py'
```

- [ ] **Step 2: Test Step 1 — Head Office has surplus**

Ensure Head Office has at least `reorder_qty × 1.5` stock for Coffee Beans via Stock Reconciliation. Then drop Branch 1 stock below reorder via Stock Reconciliation. Rerun the test script — expect a Stock Entry (Material Transfer) from Head Office and notification containing "Head Office".

- [ ] **Step 3: Test Step 2 — Branch has surplus (Head Office depleted)**

Set Head Office Coffee Beans stock to 0 via Stock Reconciliation. Ensure Branch 2 has surplus (above `reorder_level × 1.5`). Drop Branch 1 stock below reorder. Wait 25 hours (or manually delete the recent Notification Log entry to bypass dedup). Rerun test script — expect transfer from Branch 2.

- [ ] **Step 4: Test Step 3 — PO to Wholesale (all internal sources depleted)**

Set Head Office and Branch 2 Coffee Beans stock to 0. Drop Branch 1 below reorder. Delete recent Notification Log entry to bypass dedup. Rerun test — expect Draft Purchase Order with supplier `Wholesale Store`.

- [ ] **Step 5: Export fixtures and commit**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local export-fixtures --app erpnext'
```

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && git add apps/erpnext/erpnext/fixtures/server_script.json && git commit -m "feat(coffee-sourcing): Phase 5 5-tier smart sourcing hierarchy"'
```

---

## Phase 6 — Reporting Dashboard

### Task 8: Create the Coffee Shop report directory structure

**Files:**
- Create: `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/` (and 5 more directories)

- [ ] **Step 1: Create report directories and `__init__.py` files**

```powershell
$base = "\\wsl.localhost\Ubuntu-22.04\home\hilton\frappe-bench\apps\erpnext\erpnext\stock\report"
$reports = @(
    "stock_levels_by_branch",
    "daily_sales_by_branch",
    "top_selling_drinks",
    "ingredient_cost_vs_revenue",
    "waste_and_loss_tracker",
    "sourcing_history"
)
foreach ($r in $reports) {
    New-Item -ItemType Directory -Force "$base\$r" | Out-Null
    New-Item -ItemType File -Force "$base\$r\__init__.py" | Out-Null
}
Write-Host "Directories created."
```

---

### Task 9: Report — Stock Levels by Branch

**Files:**
- Create: `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/stock_levels_by_branch.json`
- Create: `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/stock_levels_by_branch.py`
- Create: `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/stock_levels_by_branch.js`

- [ ] **Step 1: Write the JSON**

Create `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/stock_levels_by_branch.json`:

```json
{
  "add_total_row": 0,
  "disabled": 0,
  "docstatus": 0,
  "doctype": "Report",
  "is_standard": "Yes",
  "module": "Stock",
  "name": "Stock Levels by Branch",
  "report_name": "Stock Levels by Branch",
  "report_type": "Script Report",
  "ref_doctype": "Bin",
  "roles": [{"role": "Namibian Coffee Roasters Manager"}]
}
```

- [ ] **Step 2: Write the Python**

Create `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/stock_levels_by_branch.py`:

```python
import frappe


def execute(filters=None):
    columns = [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Data", "width": 150},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
        {"label": "Current Qty", "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},
        {"label": "UOM", "fieldname": "stock_uom", "fieldtype": "Data", "width": 80},
        {"label": "Reorder Level", "fieldname": "reorder_level", "fieldtype": "Float", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

    data = frappe.db.sql("""
        SELECT
            b.item_code,
            i.item_name,
            i.item_group,
            b.warehouse,
            b.actual_qty,
            i.stock_uom,
            COALESCE(ir.warehouse_reorder_level, 0) AS reorder_level,
            CASE
                WHEN b.actual_qty < COALESCE(ir.warehouse_reorder_level, 0) THEN 'Low Stock'
                ELSE 'OK'
            END AS status
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        LEFT JOIN `tabItem Reorder` ir
            ON ir.parent = b.item_code AND ir.warehouse = b.warehouse
        WHERE b.warehouse LIKE 'Coffee Shop%%'
           OR b.warehouse LIKE 'Head Office%%'
        ORDER BY status DESC, b.warehouse, b.item_code
    """, as_dict=True)

    return columns, data
```

- [ ] **Step 3: Write the JS**

Create `apps/erpnext/erpnext/stock/report/stock_levels_by_branch/stock_levels_by_branch.js`:

```javascript
frappe.query_reports["Stock Levels by Branch"] = {
	"filters": []
};
```

- [ ] **Step 4: Run bench migrate to register the report**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH" && cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local migrate'
```

- [ ] **Step 5: Verify the report is accessible**

Navigate to `Stock → Reports → Stock Levels by Branch`. The report should open and display items from Coffee Shop warehouses.

---

### Task 10: Report — Daily Sales by Branch

**Files:**
- Create: `apps/erpnext/erpnext/stock/report/daily_sales_by_branch/daily_sales_by_branch.json`
- Create: `apps/erpnext/erpnext/stock/report/daily_sales_by_branch/daily_sales_by_branch.py`
- Create: `apps/erpnext/erpnext/stock/report/daily_sales_by_branch/daily_sales_by_branch.js`

- [ ] **Step 1: Write the JSON**

Create `apps/erpnext/erpnext/stock/report/daily_sales_by_branch/daily_sales_by_branch.json`:

```json
{
  "add_total_row": 1,
  "disabled": 0,
  "doctype": "Report",
  "is_standard": "Yes",
  "module": "Stock",
  "name": "Daily Sales by Branch",
  "report_name": "Daily Sales by Branch",
  "report_type": "Script Report",
  "ref_doctype": "POS Invoice",
  "roles": [{"role": "Namibian Coffee Roasters Manager"}]
}
```

- [ ] **Step 2: Write the Python**

Create `apps/erpnext/erpnext/stock/report/daily_sales_by_branch/daily_sales_by_branch.py`:

```python
import frappe
from frappe.utils import today, add_months


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or add_months(today(), -1)
    to_date = filters.get("to_date") or today()

    columns = [
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": "Warehouse (Branch)", "fieldname": "set_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": "Qty Sold", "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 130},
    ]

    data = frappe.db.sql("""
        SELECT
            pi.posting_date,
            pi.set_warehouse,
            pii.item_code,
            pii.item_name,
            SUM(pii.qty) AS qty,
            SUM(pii.amount) AS amount
        FROM `tabPOS Invoice Item` pii
        INNER JOIN `tabPOS Invoice` pi ON pi.name = pii.parent
        WHERE pi.docstatus = 1
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY pi.posting_date, pi.set_warehouse, pii.item_code
        ORDER BY pi.posting_date DESC, pi.set_warehouse, pii.item_code
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    return columns, data
```

- [ ] **Step 3: Write the JS**

Create `apps/erpnext/erpnext/stock/report/daily_sales_by_branch/daily_sales_by_branch.js`:

```javascript
frappe.query_reports["Daily Sales by Branch"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	]
};
```

- [ ] **Step 4: Run bench migrate**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH" && cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local migrate'
```

---

### Task 11: Report — Top Selling Drinks

**Files:**
- Create: `apps/erpnext/erpnext/stock/report/top_selling_drinks/top_selling_drinks.json`
- Create: `apps/erpnext/erpnext/stock/report/top_selling_drinks/top_selling_drinks.py`
- Create: `apps/erpnext/erpnext/stock/report/top_selling_drinks/top_selling_drinks.js`

- [ ] **Step 1: Write the JSON**

```json
{
  "add_total_row": 0,
  "disabled": 0,
  "doctype": "Report",
  "is_standard": "Yes",
  "module": "Stock",
  "name": "Top Selling Drinks",
  "report_name": "Top Selling Drinks",
  "report_type": "Script Report",
  "ref_doctype": "POS Invoice",
  "roles": [{"role": "Namibian Coffee Roasters Manager"}]
}
```

- [ ] **Step 2: Write the Python**

```python
import frappe
from frappe.utils import today, add_months


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or add_months(today(), -1)
    to_date = filters.get("to_date") or today()

    columns = [
        {"label": "Rank", "fieldname": "rank", "fieldtype": "Int", "width": 60},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 220},
        {"label": "Total Qty Sold", "fieldname": "total_qty", "fieldtype": "Float", "width": 140},
        {"label": "Total Revenue", "fieldname": "total_amount", "fieldtype": "Currency", "width": 140},
    ]

    rows = frappe.db.sql("""
        SELECT
            pii.item_code,
            pii.item_name,
            SUM(pii.qty) AS total_qty,
            SUM(pii.amount) AS total_amount
        FROM `tabPOS Invoice Item` pii
        INNER JOIN `tabPOS Invoice` pi ON pi.name = pii.parent
        INNER JOIN `tabItem` i ON i.name = pii.item_code
        WHERE pi.docstatus = 1
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND i.item_group = 'Finished Product'
        GROUP BY pii.item_code
        ORDER BY total_qty DESC
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    data = []
    for idx, row in enumerate(rows):
        row["rank"] = idx + 1
        data.append(row)

    return columns, data
```

- [ ] **Step 3: Write the JS**

```javascript
frappe.query_reports["Top Selling Drinks"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	]
};
```

- [ ] **Step 4: Run bench migrate**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH" && cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local migrate'
```

---

### Task 12: Report — Ingredient Cost vs Revenue

**Files:**
- Create: `apps/erpnext/erpnext/stock/report/ingredient_cost_vs_revenue/ingredient_cost_vs_revenue.json`
- Create: `apps/erpnext/erpnext/stock/report/ingredient_cost_vs_revenue/ingredient_cost_vs_revenue.py`
- Create: `apps/erpnext/erpnext/stock/report/ingredient_cost_vs_revenue/ingredient_cost_vs_revenue.js`

- [ ] **Step 1: Write the JSON**

```json
{
  "add_total_row": 0,
  "disabled": 0,
  "doctype": "Report",
  "is_standard": "Yes",
  "module": "Stock",
  "name": "Ingredient Cost vs Revenue",
  "report_name": "Ingredient Cost vs Revenue",
  "report_type": "Script Report",
  "ref_doctype": "POS Invoice",
  "roles": [{"role": "Namibian Coffee Roasters Manager"}]
}
```

- [ ] **Step 2: Write the Python**

```python
import frappe
from frappe.utils import today, add_months


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or add_months(today(), -1)
    to_date = filters.get("to_date") or today()

    columns = [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": "Qty Sold", "fieldname": "qty_sold", "fieldtype": "Float", "width": 100},
        {"label": "Revenue", "fieldname": "revenue", "fieldtype": "Currency", "width": 130},
        {"label": "Ingredient Cost", "fieldname": "ingredient_cost", "fieldtype": "Currency", "width": 140},
        {"label": "Gross Margin", "fieldname": "gross_margin", "fieldtype": "Currency", "width": 130},
        {"label": "Margin %", "fieldname": "margin_pct", "fieldtype": "Percent", "width": 100},
    ]

    sales = frappe.db.sql("""
        SELECT
            pii.item_code,
            pii.item_name,
            SUM(pii.qty) AS qty_sold,
            SUM(pii.amount) AS revenue
        FROM `tabPOS Invoice Item` pii
        INNER JOIN `tabPOS Invoice` pi ON pi.name = pii.parent
        INNER JOIN `tabItem` i ON i.name = pii.item_code
        WHERE pi.docstatus = 1
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND i.item_group = 'Finished Product'
        GROUP BY pii.item_code
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    data = []
    for sale in sales:
        cost_result = frappe.db.sql("""
            SELECT COALESCE(SUM(sed.basic_amount), 0) AS cost
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON se.name = sed.parent
            WHERE se.docstatus = 1
              AND se.stock_entry_type = 'Manufacture'
              AND se.posting_date BETWEEN %(from_date)s AND %(to_date)s
              AND sed.t_warehouse IS NULL
              AND se.bom_no IN (
                  SELECT name FROM `tabBOM`
                  WHERE item = %(item_code)s
                    AND is_default = 1
                    AND is_active = 1
                    AND docstatus = 1
              )
        """, {"from_date": from_date, "to_date": to_date, "item_code": sale.item_code}, as_dict=True)

        ingredient_cost = cost_result[0].cost if cost_result else 0
        revenue = sale.revenue or 0
        gross_margin = revenue - ingredient_cost
        margin_pct = (gross_margin / revenue * 100) if revenue else 0

        data.append({
            "item_code": sale.item_code,
            "item_name": sale.item_name,
            "qty_sold": sale.qty_sold,
            "revenue": revenue,
            "ingredient_cost": ingredient_cost,
            "gross_margin": gross_margin,
            "margin_pct": round(margin_pct, 2)
        })

    data.sort(key=lambda x: x["gross_margin"], reverse=True)
    return columns, data
```

- [ ] **Step 3: Write the JS**

```javascript
frappe.query_reports["Ingredient Cost vs Revenue"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	]
};
```

- [ ] **Step 4: Run bench migrate**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH" && cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local migrate'
```

---

### Task 13: Report — Waste & Loss Tracker

**Files:**
- Create: `apps/erpnext/erpnext/stock/report/waste_and_loss_tracker/waste_and_loss_tracker.json`
- Create: `apps/erpnext/erpnext/stock/report/waste_and_loss_tracker/waste_and_loss_tracker.py`
- Create: `apps/erpnext/erpnext/stock/report/waste_and_loss_tracker/waste_and_loss_tracker.js`

- [ ] **Step 1: Write the JSON**

```json
{
  "add_total_row": 0,
  "disabled": 0,
  "doctype": "Report",
  "is_standard": "Yes",
  "module": "Stock",
  "name": "Waste and Loss Tracker",
  "report_name": "Waste and Loss Tracker",
  "report_type": "Script Report",
  "ref_doctype": "Stock Entry",
  "roles": [{"role": "Namibian Coffee Roasters Manager"}]
}
```

- [ ] **Step 2: Write the Python**

```python
import frappe
from frappe.utils import today, add_months


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or add_months(today(), -1)
    to_date = filters.get("to_date") or today()

    columns = [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": "UOM", "fieldname": "stock_uom", "fieldtype": "Data", "width": 80},
        {"label": "Expected Consumption", "fieldname": "expected_qty", "fieldtype": "Float", "width": 180},
        {"label": "Actual Deducted", "fieldname": "actual_qty", "fieldtype": "Float", "width": 140},
        {"label": "Variance", "fieldname": "variance", "fieldtype": "Float", "width": 100},
        {"label": "Variance %", "fieldname": "variance_pct", "fieldtype": "Percent", "width": 110},
    ]

    raw_items = frappe.db.get_all("Item",
        {"item_group": "Raw Ingredient"},
        ["name", "item_name", "stock_uom"])

    data = []
    for raw_item in raw_items:
        expected_result = frappe.db.sql("""
            SELECT COALESCE(SUM(bi.qty * pii_totals.qty_sold), 0) AS expected_qty
            FROM `tabBOM Item` bi
            INNER JOIN `tabBOM` b ON b.name = bi.parent
            INNER JOIN (
                SELECT pii.item_code, SUM(pii.qty) AS qty_sold
                FROM `tabPOS Invoice Item` pii
                INNER JOIN `tabPOS Invoice` pi ON pi.name = pii.parent
                WHERE pi.docstatus = 1
                  AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
                GROUP BY pii.item_code
            ) pii_totals ON pii_totals.item_code = b.item
            WHERE bi.item_code = %(item_code)s
              AND b.is_default = 1
              AND b.is_active = 1
              AND b.docstatus = 1
        """, {"from_date": from_date, "to_date": to_date, "item_code": raw_item.name}, as_dict=True)

        expected_qty = expected_result[0].expected_qty if expected_result else 0

        actual_result = frappe.db.sql("""
            SELECT COALESCE(SUM(sed.qty), 0) AS actual_qty
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON se.name = sed.parent
            WHERE se.docstatus = 1
              AND se.stock_entry_type = 'Manufacture'
              AND se.posting_date BETWEEN %(from_date)s AND %(to_date)s
              AND sed.item_code = %(item_code)s
              AND sed.t_warehouse IS NULL
        """, {"from_date": from_date, "to_date": to_date, "item_code": raw_item.name}, as_dict=True)

        actual_qty = actual_result[0].actual_qty if actual_result else 0

        if expected_qty == 0 and actual_qty == 0:
            continue

        variance = actual_qty - expected_qty
        variance_pct = round((variance / expected_qty * 100), 2) if expected_qty else 0

        data.append({
            "item_code": raw_item.name,
            "item_name": raw_item.item_name,
            "stock_uom": raw_item.stock_uom,
            "expected_qty": expected_qty,
            "actual_qty": actual_qty,
            "variance": variance,
            "variance_pct": variance_pct
        })

    data.sort(key=lambda x: abs(x["variance"]), reverse=True)
    return columns, data
```

- [ ] **Step 3: Write the JS**

```javascript
frappe.query_reports["Waste and Loss Tracker"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	]
};
```

- [ ] **Step 4: Run bench migrate**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH" && cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local migrate'
```

---

### Task 14: Report — Sourcing History

**Files:**
- Create: `apps/erpnext/erpnext/stock/report/sourcing_history/sourcing_history.json`
- Create: `apps/erpnext/erpnext/stock/report/sourcing_history/sourcing_history.py`
- Create: `apps/erpnext/erpnext/stock/report/sourcing_history/sourcing_history.js`

- [ ] **Step 1: Write the JSON**

```json
{
  "add_total_row": 0,
  "disabled": 0,
  "doctype": "Report",
  "is_standard": "Yes",
  "module": "Stock",
  "name": "Sourcing History",
  "report_name": "Sourcing History",
  "report_type": "Script Report",
  "ref_doctype": "Notification Log",
  "roles": [{"role": "Namibian Coffee Roasters Manager"}]
}
```

- [ ] **Step 2: Write the Python**

```python
import frappe
from frappe.utils import today, add_months


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date") or add_months(today(), -1)
    to_date = filters.get("to_date") or today()

    columns = [
        {"label": "Date", "fieldname": "creation_date", "fieldtype": "Date", "width": 110},
        {"label": "Item", "fieldname": "document_name", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": "Action Taken", "fieldname": "action", "fieldtype": "Data", "width": 280},
        {"label": "Alert Message", "fieldname": "subject", "fieldtype": "Data", "width": 250},
    ]

    rows = frappe.db.sql("""
        SELECT
            DATE(nl.creation) AS creation_date,
            nl.document_name,
            i.item_name,
            nl.subject,
            CASE
                WHEN nl.email_content LIKE '%%Head Office%%' THEN 'Internal Transfer - Head Office'
                WHEN nl.email_content LIKE '%%transferred from%%' THEN 'Internal Transfer - Branch'
                WHEN nl.email_content LIKE '%%Wholesale Store%%' THEN 'Purchase Order - Wholesale Store'
                WHEN nl.email_content LIKE '%%Supermarket%%' THEN 'Purchase Order - Supermarket'
                WHEN nl.email_content LIKE '%%Small Shop%%' THEN 'Purchase Order - Small Shop (Emergency)'
                WHEN nl.email_content LIKE '%%No sourcing%%' THEN 'No Source Found - Manual Required'
                ELSE 'Alert Only'
            END AS action
        FROM `tabNotification Log` nl
        LEFT JOIN `tabItem` i ON i.name = nl.document_name
        WHERE nl.document_type = 'Item'
          AND nl.subject LIKE 'Low Stock Alert%%'
          AND DATE(nl.creation) BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY nl.document_name, DATE(nl.creation)
        ORDER BY nl.creation DESC
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    return columns, rows
```

- [ ] **Step 3: Write the JS**

```javascript
frappe.query_reports["Sourcing History"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	]
};
```

- [ ] **Step 4: Run bench migrate**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH" && cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local migrate'
```

---

### Task 15: Create the Coffee Shop Manager Workspace

**Files:**
- Create (DB): Workspace `Coffee Shop Manager` via `Settings → Workspace`
- Modify: `apps/erpnext/erpnext/hooks.py` (add Workspace to fixtures)
- Create: `apps/erpnext/erpnext/fixtures/workspace.json` (auto-generated)

- [ ] **Step 1: Open Workspace builder**

Navigate to `Settings → Workspace → New`.

- [ ] **Step 2: Fill in workspace header**

| Field | Value |
|---|---|
| Name | `Coffee Shop Manager` |
| Label | `Coffee Shop Manager` |
| Module | `Stock` |
| Is Standard | ✓ |
| Roles | `Namibian Coffee Roasters Manager` |

- [ ] **Step 3: Add shortcuts**

In the Shortcuts section add:

| Label | Link To | Type |
|---|---|---|
| Stock Balance | `Stock Balance` | Report |
| Point of Sale | `Point of Sale` | Page |
| Purchase Orders | `Purchase Order` | DocType |
| Stock Transfer | `Stock Entry` | DocType |

- [ ] **Step 4: Add report links**

In the Links section, add a card titled "Reports" with these links:

| Label | Link To | Type |
|---|---|---|
| Stock Levels by Branch | `Stock Levels by Branch` | Report |
| Daily Sales by Branch | `Daily Sales by Branch` | Report |
| Top Selling Drinks | `Top Selling Drinks` | Report |
| Ingredient Cost vs Revenue | `Ingredient Cost vs Revenue` | Report |
| Waste and Loss Tracker | `Waste and Loss Tracker` | Report |
| Sourcing History | `Sourcing History` | Report |

Click **Save**.

- [ ] **Step 5: Add Number Cards**

Navigate to `Settings → Number Card → New`. Create 4 number cards:

**Card 1:**
| Field | Value |
|---|---|
| Name | `Items Below Reorder Today` |
| Label | `Items Below Reorder` |
| Document Type | `Bin` |
| Function | `Count` |
| Filters | `actual_qty < reorder_level` (set via filter builder) |
| Color | Red |

**Card 2:**
| Field | Value |
|---|---|
| Name | `Total Sales Today` |
| Label | `Sales Today` |
| Document Type | `POS Invoice` |
| Function | `Sum` |
| Aggregate Based On | `grand_total` |
| Filters | `posting_date = Today, docstatus = 1` |
| Color | Green |

**Card 3:**
| Field | Value |
|---|---|
| Name | `Open Purchase Orders` |
| Label | `Open POs` |
| Document Type | `Purchase Order` |
| Function | `Count` |
| Filters | `docstatus = 1, status = To Receive and Bill` |
| Color | Orange |

**Card 4:**
| Field | Value |
|---|---|
| Name | `Pending Stock Transfers` |
| Label | `Pending Transfers` |
| Document Type | `Stock Entry` |
| Function | `Count` |
| Filters | `stock_entry_type = Material Transfer, docstatus = 0` |
| Color | Blue |

Add all 4 number cards to the Coffee Shop Manager workspace.

- [ ] **Step 6: Add Workspace to fixtures in hooks.py**

Read `apps/erpnext/erpnext/hooks.py`. Update `fixtures`:

```python
# Namibian Coffee Roasters — fixtures for version control
fixtures = [
    {"dt": "Server Script", "filters": [["name", "like", "%Coffee Shop%"]]},
    {"dt": "Role", "filters": [["role_name", "=", "Namibian Coffee Roasters Manager"]]},
    {"dt": "Workspace", "filters": [["name", "=", "Coffee Shop Manager"]]},
    {"dt": "Number Card", "filters": [["name", "in", [
        "Items Below Reorder Today",
        "Total Sales Today",
        "Open Purchase Orders",
        "Pending Stock Transfers"
    ]]]},
]
```

- [ ] **Step 7: Verify workspace in browser**

Navigate to `/app/coffee-shop-manager`. The workspace should load showing shortcuts, report links, and number cards.

---

### Task 16: Export all fixtures and final commit

**Files:**
- Modify: `apps/erpnext/erpnext/fixtures/server_script.json`
- Create: `apps/erpnext/erpnext/fixtures/workspace.json`
- Report files: all 24 report files created in Tasks 9–14

- [ ] **Step 1: Export all fixtures**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local export-fixtures --app erpnext'
```

- [ ] **Step 2: Verify fixture files exist**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'ls /home/hilton/frappe-bench/apps/erpnext/erpnext/fixtures/'
```

Expected:
```
role.json
server_script.json
workspace.json
```

- [ ] **Step 3: Stage all new files explicitly**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && git add apps/erpnext/erpnext/hooks.py apps/erpnext/erpnext/fixtures/ apps/erpnext/erpnext/stock/report/'
```

- [ ] **Step 4: Commit**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && git commit -m "feat(coffee-shop): Phase 6 — 6 Script Reports + Coffee Shop Manager workspace"'
```

---

## Self-Review Checklist

### Spec coverage

| Spec requirement | Task |
|---|---|
| Phase 2 — BOM per drink | Task 1 |
| Phase 3 — POS Profile per branch | Task 2 |
| Phase 3 — Auto ingredient deduction Server Script | Task 3 |
| Phase 3 — E2E test POS deduction | Task 4 |
| Phase 4 — Multi-branch warehouses + POS profiles | Task 5 |
| Phase 4 — External source warehouses | Task 5 Step 3 |
| Phase 4 — Suppliers for external sources | Task 5 Step 7 |
| Phase 5 — 5-tier sourcing hierarchy script | Task 6 |
| Phase 5 — Sourcing hierarchy tests | Task 7 |
| Phase 6 — Stock Levels by Branch | Task 9 |
| Phase 6 — Daily Sales by Branch | Task 10 |
| Phase 6 — Top Selling Drinks | Task 11 |
| Phase 6 — Ingredient Cost vs Revenue | Task 12 |
| Phase 6 — Waste & Loss Tracker | Task 13 |
| Phase 6 — Sourcing History | Task 14 |
| Phase 6 — Manager Workspace + Number Cards | Task 15 |
| Version control via fixtures | Tasks 3, 7, 16 |
| Payment methods: Cash + Card (Stripe deferred) | Task 2 |

All spec sections covered. ✓

### Type consistency

- `item_code` — consistent across all scripts and reports ✓
- `warehouse` — resolved via `frappe.db.get_value("Warehouse", ...)` consistently ✓
- `reorder_qty` / `reorder_level` — same field names from `Item Reorder` table throughout ✓
- `Namibian Coffee Roasters Manager` — exact same string in Server Script SQL and all role references ✓
- `stock_entry_type: "Manufacture"` — consistent in POS deduction script and all report queries that filter on it ✓
- `Coffee Shop` prefix — used consistently in warehouse name LIKE filters ✓
- Report names in JS match JSON `report_name` field exactly ✓
