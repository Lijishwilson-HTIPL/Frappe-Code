import frappe

def create_roles_and_workflows():
    roles = ["DMS User", "DMS Creator", "DMS Reviewer", "DMS Approver", "DMS Admin"]
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            doc = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1
            })
            doc.insert(ignore_permissions=True)

    # Workflow Actions
    actions = ["Submit for Review", "Review Complete", "Reject", "Approve and Publish", "Archive", "Make Obsolete", "Approve"]
    for action in actions:
        if not frappe.db.exists("Workflow Action Master", action):
            doc = frappe.get_doc({
                "doctype": "Workflow Action Master",
                "workflow_action_name": action
            })
            doc.insert(ignore_permissions=True)

    # Workflow States
    states = ["Draft", "Pending Review", "Pending Approval", "Published", "Obsolete", "Archived"]
    for state in states:
        if not frappe.db.exists("Workflow State", state):
            doc = frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": state,
                "icon": "edit" if state == "Draft" else "check",
                "style": "Warning" if state in ["Pending Review", "Pending Approval"] else ("Success" if state == "Published" else "Danger")
            })
            doc.insert(ignore_permissions=True)

    # Document Workflow
    if not frappe.db.exists("Workflow", "Quality Document Workflow"):
        workflow = frappe.get_doc({
            "doctype": "Workflow",
            "workflow_name": "Quality Document Workflow",
            "document_type": "Quality Document",
            "is_active": 1,
            "send_email_alert": 1,
            "states": [
                {"state": "Draft", "doc_status": 0, "allow_edit": "DMS Creator"},
                {"state": "Pending Review", "doc_status": 0, "allow_edit": "DMS Reviewer"},
                {"state": "Pending Approval", "doc_status": 0, "allow_edit": "DMS Approver"},
                {"state": "Published", "doc_status": 1, "allow_edit": "DMS Admin"},
                {"state": "Obsolete", "doc_status": 2, "allow_edit": "DMS Admin"},
                {"state": "Archived", "doc_status": 2, "allow_edit": "DMS Admin"}
            ],
            "transitions": [
                {"state": "Draft", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "DMS Creator"},
                {"state": "Pending Review", "action": "Review Complete", "next_state": "Pending Approval", "allowed": "DMS Reviewer"},
                {"state": "Pending Review", "action": "Reject", "next_state": "Draft", "allowed": "DMS Reviewer"},
                {"state": "Pending Approval", "action": "Approve and Publish", "next_state": "Published", "allowed": "DMS Approver"},
                {"state": "Pending Approval", "action": "Reject", "next_state": "Draft", "allowed": "DMS Approver"},
                {"state": "Published", "action": "Archive", "next_state": "Archived", "allowed": "DMS Admin"},
                {"state": "Published", "action": "Make Obsolete", "next_state": "Obsolete", "allowed": "DMS Admin"}
            ]
        })
        workflow.insert(ignore_permissions=True)

    # Workflow for Document Request
    req_states = ["Pending", "Approved", "Rejected"]
    for state in req_states:
        if not frappe.db.exists("Workflow State", state):
            doc = frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": state,
                "icon": "check",
                "style": "Success" if state == "Approved" else ("Danger" if state == "Rejected" else "Warning")
            })
            doc.insert(ignore_permissions=True)

    if not frappe.db.exists("Workflow", "Document Request Workflow"):
        workflow = frappe.get_doc({
            "doctype": "Workflow",
            "workflow_name": "Document Request Workflow",
            "document_type": "Document Request",
            "is_active": 1,
            "send_email_alert": 1,
            "states": [
                {"state": "Pending", "doc_status": 0, "allow_edit": "DMS Creator"},
                {"state": "Approved", "doc_status": 1, "allow_edit": "DMS Admin"},
                {"state": "Rejected", "doc_status": 2, "allow_edit": "DMS Admin"}
            ],
            "transitions": [
                {"state": "Pending", "action": "Approve", "next_state": "Approved", "allowed": "DMS Admin"},
                {"state": "Pending", "action": "Reject", "next_state": "Rejected", "allowed": "DMS Admin"}
            ]
        })
        workflow.insert(ignore_permissions=True)

    frappe.db.commit()
    print("Roles and Workflows created successfully!")
