import frappe
from frappe.utils import nowdate

def generate_test_users():
    frappe.set_user("Administrator")
    
    # Get all departments
    departments = frappe.get_list("Department", pluck="name")
    
    roles = ["DMS Creator", "DMS Reviewer", "DMS Approver"]
    
    # Password for all test users
    default_password = "Test@1234"
    
    output = []
    
    for dept in departments:
        # Create a safe prefix for emails
        safe_dept = "".join([c.lower() for c in dept if c.isalnum()])
        
        for role in roles:
            role_key = role.split(" ")[1].lower() # creator, reviewer, approver
            email = f"{safe_dept}_{role_key}@example.com"
            first_name = f"{dept} {role.split(' ')[1]}"
            
            # 1. Create User
            if not frappe.db.exists("User", email):
                user = frappe.new_doc("User")
                user.email = email
                user.first_name = first_name
                user.send_welcome_email = 0
                user.insert(ignore_permissions=True)
                frappe.utils.password.update_password(email, default_password)
            else:
                user = frappe.get_doc("User", email)
            
            # Assign roles
            for r in [role, "Desk User"]:
                has_role = False
                for existing_r in user.roles:
                    if existing_r.role == r:
                        has_role = True; break
                if not has_role:
                    user.append("roles", {"role": r})
            user.save(ignore_permissions=True)
            
            # 2. Create Employee
            if not frappe.db.exists("Employee", {"user_id": email}):
                emp = frappe.new_doc("Employee")
                emp.first_name = first_name
                emp.user_id = email
                emp.status = "Active"
                emp.date_of_joining = nowdate()
                emp.gender = "Male"
                emp.date_of_birth = "1990-01-01"
                # Link employee to department
                emp.department = dept
                emp.insert(ignore_permissions=True)
                
            # 3. Create User Permission for Department
            # To restrict them to only their department folder
            if not frappe.db.exists("User Permission", {"user": email, "allow": "Department", "for_value": dept}):
                perm = frappe.new_doc("User Permission")
                perm.user = email
                perm.allow = "Department"
                perm.for_value = dept
                perm.insert(ignore_permissions=True)
                
            output.append(f"- **{role}**: `{email}`")
            
        print(f"\\n### {dept}")
        print("\\n".join(output[-3:]))
        
    frappe.db.commit()
    print("\\nGeneration Complete")
