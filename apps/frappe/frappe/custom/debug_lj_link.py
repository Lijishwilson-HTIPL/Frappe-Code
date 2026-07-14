import frappe
import json


def execute():
    # Check links table for CRM workspace
    links = frappe.db.sql("""
        SELECT name, label, type, link_type, link_to, idx
        FROM `tabWorkspace Link`
        WHERE parent = 'CRM'
        ORDER BY idx
    """, as_dict=True)

    print(f"Total links: {len(links)}")
    for l in links:
        marker = " <-- LEADS JOURNEY" if l.link_to == 'leads-journey' else ""
        print(f"  [{l.idx}] {l.type} | {l.label} -> {l.link_to} (link_type={l.link_type}){marker}")

    # Check if workspace is public
    ws = frappe.db.get_value("Workspace", "CRM", ["is_hidden", "public", "for_user"], as_dict=True)
    print(f"\nWorkspace CRM: {ws}")

    # Rebuild the sidebar item to see what Python gets
    from frappe.desk.desktop import get_workspace_sidebar_items
    items = get_workspace_sidebar_items()
    crm = None
    for item in (items.get('pages') or []):
        if item.get('name') == 'CRM':
            crm = item
            break
    print(f"\nSidebar items count: {len(items.get('pages', []))}")
    print(f"CRM in sidebar items: {crm is not None}")
