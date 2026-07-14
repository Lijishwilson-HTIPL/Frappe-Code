import frappe


@frappe.whitelist()
def get_leads_journey(page=1, status=None, page_size=20):
	page = int(page)
	page_size = int(page_size)

	filters = {"status": ["!=", "Converted"]}
	if status and status != "null":
		filters["status"] = status

	total = frappe.db.count("Lead", filters=filters)

	leads = frappe.get_list(
		"Lead",
		filters=filters,
		fields=["name", "lead_name", "company_name", "status", "lead_owner", "modified", "lead_stage"],
		order_by="modified desc",
		start=(page - 1) * page_size,
		page_length=page_size,
	)

	total_leads = frappe.db.count("Lead")
	qualified = frappe.db.count("Lead", filters={"status": "Interested"})
	converted = frappe.db.count("Lead", filters={"status": "Converted"})
	conversion_rate = round(converted / total_leads * 100) if total_leads else 0

	return {
		"leads": leads,
		"total": total,
		"page_size": page_size,
		"stats": {
			"total": total_leads,
			"qualified": qualified,
			"converted": converted,
			"conversion_rate": conversion_rate,
		},
	}
