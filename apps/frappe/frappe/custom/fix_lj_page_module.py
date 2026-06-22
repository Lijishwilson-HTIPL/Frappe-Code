import frappe


def execute():
    # Update leads-journey page module from Crm Unify to CRM
    result = frappe.db.sql("""
        UPDATE `tabPage`
        SET module = 'CRM', modified = NOW()
        WHERE name = 'leads-journey'
    """)
    frappe.db.commit()
    print("Updated leads-journey page module to CRM")

    # Verify
    page = frappe.db.get_value("Page", "leads-journey", ["name", "module", "title"], as_dict=True)
    print(f"Page now: {page}")

    # Also check workspace shortcuts to ensure leads-journey is listed
    shortcuts = frappe.db.sql("""
        SELECT name, label, link_to, type
        FROM `tabWorkspace Shortcut`
        WHERE parent = 'CRM'
        ORDER BY idx
    """, as_dict=True)
    print(f"\nCRM Workspace shortcuts ({len(shortcuts)}):")
    for s in shortcuts:
        print(f"  {s.label} -> {s.link_to} ({s.type})")
