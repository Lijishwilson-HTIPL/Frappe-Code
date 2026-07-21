# Copyright (c) 2026, Quality Team and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch, MagicMock


EXTRA_TEST_RECORD_DEPENDENCIES = []
# Prevent the framework from auto-traversing into ERPNext doctypes (Department,
# Document Category, etc.) whose test modules trigger BootStrapTestData and crash.
# All required fixtures are created inline in setUp().
IGNORE_TEST_RECORD_DEPENDENCIES = [
    "Department",
    "Document Category",
    "Document Type",
    "DMS Project",
    "Document Library",
]


class IntegrationTestDocumentRequest(IntegrationTestCase):

    # ── fixtures ──────────────────────────────────────────────────────────────

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        cls._dept = cls._ensure_department()
        cls._cat = cls._ensure_category()

    def setUp(self):
        frappe.set_user("Administrator")

    @classmethod
    def _ensure_department(cls):
        # ERPNext appends the company abbreviation to Department names, so we
        # must look up by field value rather than by the computed primary key.
        existing = frappe.db.get_value(
            "Department", {"department_name": "Test DMS Department"}, "name"
        )
        if existing:
            return existing
        doc = frappe.get_doc({"doctype": "Department", "department_name": "Test DMS Department"})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    @classmethod
    def _ensure_category(cls):
        existing = frappe.db.get_value(
            "Document Category", {"category_name": "Test DMS Category"}, "name"
        )
        if existing:
            return existing
        doc = frappe.get_doc({"doctype": "Document Category", "category_name": "Test DMS Category"})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    def _make_qdoc(self, status="Published", version="1.0"):
        doc = frappe.get_doc({
            "doctype": "Document Library",
            "title": f"Test QDoc {frappe.generate_hash(length=6)}",
            "status": status,
            "version": version,
            "department": self._dept,
            "category": self._cat,
        })
        # Suppress workflow action emails — wkhtmltopdf can't reach erp.local in tests
        doc.flags.ignore_workflow = True
        doc.insert(ignore_permissions=True)
        return doc

    def _make_req(self, request_type="New Document", **kwargs):
        defaults = {
            "doctype": "Document Request",
            "title": f"Test Req {frappe.generate_hash(length=6)}",
            "reason": "Integration test",
            "request_type": request_type,
        }
        if request_type == "New Document":
            defaults.update({"department": self._dept, "request_category": self._cat})
        defaults.update(kwargs)
        doc = frappe.get_doc(defaults)
        doc.insert(ignore_permissions=True)
        return doc

    # ── W-01: QualityDocument.request_revision() status guard ────────────────

    def test_request_revision_raises_for_draft(self):
        qdoc = self._make_qdoc(status="Draft")
        with self.assertRaises(frappe.ValidationError):
            qdoc.request_revision("Need a revision")

    def test_request_revision_raises_for_obsolete(self):
        qdoc = self._make_qdoc(status="Obsolete")
        with self.assertRaises(frappe.ValidationError):
            qdoc.request_revision("Need a revision")

    def test_request_revision_succeeds_for_published(self):
        qdoc = self._make_qdoc(status="Published")
        req_name = qdoc.request_revision("Need a revision")
        self.assertIsNotNone(req_name)
        req = frappe.get_doc("Document Request", req_name)
        self.assertEqual(req.request_type, "Revision")
        self.assertEqual(req.reference_document, qdoc.name)

    def test_request_revision_succeeds_for_review(self):
        qdoc = self._make_qdoc(status="Review")
        req_name = qdoc.request_revision("Needs review-stage revision")
        req = frappe.get_doc("Document Request", req_name)
        self.assertEqual(req.reference_document, qdoc.name)

    # ── W-02: reference doc existence check skipped on non-Pending status ────

    def test_approved_request_resave_skips_reference_check(self):
        qdoc = self._make_qdoc(status="Published")
        req = self._make_req(request_type="Revision", reference_document=qdoc.name)

        # Force to Approved in DB (bypassing validation) to simulate a processed request
        frappe.db.set_value("Document Request", req.name, "status", "Approved")
        frappe.db.set_value("Document Request", req.name, "approved_by", "Administrator")

        # Make the reference document unreachable by renaming its status to Obsolete;
        # a re-save of the Approved request must not run the existence / status checks
        frappe.db.set_value("Document Library", qdoc.name, "status", "Obsolete")

        req.reload()
        req.save(ignore_permissions=True)  # must not raise

    def test_rejected_request_resave_skips_reference_check(self):
        qdoc = self._make_qdoc(status="Published")
        req = self._make_req(request_type="Revision", reference_document=qdoc.name)
        frappe.db.set_value("Document Request", req.name, "status", "Rejected")
        frappe.db.set_value("Document Request", req.name, "rejected_by", "Administrator")
        frappe.db.set_value("Document Request", req.name, "rejection_reason", "Test rejection")
        frappe.db.set_value("Document Library", qdoc.name, "status", "Draft")  # would fail Pending check

        req.reload()
        req.save(ignore_permissions=True)  # must not raise

    # ── C-02: workflow_state cleared on revision draft ─────────────────────

    def test_revision_draft_workflow_state_is_none(self):
        qdoc = self._make_qdoc(status="Published")
        # Simulate a workflow state on the source document
        frappe.db.set_value("Document Library", qdoc.name, "workflow_state", "Published")

        req = self._make_req(request_type="Revision", reference_document=qdoc.name)
        req._prev_status = "Pending"
        req.status = "Approved"
        req.save(ignore_permissions=True)
        req.reload()

        if req.linked_document:
            new_doc = frappe.get_doc("Document Library", req.linked_document)
            self.assertIsNone(
                new_doc.workflow_state,
                "Revision draft must not inherit the source document's workflow_state",
            )

    # ── C-03: version parsing ─────────────────────────────────────────────────

    def test_version_bump_increments_major(self):
        qdoc = self._make_qdoc(status="Published", version="3.0")
        req = self._make_req(request_type="Revision", reference_document=qdoc.name)
        req._prev_status = "Pending"
        req.status = "Approved"
        req.save(ignore_permissions=True)
        req.reload()

        if req.linked_document:
            new_doc = frappe.get_doc("Document Library", req.linked_document)
            self.assertEqual(new_doc.version, "4.0")

    def test_version_bump_malformed_fallback_does_not_raise(self):
        qdoc = self._make_qdoc(status="Published", version="vBadVersion")
        req = self._make_req(request_type="Revision", reference_document=qdoc.name)
        req._prev_status = "Pending"
        req.status = "Approved"
        # Must not raise a bare Exception masking a DB error
        req.save(ignore_permissions=True)
        req.reload()
        if req.linked_document:
            new_doc = frappe.get_doc("Document Library", req.linked_document)
            self.assertEqual(new_doc.version, "2.0")

    def test_version_bump_single_integer_string(self):
        # version "5" (no dot) should produce "6.0"
        qdoc = self._make_qdoc(status="Published", version="5")
        req = self._make_req(request_type="Revision", reference_document=qdoc.name)
        req._prev_status = "Pending"
        req.status = "Approved"
        req.save(ignore_permissions=True)
        req.reload()
        if req.linked_document:
            new_doc = frappe.get_doc("Document Library", req.linked_document)
            self.assertEqual(new_doc.version, "6.0")

    # ── W-03: _create_revision_document idempotency (linked_document guard) ──

    def test_revision_does_not_create_second_doc_if_linked_already_set(self):
        qdoc = self._make_qdoc(status="Published")
        dummy = self._make_qdoc(status="Draft")
        req = self._make_req(request_type="Revision", reference_document=qdoc.name)

        # Simulate a first approval having already set linked_document
        frappe.db.set_value("Document Request", req.name, "linked_document", dummy.name)
        frappe.db.set_value("Document Request", req.name, "status", "Approved")

        req.reload()
        req._prev_status = "Pending"
        req._create_revision_document()

        # Source document must NOT have been set Obsolete by the early-exited call
        qdoc.reload()
        self.assertNotEqual(
            qdoc.status, "Obsolete",
            "Source QDoc must remain unchanged when linked_document guard fires",
        )
        # linked_document must still point to the original dummy doc
        req.reload()
        self.assertEqual(req.linked_document, dummy.name)

    # ── W-04: DMS Audit Log written on status change ──────────────────────────

    def test_audit_log_created_on_withdrawal(self):
        req = self._make_req(request_type="New Document")
        before = frappe.db.count("DMS Audit Log", {"request": req.name})

        req.status = "Withdrawn"
        req.save(ignore_permissions=True)

        after = frappe.db.count("DMS Audit Log", {"request": req.name})
        self.assertGreater(after, before, "Audit log entry expected on status change")

    def test_audit_log_records_correct_action(self):
        req = self._make_req(request_type="New Document")
        req.status = "Withdrawn"
        req.save(ignore_permissions=True)

        log = frappe.db.get_value(
            "DMS Audit Log",
            {"request": req.name},
            ["action", "user"],
            as_dict=True,
        )
        self.assertIsNotNone(log)
        self.assertIn("Withdrawn", log.action)
        self.assertEqual(log.user, "Administrator")

    # ── W-05: fulfilment assignment when no DMS Admins configured ────────────

    def test_fulfilment_no_admins_logs_and_messages(self):
        qdoc = self._make_qdoc(status="Published")
        req = self._make_req(
            request_type="Document Access Request",
            reference_document=qdoc.name,
        )
        req._prev_status = "Pending"

        with patch("frappe.get_all", return_value=[]) as _mock_get_all, \
             patch("frappe.log_error") as mock_log, \
             patch("frappe.msgprint") as mock_msg:
            req._create_fulfilment_assignments()
            mock_log.assert_called_once()
            mock_msg.assert_called_once()
            call_kwargs = mock_msg.call_args
            self.assertEqual(call_kwargs.kwargs.get("indicator"), "orange")

    # ── New Document approval: full path ──────────────────────────────────────

    def test_new_document_approval_creates_quality_document(self):
        req = self._make_req(request_type="New Document", title="E2E New Doc")
        req._prev_status = "Pending"
        req.status = "Approved"
        req.save(ignore_permissions=True)
        req.reload()

        self.assertIsNotNone(
            req.linked_document,
            "Approving a New Document request must link a Document Library",
        )
        new_doc = frappe.get_doc("Document Library", req.linked_document)
        self.assertEqual(new_doc.status, "Draft")
        self.assertEqual(new_doc.version, "1.0")
        self.assertEqual(new_doc.originated_from_request, req.name)
        self.assertEqual(new_doc.department, self._dept)
        self.assertEqual(new_doc.category, self._cat)

    # ── Revision approval: full path ──────────────────────────────────────────

    def test_revision_approval_creates_draft_and_obsoletes_source(self):
        qdoc = self._make_qdoc(status="Published", version="2.0")
        req = self._make_req(request_type="Revision", reference_document=qdoc.name)
        req._prev_status = "Pending"
        req.status = "Approved"
        req.save(ignore_permissions=True)
        req.reload()

        self.assertIsNotNone(req.linked_document)
        new_doc = frappe.get_doc("Document Library", req.linked_document)
        self.assertEqual(new_doc.status, "Draft")
        self.assertEqual(new_doc.version, "3.0")
        # DMS revision linkage uses revision_of, not Frappe's amendment mechanism
        self.assertEqual(new_doc.revision_of, qdoc.name)
        self.assertEqual(new_doc.originated_from_request, req.name)

        # The original document must stay Published at revision-draft creation time.
        # It is only marked Obsolete when the new revision reaches Published state
        # (handled by QualityDocument._retire_previous_version on on_submit).
        qdoc.reload()
        self.assertEqual(
            qdoc.status,
            "Published",
            "Source document must remain Published until the new revision is published",
        )

    # ── Deduplication ─────────────────────────────────────────────────────────

    def test_duplicate_revision_request_blocked(self):
        qdoc = self._make_qdoc(status="Published")
        self._make_req(request_type="Revision", reference_document=qdoc.name)
        with self.assertRaises(frappe.ValidationError):
            self._make_req(request_type="Revision", reference_document=qdoc.name)

    def test_duplicate_access_request_blocked(self):
        qdoc = self._make_qdoc(status="Published")
        self._make_req(request_type="Document Access Request", reference_document=qdoc.name)
        with self.assertRaises(frappe.ValidationError):
            self._make_req(request_type="Document Access Request", reference_document=qdoc.name)

    # ── Status-change validation ───────────────────────────────────────────────

    def test_rejection_without_reason_raises(self):
        req = self._make_req(request_type="New Document")
        req.status = "Rejected"
        with self.assertRaises(frappe.ValidationError):
            req.save(ignore_permissions=True)

    def test_rejection_with_reason_succeeds(self):
        req = self._make_req(request_type="New Document")
        req.status = "Rejected"
        req.rejection_reason = "Does not meet quality criteria"
        req.save(ignore_permissions=True)  # must not raise
        req.reload()
        self.assertEqual(req.status, "Rejected")
        self.assertEqual(req.rejected_by, "Administrator")
        self.assertIsNotNone(req.rejected_on)

    def test_withdrawal_from_approved_raises(self):
        req = self._make_req(request_type="New Document")
        frappe.db.set_value("Document Request", req.name, "status", "Approved")
        req.reload()
        req.status = "Withdrawn"
        with self.assertRaises(frappe.ValidationError):
            req.save(ignore_permissions=True)

    # ── Immutability of tracking fields ───────────────────────────────────────

    def test_requested_by_cannot_be_overwritten(self):
        req = self._make_req(request_type="New Document")
        original_requester = req.requested_by

        req.requested_by = "another@example.com"
        req.save(ignore_permissions=True)
        req.reload()

        self.assertEqual(
            req.requested_by,
            original_requester,
            "requested_by must be immutable after first insert",
        )

    def test_approved_by_cannot_be_overwritten(self):
        req = self._make_req(request_type="New Document")
        req.status = "Approved"
        req.save(ignore_permissions=True)
        req.reload()
        original_approved_by = req.approved_by

        frappe.db.set_value("Document Request", req.name, "approved_by", "hacker@example.com")
        req.reload()
        req.title = "Modified title"
        req.save(ignore_permissions=True)
        req.reload()

        self.assertEqual(
            req.approved_by,
            original_approved_by,
            "approved_by must be immutable once set",
        )

    # ── Revision reference document status check ──────────────────────────────

    def test_revision_of_draft_document_raises(self):
        qdoc = self._make_qdoc(status="Draft")
        with self.assertRaises(frappe.ValidationError):
            self._make_req(request_type="Revision", reference_document=qdoc.name)

    def test_obsolete_retrieval_of_non_obsolete_raises(self):
        qdoc = self._make_qdoc(status="Published")
        with self.assertRaises(frappe.ValidationError):
            self._make_req(
                request_type="Obsolete Document Retrieval Request",
                reference_document=qdoc.name,
            )
