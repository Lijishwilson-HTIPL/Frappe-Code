import frappe
from frappe.utils import today, add_days

# ── 6. DELIVERY NOTE (from Sales Order) ─────────────────────────────────────
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

so_name = "SAL-ORD-2026-00001"
dn = make_delivery_note(so_name)
dn.insert(ignore_permissions=True)
dn.submit()
frappe.db.commit()
print(f"Delivery Note submitted: {dn.name}")

# ── 7. SALES INVOICE (from Delivery Note) ────────────────────────────────────
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

si = make_sales_invoice(dn.name)
si.due_date = add_days(today(), 30)
si.insert(ignore_permissions=True)
si.submit()
frappe.db.commit()
print(f"Sales Invoice submitted: {si.name} | Total: {si.grand_total}")

# ── 8. PAYMENT ENTRY ─────────────────────────────────────────────────────────
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

pe = get_payment_entry("Sales Invoice", si.name)
pe.reference_no = f"CASH-{si.name}"
pe.reference_date = today()
pe.insert(ignore_permissions=True)
pe.submit()
frappe.db.commit()
print(f"Payment Entry submitted: {pe.name}")

print("\n========================================")
print("FULL SALE CYCLE COMPLETE!")
print("========================================")
print(f"  Sales Order   : {so_name}")
print(f"  Delivery Note : {dn.name}")
print(f"  Sales Invoice : {si.name}  |  ₹{si.grand_total}")
print(f"  Payment Entry : {pe.name}")
print("========================================")
