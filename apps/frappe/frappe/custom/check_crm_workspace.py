import frappe

def execute():
    ws = frappe.get_doc("Workspace", "CRM")
    print(f"Workspace: {ws.name}")
    for l in ws.links:
        print(f"  [{l.idx}] type={l.type} link_type={l.link_type} link_to={l.link_to} label={l.label}")
