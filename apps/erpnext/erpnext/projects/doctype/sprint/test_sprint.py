import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestSprint(FrappeTestCase):
	def make_project(self, project_name):
		existing = frappe.db.get_value("Project", {"project_name": project_name})
		if existing:
			return frappe.get_doc("Project", existing)
		return frappe.get_doc({"doctype": "Project", "project_name": project_name}).insert()

	def make_sprint(self, sprint_name, **kwargs):
		sprint = frappe.get_doc(
			{
				"doctype": "Sprint",
				"sprint_name": sprint_name,
				"start_date": nowdate(),
				"end_date": add_days(nowdate(), 14),
				**kwargs,
			}
		)
		return sprint

	def test_end_date_before_start_date_throws(self):
		sprint = self.make_sprint(
			"_Test Sprint Bad Dates",
			start_date=nowdate(),
			end_date=add_days(nowdate(), -1),
		)

		self.assertRaises(frappe.ValidationError, sprint.insert)

	def test_second_active_sprint_for_same_project_throws(self):
		project = self.make_project("_Test Sprint Project")

		self.make_sprint(
			"_Test Sprint Active 1", project=project.name, status="Active"
		).insert()

		second = self.make_sprint(
			"_Test Sprint Active 2", project=project.name, status="Active"
		)

		self.assertRaises(frappe.ValidationError, second.insert)
