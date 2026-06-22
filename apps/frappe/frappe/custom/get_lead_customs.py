import frappe


def execute():
    fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Lead"},
        fields=["fieldname", "label", "fieldtype", "options", "insert_after", "in_list_view", "in_standard_filter"]
    )
    print("=== Custom Fields on Lead ===")
    for f in fields:
        print(f)
    print(f"Total: {len(fields)}")
