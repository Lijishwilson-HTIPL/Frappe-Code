# Coffee Shop Inventory — Design Spec

**Date:** 2026-06-16
**Author:** Hilton Paul
**Status:** Approved

---

## 1. Overview

Build a coffee shop inventory system for a manufacturing company client using ERPNext's built-in Stock module. The system tracks three categories of items, sets minimum quantity thresholds per item, and fires real-time in-app + email notifications to all users with the `Namibian Coffee Roasters Manager` role the moment stock drops below the threshold.

No new DocTypes are required. All data lives in standard ERPNext stock entities. A single Server Script provides the real-time alert logic.

---

## 2. Architecture

```
ERPNext Stock Module
│
├── Item Groups (3): Raw Ingredient | Finished Product | Equipment & Consumables
├── Warehouse: "Coffee Shop - Main"
├── Items (with reorder level per item)
│
├── Stock Ledger Entry (written on every stock change)
│         │
│         └── Server Script (Doc Event: after_insert)
│                   │
│                   ├── reads current bin qty for that item + warehouse
│                   ├── compares against item's reorder_level
│                   └── if qty < reorder_level → fires Frappe Notification
│                             ├── In-app bell (all users with "Namibian Coffee Roasters Manager" role)
│                             └── Email (all users with "Namibian Coffee Roasters Manager" role)
```

---

## 3. Data Model

### 3.1 Item Groups

Three groups to create under "All Item Groups":

| Group Name | Example Items |
|---|---|
| Raw Ingredient | Coffee Beans, Milk, Sugar, Syrups, Cups, Lids |
| Finished Product | Espresso, Latte, Cappuccino, Cold Brew |
| Equipment & Consumables | Filters, Cleaning Supplies, Paper Towels |

### 3.2 Warehouse

| Field | Value |
|---|---|
| Warehouse Name | Coffee Shop - Main |
| Warehouse Type | Stores |

### 3.3 Item Fields (per item)

| Field | ERPNext Field | Example |
|---|---|---|
| Item Name | `item_name` | Coffee Beans - Arabica |
| Unit of Measure | `stock_uom` | Kg |
| Item Group | `item_group` | Raw Ingredient |
| Reorder Level | `reorder_levels[].warehouse_reorder_level` | 5 |
| Reorder Qty | `reorder_levels[].warehouse_reorder_qty` | 20 |

Reorder levels are stored on the **Item Reorder** child table (built into ERPNext), linked per warehouse.

### 3.4 Role

| Role Name | Purpose |
|---|---|
| `Namibian Coffee Roasters Manager` | All users with this role receive low-stock alerts |

Recipients are resolved dynamically at alert time — no hardcoded emails. Adding a new manager is done by assigning the role in user settings.

---

## 4. Server Script

**DocType:** `Stock Ledger Entry`
**Event:** `after_insert`

### Logic

