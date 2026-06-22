import frappe


def execute():
    for dt in ["CRM Lead", "Lead"]:
        fields = frappe.get_all(
            "Custom Field",
            filters={"dt": dt},
            fields=["fieldname", "label", "fieldtype", "options", "insert_after"],
            order_by="idx asc"
        )
        print(f"\n=== Custom Fields on {dt} ({len(fields)}) ===")
        for f in fields:
            print(f"  {f['fieldname']} | {f['fieldtype']} | {f['label']} | opts={f.get('options','')}")
