import frappe

def fix_schema():
    frappe.db.commit()  # Commit any pending transactions to avoid implicit commit warning
    try:
        frappe.db.sql("ALTER TABLE `tabQuality Document` ADD COLUMN `project` VARCHAR(140);")
        frappe.db.commit()
        print("Database schema updated successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")

