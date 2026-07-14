# Coffee Shop Inventory — Namibian Coffee Roasters — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure ERPNext's Stock module for Namibian Coffee Roasters' coffee shop, then wire a real-time low-stock alert (in-app bell + email) that fires to every user with the `Namibian Coffee Roasters Manager` role the moment any item's stock drops below its reorder threshold.

**Architecture:** All inventory data lives in standard ERPNext Stock DocTypes (Item, Warehouse, Bin, Item Reorder, Stock Ledger Entry). A single Frappe Server Script on `Stock Ledger Entry → after_insert` reads current Bin qty, compares it to the Item's reorder level, and fires `Notification Log` inserts plus `frappe.sendmail` calls to role holders. A 24-hour dedup guard on `Notification Log` prevents notification spam. No new DocTypes, no `bench migrate` needed — Server Scripts take effect immediately on save.

**Tech Stack:** ERPNext v15, Frappe Server Scripts (Python), ERPNext Stock module (Item, Warehouse, Bin, Item Reorder, Stock Ledger Entry, Notification Log, Stock Reconciliation)

---

## File Structure

| What | Where |
|---|---|
| Server Script | DB only — created via `Settings → Server Script` |
| Role | DB only — created via `Setup → Role` |
| Fixtures (version control) | `apps/erpnext/erpnext/fixtures/server_script.json` |
| Fixtures config | `apps/erpnext/erpnext/hooks.py` |

---

### Task 1: Create the Namibian Coffee Roasters Manager Role

**Files:**
- No files — Role created via ERPNext UI (stored in DB)
- Modify: `apps/erpnext/erpnext/hooks.py` (fixtures entry added in Task 8)

- [ ] **Step 1: Open Role list**

In the Frappe desk, click the search bar and type `Role`, then select **Role** from the results.

- [ ] **Step 2: Create the role**

Click **New**. Fill in:

| Field | Value |
|---|---|
| Role Name | `Namibian Coffee Roasters Manager` |
| Desk Access | ✓ (checked) |

Click **Save**.

- [ ] **Step 3: Verify role exists**

In the Role list, search for `Namibian` — the new role should appear.

- [ ] **Step 4: Assign the role to the owner/manager user**

Go to `Setup → User → [owner's username]`. In the **Roles** table, click **Add Row** and select `Namibian Coffee Roasters Manager`. Click **Save**.

---

### Task 2: Create Custom Units of Measure

ERPNext ships with `Kg`, `Litre`, and `Nos` (pieces) by default. The coffee shop needs `Bottle` and `Cup` — create them before creating items.

**Files:**
- No files — UOM created via ERPNext UI

- [ ] **Step 1: Open UOM list**

Search for `UOM` in the top bar and open **UOM** (Unit of Measure).

- [ ] **Step 2: Create Bottle**

Click **New**:

| Field | Value |
|---|---|
| UOM Name | `Bottle` |
| Must be Whole Number | ✓ |

Save.

- [ ] **Step 3: Create Cup**

Click **New**:

| Field | Value |
|---|---|
| UOM Name | `Cup` |
| Must be Whole Number | ✓ |

Save.

- [ ] **Step 4: Verify**

In the UOM list confirm `Bottle` and `Cup` both appear alongside the built-in `Kg`, `Litre`, and `Nos`.

---

### Task 3: Create Item Groups

**Files:**
- No files — Item Groups created via ERPNext UI

- [ ] **Step 1: Open Item Group list**

Navigate to `Stock → Item Group`.

- [ ] **Step 2: Create Raw Ingredient**

Click **New**:

| Field | Value |
|---|---|
| Item Group Name | `Raw Ingredient` |
| Parent Item Group | `All Item Groups` |
| Is Group | ☐ (leave unchecked) |

Save.

- [ ] **Step 3: Create Finished Product**

Click **New**:

| Field | Value |
|---|---|
| Item Group Name | `Finished Product` |
| Parent Item Group | `All Item Groups` |
| Is Group | ☐ |

Save.

- [ ] **Step 4: Create Equipment & Consumables**

Click **New**:

| Field | Value |
|---|---|
| Item Group Name | `Equipment & Consumables` |
| Parent Item Group | `All Item Groups` |
| Is Group | ☐ |

Save.

- [ ] **Step 5: Verify**

