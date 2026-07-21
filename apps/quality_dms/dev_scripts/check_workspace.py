import frappe

def check():
    w = frappe.get_all("Workspace", filters={"module": "Quality DMS"}, fields=["name"])
    print("Workspaces:", w)

check()
