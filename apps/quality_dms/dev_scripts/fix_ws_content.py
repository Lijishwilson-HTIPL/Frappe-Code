import frappe
import json

def restore_workspace_content():
    ws = frappe.get_doc("Workspace", "DMS")
    
    # Let's rebuild the content array based on the shortcuts and links
    content = []
    
    # Add a section for Shortcuts
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {
            "text": "Shortcuts",
            "level": 3,
            "col": 12
        }
    })
    
    for s in ws.shortcuts:
        content.append({
            "id": frappe.generate_hash(length=10),
            "type": "shortcut",
            "data": {
                "shortcut_name": s.label,
                "col": 4
            }
        })
        
    # Add a section for Links/Pages
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {
            "text": "Pages & Links",
            "level": 3,
            "col": 12
        }
    })
    
    # We don't necessarily need to add cards for links if they render natively on the sidebar, 
    # but the main issue was the center page being empty. 
    # Let's just set the content JSON
    ws.content = json.dumps(content)
    ws.save(ignore_permissions=True)
    print("Fixed Workspace content!")

restore_workspace_content()