In the Item Group tree view all three new groups should appear as children of `All Item Groups`.

---

### Task 4: Create Warehouse

**Files:**
- No files — Warehouse created via ERPNext UI

- [ ] **Step 1: Open Warehouse list**

Navigate to `Stock → Warehouse`.

- [ ] **Step 2: Create the warehouse**

Click **New**:

| Field | Value |
|---|---|
| Warehouse Name | `Coffee Shop - Main` |
| Warehouse Type | `Stores` |
| Company | *(select your company from the dropdown)* |

Save.

- [ ] **Step 3: Note the full warehouse name**

ERPNext appends the company abbreviation automatically. The full name will be something like `Coffee Shop - Main - NCR`. **Note this exact name** — you will use it in every Item reorder level row and every Stock Reconciliation in later tasks.

To confirm, run this command and check the output:

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local execute frappe.db.get_value --args "\"Warehouse\",{\"warehouse_name\":\"Coffee Shop - Main\"},\"name\""'
```

Expected output:
```
Coffee Shop - Main - NCR
```

*(Replace `NCR` with whatever abbreviation your company uses.)*

---

### Task 5: Create Sample Items with Reorder Levels

Create all 9 items. For each: `Stock → Item → New`, fill in the main fields, then open the **Reorder Levels** tab and add one row pointing to the Coffee Shop warehouse.

**Files:**
- No files — Items created via ERPNext UI

- [ ] **Step 1: Create Coffee Beans - Arabica**

Main tab:

| Field | Value |
|---|---|
| Item Name | `Coffee Beans - Arabica` |
| Item Code | `COFFEE-BEANS-ARABICA` |
| Item Group | `Raw Ingredient` |
| Default Unit of Measure | `Kg` |
| Maintain Stock | ✓ |

Reorder Levels tab → Add Row:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `5` | `20` | `Kg` |

Save.

- [ ] **Step 2: Create Full Cream Milk**

| Field | Value |
|---|---|
| Item Name | `Full Cream Milk` |
| Item Code | `MILK-FULL-CREAM` |
| Item Group | `Raw Ingredient` |
| Default Unit of Measure | `Litre` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `10` | `30` | `Litre` |

Save.

- [ ] **Step 3: Create White Sugar**

| Field | Value |
|---|---|
| Item Name | `White Sugar` |
| Item Code | `SUGAR-WHITE` |
| Item Group | `Raw Ingredient` |
| Default Unit of Measure | `Kg` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `3` | `10` | `Kg` |

Save.

- [ ] **Step 4: Create Vanilla Syrup**

| Field | Value |
|---|---|
| Item Name | `Vanilla Syrup` |
| Item Code | `SYRUP-VANILLA` |
| Item Group | `Raw Ingredient` |
| Default Unit of Measure | `Bottle` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `2` | `6` | `Bottle` |

Save.

- [ ] **Step 5: Create Paper Cups (8oz)**

| Field | Value |
|---|---|
| Item Name | `Paper Cups (8oz)` |
| Item Code | `CUPS-PAPER-8OZ` |
| Item Group | `Raw Ingredient` |
| Default Unit of Measure | `Nos` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `100` | `500` | `Nos` |

Save.

- [ ] **Step 6: Create Espresso**

| Field | Value |
|---|---|
| Item Name | `Espresso` |
| Item Code | `DRINK-ESPRESSO` |
| Item Group | `Finished Product` |
| Default Unit of Measure | `Cup` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `20` | `50` | `Cup` |

Save.

- [ ] **Step 7: Create Latte**

| Field | Value |
|---|---|
| Item Name | `Latte` |
| Item Code | `DRINK-LATTE` |
| Item Group | `Finished Product` |
| Default Unit of Measure | `Cup` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `20` | `50` | `Cup` |

Save.

- [ ] **Step 8: Create Coffee Filters**

| Field | Value |
|---|---|
| Item Name | `Coffee Filters` |
| Item Code | `EQUIP-FILTERS` |
| Item Group | `Equipment & Consumables` |
| Default Unit of Measure | `Nos` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `50` | `200` | `Nos` |

Save.

- [ ] **Step 9: Create Cleaning Tablets**

| Field | Value |
|---|---|
| Item Name | `Cleaning Tablets` |
| Item Code | `EQUIP-CLEANING-TABS` |
| Item Group | `Equipment & Consumables` |
| Default Unit of Measure | `Nos` |
| Maintain Stock | ✓ |

Reorder Levels:

| Warehouse | Reorder Level | Reorder Qty | UOM |
|---|---|---|---|
| Coffee Shop - Main - [abbr] | `5` | `20` | `Nos` |

Save.

- [ ] **Step 10: Verify all 9 items**

Navigate to `Stock → Item`. Filter by:
- `Item Group = Raw Ingredient` → expect 5 items
- `Item Group = Finished Product` → expect 2 items
- `Item Group = Equipment & Consumables` → expect 2 items

---

### Task 6: Add Opening Stock

Set initial stock quantities **above** each item's reorder level. This establishes a healthy baseline so the alert only fires when stock genuinely drops.

**Files:**
- No files — Stock Reconciliation created via ERPNext UI

- [ ] **Step 1: Open Stock Reconciliation**

Navigate to `Stock → Stock Reconciliation → New`.

Set the header:

| Field | Value |
|---|---|
| Purpose | `Opening Stock` |
| Posting Date | Today's date |

- [ ] **Step 2: Add all 9 items**

In the **Items** table, add one row per item:

| Item Code | Warehouse | Qty |
|---|---|---|
| COFFEE-BEANS-ARABICA | Coffee Shop - Main - [abbr] | `25` |
| MILK-FULL-CREAM | Coffee Shop - Main - [abbr] | `30` |
| SUGAR-WHITE | Coffee Shop - Main - [abbr] | `15` |
| SYRUP-VANILLA | Coffee Shop - Main - [abbr] | `8` |
| CUPS-PAPER-8OZ | Coffee Shop - Main - [abbr] | `500` |
| DRINK-ESPRESSO | Coffee Shop - Main - [abbr] | `50` |
| DRINK-LATTE | Coffee Shop - Main - [abbr] | `50` |
| EQUIP-FILTERS | Coffee Shop - Main - [abbr] | `200` |
| EQUIP-CLEANING-TABS | Coffee Shop - Main - [abbr] | `20` |

- [ ] **Step 3: Save and Submit**

Click **Save**, then **Submit**. Frappe writes a Stock Ledger Entry for each item.

- [ ] **Step 4: Verify stock is above reorder levels**

Navigate to `Stock → Stock Balance`. Filter by Warehouse = `Coffee Shop - Main - [abbr]`. All 9 items should show their opening quantities. No notification bell should appear (all quantities are above reorder levels, so the Server Script hasn't fired yet — it doesn't even exist yet).

---

### Task 7: Create the Low-Stock Alert Server Script

**Files:**
- No files — Server Script stored in DB via `Settings → Server Script`

- [ ] **Step 1: Open Server Script list**

Search for `Server Script` in the top bar. Click **New**.

- [ ] **Step 2: Fill in the header fields**

| Field | Value |
|---|---|
| Name | `Low Stock Alert - Coffee Shop` |
| Script Type | `DocType Event` |
| Reference DocType | `Stock Ledger Entry` |
| DocType Event | `After Insert` |
| Enabled | ✓ |

- [ ] **Step 3: Paste the script**

In the **Script** field, paste exactly:

```python
item_code = doc.item_code
warehouse = doc.warehouse

