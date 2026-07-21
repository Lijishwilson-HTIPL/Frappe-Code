import frappe

def refactor_projects():
    projects = [
        "XELLABS",
        "DataXpulse",
        "SBIQC",
        "Govpulse",
        "HT MFT",
        "HT Digital Validation Accelerator",
        "HTI Chat"
    ]
    
    # 1. Delete from Document Category
    for p in projects:
        if frappe.db.exists("Document Category", p):
            frappe.delete_doc("Document Category", p, ignore_permissions=True, force=1)
            print(f"Deleted Document Category: {p}")
            
    # 2. Create DMS Project DocType
    if not frappe.db.exists("DocType", "DMS Project"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "DMS Project",
            "module": "Quality Dms",
            "custom": 0,
            "naming_rule": "Set by user",
            "autoname": "field:project_name",
            "fields": [
                {"fieldname": "project_name", "label": "Project Name", "fieldtype": "Data", "reqd": 1, "unique": 1}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)
        print("Created DocType: DMS Project")
        
    # 3. Insert Projects
    for p in projects:
        if not frappe.db.exists("DMS Project", p):
            doc = frappe.get_doc({
                "doctype": "DMS Project",
                "project_name": p
            })
            doc.insert(ignore_permissions=True)
            print(f"Created DMS Project: {p}")
            
    # 4. Add 'project' field to Quality Document
    if not frappe.db.exists("DocField", {"parent": "Quality Document", "fieldname": "project"}):
        field = frappe.get_doc({
            "doctype": "DocField",
            "parent": "Quality Document",
            "parenttype": "DocType",
            "parentfield": "fields",
            "fieldname": "project",
            "label": "Project Name",
            "fieldtype": "Link",
            "options": "DMS Project",
            "depends_on": "eval:doc.type=='Project'",
            "insert_after": "type"
        })
        field.insert(ignore_permissions=True)
        print("Added Project field to Quality Document")
        
    # 5. Sync MariaDB Schema
    try:
        frappe.db.sql("ALTER TABLE `tabQuality Document` ADD COLUMN `project` VARCHAR(140);")
        print("Database schema updated for tabQuality Document via raw SQL!")
    except Exception as e:
        print(f"Schema update notice: {str(e)}")

    frappe.db.commit()
    print("Refactoring completed successfully!")
