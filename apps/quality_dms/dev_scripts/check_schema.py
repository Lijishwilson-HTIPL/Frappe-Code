import frappe

def check_schema():
    meta = frappe.get_meta("Workspace")
    for field in meta.fields:
        if field.reqd:
            print(field.fieldname, field.label)

check_schema()
