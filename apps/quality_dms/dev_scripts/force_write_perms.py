import frappe

def force_write_perms():
    frappe.set_user("Administrator")
    dt = "Quality Document"
    roles = ["DMS Creator", "DMS Reviewer", "DMS Approver"]
    
    for role in roles:
        perms = frappe.get_all("Custom DocPerm", filters={"parent": dt, "role": role})
        if not perms:
            perm = frappe.new_doc("Custom DocPerm")
            perm.parent = dt
            perm.role = role
            perm.read = 1
            perm.write = 1
            perm.create = 1
            perm.report = 1
            perm.insert(ignore_permissions=True)
        else:
            for p in perms:
                doc = frappe.get_doc("Custom DocPerm", p.name)
                doc.read = 1
                doc.write = 1
                doc.create = 1
                doc.report = 1
                doc.save(ignore_permissions=True)
                
    # Also fix DocType perms directly just in case
    doc = frappe.get_doc("DocType", dt)
    changed = False
    for p in doc.permissions:
        if p.role in roles:
            p.read = 1
            p.write = 1
            p.create = 1
            p.report = 1
            changed = True
    if changed:
        doc.save(ignore_permissions=True)
        
    print("Forced write permissions for Quality Document.")
    frappe.db.commit()

force_write_perms()
