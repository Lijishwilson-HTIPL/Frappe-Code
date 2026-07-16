import frappe

def fix_users():
    frappe.set_user("Administrator")
    
    users = frappe.get_all("User", filters={"email": ["like", "%@example.com"]})
    
    for u in users:
        user = frappe.get_doc("User", u.name)
        changed = False
        if user.user_type != "System User":
            user.user_type = "System User"
            changed = True
            
        # Ensure they have standard Desk access
        roles = [r.role for r in user.roles]
        if "Desk User" not in roles:
            user.append("roles", {"role": "Desk User"})
            changed = True
            
        if changed:
            user.save(ignore_permissions=True)
            print(f"Fixed {u.name}")
            
    # Also explicitly add roles to the custom dms_explorer page just to be safe
    if frappe.db.exists("Page", "dms-explorer"):
        page = frappe.get_doc("Page", "dms-explorer")
        roles_to_add = ["DMS Creator", "DMS Reviewer", "DMS Approver"]
        
        page_roles = [r.role for r in page.roles]
        for role in roles_to_add:
            if role not in page_roles:
                page.append("roles", {"role": role})
                
        page.save(ignore_permissions=True)
        print("Updated dms_explorer Page roles")
            
    frappe.db.commit()

fix_users()
