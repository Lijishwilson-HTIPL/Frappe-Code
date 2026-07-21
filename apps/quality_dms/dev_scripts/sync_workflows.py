import frappe

def sync_workflow_states():
    docs = frappe.get_all("Quality Document", fields=["name", "workflow_state", "status"])
    
    state_mapping = {
        "Draft": "Draft",
        "Pending Review": "Review",
        "Pending Approval": "Approved",
        "Published": "Published",
        "Obsolete": "Obsolete",
        "Archived": "Archived"
    }
    
    count = 0
    for d in docs:
        if d.workflow_state and state_mapping.get(d.workflow_state) != d.status:
            correct_status = state_mapping.get(d.workflow_state)
            frappe.db.set_value("Quality Document", d.name, "status", correct_status)
            count += 1
            
    frappe.db.commit()
    print(f"Synced {count} documents successfully.")

