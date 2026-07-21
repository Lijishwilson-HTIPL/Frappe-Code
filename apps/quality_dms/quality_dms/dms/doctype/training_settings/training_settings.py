# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TrainingSettings(Document):
	pass


def get_pass_percentage():
	value = frappe.db.get_single_value("Training Settings", "default_pass_percentage")
	return value if value not in (None, 0) else 80.0


def get_retraining_months():
	value = frappe.db.get_single_value("Training Settings", "default_retraining_months")
	return value if value not in (None, 0) else 12


def get_escalation_days():
	value = frappe.db.get_single_value("Training Settings", "escalation_days")
	return value if value not in (None, 0) else 3
