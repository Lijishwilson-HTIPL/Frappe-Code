import frappe

def make_visible():
    if frappe.db.exists("Workspace", "Quality DMS"):
        ws = frappe.get_doc("Workspace", "Quality DMS")
        ws.is_hidden = 0
        ws.public = 1
        ws.for_user = ""
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        print("Workspace 'Quality DMS' has been made explicitly visible.")
    else:
        print("Workspace 'Quality DMS' does not exist!")
