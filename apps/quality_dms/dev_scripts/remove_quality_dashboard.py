import frappe
import json

def remove_quality_dashboard():
    # 1. Remove Page
    if frappe.db.exists("Page", "quality_dashboard"):
        frappe.delete_doc("Page", "quality_dashboard")
        print("Deleted Page record.")
        
    # 2. Clean Workspace
    ws = frappe.get_doc("Workspace", "DMS")
    
    # Remove from Links and Shortcuts
    ws.set("links", [l for l in ws.links if l.link_to != "quality_dashboard" and l.label != "Quality Dashboard"])
    ws.set("shortcuts", [s for s in ws.shortcuts if s.link_to != "quality_dashboard" and s.label != "Quality Dashboard"])
    
    # Rebuild Content Block without Quality Dashboard
    content = []
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {
            "text": "Shortcuts",
            "level": 3,
            "col": 12
        }
    })
    
    existing_shortcut_labels = []
    for s in ws.shortcuts:
        if s.label != "Quality Dashboard":
            existing_shortcut_labels.append(s.label)
            content.append({
                "id": frappe.generate_hash(length=10),
                "type": "shortcut",
                "data": {
                    "shortcut_name": s.label,
                    "col": 4
                }
            })
            
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {
            "text": "Pages & Links",
            "level": 3,
            "col": 12
        }
    })
    
    for link in ws.links:
        if link.type == "Link" and link.label not in existing_shortcut_labels:
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
    print("Cleaned up DMS Workspace!")

remove_quality_dashboard()
