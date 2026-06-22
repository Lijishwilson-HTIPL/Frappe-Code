import frappe


def execute():
    # Check Workspace Sidebar doctypes
    sidebars = frappe.db.sql("SELECT name FROM `tabWorkspace Sidebar` ORDER BY name", as_dict=True)
    print(f"Workspace Sidebars: {[s.name for s in sidebars]}")

    # Check if CRM has a sidebar
    crm_sidebar = frappe.db.exists("Workspace Sidebar", "CRM")
    print(f"CRM Workspace Sidebar exists: {crm_sidebar}")

    if crm_sidebar:
        items = frappe.db.sql("""
            SELECT label, type, link_to, link_type, idx
            FROM `tabWorkspace Sidebar Item`
            WHERE parent = 'CRM'
            ORDER BY idx
        """, as_dict=True)
        print(f"\nCRM Sidebar Items ({len(items)}):")
        for i in items:
            print(f"  [{i.idx}] {i.type} | {i.label} -> {i.link_to} (link_type={i.link_type})")

    # Check the auto_generate function to understand what module it uses for CRM
    ws = frappe.db.get_value("Workspace", "CRM", ["module", "name"], as_dict=True)
    print(f"\nCRM Workspace module: {ws}")
