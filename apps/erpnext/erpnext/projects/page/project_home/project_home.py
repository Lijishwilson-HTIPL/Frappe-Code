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

    if projects:
        project_names = [p["name"] for p in projects]
        task_stats = frappe.db.sql(
            """
            SELECT
                project,
                SUM(status IN ('Open', 'Working', 'Pending Review')) AS open_tasks,
                SUM(status = 'Overdue')                              AS overdue_tasks,
                COUNT(*)                                             AS total_tasks
            FROM `tabTask`
            WHERE project IN %(names)s
            GROUP BY project
            """,
            {"names": project_names},
            as_dict=1,
        )
        stats_map = {r.project: r for r in task_stats}
        for p in projects:
            s = stats_map.get(p["name"], {})
            p["open_tasks"]    = int(s.get("open_tasks", 0) or 0)
            p["overdue_tasks"] = int(s.get("overdue_tasks", 0) or 0)
            p["total_tasks"]   = int(s.get("total_tasks", 0) or 0)

    return projects


@frappe.whitelist()
def get_task_heatmap():
    CACHE_KEY = "task_heatmap_data"
    cached = frappe.cache().get_value(CACHE_KEY)
    if cached is not None:
        return cached

    rows = frappe.db.sql(
        """
        SELECT day, SUM(created) AS created, SUM(completed) AS completed, SUM(updated) AS updated
        FROM (
            SELECT DATE(creation) AS day,
                   COUNT(*)       AS created,
                   0              AS completed,
                   0              AS updated
            FROM `tabTask`
            WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 52 WEEK)
            GROUP BY DATE(creation)

            UNION ALL

            SELECT DATE(modified)             AS day,
                   0                          AS created,
                   SUM(status = 'Completed')  AS completed,
                   SUM(status != 'Completed') AS updated
            FROM `tabTask`
            WHERE modified >= DATE_SUB(CURDATE(), INTERVAL 52 WEEK)
            GROUP BY DATE(modified)
        ) t
        GROUP BY day
        """,
        as_dict=1,
    )
    result = {
        str(r.day): {
            "created":   int(r.created or 0),
            "completed": int(r.completed or 0),
            "updated":   int(r.updated or 0),
        }
        for r in rows
    }
    cache = frappe.cache()
    cache.set_value(CACHE_KEY, result, expires_in_sec=3600)
    # Also populate frappe.local.cache so the value is readable within the same request
    # (Frappe only populates local.cache in set_value when expires_in_sec is None)
    frappe.local.cache[cache.make_key(CACHE_KEY)] = result
    return result
