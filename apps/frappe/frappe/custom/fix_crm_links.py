import frappe
import json


def execute():
    # Fix duplicate idx in Workspace Link and ensure Leads Journey is there
    links = frappe.db.sql("""
        SELECT name, label, link_type, link_to, idx, type
        FROM `tabWorkspace Link`
        WHERE parent = 'CRM'
        ORDER BY idx, name
    """, as_dict=True)

    print("Current links:")
    for l in links:
        print(f"  [{l.idx}] {l.type} | {l.label} -> {l.link_to}")

    # Remove any duplicate leads-journey links
    lj_links = [l for l in links if l.link_to == 'leads-journey']
    for l in lj_links:
        frappe.db.delete("Workspace Link", l.name)
        print(f"Removed old: {l.name}")

    # Re-fetch and reindex cleanly, inserting Leads Journey after Opportunity (idx 25 area)
    links = frappe.db.sql("""
        SELECT name, label, link_type, link_to, idx, type
        FROM `tabWorkspace Link`
        WHERE parent = 'CRM'
        ORDER BY idx, name
    """, as_dict=True)

    # Find Opportunity link to insert after it
    opp_name = None
    opp_idx = None
    for l in links:
        if l.link_to == 'Opportunity' and l.link_type == 'DocType':
            opp_name = l.name
            opp_idx = l.idx
            break

    insert_at = (opp_idx or 25) + 1

    # Shift everything from insert_at onwards up by 1
    frappe.db.sql("""
        UPDATE `tabWorkspace Link`
        SET idx = idx + 1
        WHERE parent = 'CRM' AND idx >= %s
    """, (insert_at,))

    # Insert new link
    new_name = "lj-link-" + frappe.generate_hash(length=8)
    frappe.db.sql("""
        INSERT INTO `tabWorkspace Link`
        (name, creation, modified, modified_by, owner, docstatus, parent, parentfield, parenttype,
         idx, type, label, link_type, link_to, icon)
        VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator', 0,
                'CRM', 'links', 'Workspace', %s, 'Link', 'Leads Journey', 'Page', 'leads-journey', 'fa fa-road')
    """, (new_name, insert_at))

    frappe.db.commit()

    # Also update content JSON to add nav shortcut
    ws = frappe.get_doc("Workspace", "CRM")
    content = json.loads(ws.content or "[]")
    existing_shortcuts = [b['data'].get('shortcut_name') for b in content if b.get('type') == 'shortcut']

    if 'Leads Journey' not in existing_shortcuts:
        # Find Lead shortcut and insert after
        for i, block in enumerate(content):
            if block.get('type') == 'shortcut' and block['data'].get('shortcut_name') == 'Lead':
                content.insert(i + 1, {
                    "id": "lj-" + frappe.generate_hash(length=6),
                    "type": "shortcut",
                    "data": {"shortcut_name": "Leads Journey", "col": 3}
                })
                break
        frappe.db.set_value("Workspace", "CRM", "content", json.dumps(content), update_modified=False)
        frappe.db.commit()
        print("Added to content JSON")

    print("\nFinal links:")
    links = frappe.db.sql("""
        SELECT label, link_type, link_to, idx, type
        FROM `tabWorkspace Link`
        WHERE parent = 'CRM'
        ORDER BY idx
    """, as_dict=True)
    for l in links:
        print(f"  [{l.idx}] {l.type} | {l.label} -> {l.link_to}")
