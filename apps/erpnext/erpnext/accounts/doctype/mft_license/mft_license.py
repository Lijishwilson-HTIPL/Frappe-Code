import frappe
import secrets
import string
import datetime
from frappe.model.document import Document
from frappe.utils import today


class MFTLicense(Document):
	pass


# ── Public API ────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def process_payment(stripe_session_id, name, org, email):
	"""
	Called by MFT landing page after Stripe payment is verified.
	Creates: Customer (if new), Sales Invoice, Payment Entry, MFT License.
	Returns: invoice_number, license_key, item_name, amount, purchase_date.
	Idempotent: same stripe_session_id always returns the same result.
	"""
	# ── Idempotency: prevent duplicate processing ─────────────────────────────
	existing = frappe.db.get_value(
		"MFT License",
		{"stripe_session_id": stripe_session_id},
		["name", "license_key", "invoice_number", "amount_paid", "purchase_date"],
		as_dict=True,
	)
	if existing:
		item_name, amount = _get_item_details()
		return {
			"status":         "already_processed",
			"invoice_number": existing.invoice_number,
			"license_key":    existing.license_key,
			"item_name":      item_name,
			"amount":         float(existing.amount_paid or amount),
			"purchase_date":  str(existing.purchase_date),
		}

	# ── Get item details from ERPNext ─────────────────────────────────────────
	item_name, amount = _get_item_details()

	# ── Find or create customer (deduped by email) ────────────────────────────
	customer_name = _find_or_create_customer(name, org, email)

	# ── Get company (prefer USD company) ─────────────────────────────────────
	company = (
		frappe.db.get_value("Company", {"default_currency": "USD"}, "name")
		or frappe.db.get_value("Company", {}, "name")
	)

	# ── Create & submit Sales Invoice ─────────────────────────────────────────
	si = frappe.get_doc({
		"doctype":             "Sales Invoice",
		"company":             company,
		"customer":            customer_name,
		"due_date":            today(),
		"currency":            "USD",
		"conversion_rate":     1.0,
		"selling_price_list":  "Standard Selling",
		"price_list_currency": "USD",
		"plc_conversion_rate": 1.0,
		"items": [{
			"item_code":       "MFT-LIFETIME",
			"qty":             1,
			"rate":            amount,
			"price_list_rate": amount,
		}],
		"remarks": f"Stripe | Session: {stripe_session_id}",
	})
	si.insert(ignore_permissions=True)
	si.submit()
	frappe.db.commit()

	# ── Create & submit Payment Entry ─────────────────────────────────────────
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	pe = get_payment_entry("Sales Invoice", si.name)
	pe.reference_no   = stripe_session_id
	pe.reference_date = today()
	pe.remarks        = f"Stripe Payment | Session: {stripe_session_id}"
	pe.insert(ignore_permissions=True)
	pe.submit()
	frappe.db.commit()

	# ── Generate license key & store MFT License ─────────────────────────────
	license_key = _generate_unique_license_key()

	frappe.get_doc({
		"doctype":           "MFT License",
		"license_key":       license_key,
		"customer":          customer_name,
		"email":             email,
		"invoice_number":    si.name,
		"stripe_session_id": stripe_session_id,
		"product":           "MFT-LIFETIME",
		"purchase_date":     today(),
		"status":            "Active",
		"amount_paid":       amount,
	}).insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status":         "success",
		"invoice_number": si.name,
		"license_key":    license_key,
		"item_name":      item_name,
		"amount":         float(amount),
		"purchase_date":  str(today()),
	}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_item_details():
	item = frappe.get_doc("Item", "MFT-LIFETIME")
	price = frappe.db.get_value(
		"Item Price",
		{"item_code": "MFT-LIFETIME", "selling": 1},
		"price_list_rate",
	)
	return item.item_name, float(price) if price else 999.0


def _find_or_create_customer(name, org, email):
	contact_email = frappe.db.get_value("Contact Email", {"email_id": email}, "parent")
	if contact_email:
		for link in frappe.get_doc("Contact", contact_email).links:
			if link.link_doctype == "Customer":
				return link.link_name

	customer = frappe.get_doc({
		"doctype":          "Customer",
		"customer_name":    org if org else name,
		"customer_type":    "Company" if org else "Individual",
		"customer_group":   "MFT Customers",
		"territory":        "Rest Of The World",
		"default_currency": "USD",
	})
	customer.insert(ignore_permissions=True)

	frappe.get_doc({
		"doctype":    "Contact",
		"first_name": name,
		"email_ids":  [{"email_id": email, "is_primary": 1}],
		"links":      [{"link_doctype": "Customer", "link_name": customer.name}],
	}).insert(ignore_permissions=True)
	frappe.db.commit()

	return customer.name


def _generate_unique_license_key():
	year  = datetime.datetime.now().year
	chars = string.ascii_uppercase + string.digits
	while True:
		part1 = "".join(secrets.choice(chars) for _ in range(4))
		part2 = "".join(secrets.choice(chars) for _ in range(4))
		key   = f"MFT-LIFE-{part1}-{part2}-{year}"
		if not frappe.db.exists("MFT License", {"license_key": key}):
			return key
