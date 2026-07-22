import frappe
from frappe.modules.import_file import import_file_by_path

def restore_page():
    path = "/home/james/frappe-bench/apps/quality_dms/quality_dms/quality_dms/page/quality_dashboard/quality_dashboard.json"
    import_file_by_path(path, force=True)
    print("Page restored from JSON!")

restore_page()
