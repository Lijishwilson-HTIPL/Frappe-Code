import frappe

def reset_users():
    frappe.set_user("Administrator")
    
    # Get all example.com users
    users = frappe.get_all("User", filters={"email": ["like", "%@example.com"]})
    
    for u in users:
        email = u.name
        
        # 1. Delete associated Employee
        emp = frappe.get_all("Employee", filters={"user_id": email})
        for e in emp:
            frappe.delete_doc("Employee", e.name, ignore_permissions=True, force=True)
            
        # 2. Delete User Permissions
        perms = frappe.get_all("User Permission", filters={"user": email})
        for p in perms:
            frappe.delete_doc("User Permission", p.name, ignore_permissions=True, force=True)
            
        # 3. Delete the User
        frappe.delete_doc("User", email, ignore_permissions=True, force=True)
        print(f"Deleted user: {email}")
        
    frappe.db.commit()
    print("All test users have been wiped clean.")

reset_users()
