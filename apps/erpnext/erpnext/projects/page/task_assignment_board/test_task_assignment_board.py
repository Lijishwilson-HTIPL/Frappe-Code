import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, today

from erpnext.projects.page.task_assignment_board.task_assignment_board import (
	get_board_data,
	reassign_task,
	update_task_status,
)


class TestTaskAssignmentBoard(FrappeTestCase):
	def make_project(self, project_name):
		existing = frappe.db.get_value("Project", {"project_name": project_name})
		if existing:
			return frappe.get_doc("Project", existing)
		return frappe.get_doc({"doctype": "Project", "project_name": project_name}).insert()

	def make_task(self, subject, project=None, status="Open"):
		return frappe.get_doc(
			{
				"doctype": "Task",
				"subject": subject,
				"project": project,
				"status": status,
			}
		).insert()

	def test_get_board_data_respects_project_filter(self):
		project_a = self.make_project("_Test Board Project A")
		project_b = self.make_project("_Test Board Project B")
		task_in = self.make_task("_Test Board Task In", project=project_a.name)
		task_out = self.make_task("_Test Board Task Out", project=project_b.name)

		data = get_board_data(project=project_a.name)
		names = [t["name"] for t in data["tasks"]]

		self.assertIn(task_in.name, names)
		self.assertNotIn(task_out.name, names)

	def test_update_task_status_rejects_invalid_status(self):
		task = self.make_task("_Test Board Invalid Status Task")

		self.assertRaises(frappe.ValidationError, update_task_status, task.name, "Bogus Status")

	def test_update_task_status_rejects_template(self):
		task = self.make_task("_Test Board Template Status Task")

		self.assertRaises(frappe.ValidationError, update_task_status, task.name, "Template")

	def test_update_task_status_completed_sets_completion_fields(self):
		task = self.make_task("_Test Board Complete Task")

		update_task_status(task.name, "Completed")
		task.reload()

		self.assertEqual(task.status, "Completed")
		self.assertEqual(task.completed_by, frappe.session.user)
		self.assertEqual(getdate(task.completed_on), getdate(today()))

	def test_reassign_task_with_nonexistent_user_throws(self):
		task = self.make_task("_Test Board Reassign Task")

		self.assertRaises(
			frappe.ValidationError, reassign_task, task.name, "no-such-user@example.invalid"
		)
