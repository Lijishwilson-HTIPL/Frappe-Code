import frappe
from frappe.model.document import Document


class ProvisioningLog(Document):
	pass


def create_log(tenant_name, site_name):
	"""Create a new provisioning log entry. Returns the log doc name."""
	log = frappe.new_doc("Provisioning Log")
	log.tenant = tenant_name
	log.site_name = site_name
	log.status = "Queued"
	log.progress = 0
	log.steps_html = ""
	log.insert(ignore_permissions=True)
	frappe.db.commit()
	return log.name


def update_log_step(log_name, step, progress, status="Running"):
	"""Update the current step and progress of a provisioning log."""
	from datetime import datetime

	log = frappe.get_doc("Provisioning Log", log_name)
	log.db_set("current_step", step)
	log.db_set("progress", progress)
	log.db_set("status", status)

	if status == "Running" and not log.started_at:
		log.db_set("started_at", datetime.now())

	timestamp = datetime.now().strftime("%H:%M:%S")
	status_icon = {
		"Running": "&#9899;",
		"Completed": "&#9989;",
		"Failed": "&#10060;",
		"Queued": "&#9898;",
	}.get(status, "&#9899;")

	step_html = (
		f'<div class="prov-step prov-step-{status.lower()}" '
		f'style="padding:6px 0;border-bottom:1px solid var(--border-color,#eee);">'
		f'<span style="margin-right:8px;">{status_icon}</span>'
		f'<span style="color:var(--text-muted);font-size:12px;margin-right:12px;">{timestamp}</span>'
		f'<strong>{step}</strong>'
		f'<span style="float:right;color:var(--text-muted);font-size:12px;">{progress}%</span>'
		f"</div>"
	)

	current_html = log.steps_html or ""
	log.db_set("steps_html", current_html + step_html)
	frappe.db.commit()


def complete_log(log_name, failed=False, error=None):
	"""Mark a provisioning log as completed or failed."""
	from datetime import datetime

	status = "Failed" if failed else "Completed"
	log = frappe.get_doc("Provisioning Log", log_name)
	log.db_set("status", status)
	log.db_set("completed_at", datetime.now())
	log.db_set("progress", log.progress if failed else 100)
	log.db_set("current_step", "Failed" if failed else "Done")

	if error:
		log.db_set("error_traceback", error[:10000])

	timestamp = datetime.now().strftime("%H:%M:%S")
	icon = "&#10060;" if failed else "&#9989;"
	label = "Provisioning Failed" if failed else "Provisioning Complete"
	color = "#e74c3c" if failed else "#27ae60"

	step_html = (
		f'<div class="prov-step prov-step-{status.lower()}" '
		f'style="padding:8px 0;border-bottom:none;font-weight:600;">'
		f'<span style="margin-right:8px;">{icon}</span>'
		f'<span style="color:var(--text-muted);font-size:12px;margin-right:12px;">{timestamp}</span>'
		f'<span style="color:{color};">{label}</span>'
		f"</div>"
	)

	current_html = log.steps_html or ""
	log.db_set("steps_html", current_html + step_html)
	frappe.db.commit()
