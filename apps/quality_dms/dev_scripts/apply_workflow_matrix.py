import frappe

def apply_matrix_to_workflow():
    frappe.set_user("Administrator")
    
    # 1. Create Workflow Actions if they don't exist
    actions = ["Submit for Review", "Approve Review", "Request Changes", "Publish Document", "Reject Document"]
    for action in actions:
        if not frappe.db.exists("Workflow Action Master", action):
            doc = frappe.new_doc("Workflow Action Master")
            doc.workflow_action_name = action
            doc.insert(ignore_permissions=True)
            print(f"Created action: {action}")
            
    # 2. Create Workflow State for Rejected
    if not frappe.db.exists("Workflow State", "Rejected"):
        doc = frappe.new_doc("Workflow State")
        doc.workflow_state_name = "Rejected"
        doc.insert(ignore_permissions=True)
        print("Created state: Rejected")
            
    wf_name = "Quality Document Workflow"
    if not frappe.db.exists("Workflow", wf_name):
        print("Workflow not found!")
        return
        
    wf = frappe.get_doc("Workflow", wf_name)
    
    # Ensure Rejected is in the states
    has_rejected = False
    for state in wf.states:
        if state.state == "Rejected":
            has_rejected = True
        state.allow_edit = "Desk User"
        
    if not has_rejected:
        wf.append("states", {
            "state": "Rejected",
            "doc_status": 0,
            "allow_edit": "Desk User",
            "update_field": "status",
            "update_value": "Rejected"
        })
        
    # Clear existing transitions
    wf.set("transitions", [])
    
    # Draft -> Pending Review
    wf.append("transitions", {"state": "Draft", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "DMS Creator"})
    wf.append("transitions", {"state": "Draft", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "DMS Manager"})
    
    # Pending Review -> Pending Approval
    wf.append("transitions", {"state": "Pending Review", "action": "Approve Review", "next_state": "Pending Approval", "allowed": "DMS Reviewer"})
    wf.append("transitions", {"state": "Pending Review", "action": "Approve Review", "next_state": "Pending Approval", "allowed": "DMS Manager"})
    
    # Pending Review -> Rejected
    wf.append("transitions", {"state": "Pending Review", "action": "Request Changes", "next_state": "Rejected", "allowed": "DMS Reviewer"})
    wf.append("transitions", {"state": "Pending Review", "action": "Request Changes", "next_state": "Rejected", "allowed": "DMS Manager"})
    
    # Pending Approval -> Published
    wf.append("transitions", {"state": "Pending Approval", "action": "Publish Document", "next_state": "Published", "allowed": "DMS Approver"})
    wf.append("transitions", {"state": "Pending Approval", "action": "Publish Document", "next_state": "Published", "allowed": "DMS Manager"})
    
    # Pending Approval -> Rejected
    wf.append("transitions", {"state": "Pending Approval", "action": "Reject Document", "next_state": "Rejected", "allowed": "DMS Approver"})
    wf.append("transitions", {"state": "Pending Approval", "action": "Reject Document", "next_state": "Rejected", "allowed": "DMS Manager"})
    
    # Rejected -> Pending Review (Creator fixes it)
    wf.append("transitions", {"state": "Rejected", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "DMS Creator"})
    wf.append("transitions", {"state": "Rejected", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "DMS Manager"})
    
    wf.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workflow Matrix Updated")

apply_matrix_to_workflow()
