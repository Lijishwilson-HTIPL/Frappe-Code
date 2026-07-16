# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

# Manual types: approval triggers a fulfilment assignment to System Manager users
_MANUAL_TYPES = frozenset({
	"Document Access Request",
	"Controlled Copy Request",
	"External Document Request",
	"Obsolete Document Retrieval Request",
})

# Types where a duplicate Pending request for the same document is blocked
_DEDUP_TYPES = frozenset({
	"Revision",
	"Document Access Request",
	"Controlled Copy Request",
	"Obsolete Document Retrieval Request",
})

# Per-type extra required fields: {fieldname: label}
_TYPE_REQUIRED = {
	"New Document": {
		"department": "Department",
		"request_category": "Category",
	},
	"Revision": {
		"reference_document": "Reference Document",
	},
	"Document Access Request": {
		"reference_document": "Reference Document",
	},
	"Controlled Copy Request": {
		"reference_document": "Reference Document",
		"department": "Department",
	},
	"Obsolete Document Retrieval Request": {
		"reference_document": "Reference Document",
	},
}

# Roles that may transition status to Approved or Rejected
_APPROVAL_ROLES = frozenset({"System Manager"})


class DocumentRequest(Document):

	# ── Lifecycle hooks ───────────────────────────────────────────────────

	def before_insert(self):
		if not self.requested_by:
			self.requested_by = frappe.session.user

	def validate(self):
		# Capture previous status once; reused by before_save and on_update
		self._prev_status = (
			frappe.db.get_value("Document Request", self.name, "status") or "Pending"
			if not self.is_new() else "Pending"
		)

		self._validate_type_required_fields()
		self._validate_reference_document()
		self._validate_no_duplicate_open_request()
		self._validate_rejection_reason()
		self._validate_status_change_authorization()

	def before_save(self):
		# Fallback: ensure _prev_status is always available even if validate was skipped
		if not hasattr(self, "_prev_status"):
			self._prev_status = (
				frappe.db.get_value("Document Request", self.name, "status") or "Pending"
				if not self.is_new() else "Pending"
			)

		# Immutable tracking fields: once written they cannot be overwritten via API
		if not self.is_new():
			existing = frappe.db.get_value(
				"Document Request", self.name,
				["requested_by", "approved_by", "approved_on", "rejected_by", "rejected_on"],
				as_dict=True,
			) or {}
			if existing.get("requested_by"):
				self.requested_by = existing.requested_by
			if existing.get("approved_by"):
				self.approved_by = existing.approved_by
				self.approved_on = existing.approved_on
			if existing.get("rejected_by"):
				self.rejected_by = existing.rejected_by
				self.rejected_on = existing.rejected_on

		if self.is_new():
			return

		if self.status == "Approved" and self._prev_status != "Approved":
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approved_on:
				self.approved_on = now_datetime()

		elif self.status == "Rejected" and self._prev_status != "Rejected":
			if not self.rejected_by:
				self.rejected_by = frappe.session.user
			if not self.rejected_on:
				self.rejected_on = now_datetime()

	def on_update(self):
		prev = getattr(self, "_prev_status", self.status)
		if self.status == prev:
			return

		if self.status == "Approved":
			if self.request_type == "New Document":
				self._create_new_document()
			elif self.request_type == "Revision":
				self._create_revision_document()
			elif self.request_type in _MANUAL_TYPES:
				self._create_fulfilment_assignments()

	# ── Validation helpers ────────────────────────────────────────────────

	def _validate_type_required_fields(self):
		required = _TYPE_REQUIRED.get(self.request_type, {})
		missing = [label for field, label in required.items() if not self.get(field)]
		if missing:
			joined = ", ".join(missing)
			verb = "is" if len(missing) == 1 else "are"
			frappe.throw(f"{joined} {verb} required for a {self.request_type}.")

	def _validate_reference_document(self):
		if not self.reference_document:
			return

		# All checks (including existence) apply only while the request is Pending.
		# An Approved/Rejected re-save must not re-check the referenced document: approval
		# itself changes that document's status (e.g., to Obsolete) and may later lead to
		# its deletion, which would make the Document Request permanently uneditable.
		if self.status != "Pending":
			return

		doc = frappe.db.get_value(
			"Document Library",
			self.reference_document,
			["name", "status"],
			as_dict=True,
		)
		if not doc:
			frappe.throw(
				f"Document Library '{self.reference_document}' does not exist."
			)

		if self.request_type == "Revision":
			if doc.status not in {"Published", "Approved", "Review"}:
				frappe.throw(
					f"Revision requests require a Published or Approved document. "
					f"'{self.reference_document}' is currently '{doc.status}'."
				)

		elif self.request_type == "Obsolete Document Retrieval Request":
			if doc.status != "Obsolete":
				frappe.throw(
					f"Obsolete Document Retrieval requests must reference an Obsolete document. "
					f"'{self.reference_document}' is currently '{doc.status}'."
				)

	def _validate_no_duplicate_open_request(self):
		if self.request_type not in _DEDUP_TYPES or not self.reference_document:
			return

		filters = {
			"request_type": self.request_type,
			"reference_document": self.reference_document,
			"status": "Pending",
		}
		if not self.is_new():
			filters["name"] = ("!=", self.name)

		existing = frappe.db.get_value("Document Request", filters, "name")
		if existing:
			frappe.throw(
				f"A Pending {self.request_type} already exists for "
				f"'{self.reference_document}' ({existing}). "
				f"Resolve the existing request before submitting a new one."
			)

	def _validate_rejection_reason(self):
		if (
			self.status == "Rejected"
			and self._prev_status != "Rejected"
			and not self.rejection_reason
		):
			frappe.throw("Rejection Reason is required when rejecting a request.")

	def _validate_status_change_authorization(self):
		"""Prevent Employee (and other non-approver roles) from self-approving,
		and block resurrection of terminal requests."""
		if self.is_new() or self._prev_status == self.status:
			return

		# Approved / Rejected are terminal — never allow transitioning back out
		# of them (that would re-run document creation / fulfilment).
		if self._prev_status in ("Approved", "Rejected"):
			frappe.throw(
				f"This request is already {self._prev_status} and cannot be changed to "
				f"{self.status}. Raise a new request instead."
			)

		user_roles = set(frappe.get_roles(frappe.session.user))

		if self.status in ("Approved", "Rejected"):
			if not (_APPROVAL_ROLES & user_roles):
				frappe.throw(
					"Only System Managers can approve or reject requests."
				)

		if self.status == "Withdrawn":
			if self._prev_status != "Pending":
				frappe.throw("Only Pending requests can be withdrawn.")
			if frappe.session.user != self.requested_by and not (_APPROVAL_ROLES & user_roles):
				frappe.throw("Only the original requester (or a System Manager) can withdraw a request.")

	# ── Document creation ─────────────────────────────────────────────────

	def _create_new_document(self):
		# Row-lock this request so a concurrent approval cannot create a duplicate
		if frappe.db.get_value("Document Request", self.name, "linked_document", for_update=True):
			return

		try:
			new_doc = frappe.new_doc("Document Library")
			new_doc.title = self.title
			new_doc.status = "Draft"
			new_doc.docstatus = 0
			new_doc.version = "1.0"
			new_doc.department = self.department
			new_doc.category = self.request_category
			if self.document_type:
				new_doc.type = self.document_type
			new_doc.originated_from_request = self.name
			new_doc.insert(ignore_permissions=True)

			frappe.db.set_value("Document Request", self.name, "linked_document", new_doc.name)

			frappe.msgprint(
				f"New Document Library created: "
				f"<a href='/app/document-library/{new_doc.name}'>{new_doc.name}</a>",
				alert=True,
			)

		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				frappe.get_traceback(),
				"Document Request: New Document creation failed",
			)
			frappe.throw(
				"Failed to create the new Document Library. The approval has been rolled back."
			)

	def _create_revision_document(self):
		# Idempotency guard — mirrors _create_new_document. Row-lock this request first;
		# if linked_document is already set a concurrent approval finished before us.
		if frappe.db.get_value("Document Request", self.name, "linked_document", for_update=True):
			return

		# Row-lock the Document Library to prevent a concurrent approval reopening
		# the same document for revision simultaneously.
		orig_values = frappe.db.get_value(
			"Document Library",
			self.reference_document,
			["status", "checked_out_by", "version"],
			as_dict=True,
			for_update=True,
		)
		# Surface the problem instead of silently no-op'ing: throwing here rolls
		# back the approval so the request does NOT end up Approved-with-nothing-created.
		if not orig_values:
			frappe.throw(
				f"Cannot open a revision: referenced document '{self.reference_document}' "
				f"no longer exists. Approval cancelled."
			)
		if orig_values.status == "Obsolete":
			frappe.throw(
				f"Cannot open a revision: '{self.reference_document}' is Obsolete. "
				f"Approval cancelled."
			)

		# Respect check-out lock: only the holder (or an admin) may create a revision
		checked_out_by = orig_values.get("checked_out_by")
		if checked_out_by and checked_out_by != frappe.session.user:
			user_roles = set(frappe.get_roles(frappe.session.user))
			if not ({"System Manager"} & user_roles):
				frappe.throw(
					f"'{self.reference_document}' is currently checked out by {checked_out_by}. "
					"The revision cannot be created until the document is checked in."
				)

		try:
			major = int((orig_values.version or "1.0").split(".")[0])
			new_version = f"{major + 1}.0"
		except (ValueError, IndexError):
			new_version = "2.0"

		try:
			# Reopen the SAME Document Library record for the new version instead of
			# inserting a separate row — the document keeps one permanent ID across
			# its whole lifetime. The version being replaced is not lost: it was
			# already snapshotted into Document Revision (file + fields) the moment
			# it was published, via DocumentLibrary.create_revision_record() on
			# on_submit — so it stays fully visible in Version History / Audit Log.
			#
			# This bypasses the normal submit/cancel lifecycle intentionally
			# (direct docstatus write) because Frappe's built-in cancel+amend would
			# require docstatus=2 first, which does not fit a regulated DMS where a
			# document is reworked in place rather than cancelled.
			frappe.db.set_value(
				"Document Library",
				self.reference_document,
				{
					"docstatus": 0,
					"status": "Draft",
					"workflow_state": "Draft",
					"version": new_version,
					"file": None,
					"file_doc": None,
					"effective_date": None,
					"review_date": None,
					"checked_out_by": None,
					"checked_out_on": None,
					"originated_from_request": self.name,
				},
			)

			frappe.db.set_value("Document Request", self.name, "linked_document", self.reference_document)

			frappe.msgprint(
				f"'{self.reference_document}' has been reopened as v{new_version} "
				f"(Draft) for revision. Upload the updated file and route it through "
				f"review/approval to publish. The previous version remains available "
				f"in its Version History.",
				alert=True,
			)

		except Exception:
			frappe.db.rollback()
			frappe.log_error(
				frappe.get_traceback(),
				"Document Request: Revision creation failed",
			)
			frappe.throw(
				"Failed to reopen the document for revision. The approval has been rolled back."
			)

	# ── Manual request fulfilment ─────────────────────────────────────────

	def _create_fulfilment_assignments(self):
		"""Assign approved manual requests to all System Manager users for fulfilment."""
		admins = [
			r.parent for r in frappe.get_all(
				"Has Role",
				filters={"role": "System Manager", "parenttype": "User"},
				fields=["parent"],
			)
			if r.parent != "Administrator"
		]
		if not admins:
			frappe.log_error(
				f"No non-Administrator System Manager users found; fulfilment task for {self.name} was not assigned.",
				"Document Request: Fulfilment Assignment Skipped",
			)
			frappe.msgprint(
				"Request approved, but no System Manager users are configured to receive "
				"the fulfilment task. Please assign it manually.",
				indicator="orange",
				alert=True,
			)
			return

		ref = self.reference_document or self.title
		description = (
			f"Please fulfil the approved {self.request_type}: '{ref}'.\n"
			f"Requested by: {self.requested_by or self.owner}."
		)
		due = str(self.due_date or frappe.utils.add_days(frappe.utils.today(), 7))

		try:
			from frappe.desk.form.assign_to import add as assign_to_add
		except ImportError:
			assign_to_add = None

		for user in admins:
			try:
				if assign_to_add:
					assign_to_add({
						"assign_to": [user],
						"doctype": "Document Request",
						"name": self.name,
						"description": description,
						"date": due,
						"notify": 1,
					})
				else:
					frappe.get_doc({
						"doctype": "ToDo",
						"description": description,
						"reference_type": "Document Request",
						"reference_name": self.name,
						"assigned_by": frappe.session.user,
						"owner": user,
						"date": due,
						"status": "Open",
					}).insert(ignore_permissions=True)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					f"Document Request: Could not create assignment for {user}",
				)
