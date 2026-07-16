import frappe

def check_perms():
    frappe.set_user("Administrator")
    print("DMS Creator Custom DocPerms:")
    print(frappe.get_all("Custom DocPerm", filters={"parent": "Quality Document", "role": "DMS Creator"}, fields=["read", "write", "create"]))
    print("\nDMS Creator standard Role perms:")
    roles = frappe.get_all("DocPerm", filters={"parent": "Quality Document", "role": "DMS Creator"}, fields=["read", "write", "create"])
    print(roles)
    
check_perms()
