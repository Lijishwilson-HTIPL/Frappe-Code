import json

import frappe
from frappe import _
from frappe.utils import escape_html, today

# "Template" is intentionally excluded: template tasks must not be managed via the board.
VALID_STATUSES = {"Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled"}


@frappe.whitelist()
def get_board_data(project=None, status=None, show_completed=0, sprint=None, department=None):
	filters = {}
	if project:
		filters["project"] = project
	if sprint:
		filters["sprint"] = sprint
	if department:
		filters["department"] = department
	if status:
		filters["status"] = status
	elif not int(show_completed or 0):
		filters["status"] = ["not in", ["Completed", "Cancelled"]]
	else:
		filters["status"] = ["not in", ["Cancelled"]]

	# frappe.get_list applies the current user's permissions (frappe.get_all would not)
	tasks = frappe.get_list(
		"Task",
		filters=filters,
		fields=[
			"name",
			"subject",
			"status",
			"priority",
			"project",
			"sprint",
			"exp_end_date",
			"progress",
			"_assign",
		],
		order_by="modified desc",
	)

	# Frappe's built-in _assign field is the PRIMARY source of assignees.
	assignees_map = {}
	for task in tasks:
		if task.get("_assign"):
			try:
				users = json.loads(task["_assign"])
				if users:
					assignees_map[task["name"]] = users
			except Exception:
				pass

	# Fallback: Task Assignee child table for tasks without an _assign value.
	unassigned_names = [task["name"] for task in tasks if not assignees_map.get(task["name"])]
	if unassigned_names:
		rows = frappe.get_all(
			"Task Assignee",
			filters={"parenttype": "Task", "parent": ["in", unassigned_names]},
			fields=["parent", "user"],
		)
		for row in rows:
			assignees_map.setdefault(row["parent"], []).append(row["user"])

	for task in tasks:
		task["assignees"] = assignees_map.get(task["name"], [])
		task.pop("_assign", None)

	user_filters = {"enabled": 1, "user_type": "System User"}

	# When a department is selected, narrow the user columns to that department's employees.
	if department:
		dept_employees = frappe.get_all(
			"Employee",
			filters={"department": department, "status": "Active"},
			fields=["user_id"],
		)
		dept_user_ids = [e["user_id"] for e in dept_employees if e.get("user_id")]
		if dept_user_ids:
			user_filters["name"] = ["in", dept_user_ids]

	users = frappe.get_list(
		"User",
		filters=user_filters,
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
	)

	return {"tasks": tasks, "users": users}


@frappe.whitelist()
def update_task_status(task_name, status):
	if status not in VALID_STATUSES:
		frappe.throw(_("Invalid status: {0}").format(status))

	doc = frappe.get_doc("Task", task_name)
	doc.check_permission("write")

	doc.status = status
	if status == "Completed":
		if not doc.completed_by:
			doc.completed_by = frappe.session.user
		if not doc.completed_on:
			doc.completed_on = today()

	# Full save so validation (dependency checks) and the project's
	# percent_complete rollup run. Validation errors propagate to the client.
	doc.save()
	return {"success": True}


@frappe.whitelist()
def reassign_task(task_name, new_user):
	from frappe.desk.form.assign_to import add as add_assignment, clear as clear_assignments

	doc = frappe.get_doc("Task", task_name)
	doc.check_permission("write")

	assigning = bool(new_user and new_user != "__unassigned__")
	if assigning and not frappe.db.exists("User", new_user):
		frappe.throw(_("User {0} does not exist").format(new_user))

	# Document API keeps the audit trail (Version records) intact.
	doc.set("task_assignees", [])
	if assigning:
		doc.append("task_assignees", {"user": new_user})
	doc.save()

	# Keep Frappe's built-in _assign in sync so the Task form reflects the same assignment
	clear_assignments("Task", task_name)
	if assigning:
		add_assignment(
			{
				"doctype": "Task",
				"name": task_name,
				"assign_to": [new_user],
				"notify": 0,
			}
		)

	if assigning and new_user != frappe.session.user:
		_send_assignment_notifications(doc, new_user)

	return {"success": True}


def _send_assignment_notifications(task, new_user):
	try:
		user_doc = frappe.get_doc("User", new_user)
		assigner = frappe.get_doc("User", frappe.session.user)
		task_url = f"{frappe.utils.get_url()}/app/task/{task.name}"

		# Escape all user-controlled values interpolated into the email HTML
		subject_html = escape_html(task.subject or "")
		project_html = escape_html(task.project or "—")
		status_html = escape_html(task.status or "")
		priority_html = escape_html(task.priority or "—")
		recipient_name_html = escape_html(user_doc.full_name or "")
		assigner_name_html = escape_html(assigner.full_name or "")

		# Email notification (queued — do not send inline)
		frappe.sendmail(
			recipients=[user_doc.email],
			subject=f"Task Assigned to You: {task.subject}",
			message=f"""
				<p>Hi {recipient_name_html},</p>
				<p><b>{assigner_name_html}</b> has assigned a task to you.</p>
				<table style="margin:12px 0;border-collapse:collapse;">
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Task</td><td><b>{subject_html}</b></td></tr>
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Project</td><td>{project_html}</td></tr>
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Status</td><td>{status_html}</td></tr>
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Priority</td><td>{priority_html}</td></tr>
				</table>
				<p><a href="{task_url}" style="background:#4490f1;color:#fff;padding:8px 16px;border-radius:4px;text-decoration:none;">View Task</a></p>
			""",
		)

		# In-app notification log
		notification = frappe.get_doc(
			{
				"doctype": "Notification Log",
				"subject": f"Task assigned to you: {task.subject}",
				"for_user": new_user,
				"type": "Assignment",
				"document_type": "Task",
				"document_name": task.name,
				"from_user": frappe.session.user,
				"email_content": f"{assigner_name_html} assigned '{subject_html}' to you.",
			}
		)
		notification.insert(ignore_permissions=True)

		# Real-time bell notification
		frappe.publish_realtime(
			"notification",
			{
				"title": frappe._("Task Assigned"),
				"message": f"{task.subject} was assigned to you by {assigner.full_name}",
				"indicator": "blue",
			},
			user=new_user,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Task Assignment Notification Error")
