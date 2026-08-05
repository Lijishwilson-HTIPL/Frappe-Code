import frappe
from frappe.model.document import Document

# Same "who sees everyone" set used by DMS Training Record / My Training
# Dashboard, kept consistent across the training feature area.
_ADMIN_ROLES = {"System Manager", "DMS Admin", "DMS Approver", "DMS Reviewer"}


class DMSTrainingScoreHistory(Document):
	pass


def record_score(employee, training_record, score, quiz_passed, document=None):
	"""Append one immutable score-history row. Called from the real grading/
	signing flow (DMS Training Record) whenever a score is set -- never
	edited or deleted afterward, so it stays a trustworthy point-in-time log
	for trend charts."""
	if not employee or score is None:
		return
	frappe.get_doc({
		"doctype": "DMS Training Score History",
		"employee": employee,
		"training_record": training_record,
		"document": document,
		"score": score,
		"quiz_passed": 1 if quiz_passed else 0,
		"recorded_on": frappe.utils.now_datetime(),
	}).insert(ignore_permissions=True)


def get_permission_query_conditions(user):
	"""Row-level filter: non-admins only ever see their own score history."""
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return ""
	if set(frappe.get_roles(user)) & _ADMIN_ROLES:
		return ""
	escaped_user = frappe.db.escape(user)
	return (
		f"EXISTS ("
		f"SELECT 1 FROM `tabEmployee` emp "
		f"WHERE emp.name = `tabDMS Training Score History`.employee "
		f"AND emp.user_id = {escaped_user}"
		f")"
	)


def has_permission(doc, user=None, ptype="read"):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	if set(frappe.get_roles(user)) & _ADMIN_ROLES:
		return True
	if not doc or ptype != "read":
		return True
	employee_user = frappe.db.get_value("Employee", doc.employee, "user_id")
	return employee_user == user
