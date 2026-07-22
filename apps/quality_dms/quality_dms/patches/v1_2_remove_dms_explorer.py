# Copyright (c) 2026, Quality Team and contributors
# Patch: Remove the custom DMS Explorer page from the database

import frappe


def execute():
    if frappe.db.exists("Page", "dms-explorer"):
        frappe.delete_doc("Page", "dms-explorer", force=True, ignore_missing=True)

    # Remove stale workspace links pointing to the deleted page
    for ws_name in ("DMS", "Quality DMS"):
        ws = frappe.db.get_value("Workspace", ws_name, "name")
        if not ws:
            continue
        frappe.db.delete(
            "Workspace Link",
            {"parent": ws_name, "link_to": "dms-explorer", "link_type": "Page"},
        )
        frappe.db.delete(
            "Workspace Shortcut",
            {"parent": ws_name, "link_to": "dms-explorer", "type": "Page"},
        )

    frappe.db.commit()
