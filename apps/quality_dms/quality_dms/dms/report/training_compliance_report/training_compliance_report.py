import frappe
from frappe.utils import today


def execute(filters=None):
    filters = filters or {}
    columns = _get_columns()
    data = _get_data(filters)
    summary = _get_summary(data)
    return columns, data, None, None, summary


def _get_columns():
    return [
        {
            "label": "Training Record",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "DMS Training Record",
            "width": 160,
        },
        {
            "label": "Document",
            "fieldname": "document",
            "fieldtype": "Link",
            "options": "Document Library",
            "width": 160,
        },
        {
            "label": "Document Title",
            "fieldname": "document_title",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Version",
            "fieldname": "version",
            "fieldtype": "Data",
            "width": 70,
        },
        {
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 150,
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Due Date",
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Total Assigned",
            "fieldname": "total_assigned",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Completed",
            "fieldname": "total_completed",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Completion %",
            "fieldname": "completion_percentage",
            "fieldtype": "Percent",
            "width": 115,
        },
        {
            "label": "Assigned By",
            "fieldname": "assigned_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 150,
        },
        {
            "label": "Assigned Date",
            "fieldname": "assigned_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": "Verified By",
            "fieldname": "verified_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 140,
        },
        {
            "label": "Verified Date",
            "fieldname": "verified_date",
            "fieldtype": "Date",
            "width": 110,
        },
    ]


def _get_data(filters):
    conditions = ["1=1"]
    values = {}

    if filters.get("department"):
        conditions.append("department = %(department)s")
        values["department"] = filters["department"]

    if filters.get("status"):
        conditions.append("status = %(status)s")
        values["status"] = filters["status"]

    if filters.get("from_date"):
        conditions.append("(assigned_date >= %(from_date)s OR creation >= %(from_date)s)")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("(assigned_date <= %(to_date)s OR creation <= %(to_date)s)")
        values["to_date"] = filters["to_date"]

    where = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            name, document, document_title, version, department,
            status, due_date, total_assigned, total_completed,
            completion_percentage, assigned_by, assigned_date,
            verified_by, verified_date
        FROM `tabDMS Training Record`
        WHERE {where}
        ORDER BY creation DESC
        """,
        values,
        as_dict=True,
    )


def _get_summary(data):
    if not data:
        return []

    total = len(data)
    closed = sum(1 for r in data if r.get("status") in ("Verified", "Closed"))
    in_progress = sum(1 for r in data if r.get("status") in ("Assigned", "In Progress"))
    overdue = sum(1 for r in data if r.get("status") == "Overdue")
    compliance = round(closed / total * 100, 1) if total > 0 else 0.0

    return [
        {"value": total, "label": "Total Records", "datatype": "Int", "indicator": "blue"},
        {"value": in_progress, "label": "In Progress", "datatype": "Int", "indicator": "orange"},
        {
            "value": overdue,
            "label": "Overdue",
            "datatype": "Int",
            "indicator": "red" if overdue > 0 else "green",
        },
        {"value": closed, "label": "Verified / Closed", "datatype": "Int", "indicator": "green"},
        {
            "value": compliance,
            "label": "Compliance %",
            "datatype": "Percent",
            "indicator": "green" if compliance >= 80 else "red",
        },
    ]
