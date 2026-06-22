import frappe
import json


def execute():
    ws = frappe.get_doc("Workspace", "CRM")
    content = json.loads(ws.content)

    # Check already added
    existing = [b['data'].get('shortcut_name') for b in content if b.get('type') == 'shortcut']
    print(f"Existing shortcuts in content: {existing}")
    if 'Leads Journey' in existing:
        print("Already in content")
        return

    # Find index of Lead shortcut block
    lead_idx = None
    for i, block in enumerate(content):
        if block.get('type') == 'shortcut' and block['data'].get('shortcut_name') == 'Lead':
            lead_idx = i
            break

    new_block = {
        "id": "lj-" + frappe.generate_hash(length=8),
        "type": "shortcut",
        "data": {"shortcut_name": "Leads Journey", "col": 3}
    }

    if lead_idx is not None:
        content.insert(lead_idx + 1, new_block)
        print(f"Inserted after Lead at position {lead_idx + 1}")
    else:
        content.append(new_block)
        print("Appended at end")

    # Save directly to DB to bypass validation
    frappe.db.set_value("Workspace", "CRM", "content", json.dumps(content), update_modified=False)
    frappe.db.commit()
    print("Content updated. Leads Journey now in workspace.")
