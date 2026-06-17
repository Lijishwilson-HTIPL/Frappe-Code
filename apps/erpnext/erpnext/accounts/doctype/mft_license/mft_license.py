import frappe
import secrets
import string
import datetime
from frappe.model.document import Document
from frappe.utils import today, add_days


class MFTLicense(Document):
	pass


# ── Plan configuration ────────────────────────────────────────────────────────
PLAN_ITEM_MAP = {
	"monthly":  "MFT-MONTHLY",
	"yearly":   "MFT-YEARLY",
	"lifetime": "MFT-LIFETIME",
}

PLAN_EXPIRY_DAYS = {
	"monthly":  30,
	"yearly":   365,
	"lifetime": None,
}

PLAN_LABEL = {
	"monthly":  "Monthly Subscription",
	"yearly":   "Yearly Subscription",
	"lifetime": "Lifetime",
}

PLAN_PREFIX = {
	"monthly":  "MNTH",
	"yearly":   "YEAR",
	"lifetime": "LIFE",
}


# ── Public API ────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def process_payment(stripe_session_id, name, org, email,
                    plan="lifetime", item_code=None):
	"""
	Called by MFT landing page after Stripe payment is verified.
	Creates: Customer (if new), Sales Invoice, Payment Entry, MFT License.
	Returns: invoice_number, license_key, item_name, amount, purchase_date, expiry.
	Idempotent: same stripe_session_id always returns the same result.
	"""
	plan = (plan or "lifetime").lower()
	if plan not in PLAN_ITEM_MAP:
		plan = "lifetime"

	if not item_code or item_code not in PLAN_ITEM_MAP.values():
		item_code = PLAN_ITEM_MAP[plan]

	purchase_date = today()
	expiry_days   = PLAN_EXPIRY_DAYS[plan]
	expiry        = add_days(purchase_date, expiry_days) if expiry_days else None
	grace_expiry  = add_days(str(expiry), 7) if expiry else None

	# ── Idempotency ───────────────────────────────────────────────────────────
	existing = frappe.db.get_value(
		"MFT License",
		{"stripe_session_id": stripe_session_id},
		["name", "license_key", "invoice_number", "amount_paid",
		 "purchase_date", "expiry", "product"],
		as_dict=True,
	)
	if existing:
		item_name, amount = _get_item_details(item_code)
		return {
			"status":         "already_processed",
			"invoice_number": existing.invoice_number,
			"license_key":    existing.license_key,
			"item_name":      item_name,
			"amount":         float(existing.amount_paid or amount),
			"purchase_date":  str(existing.purchase_date),
			"expiry":         str(existing.expiry) if existing.expiry else None,
			"plan":           plan,
			"extended":       False,
		}

	# ── Layer 2: extend existing license if one already exists ────────────────
	extended_name, extended_expiry = _check_and_extend_existing(email, item_code, expiry_days)
	if extended_name:
		existing_lic = frappe.db.get_value(
			"MFT License", extended_name, ["license_key", "customer"], as_dict=True,
		)
		license_key   = existing_lic.license_key
		expiry        = extended_expiry
		grace_expiry  = add_days(str(expiry), 7) if expiry else None
		customer_name = existing_lic.customer
		item_name, amount = _get_item_details(item_code)

		company = (
			frappe.db.get_value("Company", {"default_currency": "USD"}, "name")
			or frappe.db.get_value("Company", {}, "name")
		)
		si = frappe.get_doc({
			"doctype":             "Sales Invoice",
			"company":             company,
			"customer":            customer_name,
			"due_date":            purchase_date,
			"currency":            "USD",
			"conversion_rate":     1.0,
			"selling_price_list":  "Standard Selling",
			"price_list_currency": "USD",
			"plc_conversion_rate": 1.0,
			"items": [{"item_code": item_code, "qty": 1, "rate": amount, "price_list_rate": amount}],
			"remarks": f"Stripe Renewal | Session: {stripe_session_id} | Plan: {plan}",
		})
		si.insert(ignore_permissions=True)
		si.submit()
		frappe.db.commit()

		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
		pe = get_payment_entry("Sales Invoice", si.name)
		pe.reference_no   = stripe_session_id
		pe.reference_date = purchase_date
		pe.remarks        = f"Stripe Renewal | Session: {stripe_session_id} | Plan: {plan}"
		pe.insert(ignore_permissions=True)
		pe.submit()
		frappe.db.commit()

		frappe.db.set_value("MFT License", extended_name, {
			"stripe_session_id":   stripe_session_id,
			"invoice_number":      si.name,
			"grace_period_expiry": grace_expiry,
			"amount_paid":         amount,
		})
		frappe.db.commit()

		_send_license_email(
			to_name=name, to_email=email, license_key=license_key,
			invoice_number=si.name, item_name=item_name, amount=amount,
			purchase_date=purchase_date, plan=plan, expiry=expiry, is_renewal=True,
		)
		return {
			"status":         "success",
			"invoice_number": si.name,
			"license_key":    license_key,
			"item_name":      item_name,
			"amount":         float(amount),
			"purchase_date":  str(purchase_date),
			"expiry":         str(expiry) if expiry else None,
			"plan":           plan,
			"extended":       True,
		}

	# ── Normal path: new purchase ─────────────────────────────────────────────
	item_name, amount = _get_item_details(item_code)
	customer_name     = _find_or_create_customer(name, org, email)
	company = (
		frappe.db.get_value("Company", {"default_currency": "USD"}, "name")
		or frappe.db.get_value("Company", {}, "name")
	)

	si = frappe.get_doc({
		"doctype":             "Sales Invoice",
		"company":             company,
		"customer":            customer_name,
		"due_date":            purchase_date,
		"currency":            "USD",
		"conversion_rate":     1.0,
		"selling_price_list":  "Standard Selling",
		"price_list_currency": "USD",
		"plc_conversion_rate": 1.0,
		"items": [{"item_code": item_code, "qty": 1, "rate": amount, "price_list_rate": amount}],
		"remarks": f"Stripe | Session: {stripe_session_id} | Plan: {plan}",
	})
	si.insert(ignore_permissions=True)
	si.submit()
	frappe.db.commit()

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	pe = get_payment_entry("Sales Invoice", si.name)
	pe.reference_no   = stripe_session_id
	pe.reference_date = purchase_date
	pe.remarks        = f"Stripe Payment | Session: {stripe_session_id} | Plan: {plan}"
	pe.insert(ignore_permissions=True)
	pe.submit()
	frappe.db.commit()

	license_key = _generate_unique_license_key(plan)

	lic_doc = {
		"doctype":           "MFT License",
		"license_key":       license_key,
		"customer":          customer_name,
		"email":             email,
		"invoice_number":    si.name,
		"stripe_session_id": stripe_session_id,
		"product":           item_code,
		"subscription_plan": plan,
		"purchase_date":     purchase_date,
		"status":            "Active",
		"amount_paid":       amount,
	}
	if expiry:
		lic_doc["expiry"]              = expiry
		lic_doc["grace_period_expiry"] = grace_expiry

	frappe.get_doc(lic_doc).insert(ignore_permissions=True)
	frappe.db.commit()

	_send_license_email(
		to_name=name, to_email=email, license_key=license_key,
		invoice_number=si.name, item_name=item_name, amount=amount,
		purchase_date=purchase_date, plan=plan, expiry=expiry, is_renewal=False,
	)

	return {
		"status":         "success",
		"invoice_number": si.name,
		"license_key":    license_key,
		"item_name":      item_name,
		"amount":         float(amount),
		"purchase_date":  str(purchase_date),
		"expiry":         str(expiry) if expiry else None,
		"plan":           plan,
		"extended":       False,
	}


