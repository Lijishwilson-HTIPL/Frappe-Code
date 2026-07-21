import frappe

def create_doctypes():
    frappe.flags.in_install = True
    
    # 1. Document Category
    if not frappe.db.exists("DocType", "Document Category"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Document Category",
            "module": "Quality Dms",
            "custom": 0,
            "istable": 0,
            "naming_rule": "Set by user",
            "autoname": "field:category_name",
            "fields": [
                {"fieldname": "category_name", "label": "Category Name", "fieldtype": "Data", "reqd": 1, "unique": 1},
                {"fieldname": "description", "label": "Description", "fieldtype": "Text"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)
    
    # 2. Document Type
    if not frappe.db.exists("DocType", "Document Type"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Document Type",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Set by user",
            "autoname": "field:type_name",
            "fields": [
                {"fieldname": "type_name", "label": "Type Name", "fieldtype": "Data", "reqd": 1, "unique": 1},
                {"fieldname": "description", "label": "Description", "fieldtype": "Text"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)

    # 3. Approval Matrix
    if not frappe.db.exists("DocType", "Approval Matrix"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Approval Matrix",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Expression",
            "autoname": "format:{department}-{category}",
            "fields": [
                {"fieldname": "department", "label": "Department", "fieldtype": "Link", "options": "Department", "reqd": 1},
                {"fieldname": "category", "label": "Document Category", "fieldtype": "Link", "options": "Document Category", "reqd": 1},
                {"fieldname": "reviewer", "label": "Reviewer Role", "fieldtype": "Link", "options": "Role"},
                {"fieldname": "approver", "label": "Approver Role", "fieldtype": "Link", "options": "Role", "reqd": 1}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)

    # 4. Document
    if not frappe.db.exists("DocType", "Quality Document"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Quality Document",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Expression",
            "autoname": "format:DOC-{YYYY}-{####}",
            "is_submittable": 1,
            "track_changes": 1,
            "track_views": 1,
            "fields": [
                {"fieldname": "title", "label": "Title", "fieldtype": "Data", "reqd": 1, "in_global_search": 1},
                {"fieldname": "department", "label": "Department", "fieldtype": "Link", "options": "Department", "reqd": 1},
                {"fieldname": "category", "label": "Category", "fieldtype": "Link", "options": "Document Category", "reqd": 1},
                {"fieldname": "type", "label": "Type", "fieldtype": "Link", "options": "Document Type"},
                {"fieldname": "version", "label": "Version", "fieldtype": "Data", "default": "1.0", "read_only": 1},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Draft\nReview\nApproved\nPublished\nObsolete\nArchived", "default": "Draft"},
                {"fieldname": "file", "label": "Document File", "fieldtype": "Attach"},
                {"fieldname": "effective_date", "label": "Effective Date", "fieldtype": "Date"},
                {"fieldname": "review_date", "label": "Next Review Date", "fieldtype": "Date"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)

    # 5. Document Revision
    if not frappe.db.exists("DocType", "Document Revision"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Document Revision",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Expression",
            "autoname": "format:{document}-{version}",
            "fields": [
                {"fieldname": "document", "label": "Document", "fieldtype": "Link", "options": "Quality Document", "reqd": 1, "in_list_view": 1},
                {"fieldname": "version", "label": "Version", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"fieldname": "change_log", "label": "Change Log", "fieldtype": "Text Editor", "reqd": 1},
                {"fieldname": "file", "label": "Archived File", "fieldtype": "Attach"},
                {"fieldname": "revision_date", "label": "Revision Date", "fieldtype": "Date"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)

    # 6. Acknowledgement
    if not frappe.db.exists("DocType", "Document Acknowledgement"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Document Acknowledgement",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Autoincrement",
            "autoname": "autoincrement",
            "istable": 1,
            "fields": [
                {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "reqd": 1, "in_list_view": 1},
                {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "fetch_from": "employee.employee_name"},
                {"fieldname": "acknowledged", "label": "Acknowledged", "fieldtype": "Check", "default": "0"},
                {"fieldname": "acknowledged_on", "label": "Acknowledged On", "fieldtype": "Datetime"}
            ]
        })
        doc.insert(ignore_permissions=True)

    # 7. Training Record
    if not frappe.db.exists("DocType", "DMS Training Record"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "DMS Training Record",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Expression",
            "autoname": "format:TRN-{YYYY}-{####}",
            "fields": [
                {"fieldname": "document", "label": "Document", "fieldtype": "Link", "options": "Quality Document", "reqd": 1},
                {"fieldname": "version", "label": "Version", "fieldtype": "Data", "reqd": 1},
                {"fieldname": "trainer", "label": "Trainer", "fieldtype": "Link", "options": "Employee"},
                {"fieldname": "training_date", "label": "Training Date", "fieldtype": "Date"},
                {"fieldname": "employees", "label": "Employees", "fieldtype": "Table", "options": "Document Acknowledgement"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)

    # 8. Document Request
    if not frappe.db.exists("DocType", "Document Request"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Document Request",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Expression",
            "autoname": "format:REQ-{YYYY}-{####}",
            "fields": [
                {"fieldname": "title", "label": "Proposed Title", "fieldtype": "Data", "reqd": 1},
                {"fieldname": "reason", "label": "Reason for Request", "fieldtype": "Text Editor", "reqd": 1},
                {"fieldname": "request_type", "label": "Request Type", "fieldtype": "Select", "options": "New Document\nRevision", "default": "New Document"},
                {"fieldname": "reference_document", "label": "Reference Document", "fieldtype": "Link", "options": "Quality Document", "depends_on": "eval:doc.request_type=='Revision'"},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Pending\nApproved\nRejected", "default": "Pending"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)
        
    # 9. Audit Log
    if not frappe.db.exists("DocType", "DMS Audit Log"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "DMS Audit Log",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Autoincrement",
            "autoname": "autoincrement",
            "fields": [
                {"fieldname": "document", "label": "Document", "fieldtype": "Link", "options": "Quality Document", "reqd": 1, "in_list_view": 1},
                {"fieldname": "action", "label": "Action", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
                {"fieldname": "user", "label": "User", "fieldtype": "Link", "options": "User", "reqd": 1, "in_list_view": 1},
                {"fieldname": "timestamp", "label": "Timestamp", "fieldtype": "Datetime", "reqd": 1, "in_list_view": 1},
                {"fieldname": "ip_address", "label": "IP Address", "fieldtype": "Data"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 0, "create": 0, "delete": 0}]
        })
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    print("DocTypes created successfully!")
