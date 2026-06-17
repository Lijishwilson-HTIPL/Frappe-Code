import json

import frappe
from frappe import _
from frappe.utils import nowdate, date_diff


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Task ID"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Task",
			"width": 130,
		},
		{
			"label": _("Subject"),
			"fieldname": "subject",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150,
		},
		{
			"label": _("Assignee"),
			"fieldname": "assignee",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Priority"),
			"fieldname": "priority",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Due Date"),
			"fieldname": "exp_end_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Days Overdue"),
			"fieldname": "days_overdue",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Progress %"),
			"fieldname": "progress",
			"fieldtype": "Percent",
			"width": 110,
		},
		{
			"label": _("Time Logged (hrs)"),
			"fieldname": "actual_time",
			"fieldtype": "Float",
			"width": 140,
		},
	]


def get_data(filters):
	conditions, values = get_conditions(filters)

	tasks = frappe.db.sql(
		"""
		SELECT
			t.name,
			t.subject,
			t.project,
			t.status,
			t.priority,
			t.exp_end_date,
			t.progress,
			t.actual_time,
			t._assign
		FROM `tabTask` t
		WHERE t.docstatus < 2
		{conditions}
		ORDER BY
			CASE WHEN t.exp_end_date IS NULL THEN 1 ELSE 0 END,
			t.exp_end_date ASC,
			t.modified DESC
		""".format(conditions=conditions),
		values,
		as_dict=True,
	)

	if not tasks:
		return []

	task_names = [t.name for t in tasks]

	# Fallback source: Task Assignee child table
	assignee_rows = frappe.get_all(
		"Task Assignee",
		filters={"parenttype": "Task", "parent": ["in", task_names]},
		fields=["parent", "user"],
	)
	child_assignee_map = {}
	for row in assignee_rows:
		child_assignee_map.setdefault(row["parent"], []).append(row["user"])

	# Primary source: Frappe's built-in _assign field (JSON list of users)
	assign_field_map = {}
	for task in tasks:
		if task.get("_assign"):
			try:
				users = json.loads(task._assign) or []
				if users:
					assign_field_map[task.name] = users
			except Exception:
				pass

	# Get full names for all assignee users (from both sources)
	all_user_emails = list(
		{u for users in child_assignee_map.values() for u in users}
		| {u for users in assign_field_map.values() for u in users}
	)
	full_name_map = {}
	if all_user_emails:
		users = frappe.get_all(
			"User",
			filters={"name": ["in", all_user_emails]},
			fields=["name", "full_name"],
		)
		full_name_map = {u.name: u.full_name for u in users}

	# Filter by assignee if provided
	assignee_filter = filters.get("assignee")

	today = nowdate()
	data = []

	for task in tasks:
		assign_users = assign_field_map.get(task.name, [])
		child_users = child_assignee_map.get(task.name, [])

		# _assign is primary; child table is the fallback for display
		task_assignees = assign_users or child_users

		# assignee filter matches against the union of both sources
		if assignee_filter and assignee_filter not in set(assign_users) | set(child_users):
			continue

		assignee_display = (
			", ".join([full_name_map.get(u, u) for u in task_assignees])
			if task_assignees
			else "—"
		)

		days_overdue = 0
		if task.exp_end_date and task.status not in ["Completed", "Cancelled"]:
			diff = date_diff(today, str(task.exp_end_date))
			days_overdue = diff if diff > 0 else 0

		row = {
			"name": task.name,
			"subject": task.subject,
			"project": task.project or "",
			"assignee": assignee_display,
			"status": task.status,
			"priority": task.priority or "—",
			"exp_end_date": task.exp_end_date,
			"days_overdue": days_overdue if days_overdue > 0 else None,
			"progress": task.progress or 0,
			"actual_time": round(task.actual_time or 0, 2),
		}

		data.append(row)

	return data


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("project"):
		conditions.append("t.project = %(project)s")
		values["project"] = filters["project"]

	if filters.get("status"):
		conditions.append("t.status = %(status)s")
		values["status"] = filters["status"]

	if filters.get("priority"):
		conditions.append("t.priority = %(priority)s")
		values["priority"] = filters["priority"]

	if filters.get("from_date"):
		conditions.append("t.exp_end_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("t.exp_end_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	condition_str = ("AND " + " AND ".join(conditions)) if conditions else ""
	return condition_str, values
