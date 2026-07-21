# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DMSCurriculum(Document):

	def assign_to_employee(self, employee):
		"""Ensure a DMS Training Record exists (tagged with this curriculum) for
		every document in this curriculum, and assign the given employee to
		each one. Reuses an existing Training Record for the document's current
		version if one already exists, instead of creating a duplicate."""
		results = []
		for row in self.documents:
			trn_name = frappe.db.get_value(
				"DMS Training Record",
				{"document": row.document, "curriculum": ["in", [self.name, None, ""]]},
				"name",
				order_by="creation desc",
			)
			if trn_name:
				trn = frappe.get_doc("DMS Training Record", trn_name)
				if not trn.curriculum:
					trn.curriculum = self.name
			else:
				version = frappe.db.get_value("Document Library", row.document, "version") or "1.0"
				trn = frappe.get_doc({
					"doctype": "DMS Training Record",
					"document": row.document,
					"version": version,
					"status": "Draft",
					"curriculum": self.name,
				})
				trn.insert(ignore_permissions=True)

			try:
				trn._assign_employees([employee])
				results.append(trn.name)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					f"DMS Curriculum: failed to assign {employee} to {trn.name}",
				)
		return results