```python
# 1. Get item and warehouse from the triggering SLE
item_code = doc.item_code
warehouse = doc.warehouse

# 2. Get current actual quantity from Bin
actual_qty = frappe.db.get_value("Bin",
    {"item_code": item_code, "warehouse": warehouse},
    "actual_qty") or 0

# 3. Get the item's reorder level for this warehouse
reorder_level = frappe.db.get_value("Item Reorder",
    {"parent": item_code, "warehouse": warehouse},
    "warehouse_reorder_level") or 0

# 4. Skip if stock is still above threshold
if actual_qty >= reorder_level or reorder_level == 0:
    return

# 5. Dedup guard: skip if a notification was already sent within the last 24 hours
recent = frappe.db.exists("Notification Log", {
    "document_type": "Item",
    "document_name": item_code,
    "creation": [">", frappe.utils.add_days(frappe.utils.now(), -1)]
})
if recent:
    return

# 6. Find all users with "Namibian Coffee Roasters Manager" role
recipients = frappe.db.sql("""
    SELECT u.email, u.name
    FROM `tabUser` u
    JOIN `tabHas Role` hr ON hr.parent = u.name
    WHERE hr.role = 'Namibian Coffee Roasters Manager'
      AND u.enabled = 1
      AND u.email IS NOT NULL
""", as_dict=True)

item_name = frappe.db.get_value("Item", item_code, "item_name")
uom = frappe.db.get_value("Item", item_code, "stock_uom")

subject = f"Low Stock Alert — {item_name}"
message = (
    f"{item_name} at Coffee Shop - Main has dropped to "
    f"{actual_qty} {uom}. Reorder level is {reorder_level} {uom}. "
    f"Please restock."
)

for user in recipients:
    # 7a. In-app notification
    frappe.get_doc({
        "doctype": "Notification Log",
        "subject": subject,
        "email_content": message,
        "for_user": user["name"],
        "document_type": "Item",
        "document_name": item_code,
        "type": "Alert"
    }).insert(ignore_permissions=True)

    # 7b. Email (queued — no now=True per project rules)
    frappe.sendmail(
        recipients=[user["email"]],
        subject=subject,
        message=message
    )
```

---

## 5. Notification Details

### In-app (bell icon)
- Appears in the Frappe desk notification bell immediately
- Message: `"Low Stock: {Item Name} — only {qty} {UOM} remaining"`
- Links to the Item record

### Email
- Queued through the background worker (`now=False`)
- Subject: `Low Stock Alert — {Item Name}`
- Body: plain-text message with item name, current qty, UOM, and reorder level

### Dedup rule
- One notification per item per 24-hour window
- Prevents spam when multiple small stock deductions happen in rapid succession

---

## 6. Sample Inventory Data

Seed items to demonstrate the system:

| Item Name | Group | UOM | Reorder Level | Reorder Qty |
|---|---|---|---|---|
| Coffee Beans - Arabica | Raw Ingredient | Kg | 5 | 20 |
| Full Cream Milk | Raw Ingredient | Litre | 10 | 30 |
| White Sugar | Raw Ingredient | Kg | 3 | 10 |
| Vanilla Syrup | Raw Ingredient | Bottle | 2 | 6 |
| Paper Cups (8oz) | Raw Ingredient | Pcs | 100 | 500 |
| Espresso | Finished Product | Cup | 20 | 50 |
| Latte | Finished Product | Cup | 20 | 50 |
| Coffee Filters | Equipment & Consumables | Pcs | 50 | 200 |
| Cleaning Tablets | Equipment & Consumables | Pcs | 5 | 20 |

---

## 7. Testing Plan

| Step | Action | Expected Result |
|---|---|---|
| 1 | Create Item Groups (3) | Groups visible under Stock → Item Groups |
| 2 | Create Warehouse "Coffee Shop - Main" | Warehouse listed under Stock → Warehouses |
| 3 | Create sample items with reorder levels | Items visible under Stock → Items |
| 4 | Create role `Namibian Coffee Roasters Manager`, assign to owner user | User has role in User settings |
| 5 | Add opening stock above reorder level via Stock Reconciliation | No notification fired |
| 6 | Reduce stock below reorder level via Stock Reconciliation | In-app bell + email triggered |
| 7 | Reduce stock again within 24 hours | No duplicate notification sent |
| 8 | Add a second `Namibian Coffee Roasters Manager` user | Both users receive the next alert |

---

## 8. Implementation Steps (high-level)

1. Create Item Groups in ERPNext UI
2. Create Warehouse in ERPNext UI
3. Create `Namibian Coffee Roasters Manager` role in ERPNext UI
4. Create sample Items with reorder levels
5. Create Server Script (Stock Ledger Entry → after_insert) with the alert logic above
6. Test with Stock Reconciliation
7. Assign `Namibian Coffee Roasters Manager` role to the client's owner/manager account

No `bench migrate` required — Server Scripts are stored in the database and take effect immediately on save.