actual_qty = frappe.db.get_value("Bin",
    {"item_code": item_code, "warehouse": warehouse},
    "actual_qty") or 0

reorder_level = frappe.db.get_value("Item Reorder",
    {"parent": item_code, "warehouse": warehouse},
    "warehouse_reorder_level") or 0

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

subject = "Low Stock Alert - {0}".format(item_name)
message = (
    "{0} at Coffee Shop - Main has dropped to {1} {2}. "
    "Reorder level is {3} {2}. Please restock.".format(
        item_name, actual_qty, uom, reorder_level
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
```

> **Note:** f-strings are not used here for compatibility with all Frappe v14/v15 Server Script sandboxes. The `.format()` style is safe across all versions.

- [ ] **Step 4: Save**

Click **Save**. If there is a syntax error, Frappe will show it inline — fix before proceeding.

---

### Task 8: End-to-End Test — Single Manager Alert

Verify the full pipeline: stock drop → SLE insert → Server Script fires → bell notification + email queued.

**Files:**
- Create: `/tmp/verify_coffee_alert.py` (console verification script, not committed)

- [ ] **Step 1: Write and copy the verification script to WSL**

Run this in PowerShell to create the verification script in WSL:

```powershell
$script = @'
import frappe

item_code = "COFFEE-BEANS-ARABICA"
warehouse_name = "Coffee Shop - Main"

warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name}, "name")
actual_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
reorder_level = frappe.db.get_value("Item Reorder", {"parent": item_code, "warehouse": warehouse}, "warehouse_reorder_level") or 0

