import frappe

def sync_schema():
    # Execute raw SQL to add the missing column
    try:
        frappe.db.sql("ALTER TABLE `tabDocument Acknowledgement` ADD COLUMN `e_signature` LONGTEXT;")
        frappe.db.commit()
        print("Database schema updated successfully via raw SQL!")
    except Exception as e:
        print(f"Error: {str(e)}")

