import frappe


def execute():
    # Get all custom fields on CRM Lead (Frappe CRM doctype)
    fields = frappe.get_all(
        "Custom Field",
        filters={"dt": ["in", ["CRM Lead", "Lead"]]},
        fields=["dt", "fieldname", "label", "fieldtype", "options", "insert_after", "in_list_view", "in_standard_filter"]
    )
    print("=== Custom Fields on CRM Lead / Lead ===")
    for f in fields:
        print(f)

    # Also check if mode_of_contact exists anywhere
    moc = frappe.db.get_all("Custom Field", filters={"fieldname": "mode_of_contact"}, fields=["name", "dt", "label"])
    print(f"\n=== mode_of_contact fields ===")
    for f in moc:
        print(f)
