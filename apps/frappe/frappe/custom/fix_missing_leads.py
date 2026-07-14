import frappe


def execute():
    crm_leads = frappe.get_all(
        "CRM Lead",
        fields=["name", "first_name", "last_name", "lead_name", "organization",
                "email", "mobile_no", "phone", "website", "status", "source",
                "job_title", "territory", "lead_owner",
                "website_message", "preferred_contact", "primary_interest", "how_found_us"],
        order_by="creation asc",
    )

    status_map = {
        "New": "Lead", "Contacted": "Open", "Nurture": "Open",
        "Qualified": "Interested", "Converted": "Converted",
        "Junk": "Do Not Contact", "Unqualified": "Do Not Contact", "Replied": "Replied",
    }
    preferred_contact_map = {
        "Phone Call": "Phone", "Phone": "Phone", "Email": "Email",
        "WhatsApp": "WhatsApp", "Email Exchange": "Email Exchange",
    }

    erp_leads = {r.lead_name for r in frappe.get_all("Lead", fields=["lead_name"])}
    erp_emails = {r.email_id for r in frappe.get_all("Lead", fields=["email_id"]) if r.email_id}

    created = 0
    for cl in crm_leads:
        email = cl.get("email") or ""
        lead_name = cl.get("lead_name") or (f"{cl.get('first_name','')} {cl.get('last_name','')}").strip()

        if lead_name in erp_leads or (email and email in erp_emails):
            print(f"  Skip: {lead_name}")
            continue

        try:
            lead = frappe.get_doc({
                "doctype": "Lead",
                "first_name": cl.get("first_name") or lead_name,
                "last_name": cl.get("last_name") or "",
                "lead_name": lead_name,
                "company_name": cl.get("organization") or "",
                "email_id": email,
                "mobile_no": cl.get("mobile_no") or "",
                "phone": cl.get("phone") or "",
                "website": cl.get("website") or "",
                "status": status_map.get(cl.get("status", "New"), "Lead"),
                "source": cl.get("source") or "",
                "job_title": cl.get("job_title") or "",
                "territory": cl.get("territory") or "",
                "lead_owner": cl.get("lead_owner") or "",
                "website_message": cl.get("website_message") or "",
                "preferred_contact": preferred_contact_map.get(cl.get("preferred_contact") or "", ""),
                "primary_interest": cl.get("primary_interest") or "",
                "how_found_us": cl.get("how_found_us") or "",
            })
            lead.insert(ignore_permissions=True, ignore_mandatory=True)
            created += 1
            print(f"  Created: {lead_name}")
        except Exception as e:
            print(f"  Error {lead_name}: {e}")

    frappe.db.commit()
    print(f"\nDone: {created} new leads created")
