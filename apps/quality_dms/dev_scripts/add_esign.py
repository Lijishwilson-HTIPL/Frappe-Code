import frappe

def add_esign():
    if not frappe.db.exists("DocField", {"parent": "Document Acknowledgement", "fieldname": "e_signature"}):
        field = frappe.get_doc({
            "doctype": "DocField",
            "parent": "Document Acknowledgement",
            "parenttype": "DocType",
            "parentfield": "fields",
            "fieldname": "e_signature",
            "label": "E-Signature",
            "fieldtype": "Signature",
            "in_list_view": 1,
            "insert_after": "acknowledged_on"
        })
        field.insert(ignore_permissions=True)
        frappe.db.commit()
        print("E-Signature field added successfully!")
    else:
        print("E-Signature field already exists.")

add_esign()
