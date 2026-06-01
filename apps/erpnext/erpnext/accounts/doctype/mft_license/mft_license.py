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

	purchase_date = today()

	frappe.get_doc({
		"doctype":           "MFT License",
		"license_key":       license_key,
		"customer":          customer_name,
		"email":             email,
		"invoice_number":    si.name,
		"stripe_session_id": stripe_session_id,
		"product":           "MFT-LIFETIME",
		"purchase_date":     purchase_date,
		"status":            "Active",
		"amount_paid":       amount,
	}).insert(ignore_permissions=True)
	frappe.db.commit()

	# ── Send license email via Frappe outgoing email ──────────────────────────
	_send_license_email(
		to_name=name,
		to_email=email,
		license_key=license_key,
		invoice_number=si.name,
		amount=amount,
		purchase_date=purchase_date,
	)

	return {
		"status":         "success",
		"invoice_number": si.name,
		"license_key":    license_key,
		"item_name":      item_name,
		"amount":         float(amount),
		"purchase_date":  str(purchase_date),
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


def _send_license_email(to_name, to_email, license_key, invoice_number, amount, purchase_date):
	download_url  = "https://qa.htmft.com/HT/MFTv2.1/#/"
	year          = datetime.datetime.now().year
	formatted_date = str(purchase_date)
	amount_str    = f"${float(amount or 999):.2f} USD"
	item_name     = "MFT Platform Lifetime License"

	html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#0d1117;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d1117;padding:40px 20px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:20px;overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#1a233a 0%,#0d1117 100%);padding:36px 32px;text-align:center;">
            <div style="font-size:28px;font-weight:800;color:#4078f2;">Hephzibah Technologies</div>
            <div style="color:#94a3b8;font-size:14px;margin-top:6px;">MFT Platform — License Delivery</div>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 32px 0 32px;">
            <p style="margin:0;font-size:16px;color:#111827;">Dear <strong>{to_name}</strong>,</p>
            <p style="margin:12px 0 0 0;font-size:15px;color:#374151;line-height:1.6;">
              Thank you for purchasing <strong>{item_name}</strong>. Your payment has been confirmed and your license is ready to use.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
              <tr><td style="padding:20px 24px;background:#1a233a;">
                <div style="color:#94a3b8;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">License Key</div>
                <div style="color:#ffffff;font-size:22px;font-weight:800;letter-spacing:0.12em;margin-top:6px;font-family:'Courier New',monospace;">{license_key}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Invoice Number</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{invoice_number}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Product</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{item_name}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Amount Paid</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{amount_str}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Purchase Date</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{formatted_date}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Validity</div>
                <div style="color:#16a34a;font-size:15px;font-weight:700;">Lifetime</div>
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 32px 32px 32px;text-align:center;">
            <a href="{download_url}" style="display:inline-block;background:#4078f2;color:#ffffff;text-decoration:none;font-size:15px;font-weight:700;padding:14px 36px;border-radius:10px;">
              Access MFT Platform
            </a>
            <p style="margin:16px 0 0 0;font-size:13px;color:#6b7280;">
              Use your license key above to activate the product after login.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0;font-size:13px;color:#6b7280;">
              Questions? Reply to this email or contact
              <a href="mailto:support@hephzibahtech.com" style="color:#4078f2;text-decoration:none;">support@hephzibahtech.com</a>
            </p>
            <p style="margin:8px 0 0 0;font-size:12px;color:#9ca3af;">&copy; {year} Hephzibah Technologies. All rights reserved.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

	text = f"""Dear {to_name},

Thank you for purchasing {item_name}.

LICENSE KEY   : {license_key}
INVOICE       : {invoice_number}
PRODUCT       : {item_name}
AMOUNT PAID   : {amount_str}
PURCHASE DATE : {formatted_date}
VALIDITY      : Lifetime

Access MFT Platform: {download_url}

Use your license key to activate the product after login.

Questions? Contact support@hephzibahtech.com

— Hephzibah Technologies"""

	frappe.sendmail(
		recipients=[to_email],
		subject="Your MFT License Key — Hephzibah Technologies",
		message=html,
		now=False,
	)
