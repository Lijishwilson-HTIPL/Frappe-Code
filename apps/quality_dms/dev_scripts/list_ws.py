import frappe

def list_ws():
    workspaces = frappe.get_all("Workspace", fields=["name"])
    print("Workspaces:")
    for w in workspaces:
        print(w.name)
