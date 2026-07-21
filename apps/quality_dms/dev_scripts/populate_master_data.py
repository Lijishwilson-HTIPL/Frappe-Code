import frappe

def populate_data():
    categories = ["Standard Operating Procedure (SOP)", "Policy", "Form", "Work Instruction", "Manual"]
    types = ["Internal", "Public", "Confidential", "Restricted"]
    departments = ["Quality Assurance", "Operations", "Human Resources", "Information Technology", "Executive"]

    for cat in categories:
        if not frappe.db.exists("Document Category", cat):
            doc = frappe.get_doc({"doctype": "Document Category", "category_name": cat})
            doc.insert(ignore_permissions=True)
            print(f"Created Category: {cat}")

    for t in types:
        if not frappe.db.exists("Document Type", t):
            doc = frappe.get_doc({"doctype": "Document Type", "type_name": t})
            doc.insert(ignore_permissions=True)
            print(f"Created Type: {t}")

    frappe.db.commit()
    print("Master Data successfully populated!")

