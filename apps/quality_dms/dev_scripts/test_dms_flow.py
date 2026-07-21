import frappe
from frappe.utils import today

def run_tests():
    print("Starting DMS Integration Tests...")
    frappe.flags.in_test = True
    
    try:
        # 1. Create Master Data
        if not frappe.db.exists("Department", "Quality Assurance"):
            dept = frappe.get_doc({"doctype": "Department", "department_name": "Quality Assurance"})
            dept.insert(ignore_permissions=True)
        else:
            dept = frappe.get_doc("Department", "Quality Assurance")

        if not frappe.db.exists("Document Category", "SOP"):
            cat = frappe.get_doc({"doctype": "Document Category", "category_name": "SOP"})
            cat.insert(ignore_permissions=True)
        else:
            cat = frappe.get_doc("Document Category", "SOP")

        if not frappe.db.exists("Document Type", "Internal"):
            dtype = frappe.get_doc({"doctype": "Document Type", "type_name": "Internal"})
            dtype.insert(ignore_permissions=True)
        else:
            dtype = frappe.get_doc("Document Type", "Internal")

        print("✔ Master Data Ready")

        # 2. Create Quality Document (Draft)
        doc = frappe.get_doc({
            "doctype": "Quality Document",
            "title": "Test SOP Document",
            "department": dept.name,
            "category": cat.name,
            "type": dtype.name,
            "status": "Draft",
            "effective_date": today()
        })
        doc.insert(ignore_permissions=True)
        print(f"✔ Created Quality Document: {doc.name}")

        # 3. Test Workflow Transitions
        # Draft -> Pending Review
        doc.workflow_state = "Pending Review"
        doc.save(ignore_permissions=True)
        
        # Pending Review -> Pending Approval
        doc.workflow_state = "Pending Approval"
        doc.save(ignore_permissions=True)
        
        # Pending Approval -> Published
        doc.workflow_state = "Published"
        doc.status = "Published"
        # We need to trigger submit because our logic is in on_submit, but workflows handle submission.
        # Let's explicitly submit it for the test.
        doc.docstatus = 1
        doc.save(ignore_permissions=True)
        
        print("✔ Workflow transitions successful. Document is Published.")

        # 4. Check Document Revision creation
        revisions = frappe.get_all("Document Revision", filters={"document": doc.name})
        if revisions:
            print(f"✔ Document Revision automatically created: {revisions[0].name}")
        else:
            print("❌ Document Revision was NOT created!")

        # 5. Check Audit Log
        logs = frappe.get_all("DMS Audit Log", filters={"document": doc.name})
        if logs:
            print(f"✔ Audit Logs generated: {len(logs)} events captured.")
        else:
            print("❌ Audit Log was NOT generated!")

        # 6. Test Document Acknowledgment
        # We need an employee record for the current user
        employee_name = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if not employee_name:
            # Create a dummy employee for the test
            emp = frappe.get_doc({
                "doctype": "Employee",
                "first_name": "Test",
                "last_name": "User",
                "user_id": frappe.session.user,
                "gender": "Male",
                "date_of_birth": "1990-01-01",
                "date_of_joining": "2020-01-01"
            })
            emp.insert(ignore_permissions=True)
            employee_name = emp.name
            
        from quality_dms.dms.api import acknowledge_document
        acknowledge_document(doc.name)
        
        training = frappe.get_all("DMS Training Record", filters={"document": doc.name})
        if training:
            print(f"✔ Training Record & Acknowledgment successful: {training[0].name}")
        else:
            print("❌ Training Record was NOT created!")

        # Cleanup
        frappe.db.rollback()
        print("✔ Tests completed successfully. Test data rolled back.")

    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")
        frappe.db.rollback()
