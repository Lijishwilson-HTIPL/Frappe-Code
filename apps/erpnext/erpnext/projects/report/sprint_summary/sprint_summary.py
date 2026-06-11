import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Sprint"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Sprint",
			"width": 140,
		},
		{
			"label": _("Sprint Name"),
			"fieldname": "sprint_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Total Tasks"),
			"fieldname": "total_tasks",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"label": _("Completed Tasks"),
			"fieldname": "completed_tasks",
			"fieldtype": "Int",
			"width": 130,
		},
		{
			"label": _("% Complete"),
			"fieldname": "percent_complete",
			"fieldtype": "Percent",
			"width": 110,
		},
	]


def get_data(filters):
	sprint_filters = {}
	if filters.get("project"):
		sprint_filters["project"] = filters["project"]
	if filters.get("status"):
		sprint_filters["status"] = filters["status"]

	sprints = frappe.get_list(
		"Sprint",
		filters=sprint_filters,
		fields=["name", "sprint_name", "project", "status", "start_date", "end_date"],
		order_by="start_date desc, name desc",
	)

	if not sprints:
		return []

	sprint_names = [s.name for s in sprints]

	task_counts = frappe.db.sql(
		"""
		SELECT
			sprint,
			COUNT(name) AS total_tasks,
			SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks
		FROM `tabTask`
		WHERE sprint IN %(sprints)s
		GROUP BY sprint
		""",
		{"sprints": sprint_names},
		as_dict=True,
	)
	count_map = {row.sprint: row for row in task_counts}

	data = []
	for sprint in sprints:
		counts = count_map.get(sprint.name)
		total = int(counts.total_tasks) if counts else 0
		completed = int(counts.completed_tasks or 0) if counts else 0
		percent_complete = round(completed / total * 100, 1) if total else 0

		data.append(
			{
				"name": sprint.name,
				"sprint_name": sprint.sprint_name,
				"project": sprint.project or "",
				"status": sprint.status,
				"start_date": sprint.start_date,
				"end_date": sprint.end_date,
				"total_tasks": total,
				"completed_tasks": completed,
				"percent_complete": percent_complete,
			}
		)

	return data
