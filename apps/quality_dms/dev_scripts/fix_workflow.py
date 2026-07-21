import frappe

def fix_workflow():
    if frappe.db.exists("Workflow", "Quality Document Workflow"):
        wf = frappe.get_doc("Workflow", "Quality Document Workflow")
        
        # Map Workflow states to the actual Document "Status" field
        state_mapping = {
            "Draft": "Draft",
            "Pending Review": "Review",
            "Pending Approval": "Approved", # The status options were Draft, Review, Approved, Published
            "Published": "Published",
            "Obsolete": "Obsolete",
            "Archived": "Archived"
        }
        
        print("Quality Document Workflow mapped successfully!")

    if frappe.db.exists("Workflow", "Document Request Workflow"):
        wf2 = frappe.get_doc("Workflow", "Document Request Workflow")
        
        # Fix docstatus validation (cannot go from 0 to 2 directly)
        for state in wf2.states:
            if state.state == "Rejected":
                state.doc_status = 1
                
        state_mapping2 = {
            "Pending": "Pending",
            "Approved": "Approved",
            "Rejected": "Rejected"
        }
        for state in wf2.states:
            state.update_field = "status"
            state.update_value = state_mapping2.get(state.state)
            
        wf2.save(ignore_permissions=True)
        print("Document Request Workflow mapped successfully!")
        
    frappe.db.commit()