@frappe.whitelist(allow_guest=True)
def check_active_license(email, plan):
	"""
	Layer 1: called by frontend BEFORE Stripe redirect.
	Returns has_active=False if no non-expired Active license exists.
	"""
	plan = (plan or "lifetime").lower()
	if plan not in PLAN_ITEM_MAP:
		plan = "lifetime"
	item_code = PLAN_ITEM_MAP[plan]

	lic = frappe.db.get_value(
		"MFT License",
		{"email": email, "product": item_code, "status": "Active"},
		["name", "license_key", "expiry", "purchase_date", "subscription_plan"],
		as_dict=True,
	)
	if lic and not (lic.expiry and str(lic.expiry) < today()):
		return {
			"has_active":    True,
			"is_upgrade":    False,
			"license_key":   lic.license_key,
			"expiry":        str(lic.expiry) if lic.expiry else None,
			"purchase_date": str(lic.purchase_date),
			"existing_plan": lic.subscription_plan or plan,
			"new_plan":      plan,
		}

	lic_other = frappe.db.get_value(
		"MFT License",
		{"email": email, "status": "Active"},
		["name", "license_key", "expiry", "purchase_date", "subscription_plan", "product"],
		as_dict=True,
	)
	if not lic_other:
		return {"has_active": False}
	if lic_other.expiry and str(lic_other.expiry) < today():
		return {"has_active": False}

	_item_plan_map = {v: k for k, v in PLAN_ITEM_MAP.items()}
	existing_plan = lic_other.subscription_plan or _item_plan_map.get(lic_other.product, "lifetime")
	return {
		"has_active":    True,
		"is_upgrade":    _plan_rank(plan) > _plan_rank(existing_plan),
		"license_key":   lic_other.license_key,
		"expiry":        str(lic_other.expiry) if lic_other.expiry else None,
		"purchase_date": str(lic_other.purchase_date),
		"existing_plan": existing_plan,
		"new_plan":      plan,
	}


