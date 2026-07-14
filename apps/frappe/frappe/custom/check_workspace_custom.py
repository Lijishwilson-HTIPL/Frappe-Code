import frappe

def execute():
    ws = frappe.db.get_value("Workspace", "CRM", ["is_hidden", "for_user", "public", "custom"], as_dict=True)
    print(f"Workspace CRM: {ws}")

    # Also check if there's a user-specific custom workspace overriding it
    custom = frappe.db.get_all("Workspace", filters={"extends": "CRM"}, fields=["name", "for_user", "is_hidden"])
    print(f"Custom workspaces extending CRM: {custom}")
