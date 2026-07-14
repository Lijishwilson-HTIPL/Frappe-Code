import frappe
from frappe.utils import today, add_days


def execute():
    frappe.set_user("Administrator")

    leads = [
        {"first_name": "Arjun", "last_name": "Sharma", "email_id": "arjun.sharma@techcorp.in", "mobile_no": "+91 98001 11001", "company_name": "TechCorp India", "status": "Open", "lead_name": "Arjun Sharma", "source": "Cold Calling"},
        {"first_name": "Priya", "last_name": "Nair", "email_id": "priya.nair@globalsoft.com", "mobile_no": "+91 98001 11002", "company_name": "GlobalSoft", "status": "Replied", "lead_name": "Priya Nair", "source": "Email"},
        {"first_name": "Rahul", "last_name": "Verma", "email_id": "rahul.verma@innotech.io", "mobile_no": "+91 98001 11003", "company_name": "InnoTech", "status": "Interested", "lead_name": "Rahul Verma", "source": "Advertisement"},
        {"first_name": "Sneha", "last_name": "Pillai", "email_id": "sneha.pillai@nexgen.co", "mobile_no": "+91 98001 11004", "company_name": "NexGen Co", "status": "Open", "lead_name": "Sneha Pillai", "source": "Reference"},
        {"first_name": "Vikram", "last_name": "Patel", "email_id": "vikram.patel@dataflow.in", "mobile_no": "+91 98001 11005", "company_name": "DataFlow Inc", "status": "Converted", "lead_name": "Vikram Patel", "source": "Exhibition"},
        {"first_name": "Anjali", "last_name": "Menon", "email_id": "anjali.menon@cloudbase.io", "mobile_no": "+91 98001 11006", "company_name": "CloudBase", "status": "Replied", "lead_name": "Anjali Menon", "source": "Cold Calling"},
        {"first_name": "Karthik", "last_name": "Rajan", "email_id": "karthik.rajan@smartbiz.com", "mobile_no": "+91 98001 11007", "company_name": "SmartBiz", "status": "Open", "lead_name": "Karthik Rajan", "source": "Email"},
        {"first_name": "Divya", "last_name": "Krishnan", "email_id": "divya.krishnan@finedge.in", "mobile_no": "+91 98001 11008", "company_name": "FinEdge", "status": "Interested", "lead_name": "Divya Krishnan", "source": "Reference"},
    ]

    for l in leads:
        if frappe.db.exists("Lead", {"email_id": l["email_id"]}):
            print(f"Lead exists: {l['lead_name']}")
            continue
        doc = frappe.get_doc({"doctype": "Lead", **l})
        doc.insert(ignore_permissions=True)
        print(f"Created Lead: {l['lead_name']}")

    frappe.db.commit()

    customers_data = [
        {"customer_name": "TechCorp India", "customer_type": "Company", "customer_group": "Commercial", "territory": "India"},
        {"customer_name": "GlobalSoft", "customer_type": "Company", "customer_group": "Commercial", "territory": "India"},
        {"customer_name": "InnoTech Solutions", "customer_type": "Company", "customer_group": "Commercial", "territory": "India"},
        {"customer_name": "DataFlow Inc", "customer_type": "Company", "customer_group": "Commercial", "territory": "India"},
        {"customer_name": "CloudBase Systems", "customer_type": "Company", "customer_group": "Commercial", "territory": "India"},
    ]

    for c in customers_data:
        if frappe.db.exists("Customer", c["customer_name"]):
            print(f"Customer exists: {c['customer_name']}")
            continue
        doc = frappe.get_doc({"doctype": "Customer", **c})
        doc.insert(ignore_permissions=True)
        print(f"Created Customer: {c['customer_name']}")

    frappe.db.commit()

    opps = [
        {"opportunity_from": "Customer", "party_name": "TechCorp India", "opportunity_type": "Sales", "status": "Open", "expected_closing": add_days(today(), 30), "probability": 40, "opportunity_amount": 250000},
        {"opportunity_from": "Customer", "party_name": "GlobalSoft", "opportunity_type": "Sales", "status": "Quotation", "expected_closing": add_days(today(), 15), "probability": 70, "opportunity_amount": 180000},
        {"opportunity_from": "Customer", "party_name": "InnoTech Solutions", "opportunity_type": "Sales", "status": "Open", "expected_closing": add_days(today(), 45), "probability": 25, "opportunity_amount": 320000},
        {"opportunity_from": "Customer", "party_name": "DataFlow Inc", "opportunity_type": "Support", "status": "Replied", "expected_closing": add_days(today(), 10), "probability": 60, "opportunity_amount": 95000},
        {"opportunity_from": "Customer", "party_name": "CloudBase Systems", "opportunity_type": "Sales", "status": "Open", "expected_closing": add_days(today(), 60), "probability": 20, "opportunity_amount": 500000},
    ]

    for o in opps:
        doc = frappe.get_doc({"doctype": "Opportunity", **o})
        doc.insert(ignore_permissions=True)
        print(f"Created Opportunity: {o['party_name']} - {o['opportunity_amount']}")

    frappe.db.commit()
    print("=== Done ===")
