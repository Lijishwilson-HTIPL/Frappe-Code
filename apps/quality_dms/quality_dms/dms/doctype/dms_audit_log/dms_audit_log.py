# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DMSAuditLog(Document):

	def validate(self):
		if not self.is_new():
			frappe.throw(
				"Audit log records are immutable and cannot be edited.",
				frappe.PermissionError,
			)

	def on_trash(self):
		frappe.throw(
			"Audit log records cannot be deleted.",
			frappe.PermissionError,
		)
