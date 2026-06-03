import frappe
from frappe.model.document import Document


class CareerInquiry(Document):
	def after_insert(self):
		# Skip auto-creation when a Job Applicant was already created externally
		if not self.job_applicant_ref:
			create_job_applicant(self)


def create_job_applicant(doc):
	try:
		notes_parts = [f"Role Applying For: {doc.role_applying_for}"]
		if doc.years_of_experience:
			notes_parts.append(f"Years of Experience: {doc.years_of_experience}")
		if doc.linkedin_profile_url:
			notes_parts.append(f"LinkedIn: {doc.linkedin_profile_url}")
		if doc.portfolio_site:
			notes_parts.append(f"Portfolio: {doc.portfolio_site}")
		if doc.how_did_you_hear:
			source_text = doc.how_did_you_hear
			if doc.other_source:
				source_text += f" ({doc.other_source})"
			notes_parts.append(f"How Did You Hear: {source_text}")

		applicant = frappe.get_doc({
			"doctype": "Job Applicant",
			"applicant_name": f"{doc.first_name} {doc.last_name}".strip(),
			"email_id": doc.email,
			"phone_number": doc.phone_number,
			"resume_link": doc.resume_link,
			"cover_letter": doc.tell_us_about_yourself,
			"notes": "\n".join(notes_parts),
			"status": "Open",
		})
		applicant.insert(ignore_permissions=True)
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
