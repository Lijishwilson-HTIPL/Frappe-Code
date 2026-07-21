import frappe

def test_full_workflow():
    try:
        # 1. Creator creates a document
        frappe.set_user("creator@example.com")
        doc = frappe.new_doc("Quality Document")
        doc.title = "E2E Test Document Submit"
        doc.department = "Accounts - HT"
        doc.category = "Policy"
        doc.type = "Finance"
        doc.insert()
        
        # Creator submits for review
        doc.workflow_state = "Pending Review"
        doc.save()
        
        # 2. Reviewer approves review
        frappe.set_user("reviewer@example.com")
        doc = frappe.get_doc("Quality Document", doc.name)
        doc.workflow_state = "Pending Approval"
        doc.save()
        
        # 3. Approver publishes document (Submit!)
        frappe.set_user("approver@example.com")
        doc = frappe.get_doc("Quality Document", doc.name)
        doc.workflow_state = "Published"
        
        from frappe.model.workflow import apply_workflow
        apply_workflow(doc, "Publish Document")
        
        print("Workflow Applied successfully!")
        print(f"Doc Status: {doc.docstatus}")
            
    except Exception as e:
        print(f"ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()

test_full_workflow()
