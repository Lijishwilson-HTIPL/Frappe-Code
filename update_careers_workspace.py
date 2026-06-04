import frappe

def update():
    # Update Careers workspace: move from Frappe CRM to HR
    frappe.db.set_value("Workspace", "Careers", {
        "parent_page": "HR",
        "module": "HR"
    })

    # Remove careers section from Frappe CRM workspace content
    crm_ws = frappe.get_doc("Workspace", "Frappe CRM")
    import json
    content = json.loads(crm_ws.content)
    content = [block for block in content if not (
        block.get("type") == "card" and block.get("data", {}).get("card_name") == "Career Inquiries"
    ) and not (
        block.get("type") == "header" and "CAREERS" in block.get("data", {}).get("text", "").upper()
    )]
    crm_ws.content = json.dumps(content)

    # Remove career links from CRM workspace
    crm_ws.links = [l for l in crm_ws.links if "career" not in l.get("label", "").lower() and "career" not in (l.get("link_to") or "").lower()]

    crm_ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("Done. Careers moved to HR.")

update()
