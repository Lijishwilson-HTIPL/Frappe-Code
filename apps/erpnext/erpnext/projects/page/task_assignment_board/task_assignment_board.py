import json

import frappe

VALID_STATUSES = {"Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled", "Template"}


@frappe.whitelist()
def get_board_data(project=None, status=None, show_completed=0):
	filters = {}
	if project:
		filters["project"] = project
	if status:
		filters["status"] = status
	elif not int(show_completed or 0):
		filters["status"] = ["not in", ["Completed", "Cancelled"]]
	else:
		filters["status"] = ["not in", ["Cancelled"]]

	tasks = frappe.get_all(
		"Task",
		filters=filters,
		fields=["name", "subject", "status", "priority", "project", "exp_end_date", "progress"],
		order_by="modified desc",
	)

	task_names = [t["name"] for t in tasks]

	assignees_map = {}
	if task_names:
		rows = frappe.get_all(
			"Task Assignee",
			filters={"parent": ["in", task_names]},
			fields=["parent", "user"],
		)
		for row in rows:
			assignees_map.setdefault(row["parent"], []).append(row["user"])

		# Fall back to Frappe's built-in _assign field for tasks not in task_assignees.
		# This covers tasks assigned via the Task form or task list view.
		unassigned_names = [t for t in task_names if not assignees_map.get(t)]
		if unassigned_names:
			fallback_rows = frappe.get_all(
				"Task",
				filters={"name": ["in", unassigned_names]},
				fields=["name", "_assign"],
			)
			for row in fallback_rows:
				if row.get("_assign"):
					try:
						users = json.loads(row["_assign"])
						if users:
							assignees_map[row["name"]] = users
					except Exception:
						pass

	for task in tasks:
		task["assignees"] = assignees_map.get(task["name"], [])

	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
	)

	return {"tasks": tasks, "users": users}


@frappe.whitelist()
def reassign_task(task_name, new_user):
	from frappe.desk.form.assign_to import add as add_assignment, clear as clear_assignments

	# M-2: permission check
	frappe.has_permission("Task", "write", task_name, throw=True)

	# M-3/M-7: validate user exists before touching anything
	if new_user and new_user != "__unassigned__":
		if not frappe.db.exists("User", new_user):
			frappe.throw(frappe._("User {0} does not exist").format(new_user))

	# C-4: direct child table manipulation — no full Task validation triggered
	frappe.db.delete("Task Assignee", {"parent": task_name})
	if new_user and new_user != "__unassigned__":
		frappe.db.insert({
			"doctype": "Task Assignee",
			"parent": task_name,
			"parenttype": "Task",
			"parentfield": "task_assignees",
			"user": new_user,
		})

	# M-3: only update _assign after child table write succeeds
	# Keep Frappe's built-in _assign in sync so the Task form reflects the same assignment
	clear_assignments("Task", task_name)
	if new_user and new_user != "__unassigned__":
		add_assignment({
			"doctype": "Task",
			"name": task_name,
			"assign_to": [new_user],
			"notify": 0,
		})

	if new_user and new_user != "__unassigned__" and new_user != frappe.session.user:
		doc = frappe.get_doc("Task", task_name)
		_send_assignment_notifications(doc, new_user)

	frappe.db.commit()
	return {"success": True}


@frappe.whitelist()
def update_task_status(task_name, status):
	# M-2: permission check
	frappe.has_permission("Task", "write", task_name, throw=True)
	# M-1: validate status against known values
	if status not in VALID_STATUSES:
		frappe.throw(frappe._("Invalid status: {0}").format(status))
	frappe.db.set_value("Task", task_name, "status", status)
	if status == "Completed":
		from frappe.desk.form.assign_to import close_all_assignments
		close_all_assignments("Task", task_name)
	frappe.db.commit()
	return {"success": True}


def _send_assignment_notifications(task, new_user):
	try:
		user_doc = frappe.get_doc("User", new_user)
		assigner = frappe.get_doc("User", frappe.session.user)
		task_url = f"{frappe.utils.get_url()}/app/task/{task.name}"

		# Email notification
		frappe.sendmail(
			recipients=[user_doc.email],
			subject=f"Task Assigned to You: {task.subject}",
			message=f"""
				<p>Hi {user_doc.full_name},</p>
				<p><b>{assigner.full_name}</b> has assigned a task to you.</p>
				<table style="margin:12px 0;border-collapse:collapse;">
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Task</td><td><b>{task.subject}</b></td></tr>
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Project</td><td>{task.project or "—"}</td></tr>
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Status</td><td>{task.status}</td></tr>
					<tr><td style="padding:4px 12px 4px 0;color:#666;">Priority</td><td>{task.priority or "—"}</td></tr>
				</table>
				<p><a href="{task_url}" style="background:#4490f1;color:#fff;padding:8px 16px;border-radius:4px;text-decoration:none;">View Task</a></p>
			""",
			now=True,
		)

		# In-app notification log
		notification = frappe.get_doc({
			"doctype": "Notification Log",
			"subject": f"Task assigned to you: {task.subject}",
			"for_user": new_user,
			"type": "Assignment",
			"document_type": "Task",
			"document_name": task.name,
			"from_user": frappe.session.user,
			"email_content": f"{assigner.full_name} assigned '{task.subject}' to you.",
		})
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
