import frappe

def execute():
    rows = frappe.db.sql("""
        SELECT name, type, label, link_to, idx, parentfield
        FROM `tabWorkspace Shortcut`
        WHERE parent = 'CRM'
        ORDER BY idx
    """, as_dict=True)
    print("Workspace Shortcut rows for CRM:")
    for r in rows:
        print(f"  {r}")
