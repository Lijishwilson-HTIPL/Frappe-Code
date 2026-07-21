import frappe

def create_admin_employee():
    employee_name = frappe.db.get_value("Employee", {"user_id": "Administrator"}, "name")
    if not employee_name:
        emp = frappe.get_doc({
            "doctype": "Employee",
            "first_name": "Admin",
            "last_name": "User",
            "user_id": "Administrator",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2020-01-01",
            "status": "Active"
        })
        emp.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Created Employee record: {emp.name}")
    else:
        print("Employee record already exists.")

