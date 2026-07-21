import frappe
import json
import uuid

def generate_id():
    return str(uuid.uuid4())[:10]

def create_comprehensive_workspace():
    workspace_name = "Quality DMS"
    
    # Create Reports
    reports = [
        {"name": "Master Document List", "ref_doctype": "Quality Document"},
        {"name": "Audit Trail Report", "ref_doctype": "DMS Audit Log"}
    ]
    for rep in reports:
        if not frappe.db.exists("Report", rep["name"]):
            report = frappe.get_doc({
                "doctype": "Report",
                "name": rep["name"],
                "report_name": rep["name"],
                "ref_doctype": rep["ref_doctype"],
                "report_type": "Report Builder",
                "is_standard": "Yes",
                "module": "Quality DMS"
            })
            report.insert(ignore_permissions=True)
    frappe.db.commit()
    
    # Delete if exists to recreate freshly
    if frappe.db.exists("Workspace", workspace_name):
        frappe.delete_doc("Workspace", workspace_name, ignore_permissions=True)

    links = [
        {"label": "Document Management", "type": "Card Break", "icon": "document"},
        {"label": "Quality Documents", "type": "Link", "link_type": "DocType", "link_to": "Quality Document"},
        {"label": "Document Requests", "type": "Link", "link_type": "DocType", "link_to": "Document Request"},
        
        {"label": "Folder Management", "type": "Card Break", "icon": "folder"},
        {"label": "Departments", "type": "Link", "link_type": "DocType", "link_to": "Department"},
        {"label": "Document Categories", "type": "Link", "link_type": "DocType", "link_to": "Document Category"},
        {"label": "Document Types", "type": "Link", "link_type": "DocType", "link_to": "Document Type"},
        
        {"label": "Workflow & Approvals", "type": "Card Break", "icon": "tick"},
        {"label": "Approval Matrix", "type": "Link", "link_type": "DocType", "link_to": "Approval Matrix"},
        {"label": "Workflows", "type": "Link", "link_type": "DocType", "link_to": "Workflow"},
        
        {"label": "Acknowledgements", "type": "Card Break", "icon": "check"},
        {"label": "Training Records", "type": "Link", "link_type": "DocType", "link_to": "DMS Training Record"},
        
        {"label": "Version Control", "type": "Card Break", "icon": "history"},
        {"label": "Document Revisions", "type": "Link", "link_type": "DocType", "link_to": "Document Revision"},
        
        {"label": "Document Distribution", "type": "Card Break", "icon": "share"},
        {"label": "Communications", "type": "Link", "link_type": "DocType", "link_to": "Communication"},
        
        {"label": "Compliance", "type": "Card Break", "icon": "shield"},
        {"label": "Audit Logs", "type": "Link", "link_type": "DocType", "link_to": "DMS Audit Log"},
        
        {"label": "Reports", "type": "Card Break", "icon": "report"},
        {"label": "Master Document List", "type": "Link", "link_type": "Report", "link_to": "Master Document List"},
        {"label": "Audit Trail Report", "type": "Link", "link_type": "Report", "link_to": "Audit Trail Report"},
        
        {"label": "Administration", "type": "Card Break", "icon": "setting"},
        {"label": "Users", "type": "Link", "link_type": "DocType", "link_to": "User"},
        {"label": "Roles", "type": "Link", "link_type": "DocType", "link_to": "Role"}
    ]

    shortcuts = [
        {"label": "New Quality Document", "type": "DocType", "link_to": "Quality Document", "color": "Green"},
        {"label": "New Document Request", "type": "DocType", "link_to": "Document Request", "color": "Blue"},
        {"label": "DMS Audit Log", "type": "DocType", "link_to": "DMS Audit Log", "color": "Red"}
    ]

    content = [
        {"id": generate_id(), "type": "header", "data": {"text": "DMS Quick Actions", "level": 3}},
        {"id": generate_id(), "type": "shortcut", "data": {"shortcut_name": "New Quality Document", "col": 4}},
        {"id": generate_id(), "type": "shortcut", "data": {"shortcut_name": "New Document Request", "col": 4}},
        {"id": generate_id(), "type": "shortcut", "data": {"shortcut_name": "DMS Audit Log", "col": 4}},
        {"id": generate_id(), "type": "spacer", "data": {"col": 12}},
        {"id": generate_id(), "type": "header", "data": {"text": "DMS Modules", "level": 3}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Document Management", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Folder Management", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Workflow & Approvals", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Acknowledgements", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Version Control", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Document Distribution", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Compliance", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Reports", "col": 4}},
        {"id": generate_id(), "type": "card", "data": {"card_name": "Administration", "col": 4}},
        {"id": generate_id(), "type": "spacer", "data": {"col": 12}},
        {"id": generate_id(), "type": "spacer", "data": {"col": 12}}
    ]

    workspace = frappe.get_doc({
        "doctype": "Workspace",
        "name": workspace_name,
        "title": workspace_name,
        "label": workspace_name,
        "icon": "folder",
        "is_standard": 1,
        "app": "quality_dms",
        "module": "Quality DMS",
        "public": 1,
        "is_hidden": 0,
        "parent_page": "",
        "sequence_id": 1.0,
        "content": json.dumps(content),
        "links": links,
        "shortcuts": shortcuts
    })
    
    workspace.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Comprehensive Workspace created!")
