# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DocumentCategory(Document):
	pass


def create_file_folder(doc, method=None):
	"""Create (or ensure) a matching folder in Frappe File Manager for this category."""
	try:
		from quality_dms.dms.file_manager import get_category_folder
		get_category_folder(doc.name)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"DMS: Could not create File folder for category '{doc.name}'",
		)
