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

	# Company name: Website Settings takes priority over System Settings
	company_name = (
		frappe.get_website_settings("apps_drawer_name")
		or frappe.db.get_single_value("System Settings", "app_name")
		or frappe.conf.get("app_name")
		or "Hephzibah Technologies"
	)

	# Apply ordering/hiding from Apps Drawer config
	drawer_config = frappe.get_all(
		"Website Apps Drawer App",
		filters={"parenttype": "Website Settings", "parentfield": "apps_drawer_apps"},
		fields=["app_name", "title", "logo", "is_hidden"],
		order_by="idx asc",
	)
	if drawer_config:
		hidden = {r.app_name for r in drawer_config if r.is_hidden}
		order_map = {r.app_name: i for i, r in enumerate(drawer_config)}
		title_map = {r.app_name: r.title for r in drawer_config if r.title}
		logo_map = {r.app_name: r.logo for r in drawer_config if r.logo}
		# Apply custom titles — clear title if drawer row has no Display Title set
		drawer_apps = {r.app_name for r in drawer_config}
		for app in all_apps:
			if app.get("name") in title_map:
				app["title"] = title_map[app["name"]]
			elif app.get("name") in drawer_apps:
				app["title"] = ""
		# Filter hidden apps, sort by configured order (unlisted apps go to end)
		all_apps = [a for a in all_apps if a.get("name") not in hidden]
		all_apps.sort(key=lambda a: order_map.get(a.get("name"), 9999))
		# Apply custom logos — overrides the hook-defined logo when set in drawer config
		for app in all_apps:
			if app.get("name") in logo_map:
				app["logo"] = logo_map[app["name"]]

	return {"apps": all_apps, "company_name": company_name}
