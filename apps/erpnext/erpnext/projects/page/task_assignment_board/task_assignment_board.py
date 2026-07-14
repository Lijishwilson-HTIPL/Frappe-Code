import frappe
from frappe.desk.form import assign_to


@frappe.whitelist()
def get_task_data(project=None):
	task_filters = {"status": ["not in", ["Cancelled", "Completed"]]}
	if project:
		task_filters["project"] = project

	tasks = frappe.get_all(
		"Task",
		filters=task_filters,
		fields=["name", "subject", "status", "project", "priority", "exp_end_date"],
		order_by="priority desc, exp_end_date asc",
	)

	for task in tasks:
		assigns = frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Task",
				"reference_name": task.name,
				"status": "Open",
			},
			fields=["allocated_to"],
		)
		task["assigned_to"] = [a.allocated_to for a in assigns]

	projects = frappe.get_all(
		"Project", filters={"status": "Open"}, fields=["name"], order_by="name"
	)

	return {"tasks": tasks, "projects": [p.name for p in projects]}


@frappe.whitelist()
def reassign_task(task_name, from_user, to_user):
	# Remove old assignment
	if from_user:
		todos = frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Task",
				"reference_name": task_name,
				"allocated_to": from_user,
				"status": "Open",
			},
			fields=["name"],
		)
		for todo in todos:
			frappe.db.set_value("ToDo", todo.name, "status", "Cancelled")

	# Add new assignment
	if to_user:
		assign_to.add({
			"assign_to": [to_user],
			"doctype": "Task",
			"name": task_name,
			"description": frappe.db.get_value("Task", task_name, "subject"),
		})

	frappe.db.commit()
	return True
