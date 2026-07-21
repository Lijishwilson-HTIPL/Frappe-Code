import frappe
import json
import uuid

def generate_id():
    return str(uuid.uuid4())[:10]

def add_to_home():
    home = frappe.get_doc("Workspace", "Home")
    
    content = json.loads(home.content) if home.content else []
    
    # Check if Quality DMS is already there
    exists = any(item.get("data", {}).get("shortcut_name") == "Quality DMS" for item in content if item.get("type") == "shortcut")
    
    if not exists:
        # Add to shortcuts
        if not home.shortcuts:
            home.shortcuts = []
            
        home.append("shortcuts", {
            "label": "Quality DMS",
            "type": "Page",
            "link_to": "quality-dms",
            "color": "Green"
        })
        
        # Add to content layout
        # Find the last shortcut or append at the end
        new_block = {
            "id": generate_id(),
            "type": "shortcut",
            "data": {
                "shortcut_name": "Quality DMS",
                "col": 3
            }
        }
        
        # We will insert it at index 0 or after the first header
        content.append(new_block)
        home.content = json.dumps(content)
        
        home.save(ignore_permissions=True)
        frappe.db.commit()
        print("Added Quality DMS to Home Desktop!")
    else:
        print("Quality DMS is already on Home Desktop!")