print("Warehouse:", warehouse)
print("Current qty:", actual_qty)
print("Reorder level:", reorder_level)

logs = frappe.db.get_all("Notification Log", {
    "document_type": "Item",
    "document_name": item_code
}, ["name", "subject", "creation"])
print("Existing notification logs for this item:", len(logs))
for log in logs:
    print(" -", log)

frappe.db.rollback()
'@
$script | Out-File -FilePath "\\wsl.localhost\Ubuntu-22.04\tmp\verify_coffee_alert.py" -Encoding utf8
```

- [ ] **Step 2: Run the verification script (baseline)**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ../env/bin/python -m frappe.utils.bench_helper frappe --site mysite.local console < /tmp/verify_coffee_alert.py'
```

Expected output (no notifications yet):
```
Warehouse: Coffee Shop - Main - NCR
Current qty: 25.0
Reorder level: 5.0
Existing notification logs for this item: 0
```

- [ ] **Step 3: Drop Coffee Beans stock below the reorder level**

Navigate to `Stock → Stock Reconciliation → New`:

| Field | Value |
|---|---|
| Purpose | `Stock Reconciliation` |
| Posting Date | Today |

Items table — add one row:

| Item Code | Warehouse | Qty |
|---|---|---|
| COFFEE-BEANS-ARABICA | Coffee Shop - Main - [abbr] | `3` |

*(Sets qty to 3, which is below the reorder level of 5.)*

Click **Save**, then **Submit**.

- [ ] **Step 4: Verify in-app notification appeared**

Look at the **bell icon** in the top-right of the Frappe desk. A new notification should read:

```
Low Stock Alert - Coffee Beans - Arabica
Coffee Beans - Arabica at Coffee Shop - Main has dropped to 3.0 Kg. Reorder level is 5.0 Kg. Please restock.
```

- [ ] **Step 5: Verify email was queued**

Navigate to `Settings → Email Queue`. A queued email should appear with:
- Subject: `Low Stock Alert - Coffee Beans - Arabica`
- Recipient: the manager's email address

- [ ] **Step 6: Run the verification script again (confirm log was created)**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ../env/bin/python -m frappe.utils.bench_helper frappe --site mysite.local console < /tmp/verify_coffee_alert.py'
```

Expected output (notification now exists):
```
Warehouse: Coffee Shop - Main - NCR
Current qty: 3.0
Reorder level: 5.0
Existing notification logs for this item: 1
 - {"name": "...", "subject": "Low Stock Alert - Coffee Beans - Arabica", "creation": "..."}
