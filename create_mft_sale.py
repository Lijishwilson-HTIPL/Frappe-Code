import frappe
from frappe.utils import today, add_days

frappe.connect()

site = "mysite.local"
company = frappe.get_all("Company", limit=1)
if not company:
    print("ERROR: No company found. Please set up a company first.")
    frappe.destroy()
    exit()

company_name = company[0].name
print(f"Using company: {company_name}")

# Get default currency
company_doc = frappe.get_doc("Company", company_name)
currency = company_doc.default_currency or "INR"
abbr = company_doc.abbr

default_warehouse = f"Stores - {abbr}"
# Check warehouse exists
if not frappe.db.exists("Warehouse", default_warehouse):
    warehouses = frappe.get_all("Warehouse", filters={"company": company_name}, limit=1)
    if warehouses:
        default_warehouse = warehouses[0].name
    else:
        print("ERROR: No warehouse found.")
        frappe.destroy()
        exit()

print(f"Using warehouse: {default_warehouse}")

# ── 1. ITEM ──────────────────────────────────────────────────────────────────
item_code = "MFT-001"
if not frappe.db.exists("Item", item_code):
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": item_code,
        "item_name": "Manufactured Product MFT-001",
        "item_group": "Products",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "include_item_in_manufacturing": 1,
        "item_defaults": [{
            "company": company_name,
            "default_warehouse": default_warehouse,
        }]
    })
    item.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"✅ Item created: {item_code}")
else:
    print(f"ℹ️  Item already exists: {item_code}")

# ── 2. ITEM PRICE ────────────────────────────────────────────────────────────
price_list = "Standard Selling"
if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list}):
    item_price = frappe.get_doc({
        "doctype": "Item Price",
        "item_code": item_code,
        "price_list": price_list,
        "price_list_rate": 5000.00,
        "currency": currency,
    })
    item_price.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"✅ Item Price created: ₹5000 in {price_list}")
else:
    print(f"ℹ️  Item Price already exists for {item_code}")

# ── 3. CUSTOMER ──────────────────────────────────────────────────────────────
customer_name = "MFT Test Customer"
if not frappe.db.exists("Customer", customer_name):
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": "Company",
        "customer_group": "Commercial",
        "territory": "India",
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"✅ Customer created: {customer_name}")
else:
    print(f"ℹ️  Customer already exists: {customer_name}")

# ── 4. OPENING STOCK (Stock Entry - Material Receipt) ────────────────────────
se = frappe.get_doc({
    "doctype": "Stock Entry",
    "stock_entry_type": "Material Receipt",
    "to_warehouse": default_warehouse,
    "items": [{
        "item_code": item_code,
        "qty": 10,
        "basic_rate": 3000.00,
        "t_warehouse": default_warehouse,
    }]
})
se.insert(ignore_permissions=True)
se.submit()
frappe.db.commit()
print(f"✅ Stock Entry submitted: {se.name} (10 Nos @ ₹3000 valuation)")

# ── 5. SALES ORDER ───────────────────────────────────────────────────────────
so = frappe.get_doc({
    "doctype": "Sales Order",
    "customer": customer_name,
    "company": company_name,
    "transaction_date": today(),
    "delivery_date": add_days(today(), 3),
    "order_type": "Sales",
    "currency": currency,
    "selling_price_list": price_list,
    "items": [{
        "item_code": item_code,
        "qty": 2,
        "rate": 5000.00,
        "delivery_date": add_days(today(), 3),
        "warehouse": default_warehouse,
    }]
})
so.insert(ignore_permissions=True)
so.submit()
frappe.db.commit()
print(f"✅ Sales Order submitted: {so.name} (2 Nos @ ₹5000)")

# ── 6. DELIVERY NOTE ─────────────────────────────────────────────────────────
from erpnext.stock.doctype.delivery_note.delivery_note import make_delivery_note
dn = make_delivery_note(so.name)
dn.insert(ignore_permissions=True)
dn.submit()
frappe.db.commit()
print(f"✅ Delivery Note submitted: {dn.name}")

# ── 7. SALES INVOICE ─────────────────────────────────────────────────────────
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_invoice
si = make_sales_invoice(dn.name)
si.due_date = add_days(today(), 30)
si.insert(ignore_permissions=True)
si.submit()
frappe.db.commit()
print(f"✅ Sales Invoice submitted: {si.name} (Total: ₹{si.grand_total})")

# ── 8. PAYMENT ENTRY ─────────────────────────────────────────────────────────
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
pe = get_payment_entry("Sales Invoice", si.name)
pe.reference_no = f"CASH-{si.name}"
pe.reference_date = today()
pe.insert(ignore_permissions=True)
pe.submit()
frappe.db.commit()
print(f"✅ Payment Entry submitted: {pe.name}")

print("\n" + "="*60)
print("COMPLETE SALE CYCLE DONE!")
print("="*60)
print(f"  Item          : {item_code}")
print(f"  Customer      : {customer_name}")
print(f"  Sales Order   : {so.name}")
print(f"  Delivery Note : {dn.name}")
print(f"  Sales Invoice : {si.name} — ₹{si.grand_total}")
print(f"  Payment Entry : {pe.name}")
print("="*60)

frappe.destroy()
