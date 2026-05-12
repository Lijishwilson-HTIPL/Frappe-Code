# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists
from frappe.utils import flt, validate_email_address

from hrms.hr.doctype.interview.interview import get_interviewers


class DuplicationError(frappe.ValidationError):
	pass


class JobApplicant(Document):
	def onload(self):
		job_offer = frappe.get_all("Job Offer", filters={"job_applicant": self.name})
		if job_offer:
			self.get("__onload").job_offer = job_offer[0].name

	def autoname(self):
		self.name = self.email_id

		# applicant can apply more than once for a different job title or reapply
		if frappe.db.exists("Job Applicant", self.name):
			self.name = append_number_if_name_exists("Job Applicant", self.name)

	def validate(self):
		if self.email_id:
			validate_email_address(self.email_id, True)

		if self.employee_referral:
			self.set_status_for_employee_referral()

		if not self.applicant_name and self.email_id:
			guess = self.email_id.split("@")[0]
			self.applicant_name = " ".join([p.capitalize() for p in guess.split(".")])

	def before_insert(self):
		if self.job_title:
			job_opening_status = frappe.db.get_value("Job Opening", self.job_title, "status")
			if job_opening_status == "Closed":
				frappe.throw(
					_("Cannot create a Job Applicant against a closed Job Opening"), title=_("Not Allowed")
				)

	def after_insert(self):
		self.send_acknowledgement_email()
		# Seed the timeline with the initial status so the progression is visible
		# from the moment the applicant is created.
		try:
			initial_status = self.status or "Open"
			self.add_comment("Workflow", _("Application received — status: {0}").format(initial_status))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Job Applicant: initial status comment failed")

	def on_update(self):
		# Log status transitions to the timeline as Workflow comments so the
		# applicant's progress (Open → Shortlisted → Interview → …) is easy to read.
		try:
			old_status = self.get_doc_before_save().status if self.get_doc_before_save() else None
		except Exception:
			old_status = None

		new_status = self.status
		if old_status and new_status and old_status != new_status:
			try:
				self.add_comment(
					"Workflow",
					_("Status changed: {0} → {1}").format(old_status, new_status),
				)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Job Applicant: status change comment failed")

	def send_acknowledgement_email(self):
		if not self.email_id:
			return
		try:
			validate_email_address(self.email_id, True)
		except Exception:
			return

		applicant_name = self.applicant_name or "Applicant"
		job_title = ""
		if self.job_title:
			job_title = frappe.db.get_value("Job Opening", self.job_title, "job_title") or self.job_title

		subject = _("We've received your application")
		intro = _("Dear {0},").format(applicant_name)
		body_line = _("Thank you for your interest in the{0}. We have successfully received your application, and our technical team is currently reviewing your qualifications and background.We will reach out to you soon to discuss the next stages of the hiring process.").format(
			_(" for {0}").format(job_title) if job_title else ""
		)
		signoff = _("Best regards,<br>The Recruitment Team")

		message = f"<p>{intro}</p><p>{body_line}</p><p>{signoff}</p>"

		frappe.sendmail(
			recipients=[self.email_id],
			subject=subject,
			message=message,
			reference_doctype=self.doctype,
			reference_name=self.name,
			now=False,
			with_container=False,
		)

		# Separate internal notification to the team: who applied, for which role
		team_email = frappe.db.get_value(
			"Email Account", {"default_outgoing": 1}, "email_id"
		) or frappe.db.get_value(
			"Email Account", {"default_incoming": 1}, "email_id"
		)
		if team_email and team_email != self.email_id:
			try:
				role_label = job_title or self.designation or self.job_title or "—"
				job_ref = self.job_title or "—"

				def _row(label, value):
					return (
						'<tr><td style="padding:6px 12px 6px 0;font-weight:bold;'
						'vertical-align:top;white-space:nowrap;">{0}</td>'
						'<td style="padding:6px 0;">{1}</td></tr>'
					).format(label, value if value else "—")

				phone = self.phone_number or "—"
				years_exp = getattr(self, "years_of_experience", None) or "—"
				linkedin = getattr(self, "linkedin_profile_url", None) or ""
				portfolio = getattr(self, "portfolio_site", None) or ""
				hear = self.how_did_you_hear or "—"
				other_src = getattr(self, "other_source", None)
				if hear == "Other" and other_src:
					hear = "Other: {0}".format(other_src)
				cover = self.cover_letter or ""

				email_html = (
					'<a href="mailto:{0}">{0}</a>'.format(self.email_id) if self.email_id else "—"
				)
				linkedin_html = '<a href="{0}">{0}</a>'.format(linkedin) if linkedin else "—"
				portfolio_html = '<a href="{0}">{0}</a>'.format(portfolio) if portfolio else "—"

				team_subject = _("New Job Application: {0} applied for {1} ({2})").format(
					applicant_name, role_label, job_ref
				)

				intro_html = "<p>{0}</p><p>{1}</p>".format(
					_("Hi Team,"),
					_("{0} has applied for the role {1} (Job Opening: {2}).").format(
						applicant_name, role_label, job_ref
					),
				)
				details_heading = (
					'<h3 style="color:#0a66c2;border-bottom:1px solid #ddd;'
					'padding-bottom:4px;">{0}</h3>'
				).format(_("Application Details"))
				table_html = (
					'<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">'
					+ _row(_("Reference"), self.name)
					+ _row(_("Name"), applicant_name)
					+ _row(_("Email"), email_html)
					+ _row(_("Phone"), phone)
					+ _row(_("Role applied for"), role_label)
					+ _row(_("Job Opening"), job_ref)
					+ _row(_("Years of experience"), years_exp)
					+ _row(_("LinkedIn"), linkedin_html)
					+ _row(_("Portfolio"), portfolio_html)
					+ _row(_("How did they hear"), hear)
					+ "</table>"
				)
				cover_html = ""
				if cover:
					cover_html = (
						'<h3 style="color:#0a66c2;border-bottom:1px solid #ddd;'
						'padding-bottom:4px;margin-top:18px;">{0}</h3>'
						'<div style="background:#f5f7fa;padding:10px;border-radius:4px;'
						'white-space:pre-wrap;">{1}</div>'
					).format(_("Cover Letter / About"), cover)
				team_message = intro_html + details_heading + table_html + cover_html

				frappe.sendmail(
					recipients=[team_email],
					subject=team_subject,
					message=team_message,
					reference_doctype=self.doctype,
					reference_name=self.name,
					now=False,
					with_container=False,
				)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Job Applicant: team notification email failed")

	def set_status_for_employee_referral(self):
		emp_ref = frappe.get_doc("Employee Referral", self.employee_referral)
		if self.status in ["Open", "Replied", "Hold"]:
			emp_ref.db_set("status", "In Process")
		elif self.status in ["Accepted", "Rejected"]:
			emp_ref.db_set("status", self.status)


