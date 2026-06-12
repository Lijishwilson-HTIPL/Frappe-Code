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
            "priority",
        ],
        order_by="modified desc",
        limit=100,
    )

    for p in projects:
        p["open_tasks"] = len(frappe.get_list(
            "Task",
            filters={"project": p["name"], "status": ["in", ["Open", "Working", "Pending Review"]]},
            fields=["name"],
        ))
        p["overdue_tasks"] = len(frappe.get_list(
            "Task",
            filters={"project": p["name"], "status": "Overdue"},
            fields=["name"],
        ))
        p["total_tasks"] = len(frappe.get_list(
            "Task",
            filters={"project": p["name"]},
            fields=["name"],
        ))

    return projects
