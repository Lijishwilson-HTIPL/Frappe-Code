import frappe
import json

def remove_child_tables():
    ws = frappe.get_doc("Workspace", "DMS")
    child_tables = ["Document Acknowledgement", "Approval Matrix"] # Need to check if Approval Matrix is a child table.
    
    # Let's query which are child tables directly
    tables = frappe.get_all("DocType", filters={"module": "Quality DMS", "istable": 1}, fields=["name"])
    table_names = [t.name for t in tables]
    
    # Remove from Links and Shortcuts
    ws.set("links", [l for l in ws.links if l.link_to not in table_names and l.label not in table_names])
    ws.set("shortcuts", [s for s in ws.shortcuts if s.link_to not in table_names and s.label not in table_names])
    
    # Rebuild Content Block without child tables
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
    
    for s in ws.shortcuts:
        if s.link_to not in table_names:
            content.append({
                "id": frappe.generate_hash(length=10),
                "type": "shortcut",
                "data": {
                    "shortcut_name": s.label,
                    "col": 4
                }
            })
            
    ws.content = json.dumps(content)
    ws.save(ignore_permissions=True)
    print("Removed child tables from Workspace!")

remove_child_tables()
