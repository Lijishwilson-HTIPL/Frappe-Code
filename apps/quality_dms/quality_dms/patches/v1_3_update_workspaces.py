# Copyright (c) 2026, Quality Team and contributors
# Patch: Directly update DMS workspace records in the database
# - Remove Document Explorer from both workspaces
# - Replace Folder Management with File Storage in Quality DMS workspace
# - Add File Storage shortcut and link to DMS workspace

import json
import frappe


def execute():
    _patch_dms_workspace()
    frappe.db.commit()


def _patch_dms_workspace():
    if not frappe.db.exists("Workspace", "DMS"):
        return

    ws = frappe.get_doc("Workspace", "DMS")

    # ── Remove Document Explorer from links ──────────────────────────────────
    ws.links = [
        l for l in ws.links
        if not (l.link_to == "dms-explorer" or l.label == "Document Explorer")
    ]

    # ── Remove Document Explorer from shortcuts ──────────────────────────────
    ws.shortcuts = [
        s for s in ws.shortcuts
        if not (s.link_to == "dms-explorer" or s.label == "Document Explorer")
    ]

    # ── Add File Storage link ────────────────────────────────────────────────
    has_file_link = any(l.link_to == "File" and l.label == "File Storage" for l in ws.links)
    if not has_file_link:
        ws.append("links", {
            "hidden": 0,
            "icon": "folder-open",
            "is_query_report": 0,
            "label": "File Storage",
            "link_to": "File",
            "link_type": "DocType",
            "onboard": 0,
            "type": "Link",
        })

    # ── Add File Storage shortcut ────────────────────────────────────────────
    has_file_sc = any(s.label == "File Storage" for s in ws.shortcuts)
    if not has_file_sc:
        ws.append("shortcuts", {
            "doc_view": "",
            "label": "File Storage",
            "link_to": "File",
            "type": "DocType",
        })

    # ── Update content JSON ──────────────────────────────────────────────────
    try:
        content = json.loads(ws.content or "[]")
        content = [
            b for b in content
            if not (
                b.get("type") == "shortcut"
                and b.get("data", {}).get("shortcut_name") == "Document Explorer"
            )
        ]
        if not any(
            b.get("type") == "shortcut"
            and b.get("data", {}).get("shortcut_name") == "File Storage"
            for b in content
        ):
            content.append({
                "id": "file-storage-01",
                "type": "shortcut",
                "data": {"shortcut_name": "File Storage", "col": 4},
            })
        ws.content = json.dumps(content)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DMS Patch: Could not update DMS content JSON")

    ws.save(ignore_permissions=True)


def _patch_quality_dms_workspace():
    if not frappe.db.exists("Workspace", "Quality DMS"):
        return

    ws = frappe.get_doc("Workspace", "Quality DMS")

    # ── Rename Folder Management → File Storage ──────────────────────────────
    for link in ws.links:
        if link.type == "Card Break" and link.label == "Folder Management":
            link.label = "File Storage"
            link.icon = "folder-open"

    # ── Add File link under File Storage card ────────────────────────────────
    has_file_link = any(l.link_to == "File" for l in ws.links)
    if not has_file_link:
        ws.append("links", {
            "hidden": 0,
            "is_query_report": 0,
            "label": "File Manager",
            "link_to": "File",
            "link_type": "DocType",
            "onboard": 0,
            "type": "Link",
        })

    # ── Update content JSON ──────────────────────────────────────────────────
    try:
        content = json.loads(ws.content or "[]")
        for block in content:
            if (
                block.get("type") == "card"
                and block.get("data", {}).get("card_name") == "Folder Management"
            ):
                block["data"]["card_name"] = "File Storage"
        ws.content = json.dumps(content)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DMS Patch: Could not update Quality DMS content JSON")

    ws.save(ignore_permissions=True)