@frappe.whitelist(allow_guest=True)
def check_email_registration(email):
	"""
	Pre-layer check: is this email registered in any MFT License (any status)?
	Returns registered_org so the frontend can warn if the entered org doesn't match.
	Fail-open: returns registered=False if no matching customer found.
	"""
	licenses = frappe.db.get_all(
		"MFT License",
		filters={"email": email},
		fields=["name", "customer"],
		order_by="creation desc",
		limit=1,
	)
	if not licenses:
		return {"registered": False}

	customer_id = licenses[0].get("customer")
	if not customer_id:
		return {"registered": False}

	org = frappe.db.get_value("Customer", customer_id, "customer_name") or ""
	if not org:
		return {"registered": False}

	return {"registered": True, "registered_org": org}


def _plan_rank(plan):
	return {"monthly": 1, "yearly": 2, "lifetime": 3}.get(plan, 0)


@frappe.whitelist(allow_guest=True)
def extend_license(stripe_session_id, email, plan, invoice_name):
	"""
	Called after a renewal payment is confirmed (via webhook or polling).
	Extends the existing Active MFT License expiry.
	Idempotent: same stripe_session_id always returns the same result.
	"""
	plan = (plan or "monthly").lower()
	if plan not in PLAN_ITEM_MAP or plan == "lifetime":
		frappe.throw("extend_license is not applicable for this plan")

	item_code   = PLAN_ITEM_MAP[plan]
	expiry_days = PLAN_EXPIRY_DAYS[plan]

	existing = frappe.db.get_value(
		"MFT License",
		{"stripe_session_id": stripe_session_id},
		["name", "license_key", "expiry", "invoice_number"],
		as_dict=True,
	)
	if existing:
		item_name, amount = _get_item_details(item_code)
		return {
			"status":         "already_processed",
			"license_key":    existing.license_key,
			"invoice_number": existing.invoice_number,
			"item_name":      item_name,
			"amount":         float(amount),
			"expiry":         str(existing.expiry) if existing.expiry else None,
			"plan":           plan,
			"extended":       True,
		}

	lic = frappe.db.get_value(
		"MFT License",
		{"email": email, "status": "Active"},
		["name", "license_key", "expiry", "customer", "product", "subscription_plan"],
		as_dict=True,
	)
	if not lic:
		frappe.throw(f"No active MFT License found for {email}")

	from frappe.utils import getdate
	base_date    = max(getdate(today()), getdate(str(lic.expiry))) if lic.expiry else getdate(today())
	new_expiry   = add_days(str(base_date), expiry_days)
	grace_expiry = add_days(str(new_expiry), 7)
	purchase_date = today()

	item_name, amount = _get_item_details(item_code)

	try:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
		pe = get_payment_entry("Sales Invoice", invoice_name)
		pe.reference_no   = stripe_session_id
		pe.reference_date = purchase_date
		pe.remarks        = f"Stripe Renewal | Session: {stripe_session_id} | Plan: {plan}"
		pe.insert(ignore_permissions=True)
		pe.submit()
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"MFT extend_license: Payment Entry failed for {invoice_name}: {e}")

	frappe.db.set_value("MFT License", lic.name, {
		"expiry":              new_expiry,
		"grace_period_expiry": grace_expiry,
		"stripe_session_id":   stripe_session_id,
		"invoice_number":      invoice_name,
		"amount_paid":         amount,
		"subscription_plan":   plan,
		"product":             item_code,
	})
	frappe.db.commit()

	customer_name = frappe.db.get_value("Customer", lic.customer, "customer_name") or lic.customer

	_send_license_email(
		to_name=customer_name, to_email=email,
		license_key=lic.license_key, invoice_number=invoice_name,
		item_name=item_name, amount=amount,
		purchase_date=purchase_date, plan=plan, expiry=new_expiry,
		is_renewal=True,
	)

	return {
		"status":         "success",
		"license_key":    lic.license_key,
		"invoice_number": invoice_name,
		"item_name":      item_name,
		"amount":         float(amount),
		"purchase_date":  str(purchase_date),
		"expiry":         str(new_expiry),
		"plan":           plan,
		"extended":       True,
	}


