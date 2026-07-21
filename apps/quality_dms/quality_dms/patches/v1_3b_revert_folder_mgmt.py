import json
import frappe


def execute():
    if not frappe.db.exists("Workspace", "Quality DMS"):
        return

    ws = frappe.get_doc("Workspace", "Quality DMS")

    for link in ws.links:
        if link.type == "Card Break" and link.label == "File Storage":
            link.label = "Folder Management"
            link.icon = "folder"

    try:
        content = json.loads(ws.content or "[]")
        for block in content:
            if (
                block.get("type") == "card"
                and block.get("data", {}).get("card_name") == "File Storage"
            ):
                block["data"]["card_name"] = "Folder Management"
        ws.content = json.dumps(content)
    except Exception:
        pass

    ws.save(ignore_permissions=True)
    frappe.db.commit()
