import frappe

def force_submit_perms():
    frappe.set_user("Administrator")
    dt = "Quality Document"
    roles = ["DMS Approver", "DMS Admin"]
    
    for role in roles:
        perms = frappe.get_all("Custom DocPerm", filters={"parent": dt, "role": role})
        for p in perms:
            doc = frappe.get_doc("Custom DocPerm", p.name)
            doc.submit = 1
            doc.save(ignore_permissions=True)
                
    # Also fix DocType perms directly
    doc = frappe.get_doc("DocType", dt)
    changed = False
    for p in doc.permissions:
        if p.role in roles:
            p.submit = 1
            changed = True
            
    if changed:
        doc.save(ignore_permissions=True)
        
    print("Forced submit permissions for Quality Document.")
    frappe.db.commit()

force_submit_perms()
