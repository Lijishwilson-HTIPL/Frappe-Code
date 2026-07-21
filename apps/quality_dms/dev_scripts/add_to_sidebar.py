import frappe

def add_workspace_to_sidebar():
    workspace_name = "Quality DMS"
    
    # 1. Ensure the workspace exists and is public
    if frappe.db.exists("Workspace", workspace_name):
        ws = frappe.get_doc("Workspace", workspace_name)
        if getattr(ws, "is_hidden", None):
            ws.is_hidden = 0
            ws.save(ignore_permissions=True)

    # 2. Add to Workspace Settings if it exists
    if frappe.db.exists("DocType", "Workspace Settings"):
        settings = frappe.get_doc("Workspace Settings")
        
        # Check if it's already there
        exists = False
        for page in settings.get("workspace_setup", []):
            if page.workspace == workspace_name:
                exists = True
                break
                
        if not exists:
            settings.append("workspace_setup", {
                "workspace": workspace_name
            })
            settings.save(ignore_permissions=True)
            print("Added to Workspace Settings sidebar.")
    
    frappe.db.commit()
    print("Done!")
