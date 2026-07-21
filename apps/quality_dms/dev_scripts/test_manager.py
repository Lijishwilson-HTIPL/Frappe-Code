import frappe
from frappe.model.workflow import apply_workflow

def test_manager():
    frappe.set_user("creator@example.com")
    doc = frappe.new_doc("Quality Document")
    doc.title = "Manager Test Document"
    doc.department = "Accounts - HT"
    doc.category = "Policy"
    doc.type = "Finance"
    doc.insert()
    
    frappe.set_user("manager@example.com")
    doc = frappe.get_doc("Quality Document", doc.name)
    print("Manager can view draft?", doc.name)
    
    # Manager rejects directly
    apply_workflow(doc, "Reject Document")
    print("Manager successfully rejected Draft!")
    
    # Another test: Manager publishes directly
    frappe.set_user("creator@example.com")
    doc2 = frappe.new_doc("Quality Document")
    doc2.title = "Manager Test Document 2"
    doc2.department = "Accounts - HT"
    doc2.category = "Policy"
    doc2.type = "Finance"
    doc2.insert()
    
    frappe.set_user("manager@example.com")
    doc2 = frappe.get_doc("Quality Document", doc2.name)
    apply_workflow(doc2, "Force Publish")
    print(f"Manager successfully forced publish! Status: {doc2.docstatus}")

test_manager()
