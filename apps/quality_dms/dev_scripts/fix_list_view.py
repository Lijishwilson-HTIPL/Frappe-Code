import frappe

def fix_list_view():
    frappe.db.set_value("DocField", {"parent": "Document Acknowledgement", "fieldname": "acknowledged"}, "in_list_view", 1)
    frappe.db.set_value("DocField", {"parent": "Document Acknowledgement", "fieldname": "acknowledged_on"}, "in_list_view", 1)
    frappe.db.set_value("DocField", {"parent": "Document Acknowledgement", "fieldname": "employee_name"}, "in_list_view", 1)
    frappe.db.commit()
    print("Fixed list view properties for Document Acknowledgement")
