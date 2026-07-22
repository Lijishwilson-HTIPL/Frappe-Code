import frappe

def check_ws():
    fields = frappe.get_meta("Workspace").fields
    for f in fields:
        print(f"{f.fieldname} ({f.fieldtype})")

check_ws()
