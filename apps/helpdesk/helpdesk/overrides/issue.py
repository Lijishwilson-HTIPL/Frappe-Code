import frappe


# Map ERPNext Issue status → HD Ticket status
_STATUS_MAP = {
    "Resolved": "Resolved",
    "Closed": "Closed",
    "Open": None,       # don't revert HD Ticket to Open on reopen — let agents decide
    "On Hold": None,
    "Replied": None,
}

# RCA fields to sync from Issue → HD Ticket
_RCA_FIELDS = ["rca_root_cause", "rca_fix_workaround", "rca_prevention"]


def on_update(doc, method=None):
    """Sync Issue status and RCA fields back to the linked HD Ticket."""
    tickets = frappe.get_all(
        "HD Ticket",
        filters={"erp_issue": doc.name},
        fields=["name", "status"],
        limit=1,
    )
    if not tickets:
        return

    status_changed = doc.has_value_changed("status")
    rca_changed = any(doc.has_value_changed(f) for f in _RCA_FIELDS)

    if not status_changed and not rca_changed:
        return

    hd_ticket = frappe.get_doc("HD Ticket", tickets[0].name)
    changed = False

    # Sync status
    if status_changed:
        hd_status = _STATUS_MAP.get(doc.status)
        if hd_status and hd_ticket.status != hd_status:
            hd_ticket.status = hd_status
            changed = True

    # Sync RCA fields
    if rca_changed:
        for field in _RCA_FIELDS:
            issue_val = doc.get(field)
            if issue_val and issue_val != hd_ticket.get(field):
                hd_ticket.set(field, issue_val)
                changed = True
        # Auto-mark RCA in progress if they started filling it
        if hd_ticket.rca_required and hd_ticket.rca_status == "Pending":
            hd_ticket.rca_status = "In Progress"
            changed = True
        # Auto-complete RCA if all three fields are filled
        if (
            hd_ticket.rca_required
            and hd_ticket.rca_root_cause
            and hd_ticket.rca_fix_workaround
            and hd_ticket.rca_prevention
            and hd_ticket.rca_status != "Completed"
        ):
            hd_ticket.rca_status = "Completed"
            hd_ticket.rca_completed_on = frappe.utils.now()
            agent = frappe.db.get_value("HD Agent", frappe.session.user, "name")
            if agent:
                hd_ticket.rca_completed_by = agent
            changed = True

    if changed:
        hd_ticket.flags.from_issue_sync = True
        hd_ticket.save(ignore_permissions=True)
