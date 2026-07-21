import frappe
from frappe.utils import nowdate

def generate_manager_and_users():
    frappe.set_user("Administrator")
    
    # 1. Create DMS Manager Role
    if not frappe.db.exists("Role", "DMS Manager"):
        role = frappe.new_doc("Role")
        role.role_name = "DMS Manager"
        role.desk_access = 1
        role.insert(ignore_permissions=True)
        print("Created DMS Manager Role")
        
    # Grant core access to Manager
    doctypes_to_allow = ["Page", "Report", "Workspace", "DocType", "Document Category", "Document Type", "Department", "DMS Project"]
    for dt in doctypes_to_allow:
        if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": "DMS Manager"}):
            perm = frappe.new_doc("Custom DocPerm")
            perm.parent = dt
            perm.role = "DMS Manager"
            perm.read = 1
            if dt in ["Page", "Report", "Workspace", "DocType"]:
                perm.report = 1
            perm.insert(ignore_permissions=True)
            
    # Add Manager to Workspace
    if frappe.db.exists("Workspace", "DMS"):
        ws = frappe.get_doc("Workspace", "DMS")
        has_role = False
        for r in ws.roles:
            if r.role == "DMS Manager": has_role = True; break
        if not has_role:
            ws.append("roles", {"role": "DMS Manager"})
            ws.save(ignore_permissions=True)
            
    # Add Manager to Report
    report_name = "Master Document List"
    if frappe.db.exists("Report", report_name):
        report = frappe.get_doc("Report", report_name)
        has_role = False
        for r in report.roles:
            if r.role == "DMS Manager": has_role = True; break
        if not has_role:
            report.append("roles", {"role": "DMS Manager"})
            report.save(ignore_permissions=True)
            
    # Add Manager to Page
    if frappe.db.exists("Page", "dms-explorer"):
        page = frappe.get_doc("Page", "dms-explorer")
        has_role = False
        for r in page.roles:
            if r.role == "DMS Manager": has_role = True; break
        if not has_role:
            page.append("roles", {"role": "DMS Manager"})
            page.save(ignore_permissions=True)

    # 2. Generate Test Users
    departments = frappe.get_list("Department", pluck="name")
    roles = ["DMS Creator", "DMS Reviewer", "DMS Approver", "DMS Manager"]
    default_password = "Test@1234"
    
    for dept in departments:
        safe_dept = "".join([c.lower() for c in dept if c.isalnum()])
        for role in roles:
            role_key = role.split(" ")[1].lower()
            email = f"{safe_dept}_{role_key}@example.com"
            first_name = f"{dept} {role.split(' ')[1]}"
            
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
                
            for r in [role, "Desk User"]:
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
                emp.department = dept
                emp.insert(ignore_permissions=True)
                
            # Create User Permission
            if not frappe.db.exists("User Permission", {"user": email, "allow": "Department", "for_value": dept}):
                perm = frappe.new_doc("User Permission")
                perm.user = email
                perm.allow = "Department"
                perm.for_value = dept
                perm.insert(ignore_permissions=True)
                
    frappe.db.commit()
    print("Generation of users and Manager setup complete.")

generate_manager_and_users()
