import frappe


def execute(filters=None):
    filters = filters or {}
    columns = _get_columns()
    data = _get_data(filters)
    return columns, data


def _get_columns():
    return [
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 140,
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 150,
        },
        {
            "label": "Document Category",
            "fieldname": "category",
            "fieldtype": "Link",
            "options": "Document Category",
            "width": 160,
        },
        {
            "label": "Total Assigned",
            "fieldname": "total_assigned",
            "fieldtype": "Int",
            "width": 110,
        },
        {
            "label": "Completed",
            "fieldname": "completed",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Overdue",
            "fieldname": "overdue",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": "Pending",
            "fieldname": "pending",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": "Compliance %",
            "fieldname": "compliance_percentage",
            "fieldtype": "Percent",
            "width": 115,
        },
    ]


def _get_data(filters):
    conditions = ["1=1"]
    values = {}

    if filters.get("department"):
        conditions.append("emp.department = %(department)s")
        values["department"] = filters["department"]

    if filters.get("employee"):
        conditions.append("da.employee = %(employee)s")
        values["employee"] = filters["employee"]

    if filters.get("category"):
        conditions.append("doc.category = %(category)s")
        values["category"] = filters["category"]

    where = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            da.employee AS employee,
            emp.employee_name AS employee_name,
            emp.department AS department,
            doc.category AS category,
            da.status AS row_status
        FROM `tabDocument Acknowledgement` da
        INNER JOIN `tabDMS Training Record` trn ON trn.name = da.parent AND da.parenttype = 'DMS Training Record'
        INNER JOIN `tabDocument Library` doc ON doc.name = trn.document
        LEFT JOIN `tabEmployee` emp ON emp.name = da.employee
        WHERE {where}
        """,
        values,
        as_dict=True,
    )

    grouped = {}
    for row in rows:
        key = (row.employee, row.category)
        bucket = grouped.setdefault(
            key,
            {
                "employee": row.employee,
                "employee_name": row.employee_name,
                "department": row.department,
                "category": row.category,
                "total_assigned": 0,
                "completed": 0,
                "overdue": 0,
                "pending": 0,
            },
        )
        bucket["total_assigned"] += 1
        if row.row_status == "Completed":
            bucket["completed"] += 1
        elif row.row_status == "Overdue":
            bucket["overdue"] += 1
        else:
            bucket["pending"] += 1

    data = []
    for bucket in grouped.values():
        total = bucket["total_assigned"]
        bucket["compliance_percentage"] = (
            round(bucket["completed"] / total * 100, 1) if total else 0.0
        )
        data.append(bucket)

    data.sort(key=lambda r: (r["employee_name"] or "", r["category"] or ""))
    return data
