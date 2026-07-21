import frappe
from frappe.utils import nowdate

def reset_to_global_users():
    frappe.set_user("Administrator")
    
    # 1. Wipe all existing test users EXCEPT Guest and Administrator
    users = frappe.get_all("User", filters={"email": ["like", "%@example.com"]})
    for u in users:
        email = u.name
        if email.lower() == "guest" or email.lower() == "guest@example.com" or email.lower() == "administrator" or email.lower() == "admin@example.com":
            continue
            
        try:
            # Delete Employee
            emp = frappe.get_all("Employee", filters={"user_id": email})
            for e in emp:
                frappe.delete_doc("Employee", e.name, ignore_permissions=True, force=True)
                
            # Delete User Permissions
            perms = frappe.get_all("User Permission", filters={"user": email})
            for p in perms:
                frappe.delete_doc("User Permission", p.name, ignore_permissions=True, force=True)
                
            # Delete User
            frappe.delete_doc("User", email, ignore_permissions=True, force=True)
            print(f"Deleted user: {email}")
        except Exception as e:
            print(f"Could not delete {email}: {e}")
        
    # 2. Create Global Test Users
    roles = {
        "creator@example.com": ["DMS Creator"],
        "reviewer@example.com": ["DMS Reviewer"],
        "approver@example.com": ["DMS Approver"],
        "manager@example.com": ["DMS Manager"]
    }
    
    default_password = "Test@1234"
    
    for email, assigned_roles in roles.items():
        first_name = email.split("@")[0].capitalize()
        
        # Create User
        if not frappe.db.exists("User", email):
            user = frappe.new_doc("User")
            user.email = email
            user.first_name = first_name
            user.send_welcome_email = 0
            user.user_type = "System User"
            user.insert(ignore_permissions=True)
            frappe.utils.password.update_password(email, default_password)
        else:
            user = frappe.get_doc("User", email)
            
        # Assign Roles
        for r in assigned_roles + ["Desk User"]:
            has_role = False
            for existing_r in user.roles:
                if existing_r.role == r: has_role = True; break
            if not has_role: user.append("roles", {"role": r})
        user.save(ignore_permissions=True)
        
        # Create Employee
        if not frappe.db.exists("Employee", {"user_id": email}):
            emp = frappe.new_doc("Employee")
            emp.first_name = first_name
            emp.user_id = email
            emp.status = "Active"
            emp.date_of_joining = nowdate()
            emp.gender = "Male"
            emp.date_of_birth = "1990-01-01"
            dept = frappe.db.get_value("Department", {"name": ["!=", ""]})
            if dept:
                emp.department = dept
            emp.insert(ignore_permissions=True)
            
    frappe.db.commit()
    print("Global test users created successfully.")

reset_to_global_users()
