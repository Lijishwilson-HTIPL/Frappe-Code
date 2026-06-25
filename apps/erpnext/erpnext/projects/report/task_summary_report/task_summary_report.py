import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Task"), "fieldname": "name", "fieldtype": "Link", "options": "Task", "width": 180},
		{"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 220},
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 90},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Data", "width": 150},
		{"label": _("Expected End Date"), "fieldname": "exp_end_date", "fieldtype": "Date", "width": 130},
		{"label": _("Completed On"), "fieldname": "completed_on", "fieldtype": "Date", "width": 120},
		{"label": _("Is Overdue"), "fieldname": "is_overdue", "fieldtype": "Check", "width": 90},
	]


def get_data(filters):
	task_filters = {}
	if filters.get("project"):
		task_filters["project"] = filters.project
	if filters.get("status"):
		task_filters["status"] = filters.status
	if filters.get("priority"):
		task_filters["priority"] = filters.priority

	tasks = frappe.get_all(
		"Task",
		filters=task_filters,
		fields=[
			"name", "subject", "project", "status", "priority",
			"exp_end_date", "completed_on",
		],
		order_by="status asc, priority desc, exp_end_date asc",
	)

	today = getdate(nowdate())
	for task in tasks:
		# Get assignees
		assigns = frappe.get_all(
			"ToDo",
			filters={"reference_type": "Task", "reference_name": task.name, "status": "Open"},
			fields=["allocated_to"],
		)
		task["assigned_to"] = ", ".join([a.allocated_to for a in assigns]) if assigns else ""
		task["is_overdue"] = (
			1
			if task.exp_end_date
			and getdate(task.exp_end_date) < today
			and task.status not in ("Completed", "Cancelled")
			else 0
		)

	return tasks
