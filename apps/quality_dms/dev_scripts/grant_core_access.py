import frappe

def grant_core_access():
    frappe.set_user("Administrator")
    
    roles = ["DMS Creator", "DMS Reviewer", "DMS Approver", "DMS Admin"]
    
    doctypes_to_allow = ["Page", "Report", "Workspace", "DocType"]
    
    for dt in doctypes_to_allow:
        for role in roles:
            # Check if Custom DocPerm exists
            if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role}):
                perm = frappe.new_doc("Custom DocPerm")
                perm.parent = dt
                perm.role = role
                perm.read = 1
                perm.report = 1
                perm.insert(ignore_permissions=True)
                
    frappe.db.commit()
    print("Granted core read access for Page and Report to custom roles.")

grant_core_access()
