import frappe
from frappe.utils import today, getdate


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
            "fieldname": "training_record",
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
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 130,
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Employee Dept",
            "fieldname": "employee_department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 150,
        },
        {
            "label": "Due Date",
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Days Overdue",
            "fieldname": "days_overdue",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Assigned By",
            "fieldname": "assigned_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 150,
        },
    ]


def _get_data(filters):
    # Exclude staged ("Suggested") candidates and "Excused" rows — neither is a
    # real, outstanding assignment, so they must not appear as overdue.
    conditions = [
        "da.acknowledged = 0",
        "da.status NOT IN ('Suggested', 'Excused')",
        "tr.status IN ('Overdue', 'Assigned', 'In Progress')",
    ]
    values = {}
    today_date = getdate(today())

    if filters.get("department"):
        conditions.append("tr.department = %(department)s")
        values["department"] = filters["department"]

    if filters.get("employee"):
        conditions.append("da.employee = %(employee)s")
        values["employee"] = filters["employee"]

    where = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            tr.name AS training_record,
            tr.document,
            tr.document_title,
            tr.version,
            tr.department,
            tr.assigned_by,
            da.employee,
            da.employee_name,
            da.department AS employee_department,
            da.due_date
        FROM `tabDMS Training Record` tr
        INNER JOIN `tabDocument Acknowledgement` da
            ON da.parent = tr.name
            AND da.parenttype = 'DMS Training Record'
        WHERE {where}
            AND (da.due_date IS NOT NULL AND da.due_date < %(today)s)
        ORDER BY da.due_date ASC
        """,
        {**values, "today": today_date},
        as_dict=True,
    )

    for row in rows:
        if row.due_date:
            row["days_overdue"] = (today_date - getdate(row.due_date)).days
        else:
            row["days_overdue"] = 0

    return rows


def _get_summary(data):
    if not data:
        return [{"value": 0, "label": "Overdue Employees", "datatype": "Int", "indicator": "green"}]

    total = len(data)
    max_days = max((r.get("days_overdue", 0) for r in data), default=0)
    departments = len({r.get("department") for r in data if r.get("department")})

    return [
        {"value": total, "label": "Overdue Employees", "datatype": "Int", "indicator": "red"},
        {"value": departments, "label": "Departments Affected", "datatype": "Int", "indicator": "orange"},
        {"value": max_days, "label": "Max Days Overdue", "datatype": "Int", "indicator": "red" if max_days > 14 else "orange"},
    ]