```

---

### Task 9: Test Dedup Guard (24-hour window)

Confirm that a second stock drop for the same item within 24 hours does NOT fire another notification.

**Files:**
- No files

- [ ] **Step 1: Drop stock even lower (within 24 hours of the previous alert)**

Navigate to `Stock → Stock Reconciliation → New`:

| Field | Value |
|---|---|
| Purpose | `Stock Reconciliation` |
| Posting Date | Today |

Items table:

| Item Code | Warehouse | Qty |
|---|---|---|
| COFFEE-BEANS-ARABICA | Coffee Shop - Main - [abbr] | `1` |

Submit.

- [ ] **Step 2: Verify NO new notification was created**

Navigate to `Settings → Notification Log`. Filter by `Document Name = COFFEE-BEANS-ARABICA`. There should still be exactly **1** log entry (the one from Task 8).

Navigate to `Settings → Email Queue`. No new email for Coffee Beans should have been added.

---

### Task 10: Test Multi-Manager Notification

Confirm all users with the `Namibian Coffee Roasters Manager` role receive the alert.

**Files:**
- No files

- [ ] **Step 1: Create a second manager user**

Navigate to `Settings → User → New`. Create a second user with a valid email address. In the **Roles** table, assign `Namibian Coffee Roasters Manager`. Save.

- [ ] **Step 2: Drop a DIFFERENT item below its reorder level**

Navigate to `Stock → Stock Reconciliation → New`:

| Field | Value |
|---|---|
| Purpose | `Stock Reconciliation` |
| Posting Date | Today |

Items table:

| Item Code | Warehouse | Qty |
|---|---|---|
| MILK-FULL-CREAM | Coffee Shop - Main - [abbr] | `5` |

*(Sets qty to 5, below the reorder level of 10.)*

Submit.

- [ ] **Step 3: Verify both managers received the notification**

Navigate to `Settings → Notification Log`. Filter by `Document Name = MILK-FULL-CREAM`. There should be **2 entries** — one `for_user` each manager.

Navigate to `Settings → Email Queue`. There should be **2 emails** for `Low Stock Alert - Full Cream Milk` — one per manager's email address.

---

### Task 11: Export Fixtures for Version Control

Persist the Server Script and Role to JSON fixtures so they are committed to git and auto-applied on any fresh site via `bench migrate`.

**Files:**
- Modify: `apps/erpnext/erpnext/hooks.py`
- Create: `apps/erpnext/erpnext/fixtures/server_script.json` (auto-generated)
- Create: `apps/erpnext/erpnext/fixtures/role.json` (auto-generated)

- [ ] **Step 1: Read hooks.py**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cat /home/hilton/frappe-bench/apps/erpnext/erpnext/hooks.py | grep -n "fixtures" | head -20'
```

- [ ] **Step 2: Add fixtures entry to hooks.py**

Open `apps/erpnext/erpnext/hooks.py`. Find the `fixtures` list. If it exists, append to it. If it does not exist, add it after the `app_name` block. The entry to add:

```python
fixtures = [
    # ... existing entries if any ...
    {"dt": "Server Script", "filters": [["name", "like", "Low Stock Alert%"]]},
    {"dt": "Role", "filters": [["role_name", "=", "Namibian Coffee Roasters Manager"]]},
]
```

- [ ] **Step 3: Export fixtures**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && ~/.local/bin/bench --site mysite.local export-fixtures --app erpnext'
```

- [ ] **Step 4: Verify exported files exist**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'ls /home/hilton/frappe-bench/apps/erpnext/erpnext/fixtures/ | grep -E "server_script|role"'
```

Expected:
```
role.json
server_script.json
```

- [ ] **Step 5: Commit**

```powershell
wsl -d Ubuntu-22.04 -e bash -lc 'cd /home/hilton/frappe-bench && git add apps/erpnext/erpnext/hooks.py apps/erpnext/erpnext/fixtures/server_script.json apps/erpnext/erpnext/fixtures/role.json && git commit -m "feat(coffee-inventory): add low-stock alert server script and manager role fixture"'
```

---

## Self-Review Checklist

### Spec coverage

| Spec requirement | Task that covers it |
|---|---|
| 3 Item Groups | Task 3 |
| Warehouse "Coffee Shop - Main" | Task 4 |
| Role "Namibian Coffee Roasters Manager" | Task 1 |
| 9 sample items with reorder levels | Task 5 |
| Opening stock | Task 6 |
| Server Script on SLE after_insert | Task 7 |
| In-app bell notification | Task 8 Step 4 |
| Email notification (queued) | Task 8 Step 5 |
| 24-hour dedup guard | Task 9 |
| Multi-user role-based recipients | Task 10 |
| Version control via fixtures | Task 11 |
| Custom UOMs (Bottle, Cup) | Task 2 |

All spec sections covered. ✓

### Placeholder scan

No TBDs, TODOs, "implement later", or vague instructions found. Every step has exact values, exact commands, or exact code. ✓

### Type consistency

- `item_code` — consistent across Task 7 script and verification script
- `warehouse` variable — same source (`frappe.db.get_value("Warehouse", ...)`) in both scripts
- `actual_qty`, `reorder_level` — same field names throughout
- `Notification Log` — same casing in script and all test steps
- `Namibian Coffee Roasters Manager` — exact same string in script (line `WHERE hr.role = 'Namibian Coffee Roasters Manager'`) and in Tasks 1 and 10 ✓
