import frappe


@frappe.whitelist()
def get_projects(status=None, search=None):
    filters = {}
    if status and status != "All":
        filters["status"] = status
    if search:
        filters["project_name"] = ["like", f"%{search}%"]

    projects = frappe.get_list(
        "Project",
        filters=filters,
        fields=[
            "name",
            "project_name",
            "status",
            "percent_complete",
            "expected_end_date",
            "department",
            "priority",
            "customer",
        ],
        order_by="modified desc",
        limit=100,
    )

    for p in projects:
        p["open_tasks"] = frappe.db.count(
            "Task",
            {"project": p["name"], "status": ["in", ["Open", "Working", "Pending Review"]]},
        )
        p["overdue_tasks"] = frappe.db.count(
            "Task", {"project": p["name"], "status": "Overdue"}
        )
        p["total_tasks"] = frappe.db.count("Task", {"project": p["name"]})

    return projects
