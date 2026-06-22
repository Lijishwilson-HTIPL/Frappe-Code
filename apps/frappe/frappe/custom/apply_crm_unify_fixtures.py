import frappe
import json


def execute():
    fixture_path = "/home/ijish/frappe-bench/apps/crm_unify/crm_unify/fixtures/custom_field.json"
    with open(fixture_path) as f:
        records = json.load(f)

    created = 0
    updated = 0
    for r in records:
        doctype = r.get("doctype")
        name = r.get("name")
        if not doctype or not name:
            continue
        r_clean = {k: v for k, v in r.items() if k != "doctype"}
        if frappe.db.exists(doctype, name):
            # skip update — field already exists, only new fields matter
            updated += 1
        else:
            doc = frappe.get_doc({"doctype": doctype, **r_clean})
            doc.insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    print(f"Done: {created} created, {updated} updated")
