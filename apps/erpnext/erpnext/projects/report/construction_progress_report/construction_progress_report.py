import frappe
from frappe.utils import nowdate


def execute(filters=None):
    filters = filters or {}

    columns = [
        {
            "fieldname": "project_name",
            "fieldtype": "Link",
            "options": "Project",
            "label": "Project",
            "width": 200
        },
        {
            "fieldname": "status",
            "fieldtype": "Data",
            "label": "Status",
            "width": 100
        },
        {
            "fieldname": "priority",
            "fieldtype": "Data",
            "label": "Priority",
            "width": 80
        },
        {
            "fieldname": "expected_end_date",
            "fieldtype": "Date",
            "label": "Expected End Date",
            "width": 120
        },
        {
            "fieldname": "total_tasks",
            "fieldtype": "Int",
            "label": "Total Tasks",
            "width": 90
        },
        {
            "fieldname": "completed_tasks",
            "fieldtype": "Int",
            "label": "Completed",
            "width": 90
        },
        {
            "fieldname": "in_progress_tasks",
            "fieldtype": "Int",
            "label": "In Progress",
            "width": 90
        },
        {
            "fieldname": "overdue_tasks",
            "fieldtype": "Int",
            "label": "Overdue",
            "width": 80
        },
        {
            "fieldname": "percent_complete",
            "fieldtype": "Percent",
            "label": "% Complete",
            "width": 100
        }
    ]

    project_filters = {}

    if filters.get("company"):
        project_filters["company"] = filters["company"]

    if filters.get("status"):
        project_filters["status"] = filters["status"]

    project_conditions = {}
    if filters.get("from_date"):
        project_conditions["expected_end_date"] = [">=", filters["from_date"]]
    if filters.get("to_date"):
        if project_conditions.get("expected_end_date"):
            # Both from and to — use a two-sided range
            project_conditions["expected_end_date"] = [
                "between",
                [filters["from_date"], filters["to_date"]]
            ]
        else:
            project_conditions["expected_end_date"] = ["<=", filters["to_date"]]

    project_filters.update(project_conditions)

    projects = frappe.get_list(
        "Project",
        filters=project_filters,
        fields=["name", "project_name", "status", "priority", "expected_end_date",
                "percent_complete"],
        order_by="expected_end_date asc"
    )

    today = nowdate()
    data = []

    for project in projects:
        tasks = frappe.get_list(
            "Task",
            filters={"project": project.name},
            fields=["name", "status", "expected_end_date"]
        )

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == "Completed")
        in_progress_tasks = sum(1 for t in tasks if t.status == "Working")
        overdue_tasks = sum(
            1 for t in tasks
            if t.status != "Completed"
            and t.expected_end_date
            and str(t.expected_end_date) < today
        )

        percent_complete = 0.0
        if total_tasks > 0:
            percent_complete = round((completed_tasks / total_tasks) * 100, 2)

        data.append({
            "project_name": project.name,
            "status": project.status or "",
            "priority": project.priority or "",
            "expected_end_date": project.expected_end_date,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": overdue_tasks,
            "percent_complete": percent_complete
        })

    return columns, data
