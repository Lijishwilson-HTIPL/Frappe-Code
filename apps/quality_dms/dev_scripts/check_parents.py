import frappe

def check_parents():
    workspaces = frappe.get_all("Workspace", fields=["name", "parent_page"])
    for w in workspaces:
        print(f"{w.name} -> {w.parent_page}")

check_parents()
