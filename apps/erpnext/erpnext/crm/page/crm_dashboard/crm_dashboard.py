import frappe
from frappe import _
from frappe.utils import nowdate, get_first_day, get_last_day, flt

@frappe.whitelist()
def get_dashboard_data():
    if not (frappe.has_role("Sales Manager") or frappe.has_role("System Manager") or frappe.has_role("CRM User")):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    today = nowdate()
    first_day = get_first_day(today)
    last_day = get_last_day(today)

    # ERPNext Leads
    erpnext_leads = frappe.get_all("Lead",
        filters={"status": ["not in", ["Converted", "Do Not Contact"]]},
        fields=["name", "lead_name", "company_name", "status", "lead_owner", "creation", "source"],
        order_by="creation desc", limit=100)
    open_leads = len(erpnext_leads)

    # ERPNext Opportunities
    erpnext_opps = frappe.get_all("Opportunity",
        filters={"status": ["not in", ["Lost", "Closed"]]},
        fields=["name", "opportunity_from", "party_name", "opportunity_amount", "expected_closing", "owner", "sales_stage", "status"],
        order_by="creation desc", limit=200)
    open_opps = len(erpnext_opps)
    pipeline_value = sum(flt(o.get("opportunity_amount") or 0) for o in erpnext_opps)

    # Won this month (ERPNext)
    won_erpnext = frappe.db.count("Opportunity", filters={
        "status": "Won",
        "modified": ["between", [first_day, last_day]]
    })

    # Frappe CRM data (guarded)
    crm_leads = []
    crm_deals = []
    crm_deal_statuses = []
    open_crm_leads = 0
    open_crm_deals = 0
    crm_pipeline_value = 0
    won_crm = 0

    try:
        crm_leads = frappe.get_all("CRM Lead",
            filters={"converted": 0},
            fields=["name", "lead_name", "organization", "status", "lead_owner", "creation", "source"],
            order_by="creation desc", limit=100)
        open_crm_leads = len(crm_leads)
    except Exception:
        pass

    try:
        crm_deals = frappe.get_all("CRM Deal",
            filters={"status": ["not in", ["Won", "Lost"]]},
            fields=["name", "lead_name", "organization", "deal_value", "expected_closure_date", "deal_owner", "status"],
            order_by="creation desc", limit=200)
        open_crm_deals = len(crm_deals)
        crm_pipeline_value = sum(flt(d.get("deal_value") or 0) for d in crm_deals)
    except Exception:
        pass

    try:
        won_crm = frappe.db.count("CRM Deal", filters={
            "status": "Won",
            "modified": ["between", [first_day, last_day]]
        })
    except Exception:
        pass

    try:
        statuses = frappe.get_all("CRM Deal Status", fields=["name"], order_by="name")
        crm_deal_statuses = [s["name"] for s in statuses]
    except Exception:
        crm_deal_statuses = ["Qualification", "Demo/Making", "Proposal", "Negotiation", "Won", "Lost"]

    # Activities
    activities = []
    if frappe.has_permission("Communication", "read"):
        try:
            comms = frappe.get_all("Communication",
                filters={"reference_doctype": ["in", ["Lead", "Opportunity", "CRM Lead", "CRM Deal"]]},
                fields=["name", "subject", "sent_or_received", "creation", "reference_doctype", "reference_name"],
                order_by="creation desc", limit=30)
            for c in comms:
                activities.append({
                    "type": "communication",
                    "icon": "mail",
                    "title": c.get("subject") or "Communication",
                    "subtitle": c.get("sent_or_received") or "",
                    "creation": str(c.get("creation") or ""),
                    "ref": c.get("reference_name") or ""
                })
        except Exception:
            pass

    try:
        call_logs = frappe.get_all("CRM Call Log",
            fields=["name", "creation", "duration", "status"],
            order_by="creation desc", limit=20)
        for cl in call_logs:
            activities.append({
                "type": "call",
                "icon": "phone",
                "title": "Call ({}) — {} sec".format(cl.get("status", ""), cl.get("duration", "") or "—"),
                "subtitle": "",
                "creation": str(cl.get("creation") or ""),
                "ref": cl.get("name") or ""
            })
    except Exception:
        pass

    try:
        notes = frappe.get_all("FCRM Note",
            fields=["name", "title", "creation", "owner"],
            order_by="creation desc", limit=20)
        for n in notes:
            activities.append({
                "type": "note",
                "icon": "file-text",
                "title": n.get("title") or "Note",
                "subtitle": n.get("owner") or "",
                "creation": str(n.get("creation") or ""),
                "ref": n.get("name") or ""
            })
    except Exception:
        pass

    activities.sort(key=lambda x: x.get("creation", ""), reverse=True)
    activities = activities[:40]

    return {
        "kpis": {
            "open_leads": open_leads + open_crm_leads,
            "open_deals": open_opps + open_crm_deals,
            "pipeline_value": pipeline_value + crm_pipeline_value,
            "won_this_month": (won_erpnext or 0) + (won_crm or 0)
        },
        "erpnext_opportunities": [dict(o) for o in erpnext_opps],
        "crm_deals": [dict(d) for d in crm_deals],
        "crm_deal_statuses": crm_deal_statuses,
        "erpnext_leads": [dict(l) for l in erpnext_leads],
        "crm_leads": [dict(l) for l in crm_leads],
        "activities": activities
    }
