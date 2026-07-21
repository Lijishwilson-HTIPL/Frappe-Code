# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

_MANAGER_ROLES = frozenset({"System Manager"})


class DMSTrainingSession(Document):

	@frappe.whitelist()
	def mark_attendance(self):
		"""Trainer or manager attests attendance for an instructor-led session.
		Attended employees are pushed into the linked Training Record as
		acknowledged — no employee e-signature is required here since the
		trainer is vouching for in-person attendance, not the employee
		self-certifying (see DMSTrainingRecord.sign_acknowledgement for that
		self-service flow)."""
		is_manager = bool(set(frappe.get_roles(frappe.session.user)) & _MANAGER_ROLES)
		if frappe.session.user != self.trainer and not is_manager:
			frappe.throw("Only the trainer or a System Manager can mark attendance for this session.")

		if not self.attendees:
			frappe.throw("Add at least one attendee before marking attendance.")

		trn = frappe.get_doc("DMS Training Record", self.training_record)
		updated = 0

		for attendee in self.attendees:
			if not attendee.attended:
				continue
			row = next((r for r in trn.employees if r.employee == attendee.employee), None)
			if not row:
				trn.append("employees", {
					"employee": attendee.employee,
					"employee_name": attendee.employee_name,
					"status": "Pending",
				})
				row = trn.employees[-1]
			if not row.acknowledged:
				row.acknowledged = 1
				row.acknowledged_on = now_datetime()
				updated += 1

		trn.save(ignore_permissions=True)
		self.status = "Completed"
		self.save(ignore_permissions=True)
		return {"updated": updated}
