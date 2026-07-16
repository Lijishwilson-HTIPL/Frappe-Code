import frappe


def execute():
    for sidebar_name in ("DMS", "Quality DMS"):
        if not frappe.db.exists("Workspace Sidebar", sidebar_name):
            continue
        sidebar = frappe.get_doc("Workspace Sidebar", sidebar_name)
        for item in sidebar.items:
            if item.label == "File Storage":
                item.link_type = "URL"
                item.link_to = None
                item.url = "/desk/file?folder=Home/Quality DMS"
                print(f"{sidebar_name}: set url to /desk/file?folder=Home/Quality DMS")
        sidebar.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.cache().flushall()
    print("Done.")
