import frappe

def create_reports_and_dashboards():
    # 1. Master Document List Report
    if not frappe.db.exists("Report", "Master Document List"):
        report = frappe.get_doc({
            "doctype": "Report",
            "name": "Master Document List",
            "report_name": "Master Document List",
            "ref_doctype": "Quality Document",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "Quality Dms"
        })
        report.insert(ignore_permissions=True)

    # 2. Audit Trail Report
    if not frappe.db.exists("Report", "Audit Trail Report"):
        report = frappe.get_doc({
            "doctype": "Report",
            "name": "Audit Trail Report",
            "report_name": "Audit Trail Report",
            "ref_doctype": "DMS Audit Log",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "Quality Dms"
        })
        report.insert(ignore_permissions=True)

    # 3. Dashboard Chart - Documents by Status
    if not frappe.db.exists("Dashboard Chart", "Documents by Status"):
        chart = frappe.get_doc({
            "doctype": "Dashboard Chart",
            "chart_name": "Documents by Status",
            "chart_type": "Group By",
            "type": "Donut",
            "document_type": "Quality Document",
            "group_by_type": "Count",
            "group_by_based_on": "status",
            "filters_json": "{}",
            "timeseries": 0,
            "is_standard": 1,
            "module": "Quality Dms"
        })
        chart.insert(ignore_permissions=True)

    # 4. Workspace
    if not frappe.db.exists("Workspace", "Quality DMS"):
        workspace = frappe.get_doc({
            "doctype": "Workspace",
            "name": "Quality DMS",
            "title": "Quality DMS",
            "icon": "folder",
            "is_standard": 1,
            "module": "Quality Dms",
            "public": 1,
            "content": '[{"id":"1","type":"header","data":{"text":"Quality Documents","level":2}},{"id":"2","type":"shortcut","data":{"shortcut_name":"Quality Document","label":"Quality Document","type":"DocType","link_to":"Quality Document","color":"Grey"}},{"id":"3","type":"shortcut","data":{"shortcut_name":"DMS Audit Log","label":"Audit Log","type":"DocType","link_to":"DMS Audit Log","color":"Grey"}},{"id":"4","type":"header","data":{"text":"Dashboards","level":2}},{"id":"5","type":"chart","data":{"chart_name":"Documents by Status"}}]'
        })
        workspace.insert(ignore_permissions=True)

    frappe.db.commit()
    print("Reports and Dashboards created successfully!")
