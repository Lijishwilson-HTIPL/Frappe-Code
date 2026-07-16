import frappe

def create_workspace():
    if not frappe.db.exists("Workspace", "Quality DMS"):
        workspace = frappe.get_doc({
            "doctype": "Workspace",
            "name": "Quality DMS",
            "title": "Quality DMS",
            "label": "Quality DMS",
            "icon": "folder",
            "is_standard": 1,
            "module": "Quality Dms",
            "public": 1,
            "content": '[{"id":"1","type":"header","data":{"text":"Quality Documents","level":2}},{"id":"2","type":"shortcut","data":{"shortcut_name":"Quality Document","label":"Quality Document","type":"DocType","link_to":"Quality Document","color":"Grey"}},{"id":"3","type":"shortcut","data":{"shortcut_name":"DMS Audit Log","label":"Audit Log","type":"DocType","link_to":"DMS Audit Log","color":"Grey"}},{"id":"4","type":"header","data":{"text":"Reports","level":2}},{"id":"5","type":"shortcut","data":{"shortcut_name":"Master Document List","label":"Master Document List","type":"Report","link_to":"Master Document List","color":"Grey"}}]'
        })
        workspace.insert(ignore_permissions=True)
    print("Workspace created!")
