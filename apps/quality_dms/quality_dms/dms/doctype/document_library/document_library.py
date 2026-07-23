# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import today, now_datetime

_DMS_ROLES = {"Employee", "System Manager"}


class DocumentLibrary(Document):

	def autoname(self):
		# Number new documents as {PREFIX}-#### using the prefix configured on the
		# selected Document Type (e.g. SOP-0001, WI-0004, TD-0012). Each prefix keeps
		# its own independent counter via Frappe's Series table, so numbers never
		# collide or reset across types.
		#
		# If the document has no type, or its type has no prefix configured, we leave
		# self.name unset so Frappe falls back to the legacy JSON autoname
		# (format:DOC-{YYYY}-{####}) — existing documents and any untyped drafts keep
		# working unchanged.
		if not self.type:
			return
		prefix = frappe.db.get_value("Document Type", self.type, "prefix")
		if not prefix:
			return
		self.name = make_autoname(f"{prefix}-.####")

	def before_insert(self):
		if not self.version:
			self.version = "1.0"

		# A revision inherits its predecessor's Document Number so the same
		# document keeps one identity across every version (only the internal
		# record name and the version field change).
		if self.revision_of and not self.document_number:
			self.document_number = frappe.db.get_value(
				"Document Library", self.revision_of, "document_number"
			)

	def after_insert(self):
		# Brand-new documents (no revision_of) don't get a Document Number
		# until the autoname-assigned name exists — seed it from that name.
		if not self.document_number:
			self.db_set("document_number", self.name, update_modified=False)

	def validate(self):
		self._check_checkout_before_file_change()

	def on_update(self):
		# NOTE: on_update is a real Frappe controller hook (fires after every
		# save); after_save is NOT and silently never ran.
		if self.file and self.has_value_changed("file"):
			try:
				from quality_dms.dms.file_manager import organize_document_file
				organize_document_file(self)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "DMS: Failed to organize document file in File Manager")

	def on_submit(self):
		# on_submit fires exclusively when docstatus reaches 1 (the "Approve and Publish"
		# workflow transition). The workflow_state check was removed because the workflow
		# engine sets workflow_state before calling submit, but an admin direct-submit
		# would leave workflow_state at its pre-submit value and silently skip these steps.
		self._retire_previous_version()
		self.create_revision_record()
		self._create_training_record()

	def _check_checkout_before_file_change(self):
		"""Block a file replacement while another user holds the checkout lock."""
		if not self.checked_out_by:
			return
		if not self.has_value_changed("file"):
			return
		if self.checked_out_by == frappe.session.user:
			return
		roles = frappe.get_roles(frappe.session.user)
		if "System Manager" in roles:
			return
		frappe.throw(
			f"This document is currently checked out by {self.checked_out_by}. "
			"You cannot replace the file while it is checked out."
		)

	def _retire_previous_version(self):
		"""Mark the document this revision supersedes as Obsolete."""
		if not self.revision_of:
			return

		prev_status = frappe.db.get_value("Document Library", self.revision_of, "status")
		if prev_status not in {"Published", "Approved"}:
			return

		frappe.db.set_value(
			"Document Library",
			self.revision_of,
			{"status": "Obsolete", "workflow_state": "Obsolete"},
		)

		try:
			frappe.get_doc({
				"doctype": "DMS Audit Log",
				"document": self.revision_of,
				"action": f"Marked Obsolete — superseded by {self.name} (v{self.version})",
				"user": frappe.session.user,
				"timestamp": now_datetime(),
				"ip_address": getattr(frappe.local, "request_ip", ""),
			}).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "DMS: Failed to log obsolescence audit")

	def create_revision_record(self):
		if frappe.db.exists("Document Revision", {"document": self.name, "version": self.version}):
			return

		if self.version == "1.0":
			change_log = "Initial publication."
		elif self.revision_of:
			prev_ver = (
				frappe.db.get_value("Document Library", self.revision_of, "version") or "previous"
			)
			change_log = (
				f"Revision of {self.revision_of} (v{prev_ver}). "
				f"Supersedes previous version."
			)
		else:
			change_log = "Document revised and republished."

		rev = frappe.get_doc({
			"doctype": "Document Revision",
			"document": self.name,
			"version": self.version,
			"change_log": change_log,
			"file": self.file,
			"file_doc": self.file_doc,
			"revision_date": today(),
		})
		rev.insert(ignore_permissions=True)

	def _create_training_record(self):
		"""Auto-create a DMS Training Record in Draft state when this document is Published."""
		if frappe.db.exists("DMS Training Record", {"document": self.name, "version": self.version}):
			return
		try:
			trn = frappe.get_doc({
				"doctype": "DMS Training Record",
				"document": self.name,
				"version": self.version,
				"status": "Draft",
			})
			trn.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"DMS: Failed to auto-create Training Record for {self.name}",
			)
			return

		try:
			from quality_dms.dms.doctype.dms_training_assignment_rule.dms_training_assignment_rule import (
				apply_rules,
			)
			apply_rules(trn)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"DMS: Failed to apply auto-assignment rules for {trn.name}",
			)

		try:
			self._carry_forward_prior_completers(trn)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"DMS: Failed to carry forward prior-version completers for {trn.name}",
			)

	def _carry_forward_prior_completers(self, trn):
		"""When a document gets a new version, employees who had completed
		training on the prior version must re-review the updated content —
		auto-assign them to the new version's Training Record instead of
		waiting for them to notice the change themselves."""
		# In-place revision model (current): a revision reopens THIS same record
		# and bumps the version, so prior-version Training Records share this
		# document name but carry an earlier version. Find the most recent
		# Training Record for this document other than the one just created.
		prior_trn_name = frappe.db.get_value(
			"DMS Training Record",
			{
				"document": self.name,
				"version": ("!=", self.version),
				"name": ("!=", trn.name),
			},
			"name",
			order_by="creation desc",
		)

		# Legacy separate-record model: fall back to the revision_of lineage
		# for older data where each version was its own Document Library record.
		if not prior_trn_name and self.revision_of:
			prior_trn_name = frappe.db.get_value(
				"DMS Training Record",
				{"document": self.revision_of},
				"name",
				order_by="creation desc",
			)

		if not prior_trn_name:
			return

		completers = frappe.get_all(
			"Document Acknowledgement",
			filters={"parent": prior_trn_name, "parenttype": "DMS Training Record", "acknowledged": 1},
			pluck="employee",
		)
		if not completers:
			return

		trn._assign_employees(completers)

	@frappe.whitelist()
	def request_revision(self, reason):
		_DMS_ACTIVE_ROLES = {"Employee", "System Manager"}
		if not (_DMS_ACTIVE_ROLES & set(frappe.get_roles())):
			frappe.throw("You must hold a DMS role to request a document revision.", frappe.PermissionError)

		if self.status not in {"Published", "Approved", "Review"}:
			frappe.throw(
				f"Revision requests can only be raised for Published, Approved, or Review documents. "
				f"'{self.name}' is currently '{self.status}'."
			)
		req = frappe.new_doc("Document Request")
		req.title = f"Revision for {self.title}"
		req.reason = reason
		req.request_type = "Revision"
		req.reference_document = self.name
		# carry document context and requester defaults into the request
		req.department = self.department
		req.request_category = self.category
		req.document_type = self.type
		req.requested_for = frappe.session.user
		req.due_date = frappe.utils.add_days(frappe.utils.today(), 7)
		req.insert(ignore_permissions=True)
		return req.name

	@frappe.whitelist()
	def check_out(self):
		"""Lock the document so only the current user can initiate a revision.
		Restricted to DMS roles; the lock is taken under a row lock so two
		concurrent check-outs cannot both succeed."""
		if not (set(frappe.get_roles(frappe.session.user)) & _DMS_ROLES):
			frappe.throw("You must hold a DMS role to check out a document.", frappe.PermissionError)
		if self.docstatus != 1 or self.status != "Published":
			frappe.throw("Only Published (submitted) documents can be checked out.")

		# Re-read the lock field under FOR UPDATE so a concurrent check-out blocks
		# here instead of silently overwriting the other user's lock.
		current = frappe.db.get_value(
			"Document Library", self.name, "checked_out_by", for_update=True
		)
		if current:
			frappe.throw(
				f"This document is already checked out by {current}. Check it in first."
			)

		frappe.db.set_value(
			"Document Library",
			self.name,
			{"checked_out_by": frappe.session.user, "checked_out_on": now_datetime()},
		)

		from quality_dms.dms.file_manager import log_file_event
		log_file_event(self.name, "Check Out", revision=self.version)
		if not frappe.flags.in_test:
			frappe.db.commit()
		return True

	@frappe.whitelist()
	def check_in(self):
		"""Release the checkout lock on this document."""
		if not self.checked_out_by:
			frappe.throw("This document is not currently checked out.")

		roles = frappe.get_roles(frappe.session.user)
		is_admin = "System Manager" in roles
		if self.checked_out_by != frappe.session.user and not is_admin:
			frappe.throw(
				f"Only {self.checked_out_by} (or a System Manager) can check in this document."
			)

		frappe.db.set_value(
			"Document Library",
			self.name,
			{"checked_out_by": None, "checked_out_on": None},
		)

		from quality_dms.dms.file_manager import log_file_event
		log_file_event(self.name, "Check In", revision=self.version)
		if not frappe.flags.in_test:
			frappe.db.commit()
		return True

	def _get_version_family_names(self):
		"""Walk the revision_of chain in both directions to find every
		Document Library record that belongs to this document's version lineage."""
		family = {self.name}
		frontier = {self.name}

		while frontier:
			next_frontier = set()

			placeholders = ", ".join(["%s"] * len(frontier))
			rows = frappe.db.sql(
				f"""
				select name, revision_of from `tabDocument Library`
				where name in ({placeholders}) or revision_of in ({placeholders})
				""",
				tuple(frontier) * 2,
				as_dict=True,
			)
			for row in rows:
				for candidate in (row.name, row.revision_of):
					if candidate and candidate not in family:
						family.add(candidate)
						next_frontier.add(candidate)

			frontier = next_frontier

		return list(family)

	@frappe.whitelist()
	def get_version_family(self):
		"""Return every version of this document so the UI can show all
		versions/files in a single view.

		A revision no longer creates a separate Document Library record — it
		reopens this same record in place (see Document Request._create_revision_document),
		with each prior version preserved as a Document Revision snapshot
		(document_library.py::create_revision_record, fired on_submit). Older
		test/legacy data may still have a revision_of chain of separate
		records, which is merged in here too so nothing already created is
		hidden from the view.
		"""
		versions = {}

		family_names = self._get_version_family_names()
		if len(family_names) > 1:
			legacy_docs = frappe.get_all(
				"Document Library",
				filters={"name": ["in", family_names]},
				fields=[
					"name", "title", "version", "status",
					"file", "file_doc", "creation", "owner",
				],
				order_by="creation asc",
			)
			for d in legacy_docs:
				versions[d["version"]] = {
					**d,
					"is_current": d["name"] == self.name,
					"linked_record": d["name"] != self.name,
				}

		revisions = frappe.get_all(
			"Document Revision",
			filters={"document": self.name},
			fields=["version", "file", "file_doc", "revision_date"],
			order_by="revision_date asc",
		)
		for r in revisions:
			if r["version"] in versions:
				continue
			versions[r["version"]] = {
				"name": self.name,
				"title": self.title,
				"version": r["version"],
				"status": "Archived" if r["version"] != self.version else self.status,
				"file": r["file"],
				"file_doc": r["file_doc"],
				"creation": r["revision_date"],
				"owner": None,
				"is_current": r["version"] == self.version,
				"linked_record": False,
			}

		versions.setdefault(self.version, {
			"name": self.name,
			"title": self.title,
			"version": self.version,
			"status": self.status,
			"file": self.file,
			"file_doc": self.file_doc,
			"creation": self.creation,
			"owner": self.owner,
			"is_current": True,
			"linked_record": False,
		})

		return sorted(versions.values(), key=lambda v: str(v["version"] or ""))

	@frappe.whitelist()
	def get_audit_trail(self):
		"""Return the combined audit history for every version of this document."""
		family_names = self._get_version_family_names()
		return frappe.get_all(
			"DMS Audit Log",
			filters={"document": ["in", family_names]},
			fields=["name", "document", "action", "user", "timestamp", "ip_address"],
			order_by="timestamp desc",
		)

	@frappe.whitelist()
	def get_pending_revision_requests(self):
		"""Return open Document Requests (Revision) raised against any version
		in this document's lineage, so the unified panel can show in-flight
		revisions before their draft version even exists."""
		family_names = self._get_version_family_names()
		return frappe.get_all(
			"Document Request",
			filters={
				"reference_document": ["in", family_names],
				"request_type": "Revision",
				"status": "Pending",
			},
			fields=["name", "reference_document", "reason", "requested_by", "creation"],
			order_by="creation desc",
		)

	@frappe.whitelist()
	def get_file_history(self):
		"""Return revision history with file links for the UI File History panel."""
		revisions = frappe.get_all(
			"Document Revision",
			filters={"document": self.name},
			fields=["name", "version", "revision_date", "change_log", "file", "file_doc"],
			order_by="revision_date asc",
		)
		return revisions

	def has_read_permission(self, user=None):
		if not user:
			user = frappe.session.user
		if user == "Administrator":
			return True
		roles = frappe.get_roles(user)
		if "System Manager" in roles:
			return True

		if "Employee" in roles:
			if self.owner == user:
				return True
			from quality_dms.dms.api import _is_assigned_via_training, _is_linked_via_request
			if _is_assigned_via_training(self.name, user):
				return True
			if _is_linked_via_request(self.name, user):
				return True

		return False