def send_renewal_requests():
	"""
	Scheduled daily job.
	Finds Active licenses expiring within mft_renewal_days_ahead days (default 7).
	Creates unpaid Sales Invoice → calls Express for Stripe URL → sends renewal email.
	"""
	import requests as http_req

	RENEWAL_DAYS_AHEAD = int(frappe.conf.get("mft_renewal_days_ahead") or 7)
	EXPRESS_URL        = frappe.conf.get("mft_express_url") or "http://localhost:5010"
	expiry_to          = add_days(today(), RENEWAL_DAYS_AHEAD)

	licenses = frappe.db.get_all(
		"MFT License",
		filters={"status": "Active", "expiry": ["between", [today(), expiry_to]]},
		fields=["name", "email", "license_key", "expiry", "product",
		        "subscription_plan", "customer", "amount_paid"],
	)

	_item_plan_map = {v: k for k, v in PLAN_ITEM_MAP.items()}

	for lic in licenses:
		plan = lic.subscription_plan or _item_plan_map.get(lic.product, "lifetime")
		if plan == "lifetime":
			continue
		item_code = PLAN_ITEM_MAP.get(plan)
		if not item_code:
			continue

		# Skip if unpaid renewal invoice already exists
		existing_invoice = frappe.db.get_value(
			"Sales Invoice",
			{"customer": lic.customer, "status": ["in", ["Unpaid", "Overdue"]],
			 "remarks": ["like", f"%Renewal%{lic.name}%"]},
			"name",
		)
		if existing_invoice:
			continue

		item_name, amount = _get_item_details(item_code)
		customer_name = frappe.db.get_value("Customer", lic.customer, "customer_name") or lic.customer
		company = (
			frappe.db.get_value("Company", {"default_currency": "USD"}, "name")
			or frappe.db.get_value("Company", {}, "name")
		)

		try:
			si = frappe.get_doc({
				"doctype":             "Sales Invoice",
				"company":             company,
				"customer":            lic.customer,
				"due_date":            today(),
				"currency":            "USD",
				"conversion_rate":     1.0,
				"selling_price_list":  "Standard Selling",
				"price_list_currency": "USD",
				"plc_conversion_rate": 1.0,
				"items": [{"item_code": item_code, "qty": 1, "rate": amount, "price_list_rate": amount}],
				"remarks": f"MFT Renewal | License: {lic.name} | Plan: {plan}",
			})
			si.insert(ignore_permissions=True)
			si.submit()
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"MFT Renewal: Invoice creation failed for {lic.email}: {e}")
			continue

		stripe_url = None
		try:
			resp = http_req.post(
				f"{EXPRESS_URL}/mft/create-renewal-session",
				json={"email": lic.email, "plan": plan, "invoiceNumber": si.name,
				      "customerName": customer_name, "amount": str(float(amount))},
				timeout=15,
			)
			if resp.ok:
				stripe_url = resp.json().get("url")
		except Exception as e:
			frappe.log_error(f"MFT Renewal: Express call failed for {lic.email}", "MFT Renewal Error")

		if not stripe_url:
			frappe.log_error(
				f"MFT Renewal: No Stripe URL for {lic.email} — invoice {si.name} not sent",
				"MFT Renewal Error",
			)
			continue

		_send_renewal_request_email(
			to_name=customer_name, to_email=lic.email,
			license_key=lic.license_key, invoice_number=si.name,
			item_name=item_name, amount=amount,
			current_expiry=lic.expiry, plan=plan, payment_url=stripe_url,
		)


