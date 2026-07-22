import frappe

def add_types():
    types_to_add = [
        "External",
        "Quality",
        "IT",
        "Finance",
        "Legal",
        "Training"
    ]
    
    for t in types_to_add:
        if not frappe.db.exists("Document Type", t):
            doc = frappe.get_doc({
                "doctype": "Document Type",
                "type_name": t
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Document Type: {t}")
        else:
            print(f"Document Type already exists: {t}")
            
    frappe.db.commit()
    print("Finished adding Document Types!")
