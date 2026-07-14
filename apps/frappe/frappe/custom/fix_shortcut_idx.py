import frappe

def execute():
    # Reorder CRM shortcuts: Lead(1), Leads Journey(2), Opportunity(3), Customer(4), Sales Analytics(5), Dashboard(6), CRM Dashboard(7)
    order = [
        ("crcna20iuq", 1),   # Lead
        ("lj-shortcut-26f56d71", 2),  # Leads Journey
        ("crck4tjujc", 3),   # Opportunity
        ("crci2agrd8", 4),   # Customer
        ("crc9egqjlp", 5),   # Sales Analytics
        ("crcmogqsj9", 6),   # Dashboard
        ("crcmoi1n36", 7),   # CRM Dashboard
    ]
    for name, idx in order:
        frappe.db.set_value("Workspace Shortcut", name, "idx", idx, update_modified=False)

    frappe.db.commit()
    print("Reordered. Verifying:")
    rows = frappe.db.sql("SELECT name, label, idx FROM `tabWorkspace Shortcut` WHERE parent='CRM' ORDER BY idx", as_dict=True)
    for r in rows:
        print(f"  {r.idx}: {r.label}")
