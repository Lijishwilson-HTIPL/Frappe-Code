import frappe


def execute():
	frappe.reload_doc("setup", "doctype", "career_inquiry")
	frappe.reload_doc("setup", "web_form", "career_inquiry")
	frappe.reload_doc("setup", "workspace", "careers")
