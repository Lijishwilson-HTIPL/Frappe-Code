"""
Demo setup for CRM → Sales Invoice flow.

Run via bench console:
    bench --site mysite.local execute crm.demo.setup_invoice_demo.run
"""

import frappe


def run():
	frappe.set_user("Administrator")

	_ensure_company()
	_ensure_income_account()
	_ensure_items()
	_ensure_customer()
	_configure_erpnext_crm_settings()
	_create_demo_deal()

	frappe.db.commit()
	print("Demo setup complete.")


def _ensure_company():
	if frappe.db.exists("Company", "Demo Company"):
		return
	company = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": "Demo Company",
			"abbr": "DC",
			"default_currency": "INR",
			"country": "India",
		}
	)
	company.insert(ignore_permissions=True)
	print("Created company: Demo Company")


def _ensure_income_account():
	"""Ensure a Sales income account exists under Demo Company."""
	company = "Demo Company"
	if not frappe.db.exists("Account", {"account_name": "Sales", "company": company}):
		# Let ERPNext create chart of accounts automatically via company creation
		pass
	print("Income account check done.")


def _ensure_items():
	items = [
		{"item_code": "ITEM-001", "item_name": "Consulting Services", "standard_selling_rate": 5000},
		{"item_code": "ITEM-002", "item_name": "Software License", "standard_selling_rate": 10000},
		{"item_code": "ITEM-003", "item_name": "Annual Support", "standard_selling_rate": 3000},
	]
	for i in items:
		if not frappe.db.exists("Item", i["item_code"]):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": i["item_code"],
					"item_name": i["item_name"],
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
					"is_stock_item": 0,
					"is_sales_item": 1,
					"standard_rate": i["standard_selling_rate"],
				}
			).insert(ignore_permissions=True)
			print(f"Created item: {i['item_code']}")

		# Also create matching CRM Product so CRM deals can reference them
		if not frappe.db.exists("CRM Product", i["item_code"]):
			frappe.get_doc(
				{
					"doctype": "CRM Product",
					"product_code": i["item_code"],
					"product_name": i["item_name"],
					"standard_rate": i["standard_selling_rate"],
				}
			).insert(ignore_permissions=True)
			print(f"Created CRM Product: {i['item_code']}")


def _get_leaf_customer_group():
	group = frappe.db.get_value(
		"Customer Group", {"is_group": 0}, "name"
	)
	if not group:
		frappe.throw("No non-group Customer Group found. Please create one first.")
	return group


def _get_leaf_territory():
	territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
	return territory or "All Territories"


def _ensure_customer():
	if not frappe.db.exists("Customer", "Demo Customer"):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Demo Customer",
				"customer_group": _get_leaf_customer_group(),
				"customer_type": "Company",
				"territory": _get_leaf_territory(),
			}
		).insert(ignore_permissions=True)
		print("Created customer: Demo Customer")

	# Ensure matching CRM Organization
	if not frappe.db.exists("CRM Organization", "Demo Customer"):
		frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Demo Customer",
			}
		).insert(ignore_permissions=True)
		print("Created CRM Organization: Demo Customer")


def _configure_erpnext_crm_settings():
	settings = frappe.get_single("ERPNext CRM Settings")
	settings.enabled = 1
	settings.is_erpnext_in_different_site = 0
	settings.erpnext_company = "Demo Company"
	settings.create_customer_on_status_change = 1

	# Map to a "Won" deal status — adjust name to match your setup
	won_status = frappe.db.get_value("CRM Deal Status", {"deal_status": "Won"}, "name")
	if not won_status:
		won_status = frappe.db.get_value("CRM Deal Status", {"type": "Won"}, "name")
	if not won_status:
		won_status = frappe.db.get_value("CRM Deal Status", {}, "name")
	settings.deal_status = won_status
	settings.save(ignore_permissions=True)
	print(f"ERPNext CRM Settings configured. Deal status trigger: {won_status}")


def _create_demo_deal():
	if frappe.db.exists("CRM Deal", {"lead_name": "Demo Deal"}):
		print("Demo deal already exists, skipping.")
		return

	deal = frappe.get_doc(
		{
			"doctype": "CRM Deal",
			"lead_name": "Demo Deal",
			"organization": "Demo Customer",
			"currency": "INR",
			"deal_value": 18000,
			"status": (
				frappe.db.get_value("CRM Deal Status", {"type": "Open"}, "name")
				or frappe.db.get_value("CRM Deal Status", {"deal_status": ("not in", ["Lost", "Won"])}, "name")
				or frappe.db.get_value("CRM Deal Status", {}, "name")
			),
		}
	)
	deal.append("products", {"product_code": "ITEM-001", "product_name": "Consulting Services", "qty": 1, "rate": 5000})
	deal.append("products", {"product_code": "ITEM-002", "product_name": "Software License", "qty": 1, "rate": 10000})
	deal.append("products", {"product_code": "ITEM-003", "product_name": "Annual Support", "qty": 1, "rate": 3000})
	deal.insert(ignore_permissions=True)
	print(f"Created demo deal: {deal.name}")
	print(
		f"\nTo trigger invoice: change deal status to 'Won' in the CRM UI, "
		f"or run:\n  frappe.set_value('CRM Deal', '{deal.name}', 'status', <won-status>)"
	)
