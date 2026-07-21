import frappe

def test_full_workflow():
    try:
        # 1. Creator creates a document
        frappe.set_user("creator@example.com")
        print("Logged in as Creator.")
        doc = frappe.new_doc("Quality Document")
        doc.title = "E2E Test Document"
        doc.department = "Accounts - HT"
        doc.category = "Policy"
        doc.type = "Finance"
        doc.insert()
        print(f"Created Document: {doc.name}")
        
        # Creator submits for review
        doc.workflow_state = "Pending Review"
        doc.save()
        print(f"Creator successfully transitioned to: {doc.workflow_state}")
        
        # 2. Reviewer approves review
        frappe.set_user("reviewer@example.com")
        print("\nLogged in as Reviewer.")
        doc = frappe.get_doc("Quality Document", doc.name)
        doc.workflow_state = "Pending Approval"
        doc.save()
        print(f"Reviewer successfully transitioned to: {doc.workflow_state}")
        
        # 3. Approver publishes document
        frappe.set_user("approver@example.com")
        print("\nLogged in as Approver.")
        doc = frappe.get_doc("Quality Document", doc.name)
        doc.workflow_state = "Published"
        doc.save()
        print(f"Approver successfully transitioned to: {doc.workflow_state}")
        
        # Check if the document was submitted successfully
        if doc.docstatus == 1:
            print("\nSUCCESS! The document has been fully Published and Submitted!")
        else:
            print("\nWARNING: The document is marked as 'Published', but docstatus is still 0 (Draft).")
            
    except Exception as e:
        print(f"\nERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()

test_full_workflow()
