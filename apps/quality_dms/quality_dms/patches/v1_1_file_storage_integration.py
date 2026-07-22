# Copyright (c) 2026, Quality Team and contributors
# Patch: Integrate Frappe File Storage into DMS
# - Ensure Quality DMS folder structure exists in File Manager
# - Back-fill file_doc on existing Document Library records

import frappe


def execute():
	# 1. Bootstrap the DMS folder structure for all existing categories
	try:
		from quality_dms.dms.file_manager import ensure_all_category_folders
		ensure_all_category_folders()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "DMS Patch: Failed to bootstrap category folders")

	# 2. Back-fill file_doc on existing Document Library records that have a file
	records = frappe.get_all(
		"Document Library",
		filters={"file": ("is", "set"), "file_doc": ("is", "not set")},
		fields=["name", "file", "category"],
	)

	for rec in records:
		try:
			file_record = frappe.db.get_value(
				"File",
				{
					"file_url": rec.file,
					"attached_to_doctype": "Document Library",
					"attached_to_name": rec.name,
				},
				"name",
			)
			if not file_record:
				file_record = frappe.db.get_value("File", {"file_url": rec.file}, "name")

			if file_record:
				from quality_dms.dms.file_manager import get_category_folder
				target_folder = get_category_folder(rec.category)
				frappe.db.set_value("File", file_record, {
					"folder": target_folder,
					"attached_to_doctype": "Document Library",
					"attached_to_name": rec.name,
					"is_private": 1,
				})
				frappe.db.set_value("Document Library", rec.name, "file_doc", file_record)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"DMS Patch: Could not back-fill file_doc for {rec.name}",
			)

	# 3. Back-fill file_doc on existing Document Revision records
	revisions = frappe.get_all(
		"Document Revision",
		filters={"file": ("is", "set"), "file_doc": ("is", "not set")},
		fields=["name", "file"],
	)

	for rev in revisions:
		try:
			file_record = frappe.db.get_value("File", {"file_url": rev.file}, "name")
			if file_record:
				frappe.db.set_value("Document Revision", rev.name, "file_doc", file_record)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"DMS Patch: Could not back-fill file_doc for revision {rev.name}",
			)

	frappe.db.commit()
