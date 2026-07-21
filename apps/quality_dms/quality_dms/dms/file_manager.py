# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime

DMS_FOLDER_NAME = "Quality DMS"


def get_or_create_folder(folder_name, parent_folder_name):
    """
    Get or create a folder in Frappe File Manager.
    Returns the File record *name* (not file_name) so it can be used as a Link value.
    """
    existing = frappe.db.get_value(
        "File",
        {"file_name": folder_name, "folder": parent_folder_name, "is_folder": 1},
        "name",
    )
    if existing:
        return existing

    folder_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": folder_name,
        "folder": parent_folder_name,
        "is_folder": 1,
        "is_private": 1,
    })
    folder_doc.insert(ignore_permissions=True)
    return folder_doc.name


def get_dms_root_folder():
    """Get or create the 'Quality DMS' root folder under Home."""
    return get_or_create_folder(DMS_FOLDER_NAME, "Home")


def get_category_folder(category):
    """Get or create a category sub-folder under Quality DMS. Falls back to root."""
    dms_root = get_dms_root_folder()
    if not category:
        return dms_root
    return get_or_create_folder(category, dms_root)


def rename_category_folder(old_name, new_name):
    """Rename a category folder in Frappe File Manager after a Document Category rename."""
    dms_root = get_dms_root_folder()
    folder_name = frappe.db.get_value(
        "File",
        {"file_name": old_name, "folder": dms_root, "is_folder": 1},
        "name",
    )
    if folder_name:
        frappe.db.set_value("File", folder_name, "file_name", new_name)


def organize_document_file(doc):
    """
    Move the document's attached file into its DMS category folder and populate file_doc.
    Safe to call on every save — only writes when the File record is found.
    Returns the File record name if found, else None.
    """
    if not doc.file:
        return None

    target_folder = get_category_folder(doc.category)

    # Look for File record attached to this Document Library record
    file_record = frappe.db.get_value(
        "File",
        {
            "file_url": doc.file,
            "attached_to_doctype": "Document Library",
            "attached_to_name": doc.name,
        },
        "name",
    )
    if not file_record:
        # Fall back: file uploaded without attachment context (e.g. bulk import)
        file_record = frappe.db.get_value("File", {"file_url": doc.file}, "name")

    if file_record:
        frappe.db.set_value(
            "File",
            file_record,
            {
                "folder": target_folder,
                "attached_to_doctype": "Document Library",
                "attached_to_name": doc.name,
                "is_private": 1,
            },
        )
        # Persist the explicit File link without re-triggering save hooks
        frappe.db.set_value("Document Library", doc.name, "file_doc", file_record)

    return file_record


def log_file_event(document_name, action, revision=None):
    """Insert a DMS Audit Log entry for a file-related event."""
    try:
        action_label = f"{action} (v{revision})" if revision else action
        frappe.get_doc({
            "doctype": "DMS Audit Log",
            "document": document_name,
            "action": action_label,
            "user": frappe.session.user,
            "timestamp": now_datetime(),
            "ip_address": getattr(frappe.local, "request_ip", ""),
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DMS: Failed to log file event")


def ensure_all_category_folders():
    """
    Bootstrap: ensure a File folder exists for every Document Category already in the system.
    Safe to call repeatedly — get_or_create_folder is idempotent.
    """
    categories = frappe.get_all("Document Category", pluck="name")
    for cat in categories:
        try:
            get_category_folder(cat)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"DMS: Could not create folder for category '{cat}'")
