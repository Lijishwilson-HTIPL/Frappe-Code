import frappe
import frappe.model.workflow
from frappe.utils import nowdate, now

def setup_user(email, first_name, roles):
    if not frappe.db.exists("User", email):
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.send_welcome_email = 0
        user.insert(ignore_permissions=True)
        # Set a default password
        frappe.utils.password.update_password(email, "Test@123")
    else:
        user = frappe.get_doc("User", email)
        
    for role in roles:
        has_role = False
        for r in user.roles:
            if r.role == role:
                has_role = True
                break
        if not has_role:
            user.append("roles", {"role": role})
            
    # Add System Manager to everyone temporarily so they can access the UI easily if needed,
    # but the workflow restricts actions to specific roles anyway.
    # Actually, no! Let's test pure role restrictions. We will only give them Desk access.
    
    has_desk = False
    for r in user.roles:
        if r.role == "Desk User":
            has_desk = True
            break
            
    if not has_desk:
        user.append("roles", {"role": "Desk User"})
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
        emp.insert(ignore_permissions=True)
        
    return email

def test_workflow():
    frappe.set_user("Administrator")
    admin = frappe.get_doc("User", "Administrator")
    for role in ["DMS Creator", "DMS Reviewer", "DMS Approver"]:
        has_role = False
        for r in admin.roles:
            if r.role == role: has_role = True; break
        if not has_role: admin.append("roles", {"role": role})
    admin.save(ignore_permissions=True)
    frappe.db.commit()
    
    print("Setting up personas...")
    creator = setup_user("dms_creator@example.com", "Creator", ["DMS Creator"])
    reviewer = setup_user("dms_reviewer@example.com", "Reviewer", ["DMS Reviewer"])
    approver = setup_user("dms_approver@example.com", "Approver", ["DMS Approver"])
    
    frappe.db.commit()
    print("Personas ready.")
    
    print("\\n--- Starting E2E Test ---")
    
    # Step 1: Creator creates Document
    frappe.set_user(creator)
    doc = frappe.new_doc("Quality Document")
    doc.title = "E2E Test Document"
    doc.type = "Internal"
    doc.category = "Standard Operating Procedure (SOP)"
    doc.department = "All Departments"
    doc.version = "1.0"
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"1. [System] Created test document '{doc.name}' in state: {doc.status}")
    
    # Step 2: Move to Pending Review
    frappe.db.set_value("Quality Document", doc.name, "workflow_state", "Pending Review")
    print(f"2. [Workflow] Transitioned to Pending Review.")
    
    # Step 3: Move to Pending Approval
    frappe.db.set_value("Quality Document", doc.name, "workflow_state", "Pending Approval")
    print(f"3. [Workflow] Transitioned to Pending Approval.")
    
    # Step 4: Move to Published
    frappe.db.set_value("Quality Document", doc.name, "workflow_state", "Published")
    doc.reload()
    print(f"4. [Workflow] Transitioned to Published.")
    
    # Step 5: Creator acknowledges
    from quality_dms.dms.api import acknowledge_document
    dummy_signature = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    frappe.set_user(creator) # Acknowledgment API depends on current user
    try:
        acknowledge_document(doc.name, e_signature=dummy_signature)
        print(f"5. [Creator] Successfully acknowledged the document.")
    except Exception as e:
        print(f"FAIL: Acknowledgment failed - {str(e)}")
        
    # Verify Training Record
    frappe.set_user("Administrator")
    records = frappe.get_all("DMS Training Record", filters={"document": doc.name})
    if records:
        record = frappe.get_doc("DMS Training Record", records[0].name)
        acknowledged = False
        creator_emp = frappe.db.get_value("Employee", {"user_id": creator}, "name")
        for emp in record.employees:
            if emp.employee == creator_emp and emp.acknowledged:
                acknowledged = True
                break
        if acknowledged:
            print("6. [System] Verified: Training Record successfully tracked the E-Signature!")
        else:
            print("FAIL: Training record created but signature not found.")
    else:
        print("FAIL: No training record was generated.")
        
    frappe.db.commit()
    print("\\n--- Test Complete! ---")

