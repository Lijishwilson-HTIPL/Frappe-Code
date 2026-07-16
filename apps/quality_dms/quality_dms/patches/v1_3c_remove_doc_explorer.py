import frappe


def execute():
    for ws_name in ("DMS", "Quality DMS"):
        if not frappe.db.exists("Workspace", ws_name):
            continue
        ws = frappe.get_doc("Workspace", ws_name)
        ws.links = [
            l for l in ws.links
            if l.link_to != "dms-explorer" and l.label != "Document Explorer"
        ]
        ws.shortcuts = [
            s for s in ws.shortcuts
            if s.link_to != "dms-explorer" and s.label != "Document Explorer"
        ]
        ws.save(ignore_permissions=True)

    frappe.db.commit()
