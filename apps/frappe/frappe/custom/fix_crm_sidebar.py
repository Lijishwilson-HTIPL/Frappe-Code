import frappe


def execute():
    ws = frappe.get_doc("Workspace", "CRM")

    # Show current shortcuts
    print("Current shortcuts:")
    for s in ws.shortcuts:
        print(f"  [{s.idx}] type={s.type} link_to={s.link_to} label={s.label}")

    # Check if already added
    existing = [s.link_to for s in ws.shortcuts if s.type == "Page"]
    if "leads-journey" in existing:
        print("Already in shortcuts")
        return

    # Find Lead shortcut position
    lead_idx = None
    for i, s in enumerate(ws.shortcuts):
        if s.link_to == "Lead":
            lead_idx = i
            break

    # Insert via direct DB (bypass link validation)
    max_idx = max((s.idx for s in ws.shortcuts), default=0)
    insert_idx = (ws.shortcuts[lead_idx].idx + 1) if lead_idx is not None else (max_idx + 1)

    frappe.db.sql("""
        INSERT INTO `tabWorkspace Shortcut`
        (name, creation, modified, modified_by, owner, docstatus, parent, parentfield, parenttype,
         idx, type, label, link_to, color)
        VALUES (
            %(name)s, NOW(), NOW(), 'Administrator', 'Administrator', 0,
            'CRM', 'shortcuts', 'Workspace',
            %(idx)s, 'Page', 'Leads Journey', 'leads-journey', 'Purple'
        )
    """, {
        "name": "lj-shortcut-" + frappe.generate_hash(length=8),
        "idx": insert_idx,
    })

    frappe.db.commit()
    print(f"Added 'Leads Journey' shortcut to CRM sidebar at idx {insert_idx}")
