# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt
"""Quality Document Workflow — the signable publish lifecycle for Document Library.

Created programmatically (and idempotently) so every install — a fresh site and
the live server — gets the workflow via `bench migrate`. Without it, Document
Library falls back to the raw docstatus Submit button and the DMS e-signature
(bound to workflow actions in document_library.js `before_workflow_action`)
never fires.

This mirrors the reference workflow running on the primary site: it drives the
`workflow_state` field, and each state's `update_field`/`update_value` also syncs
the `status` field (Pending Review -> "Review", Pending Approval -> "Approved",
etc.) so the permission logic (get_permission_query_conditions / has_permission
check status IN Review/Approved/Published) and the number cards stay consistent.
"""

import frappe

WORKFLOW_NAME = "Quality Document Workflow"
DOCTYPE = "Document Library"
STATE_FIELD = "workflow_state"

ACTIONS = [
    "Submit for Review",
    "Approve Review",
    "Request Changes",
    "Publish Document",
    "Reject Document",
    "Mark as Obsolete",
    "Archive",
]

# workflow_state -> (doc_status, status-field value it syncs to, style)
STATES = {
    "Draft":            (0, "Draft",     "Warning"),
    "Pending Review":   (0, "Review",    "Warning"),
    "Pending Approval": (0, "Approved",  "Info"),
    "Published":        (1, "Published", "Success"),
    "Obsolete":         (2, "Obsolete",  "Danger"),
    "Archived":         (2, "Archived",  "Inverse"),
    "Rejected":         (0, "Rejected",  "Danger"),
}
ALLOW_EDIT = "Desk User"

# (from_state, action, next_state, [allowed roles]) — one Workflow Transition row per role
TRANSITIONS = [
    ("Draft",            "Submit for Review", "Pending Review",   ["Employee", "System Manager"]),
    ("Pending Review",   "Approve Review",    "Pending Approval", ["System Manager"]),
    ("Pending Review",   "Request Changes",   "Rejected",         ["System Manager"]),
    ("Pending Approval", "Publish Document",  "Published",        ["System Manager"]),
    ("Pending Approval", "Reject Document",   "Rejected",         ["System Manager"]),
    ("Rejected",         "Submit for Review", "Pending Review",   ["Employee", "System Manager"]),
    ("Published",        "Mark as Obsolete",  "Obsolete",         ["System Manager"]),
    ("Published",        "Archive",           "Archived",         ["System Manager"]),
]


def setup_quality_document_workflow():
    """Idempotently (re)create the Quality Document Workflow to match the
    reference site. Safe to run repeatedly (called from the migration patch)."""
    if not frappe.db.exists("DocType", DOCTYPE):
        return

    for action in ACTIONS:
        if not frappe.db.exists("Workflow Action Master", action):
            frappe.get_doc({
                "doctype": "Workflow Action Master",
                "workflow_action_name": action,
            }).insert(ignore_permissions=True)

    for state, (_ds, _sv, style) in STATES.items():
        if not frappe.db.exists("Workflow State", state):
            frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": state,
                "style": style,
            }).insert(ignore_permissions=True)

    # Recreate the workflow so edits always apply cleanly.
    if frappe.db.exists("Workflow", WORKFLOW_NAME):
        frappe.delete_doc("Workflow", WORKFLOW_NAME, force=1, ignore_permissions=True)

    wf = frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": WORKFLOW_NAME,
        "document_type": DOCTYPE,
        "workflow_state_field": STATE_FIELD,
        "is_active": 1,
        "send_email_alert": 1,
        "states": [
            {
                "state": state,
                "doc_status": doc_status,
                "allow_edit": ALLOW_EDIT,
                "update_field": "status",
                "update_value": status_value,
            }
            for state, (doc_status, status_value, _style) in STATES.items()
        ],
        "transitions": [
            {"state": s, "action": action, "next_state": ns, "allowed": role}
            for (s, action, ns, roles) in TRANSITIONS
            for role in roles
        ],
    })
    wf.insert(ignore_permissions=True)
    frappe.db.commit()
