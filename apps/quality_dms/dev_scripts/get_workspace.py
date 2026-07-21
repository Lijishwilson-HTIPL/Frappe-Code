import frappe

def get_workspace():
    w = frappe.get_doc("Workspace", "DMS")
    print(frappe.as_json(w.as_dict()))

get_workspace()
