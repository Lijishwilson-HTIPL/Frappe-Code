import frappe

def fix_workspace_roles():
    frappe.set_user("Administrator")
    
    # Add roles to workspace
    if frappe.db.exists("Workspace", "DMS"):
        ws = frappe.get_doc("Workspace", "DMS")
        
        # Make it public just in case
        ws.public = 1
        ws.for_user = ""
        
        roles_to_add = ["DMS Creator", "DMS Reviewer", "DMS Approver"]
        
        for role in roles_to_add:
            has_role = False
            for r in ws.roles:
                if r.role == role: has_role = True; break
            if not has_role:
                ws.append("roles", {"role": role})
                
        ws.save(ignore_permissions=True)
        print("Updated DMS Workspace Roles")
    else:
        print("DMS Workspace not found")
        
    frappe.db.commit()

fix_workspace_roles()
