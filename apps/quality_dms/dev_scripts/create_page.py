import frappe

def create_page():
    if not frappe.db.exists("Page", "quality_dashboard"):
        page = frappe.new_doc("Page")
        page.page_name = "quality_dashboard"
        page.title = "Quality Dashboard"
        page.module = "Quality DMS"
        page.standard = "Yes"
        page.insert(ignore_permissions=True)
        print("Page created!")
    else:
        print("Page already exists.")

create_page()
