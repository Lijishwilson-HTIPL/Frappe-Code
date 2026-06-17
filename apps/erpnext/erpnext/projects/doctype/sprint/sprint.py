import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class Sprint(Document):
	def validate(self):
		self.validate_dates()
		self.validate_single_active_sprint_per_project()

	def validate_dates(self):
		if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("End Date cannot be before Start Date"))

	def validate_single_active_sprint_per_project(self):
		if self.status != "Active" or not self.project:
			return

		other_active = frappe.db.exists(
			"Sprint",
			{
				"project": self.project,
				"status": "Active",
				"name": ["!=", self.name],
			},
		)
		if other_active:
			frappe.throw(
				_("Another Active Sprint {0} already exists for Project {1}.").format(
					frappe.bold(other_active), frappe.bold(self.project)
				)
			)
