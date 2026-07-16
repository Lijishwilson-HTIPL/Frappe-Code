import frappe

def apply_docperms():
    frappe.set_user("Administrator")
    dt = "Quality Document"
    
    # 1. Clear existing Custom DocPerms for these roles to start fresh
    roles = ["DMS Creator", "DMS Reviewer", "DMS Approver", "DMS Manager", "DMS Admin"]
    for role in roles:
        existing = frappe.get_all("Custom DocPerm", filters={"parent": dt, "role": role})
        for e in existing:
            frappe.delete_doc("Custom DocPerm", e.name, ignore_permissions=True, force=True)
            
    # 2. Add correct baseline permissions
    # Note: We rely on python permission hooks to restrict visibility (read access) 
    # based on ownership/workflow state, so we do NOT use if_owner=1 here.
    
    perms = [
        {"role": "DMS Creator", "read": 1, "write": 1, "create": 1, "report": 1},
        {"role": "DMS Reviewer", "read": 1, "write": 1, "report": 1},
        {"role": "DMS Approver", "read": 1, "write": 1, "submit": 1, "report": 1},
        {"role": "DMS Manager", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1, "delete": 1, "report": 1},
        {"role": "DMS Admin", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1, "delete": 1, "report": 1, "set_user_permissions": 1}
    ]
    
    for p in perms:
        doc = frappe.new_doc("Custom DocPerm")
        doc.parent = dt
        doc.role = p.get("role")
        for key, val in p.items():
            if key != "role":
                setattr(doc, key, val)
        doc.insert(ignore_permissions=True)
        
    print("Baseline DocPerms configured.")
    frappe.db.commit()

apply_docperms()
