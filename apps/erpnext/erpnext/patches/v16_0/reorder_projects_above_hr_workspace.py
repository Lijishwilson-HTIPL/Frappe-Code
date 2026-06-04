import frappe


def execute():
	frappe.db.set_value("Workspace", "Projects", "sequence_id", 11.0)
	frappe.db.set_value("Workspace", "HR", "sequence_id", 21.0)