@frappe.whitelist()
def create_interview(doc, interview_round):
	import json

	if isinstance(doc, str):
		doc = json.loads(doc)
		doc = frappe.get_doc(doc)

	round_designation = frappe.db.get_value("Interview Round", interview_round, "designation")

	if round_designation and doc.designation and round_designation != doc.designation:
		frappe.throw(
			_("Interview Round {0} is only applicable for the Designation {1}").format(
				interview_round, round_designation
			)
		)

	interview = frappe.new_doc("Interview")
	interview.interview_round = interview_round
	interview.job_applicant = doc.name
	interview.designation = doc.designation
	interview.resume_link = doc.resume_link
	interview.job_opening = doc.job_title

	interviewers = get_interviewers(interview_round)
	for d in interviewers:
		interview.append("interview_details", {"interviewer": d.interviewer})

	return interview


@frappe.whitelist()
def get_interview_details(job_applicant):
	interview_details = frappe.db.get_all(
		"Interview",
		filters={"job_applicant": job_applicant, "docstatus": ["!=", 2]},
		fields=["name", "interview_round", "scheduled_on", "average_rating", "status"],
	)
	interview_detail_map = {}
	meta = frappe.get_meta("Interview")
	number_of_stars = meta.get_options("average_rating") or 5

	for detail in interview_details:
		detail.average_rating = detail.average_rating * number_of_stars if detail.average_rating else 0

		interview_detail_map[detail.name] = detail

	return {"interviews": interview_detail_map, "stars": number_of_stars}


@frappe.whitelist()
def get_applicant_to_hire_percentage():
	frappe.has_permission("Job Applicant", throw=True)

	total_applicants = frappe.db.count("Job Applicant")
	total_hired = frappe.db.count("Job Applicant", filters={"status": "Accepted"})

	return {
		"value": flt(total_hired) / flt(total_applicants) * 100 if total_applicants else 0,
		"fieldtype": "Percent",
	}