def auto_expire_licenses():
	"""
	Scheduled daily job.
	Finds Active licenses whose grace_period_expiry has passed → sets status = Expired.
	Skips Lifetime licenses (grace_period_expiry is null/empty).
	"""
	expired = frappe.db.get_all(
		"MFT License",
		filters=[
			["status", "=", "Active"],
			["grace_period_expiry", "is", "set"],
			["grace_period_expiry", "<", today()],
		],
		fields=["name", "email", "license_key", "grace_period_expiry"],
	)

	for lic in expired:
		frappe.db.set_value("MFT License", lic.name, "status", "Expired")
		frappe.log_error(
			f"MFT License {lic.name} ({lic.license_key}) expired for {lic.email} "
			f"— grace_period_expiry was {lic.grace_period_expiry}",
			"MFT License Expired",
		)

	if expired:
		frappe.db.commit()


def restore_all_to_active():
	"""ONE-TIME restore: resets all Expired licenses to Active (emergency use only)."""
	frappe.db.sql("UPDATE `tabMFT License` SET status='Active' WHERE status='Expired'")
	frappe.db.commit()


def _send_renewal_request_email(to_name, to_email, license_key, invoice_number,
                                 item_name, amount, current_expiry, plan, payment_url):
	"""Sends the renewal due email with Stripe Pay Now button (BEFORE payment)."""
	year       = datetime.datetime.now().year
	amount_str = f"${float(amount or 0):.2f} USD"
	plan_label = PLAN_LABEL.get(plan, "Subscription")
	expiry_str = str(current_expiry) if current_expiry else "—"

	html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#0d1117;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d1117;padding:40px 20px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:20px;overflow:hidden;">
        <tr>
          <td style="background-color:#1a233a;padding:36px 32px;text-align:center;">
            <div style="font-size:28px;font-weight:800;color:#4078f2;">Hephzibah Technologies</div>
            <div style="color:#94a3b8;font-size:14px;margin-top:6px;">MFT Platform — License Renewal</div>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 32px 0 32px;">
            <p style="margin:0;font-size:16px;color:#111827;">Dear <strong>{to_name}</strong>,</p>
            <p style="margin:12px 0 0 0;font-size:15px;color:#374151;line-height:1.6;">
              Your MFT Platform license is expiring on <strong>{expiry_str}</strong>.
              Renew now to continue uninterrupted access.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
              <tr><td style="padding:16px 24px;border-bottom:1px solid #e2e8f0;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Invoice</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{invoice_number}</div>
              </td></tr>
              <tr><td style="padding:16px 24px;border-bottom:1px solid #e2e8f0;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Plan</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{plan_label}</div>
              </td></tr>
              <tr><td style="padding:16px 24px;border-bottom:1px solid #e2e8f0;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Amount Due</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{amount_str}</div>
              </td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Current Expiry</div>
                <div style="color:#dc2626;font-size:15px;font-weight:700;">{expiry_str}</div>
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 32px 32px 32px;text-align:center;">
            <a href="{payment_url}" style="display:inline-block;background:#4078f2;color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;padding:16px 48px;border-radius:10px;">
              Renew Now →
            </a>
            <p style="margin:16px 0 0 0;font-size:13px;color:#6b7280;">
              Your license key <strong>{license_key}</strong> stays the same after renewal.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0;font-size:13px;color:#6b7280;">
              Questions? Contact <a href="mailto:support@hephzibahtech.com" style="color:#4078f2;text-decoration:none;">support@hephzibahtech.com</a>
            </p>
            <p style="margin:8px 0 0 0;font-size:12px;color:#9ca3af;">&copy; {year} Hephzibah Technologies. All rights reserved.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

	frappe.sendmail(
		recipients=[to_email],
		subject="Your MFT License Renewal is Due — Hephzibah Technologies",
		message=html,
		now=False,
	)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _check_and_extend_existing(email, item_code, expiry_days):
	"""
	Layer 2: finds an existing Active license and extends it.
	Case A — same plan: extends expiry from max(today, current_expiry).
	Case B — upgrade: updates product+plan, extends expiry.
	Lifetime (expiry_days=None) always returns (None, None).
	"""
	if expiry_days is None:
		return None, None

	from frappe.utils import getdate

	lic = frappe.db.get_value(
		"MFT License",
		{"email": email, "product": item_code, "status": "Active"},
		["name", "expiry"], as_dict=True,
	)
	if lic:
		base_date  = max(getdate(today()), getdate(str(lic.expiry))) if lic.expiry else getdate(today())
		new_expiry = add_days(str(base_date), expiry_days)
		frappe.db.set_value("MFT License", lic.name, "expiry", new_expiry)
		frappe.db.commit()
		return lic.name, new_expiry

	lic_other = frappe.db.get_value(
		"MFT License",
		{"email": email, "status": "Active"},
		["name", "expiry", "product", "subscription_plan"], as_dict=True,
	)
	if not lic_other:
		return None, None
	if lic_other.expiry and getdate(str(lic_other.expiry)) < getdate(today()):
		return None, None

	new_plan   = next((p for p, c in PLAN_ITEM_MAP.items() if c == item_code), "yearly")
	base_date  = max(getdate(today()), getdate(str(lic_other.expiry))) if lic_other.expiry else getdate(today())
	new_expiry = add_days(str(base_date), expiry_days)

	frappe.db.set_value("MFT License", lic_other.name, {
		"expiry":            new_expiry,
		"product":           item_code,
		"subscription_plan": new_plan,
	})
	frappe.db.commit()
	return lic_other.name, new_expiry


