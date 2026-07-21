import frappe

def create_projects():
    # Create Document Type "Project"
    if not frappe.db.exists("Document Type", "Project"):
        doc = frappe.get_doc({
            "doctype": "Document Type",
            "type_name": "Project"
        })
        doc.insert(ignore_permissions=True)
        print("Created Document Type: Project")
        
    projects = [
        "XELLABS",
        "DataXpulse",
        "SBIQC",
        "Govpulse",
        "HT MFT",
        "HT Digital Validation Accelerator",
        "HTI Chat"
    ]
    
    # Create Document Categories for the projects
    for p in projects:
        if not frappe.db.exists("Document Category", p):
            doc = frappe.get_doc({
                "doctype": "Document Category",
                "category_name": p
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Document Category: {p}")

    frappe.db.commit()
    print("All projects added successfully!")
