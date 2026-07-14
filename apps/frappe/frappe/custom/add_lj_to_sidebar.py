import frappe


def execute():
    # Check if already added
    existing = frappe.db.exists("Workspace Sidebar Item", {
        "parent": "CRM",
        "link_to": "leads-journey"
    })
    if existing:
        print(f"Leads Journey already in CRM sidebar: {existing}")
        return

    # Shift all items from idx 5 onwards up by 1
    # (Insert after Customer which is at idx 4, before Reports section at idx 5)
    frappe.db.sql("""
        UPDATE `tabWorkspace Sidebar Item`
        SET idx = idx + 1
        WHERE parent = 'CRM' AND idx >= 5
    """)

    # Insert Leads Journey at idx 5
    new_name = frappe.generate_hash(length=10)
    frappe.db.sql("""
        INSERT INTO `tabWorkspace Sidebar Item`
        (name, creation, modified, modified_by, owner, docstatus,
         parent, parentfield, parenttype, idx, type, label, link_to, link_type, icon)
        VALUES (%s, NOW(), NOW(), 'Administrator', 'Administrator', 0,
                'CRM', 'items', 'Workspace Sidebar', 5,
                'Link', 'Leads Journey', 'leads-journey', 'Page', 'fa fa-road')
    """, (new_name,))

    # Also update the modified timestamp on the Workspace Sidebar
    frappe.db.sql("UPDATE `tabWorkspace Sidebar` SET modified = NOW() WHERE name = 'CRM'")

    frappe.db.commit()
    print(f"Inserted Leads Journey at idx=5 in CRM Workspace Sidebar (name={new_name})")

    # Verify
    items = frappe.db.sql("""
        SELECT idx, type, label, link_to, link_type
        FROM `tabWorkspace Sidebar Item`
        WHERE parent = 'CRM' AND idx <= 8
        ORDER BY idx
    """, as_dict=True)
    print("\nTop CRM sidebar items:")
    for i in items:
        print(f"  [{i.idx}] {i.type} | {i.label} -> {i.link_to}")
