import frappe


def execute():
	"""Delete leftover DB-only Custom Fields on Task.

	These fields are now part of the Task doctype JSON (sprint, is_blocked,
	cancel_reason, resolution_note, subtasks_html), so any Custom Field docs
	created earlier via Customize Form must be removed to avoid duplicates.
	"""
	for custom_field in (
		"Task-sprint",
		"Task-is_blocked",
		"Task-cancel_reason",
		"Task-resolution_note",
		"Task-subtasks_html",
	):
		frappe.delete_doc("Custom Field", custom_field, ignore_missing=True)