def _get_item_details(item_code="MFT-LIFETIME"):
	try:
		item = frappe.get_doc("Item", item_code)
	except frappe.DoesNotExistError:
		item_code = "MFT-LIFETIME"
		item = frappe.get_doc("Item", item_code)

	price = frappe.db.get_value(
		"Item Price", {"item_code": item_code, "selling": 1}, "price_list_rate",
	)
	FALLBACK = {"MFT-MONTHLY": 9.0, "MFT-YEARLY": 99.0, "MFT-LIFETIME": 999.0}
	return item.item_name, float(price) if price else FALLBACK.get(item_code, 999.0)


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


def _generate_unique_license_key(plan="lifetime"):
	year   = datetime.datetime.now().year
	chars  = string.ascii_uppercase + string.digits
	prefix = PLAN_PREFIX.get(plan, "LIFE")
	while True:
		part1 = "".join(secrets.choice(chars) for _ in range(4))
		part2 = "".join(secrets.choice(chars) for _ in range(4))
		key   = f"MFT-{prefix}-{part1}-{part2}-{year}"
		if not frappe.db.exists("MFT License", {"license_key": key}):
			return key


def _send_license_email(to_name, to_email, license_key, invoice_number,
                        item_name, amount, purchase_date, plan="lifetime",
                        expiry=None, is_renewal=False):
	download_url = frappe.conf.get("mft_download_url", "https://qa.htmft.com/HT/MFTv2.1/#/")
	year         = datetime.datetime.now().year
	amount_str   = f"${float(amount or 0):.2f} USD"
	validity_label = f"Valid until {str(expiry)}" if expiry else "Lifetime"
	validity_color = "#2563eb" if expiry else "#16a34a"
	plan_label     = PLAN_LABEL.get(plan, "Lifetime")
	subject = (
		"Your MFT License Renewed — Hephzibah Technologies" if is_renewal
		else "Your MFT License Key — Hephzibah Technologies"
	)
	intro = (
		"Your renewal payment has been confirmed. Your license expiry has been extended." if is_renewal
		else "Your payment has been confirmed and your license is ready to use."
	)

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
            <p style="margin:12px 0 0 0;font-size:15px;color:#374151;line-height:1.6;">{intro}</p>
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
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Plan</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{plan_label}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Amount Paid</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{amount_str}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Purchase Date</div>
                <div style="color:#111827;font-size:15px;font-weight:600;">{str(purchase_date)}</div>
              </td></tr>
              <tr><td style="height:1px;background:#e2e8f0;"></td></tr>
              <tr><td style="padding:16px 24px;">
                <div style="color:#9ca3af;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Validity</div>
                <div style="color:{validity_color};font-size:15px;font-weight:700;">{validity_label}</div>
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

	frappe.sendmail(
		recipients=[to_email],
		subject=subject,
		message=html,
		now=False,
	)
