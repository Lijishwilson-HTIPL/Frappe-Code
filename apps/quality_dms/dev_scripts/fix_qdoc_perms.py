import frappe

def fix_quality_document_perms():
    frappe.set_user("Administrator")
    
    dt = "Quality Document"
    roles = ["DMS Creator", "DMS Reviewer", "DMS Approver"]
    
    for role in roles:
        if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role}):
            perm = frappe.new_doc("Custom DocPerm")
            perm.parent = dt
            perm.role = role
            perm.read = 1
            perm.write = 1
            perm.create = 1
            perm.delete = 1 if role == "DMS Admin" else 0
            perm.report = 1
            perm.insert(ignore_permissions=True)
        else:
            # Update existing
            perms = frappe.get_all("Custom DocPerm", filters={"parent": dt, "role": role})
            for p in perms:
                doc = frappe.get_doc("Custom DocPerm", p.name)
                doc.read = 1
                doc.report = 1
                doc.save(ignore_permissions=True)
                
    # We must also ensure standard DocPerm has report enabled
    doc = frappe.get_doc("DocType", dt)
    changed = False
    for p in doc.permissions:
        if p.role in roles:
            p.read = 1
            p.report = 1
            changed = True
            
    if changed:
        doc.save(ignore_permissions=True)
        
    print("Permissions updated for Quality Document.")
    frappe.db.commit()

fix_quality_document_perms()
