import frappe

def delete_page():
    if frappe.db.exists("Page", "quality_dashboard"):
        frappe.delete_doc("Page", "quality_dashboard")
        print("Deleted quality_dashboard page.")
    else:
        print("quality_dashboard page does not exist.")

delete_page()
