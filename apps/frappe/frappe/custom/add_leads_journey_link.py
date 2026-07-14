import frappe


def execute():
    # Add Leads Journey to the CRM workspace sidebar
    workspace_name = "CRM"
    if not frappe.db.exists("Workspace", workspace_name):
        print(f"Workspace '{workspace_name}' not found")
        # List available workspaces
        ws = frappe.get_all("Workspace", pluck="name")
        print("Available:", ws)
        return

    ws = frappe.get_doc("Workspace", workspace_name)

    # Check if already added
    existing = [l.link_to for l in ws.links if l.link_type == "Page"]
    if "leads-journey" in existing:
        print("Already added")
        return

    # Find position after Leads link
    leads_idx = None
    for i, l in enumerate(ws.links):
        if l.link_to == "Lead" and l.link_type == "DocType":
            leads_idx = i
            break

    # Get max idx in workspace links
    max_idx = frappe.db.get_value(
        "Workspace Link", {"parent": workspace_name}, "idx", order_by="idx desc"
    ) or 0

    insert_idx = (leads_idx + 2) if leads_idx is not None else (max_idx + 1)

    frappe.db.sql("""
        INSERT INTO `tabWorkspace Link`
        (name, creation, modified, modified_by, owner, docstatus, parent, parentfield, parenttype,
         idx, type, label, link_type, link_to, icon)
        VALUES (
            %(name)s, NOW(), NOW(), 'Administrator', 'Administrator', 0,
            %(parent)s, 'links', 'Workspace',
            %(idx)s, 'Link', 'Leads Journey', 'Page', 'leads-journey', 'fa fa-road'
        )
    """, {
        "name": "leads-journey-link-" + frappe.generate_hash(length=8),
        "parent": workspace_name,
        "idx": insert_idx,
    })

    frappe.db.commit()
    print("Added Leads Journey to CRM workspace")
