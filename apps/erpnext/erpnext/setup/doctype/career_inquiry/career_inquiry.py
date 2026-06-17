import frappe
from frappe.model.document import Document


class CareerInquiry(Document):
	def after_insert(self):
		if self.job_applicant_ref:
			return
		create_job_applicant(self)


def create_job_applicant(doc):
	try:
		applicant = frappe.get_doc({
			"doctype": "Job Applicant",
			"applicant_name": f"{doc.first_name} {doc.last_name}".strip(),
			"email_id": doc.email,
			"phone_number": doc.phone_number,
			"resume_attachment": doc.resume_link,
			"cover_letter": doc.tell_us_about_yourself,
			"role_applying_for": doc.role_applying_for,
			"years_of_experience": doc.years_of_experience,
			"linkedin_profile_url": doc.linkedin_profile_url,
			"portfolio_site": doc.portfolio_site,
			"how_did_you_hear": doc.how_did_you_hear,
			"other_source": doc.other_source,
			"status": "Open",
		})
		applicant.insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Career Inquiry: Failed to create Job Applicant")


@frappe.whitelist(allow_guest=True)
def submit_career_inquiry(
	first_name,
	last_name,
	email,
	phone_number,
	role_applying_for,
	years_of_experience,
	linkedin_profile_url,
	tell_us_about_yourself,
	resume_link=None,
	portfolio_site=None,
	how_did_you_hear=None,
	other_source=None,
	job_applicant_ref=None,
):
	hear_value = how_did_you_hear
	other_value = other_source

	if how_did_you_hear and how_did_you_hear.startswith("Other:"):
		hear_value = "Other"
		other_value = how_did_you_hear[len("Other:"):].strip()

	doc = frappe.get_doc({
		"doctype": "Career Inquiry",
		"first_name": first_name,
		"last_name": last_name,
		"email": email,
		"phone_number": phone_number,
		"role_applying_for": role_applying_for,
		"years_of_experience": years_of_experience,
		"linkedin_profile_url": linkedin_profile_url,
		"tell_us_about_yourself": tell_us_about_yourself,
		"resume_link": resume_link,
		"portfolio_site": portfolio_site,
		"how_did_you_hear": hear_value,
		"other_source": other_value,
		"job_applicant_ref": job_applicant_ref,
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"status": "success", "name": doc.name}
