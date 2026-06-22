import frappe

def execute():
    total = frappe.db.count("Lead")
    crm_total = frappe.db.count("CRM Lead")
    names = frappe.get_all("Lead", fields=["lead_name", "status", "email_id"], order_by="creation asc")
    print(f"ERPNext Leads: {total}, CRM Leads: {crm_total}")
    for n in names:
        print(f"  {n.lead_name} | {n.status} | {n.email_id}")
