# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe
from frappe import _
from frappe.apps import get_apps


def get_context():
	all_apps = get_apps()

	system_default_app = frappe.get_system_settings("default_app")
	user_default_app = frappe.db.get_value("User", frappe.session.user, "default_app")
	default_app = user_default_app if user_default_app else system_default_app

	if len(all_apps) == 0:
		frappe.local.flags.redirect_location = "/app"
		raise frappe.Redirect

	for app in all_apps:
		app["is_default"] = True if app.get("name") == default_app else False

	company_name = (
		frappe.db.get_single_value("System Settings", "app_name")
		or frappe.conf.get("app_name")
		or "Hephzibah Technologies"
	)

	return {"apps": all_apps, "company_name": company_name}
