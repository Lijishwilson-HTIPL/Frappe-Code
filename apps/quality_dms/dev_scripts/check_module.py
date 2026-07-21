import frappe

def check_module():
    modules = frappe.get_all("Module Def", filters={"app_name": "quality_dms"}, fields=["name", "app_name", "custom"])
    print("Modules for quality_dms:")
    for m in modules:
        print(m)

    # Let's create it if it doesn't exist
    if not frappe.db.exists("Module Def", "Quality Dms"):
        m = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Quality Dms",
            "app_name": "quality_dms",
            "custom": 0
        })
        m.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Module Def: Quality Dms")
