import frappe


def execute():
    # Check how many CRM Leads exist
    crm_leads = frappe.get_all(
        "CRM Lead",
        fields=[
            "name", "first_name", "last_name", "lead_name", "organization",
            "email", "mobile_no", "phone", "website", "status", "source",
            "job_title", "territory", "lead_owner", "modified",
            "website_message", "preferred_contact", "primary_interest", "how_found_us",
            "no_of_employees", "annual_revenue",
        ],
        order_by="creation asc",
    )

    print(f"Found {len(crm_leads)} CRM Leads to migrate")

    # Status mapping from CRM Lead Status to ERPNext Lead status
    status_map = {
        "New": "Lead",
        "Contacted": "Open",
        "Nurture": "Open",
        "Qualified": "Interested",
        "Converted": "Converted",
        "Junk": "Do Not Contact",
        "Unqualified": "Do Not Contact",
        "Replied": "Replied",
    }

    preferred_contact_map = {
        "Phone Call": "Phone",
        "Phone": "Phone",
        "Email": "Email",
        "WhatsApp": "WhatsApp",
        "Email Exchange": "Email Exchange",
        "In-Person": "",
        "Video Call": "",
    }

    created = 0
    skipped = 0
    errors = 0

    for cl in crm_leads:
        email = cl.get("email") or ""
        lead_name = cl.get("lead_name") or (f"{cl.get('first_name','')} {cl.get('last_name','')}").strip()

        # Check if already migrated (by email or name)
        exists = False
        if email:
            exists = frappe.db.exists("Lead", {"email_id": email})
        if not exists and lead_name:
            exists = frappe.db.exists("Lead", {"lead_name": lead_name})

        if exists:
            skipped += 1
            continue

        try:
            erp_status = status_map.get(cl.get("status", "New"), "Open")
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
                "status": erp_status,
                "source": cl.get("source") or "",
                "job_title": cl.get("job_title") or "",
                "territory": cl.get("territory") or "",
                "lead_owner": cl.get("lead_owner") or "",
                # Custom fields (crm_unify)
                "website_message": cl.get("website_message") or "",
                "preferred_contact": preferred_contact_map.get(cl.get("preferred_contact") or "", cl.get("preferred_contact") or ""),
                "primary_interest": cl.get("primary_interest") or "",
                "how_found_us": cl.get("how_found_us") or "",
            })
            lead.insert(ignore_permissions=True, ignore_mandatory=True)
            created += 1
            if created % 10 == 0:
                frappe.db.commit()
                print(f"  Migrated {created} so far...")
        except Exception as e:
            errors += 1
            print(f"  Error migrating {lead_name}: {e}")

    frappe.db.commit()
    print(f"\n=== Done: {created} created, {skipped} skipped (already exist), {errors} errors ===")
