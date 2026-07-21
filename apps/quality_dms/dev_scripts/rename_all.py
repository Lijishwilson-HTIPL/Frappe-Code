import frappe

def rename_all_workspaces():
    # Find ALL workspaces that still say "Quality DMS"
    workspaces = frappe.get_all("Workspace", filters={"title": "Quality DMS"})
    for ws in workspaces:
        print(f"Renaming personalized workspace: {ws.name}")
        frappe.db.set_value("Workspace", ws.name, "title", "DMS")
        frappe.db.set_value("Workspace", ws.name, "label", "DMS")
        
    # Also update module name if it's showing the module name
    if frappe.db.exists("Module Def", "Quality Dms"):
        frappe.db.set_value("Module Def", "Quality Dms", "module_name", "DMS")
        frappe.db.set_value("Module Def", "Quality Dms", "app_name", "DMS")
        
    frappe.db.commit()
    print("Force renamed all instances of Quality DMS to DMS!")
