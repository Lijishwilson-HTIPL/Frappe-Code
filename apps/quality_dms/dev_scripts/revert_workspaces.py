import frappe
import json

def revert_workspaces():
    frappe.set_user("Administrator")
    
    # 1. Delete the role-based workspaces
    for role in ["Creator", "Reviewer", "Approver", "Manager", "Admin"]:
        ws_name = f"DMS {role}"
        if frappe.db.exists("Workspace", ws_name):
            frappe.delete_doc("Workspace", ws_name)
            print(f"Deleted Workspace: {ws_name}")
            
    # 2. Re-create the "DMS" workspace
    if not frappe.db.exists("Workspace", "DMS"):
        ws = frappe.new_doc("Workspace")
        ws.name = "DMS"
        ws.label = "DMS"
        ws.title = "DMS"
        ws.module = "Quality DMS"
        ws.public = 1
        ws.type = "Workspace"
        
        # Add roles
        ws.append("roles", {"role": "DMS Creator"})
        ws.append("roles", {"role": "DMS Reviewer"})
        ws.append("roles", {"role": "DMS Approver"})
        ws.append("roles", {"role": "DMS Manager"})
        
        # Add shortcuts
        shortcuts = [
            {"label": "New Quality Document", "link_to": "Quality Document", "type": "DocType", "color": "Green"},
            {"label": "New Document Request", "link_to": "Document Request", "type": "DocType", "color": "Blue"},
            {"label": "DMS Audit Log", "link_to": "DMS Audit Log", "type": "DocType", "color": "Red"}
        ]
        
        idx = 1
        for s in shortcuts:
            ws.append("shortcuts", {
                "idx": idx,
                "type": s["type"],
                "label": s["label"],
                "link_to": s["link_to"],
                "color": s["color"]
            })
            idx += 1
            
        ws.insert(ignore_permissions=True)
        print("Restored original DMS Workspace.")
    else:
        print("DMS Workspace already exists.")

revert_workspaces()
