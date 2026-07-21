import frappe
import json

def setup_workspaces():
    frappe.set_user("Administrator")
    
    # 1. Delete the old "DMS" workspace
    if frappe.db.exists("Workspace", "DMS"):
        frappe.delete_doc("Workspace", "DMS")
        
    # Clear any old role-based workspaces
    for role in ["Creator", "Reviewer", "Approver", "Manager", "Admin"]:
        ws_name = f"DMS {role}"
        if frappe.db.exists("Workspace", ws_name):
            frappe.delete_doc("Workspace", ws_name)

    # Helper function to create workspace
    def create_ws(name, role, shortcuts):
        ws = frappe.new_doc("Workspace")
        ws.label = name
        ws.name = name
        ws.title = name
        ws.module = "Quality DMS"
        ws.public = 1
        ws.type = "Workspace"
        ws.append("roles", {"role": role})
        
        idx = 1
        for s in shortcuts:
            ws.append("shortcuts", {
                "idx": idx,
                "type": s.get("type", "DocType"),
                "label": s["label"],
                "link_to": s["link_to"],
                "stats_filter": s.get("stats_filter"),
                "color": s.get("color", "Blue")
            })
            idx += 1
            
        ws.insert(ignore_permissions=True)
        print(f"Created Workspace: {name}")

    # Define the base shortcuts
    my_docs = {
        "label": "My Documents",
        "link_to": "Quality Document",
        "color": "Blue"
    }
    review_queue = {
        "label": "Review Queue",
        "link_to": "Quality Document",
        "stats_filter": json.dumps({"workflow_state": "Pending Review"}),
        "color": "Orange"
    }
    approval_queue = {
        "label": "Approval Queue",
        "link_to": "Quality Document",
        "stats_filter": json.dumps({"workflow_state": "Pending Approval"}),
        "color": "Red"
    }
    dept_reports = {
        "type": "Report",
        "label": "Department Reports",
        "link_to": "Master Document List",
        "color": "Green"
    }
    user_mgmt = {
        "label": "User Management",
        "link_to": "User",
        "color": "Grey"
    }
    workflow_settings = {
        "label": "Workflow Settings",
        "link_to": "Workflow",
        "color": "Grey"
    }
    audit_logs = {
        "label": "Audit Logs",
        "link_to": "DMS Audit Log",
        "color": "Red"
    }
    sys_stats = {
        "type": "Report",
        "label": "System Statistics",
        "link_to": "Audit Trail Report",
        "color": "Light Blue"
    }

    # Create the matrices!
    
    create_ws("DMS Creator", "DMS Creator", [
        my_docs
    ])
    
    create_ws("DMS Reviewer", "DMS Reviewer", [
        my_docs, review_queue
    ])
    
    create_ws("DMS Approver", "DMS Approver", [
        my_docs, review_queue, approval_queue
    ])
    
    create_ws("DMS Manager", "DMS Manager", [
        my_docs, review_queue, approval_queue, dept_reports, audit_logs
    ])
    
    create_ws("DMS Admin", "DMS Admin", [
        my_docs, review_queue, approval_queue, dept_reports, user_mgmt, workflow_settings, audit_logs, sys_stats
    ])

setup_workspaces()
