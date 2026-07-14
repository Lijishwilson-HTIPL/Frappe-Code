import frappe

def execute():
    ws = frappe.db.get_value("Workspace", "CRM", ["is_hidden", "for_user", "public"], as_dict=True)
    print(f"Workspace CRM: {ws}")

    custom = frappe.db.get_all("Workspace", filters={"extends": "CRM"}, fields=["name", "for_user", "is_hidden"])
    print(f"Custom workspaces extending CRM: {custom}")

    # Check what the API returns for workspace sidebar
    from frappe.desk.desktop import get_workspace_sidebar_items
    items = get_workspace_sidebar_items()
    crm_items = [i for i in items.get("pages", []) if i.get("name") == "CRM"]
    print(f"Sidebar API CRM entry: {crm_items}")
