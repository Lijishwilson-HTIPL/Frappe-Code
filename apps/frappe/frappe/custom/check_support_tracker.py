import frappe


def execute():
    page = frappe.db.get_value("Page", "support-tracker", ["name", "module", "title"], as_dict=True)
    print(f"Page record: {page}")

    if page:
        from frappe.modules.utils import get_module_app
        app = get_module_app(page.module) if page.module else None
        print(f"App for module '{page.module}': {app}")

        import os
        module_path = frappe.get_module_path(page.module) if page.module else None
        print(f"Module path: {module_path}")
        if module_path:
            page_path = os.path.join(module_path, 'page', 'support_tracker')
            print(f"Expected page path: {page_path}")
            print(f"Path exists: {os.path.exists(page_path)}")
    else:
        # Search for it
        pages = frappe.db.sql("SELECT name, module, title FROM `tabPage` WHERE name LIKE '%support%'", as_dict=True)
        print(f"Support-related pages: {pages}")
