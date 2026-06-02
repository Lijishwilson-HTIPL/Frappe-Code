import frappe
import random
import string


@frappe.whitelist(allow_guest=True)
def generate_otp(email):
	email = email.strip().lower()

	license_doc = frappe.db.get_value(
		"MFT License", {"email": email}, ["name", "customer"], as_dict=True
	)
	if not license_doc:
		frappe.throw("No license found for this email address.", frappe.DoesNotExistError)

	otp = "".join(random.choices(string.digits, k=6))
	cache_key = f"mft_otp_{email}"
	frappe.cache().set_value(cache_key, otp, expires_in_sec=600)

	frappe.sendmail(
		recipients=[email],
		subject="Your MFT License OTP",
		message=f"""
		<p>Hello {license_doc.customer},</p>
		<p>Your One-Time Password to access your MFT License details is:</p>
		<h2 style="letter-spacing: 8px; font-family: monospace;">{otp}</h2>
		<p>This OTP is valid for <strong>10 minutes</strong>.</p>
		<p>If you did not request this, please ignore this email.</p>
		<br>
		<p>— SBIQ Core | Hephzibah Technologies</p>
		""",
		now=True,
	)

	return {"message": "OTP sent successfully"}


@frappe.whitelist(allow_guest=True)
def verify_otp(email, otp):
	email = email.strip().lower()
	otp = otp.strip()

	cache_key = f"mft_otp_{email}"
	stored_otp = frappe.cache().get_value(cache_key)

	if not stored_otp:
		frappe.throw("OTP has expired. Please generate a new one.")

	if stored_otp != otp:
		frappe.throw("Invalid OTP. Please try again.")

	frappe.cache().delete_value(cache_key)

	doc = frappe.db.get_value(
		"MFT License",
		{"email": email},
		["license_key", "status", "customer", "email", "product", "purchase_date", "expiry", "amount_paid", "invoice_number"],
		as_dict=True,
	)

	if not doc:
		frappe.throw("License not found.")

	return {
		"license_key": doc.license_key,
		"status": doc.status,
		"customer": doc.customer,
		"email": doc.email,
		"product": doc.product,
		"purchase_date": str(doc.purchase_date) if doc.purchase_date else None,
		"expiry": str(doc.expiry) if doc.expiry else "Lifetime",
		"amount_paid": doc.amount_paid,
		"invoice_number": doc.invoice_number,
	}
