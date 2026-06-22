import frappe

def execute():
    # 1. Check page exists
    page_exists = frappe.db.exists("Page", "leads-journey")
    print(f"1. Page 'leads-journey' exists: {page_exists}")

    # 2. Check shortcut in sidebar
    shortcuts = frappe.db.sql(
        "SELECT label, idx, type, link_to FROM `tabWorkspace Shortcut` WHERE parent='CRM' ORDER BY idx",
        as_dict=True
    )
    print(f"2. CRM Sidebar shortcuts:")
    for s in shortcuts:
        marker = " <-- LEADS JOURNEY" if s.link_to == "leads-journey" else ""
        print(f"   [{s.idx}] {s.label} ({s.type} -> {s.link_to}){marker}")

    # 3. Check API works
    from crm_unify.crm_unify.page.leads_journey.leads_journey import get_leads_journey
    result = get_leads_journey(page=1)
    print(f"3. API response: {result['stats']['total']} total leads, {len(result['leads'])} on this page")

    # 4. Check JS file exists
    import os
    js_path = "/home/ijish/frappe-bench/apps/crm_unify/crm_unify/crm_unify/page/leads_journey/leads_journey.js"
    print(f"4. JS file exists: {os.path.exists(js_path)}")
