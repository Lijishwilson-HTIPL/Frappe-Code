import frappe

def fix_project_permissions():
    frappe.set_user("Administrator")
    
    roles = ["DMS Creator", "DMS Reviewer", "DMS Approver"]
    dt = "DMS Project"
    
    if frappe.db.exists("DocType", dt):
        for role in roles:
            if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role}):
                perm = frappe.new_doc("Custom DocPerm")
                perm.parent = dt
                perm.role = role
                perm.read = 1
                perm.insert(ignore_permissions=True)
            else:
                perms = frappe.get_all("Custom DocPerm", filters={"parent": dt, "role": role})
                for p in perms:
                    doc = frappe.get_doc("Custom DocPerm", p.name)
                    doc.read = 1
                    doc.save(ignore_permissions=True)
                    
        # Update standard permissions to make sure read is 1
        doc = frappe.get_doc("DocType", dt)
        changed = False
        for p in doc.permissions:
            if p.role in roles:
                p.read = 1
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
            
        print("Permissions updated for DMS Project doctype.")
        frappe.db.commit()
    else:
        print("DMS Project doctype not found!")

fix_project_permissions()
