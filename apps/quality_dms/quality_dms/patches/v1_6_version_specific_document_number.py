# Copyright (c) 2026, Quality Team and contributors
"""Migrate to the permanent-Document-ID + version-specific-Document-Number model.

Before: `Document Library.document_number` was one constant value per document
(seeded from the record name) and Document Revision rows carried no number.

After: the record's `name` is the permanent Document ID; `document_number` holds
the CURRENT published version's version-specific number; and every Document
Revision (released version) carries its own `document_number`.

This migration is intentionally NON-DESTRUCTIVE and preserves existing numbers
(per the agreed decision to leave historical numbers as-is):

  1. Backfill each existing Document Revision's `document_number` from its parent
     document's current number, and stamp effective_date / approval_status.
  2. Ensure every Document Library has at least one Document Revision (its current
     version) so nothing is left without a version record.

Existing Document IDs (names) and existing document_number values are untouched.
"""

import frappe
from frappe.utils import today


def execute():
    if not frappe.db.exists("DocType", "Document Library"):
        return

    docs = frappe.get_all(
        "Document Library",
        fields=["name", "version", "document_number", "status", "file", "file_doc", "effective_date"],
    )

    for d in docs:
        current_number = d.document_number or d.name  # legacy fallback
        version = d.version or "1.0"

        existing_rev = frappe.db.get_value(
            "Document Revision", {"document": d.name, "version": version}, "name"
        )

        if existing_rev:
            # Backfill the new fields on the existing version row only where empty.
            updates = {}
            if not frappe.db.get_value("Document Revision", existing_rev, "document_number"):
                updates["document_number"] = current_number
            if not frappe.db.get_value("Document Revision", existing_rev, "effective_date"):
                updates["effective_date"] = d.effective_date or today()
            if not frappe.db.get_value("Document Revision", existing_rev, "approval_status"):
                updates["approval_status"] = d.status or "Published"
            if updates:
                frappe.db.set_value("Document Revision", existing_rev, updates, update_modified=False)
        else:
            # No version row yet — create one representing the document's current version.
            try:
                frappe.get_doc({
                    "doctype": "Document Revision",
                    "document": d.name,
                    "version": version,
                    "document_number": current_number,
                    "change_log": "Version 1 record created during numbering migration.",
                    "file": d.file,
                    "file_doc": d.file_doc,
                    "revision_date": today(),
                    "effective_date": d.effective_date or today(),
                    "approval_status": d.status or "Published",
                }).insert(ignore_permissions=True)
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"DMS v1_6 migration: could not create Version record for {d.name}",
                )

        # Also backfill any OTHER existing revision rows for this document that still
        # lack a number (older multi-version data shared one number under the old model).
        stray = frappe.get_all(
            "Document Revision",
            filters={"document": d.name, "document_number": ["in", [None, ""]]},
            pluck="name",
        )
        for rev_name in stray:
            frappe.db.set_value("Document Revision", rev_name, "document_number", current_number,
                                update_modified=False)

    frappe.db.commit()
