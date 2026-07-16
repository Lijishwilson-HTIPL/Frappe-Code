import frappe
import json

def restore_workspace_content():
    ws = frappe.get_doc("Workspace", "DMS")
    
    # Rebuild the content array
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
        
    # Add a section for Pages & Links
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {
            "text": "Pages & Links",
            "level": 3,
            "col": 12
        }
    })
    
    # Render all the sidebar links as cards in the center!
    # Wait, in Frappe, to render a link as a card, we can use the 'card' type
    # But a 'card' requires a Card record. 
    # Alternatively, we can just render them as 'shortcut' blocks by adding them to ws.shortcuts!
    # Let's just create shortcuts for the missing items if they aren't there, or just add them to the content as shortcuts.
    # Actually, a 'shortcut' block requires the label to exist in ws.shortcuts.
    
    # Let's collect all links that aren't already shortcuts
    existing_shortcut_labels = [s.label for s in ws.shortcuts]
    
    for link in ws.links:
        if link.type == "Link" and link.label not in existing_shortcut_labels:
            # We must add them to ws.shortcuts to display them as shortcut blocks
            ws.append("shortcuts", {
                "type": link.link_type if link.link_type else "DocType",
                "label": link.label,
                "link_to": link.link_to,
                "color": "Grey"
            })
            
            content.append({
                "id": frappe.generate_hash(length=10),
                "type": "shortcut",
                "data": {
                    "shortcut_name": link.label,
                    "col": 3
                }
            })

    ws.content = json.dumps(content)
    ws.save(ignore_permissions=True)
    print("Fixed Workspace content with all links!")

restore_workspace_content()
