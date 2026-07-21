import frappe

def fix_report_roles():
    frappe.set_user("Administrator")
    
    report_name = "Master Document List"
    if frappe.db.exists("Report", report_name):
        report = frappe.get_doc("Report", report_name)
        
        roles_to_add = ["DMS Creator", "DMS Reviewer", "DMS Approver", "DMS Admin"]
        existing_roles = [r.role for r in report.roles]
        
        changed = False
        for role in roles_to_add:
            if role not in existing_roles:
                report.append("roles", {"role": role})
                changed = True
                
        if changed:
            report.save(ignore_permissions=True)
            print(f"Updated Roles for Report '{report_name}'")
    else:
        print(f"Report '{report_name}' not found!")
        
    frappe.db.commit()

fix_report_roles()
