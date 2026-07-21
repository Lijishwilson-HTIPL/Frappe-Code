import frappe

def check_workflow():
    states = frappe.get_all("Workflow Document State", filters={"parent": "Quality Document Workflow"}, fields=["state", "doc_status"])
    print(states)

check_workflow()
