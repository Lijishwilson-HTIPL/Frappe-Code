# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate
from unittest import mock

_DUMMY_SIG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class TestQualityDocumentE2E(IntegrationTestCase):
    """End-to-end integration tests: full lifecycle of a Document Library."""

    # ── class-level fixtures (created once per test run) ───────────────────────

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # This Frappe build runs workflow action emails synchronously in tests
        # (now=frappe.in_test), which calls wkhtmltopdf and fails on erp.local.
        # Patch at the source so no test document triggers that pipeline.
        cls._wf_patch = mock.patch(
            "frappe.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
            return_value=None,
        )
        cls._wf_patch.start()

        frappe.set_user("Administrator")
        cls._dept = cls._ensure_dept()
        cls._cat = cls._ensure_category()
        cls._creator = cls._ensure_user(
            "e2e_creator@test.qms", "E2E Creator", ["Employee"], "Test@1234"
        )
        cls._reviewer = cls._ensure_user(
            "e2e_reviewer@test.qms", "E2E Reviewer", ["DMS Approver"], "Test@1234"
        )
        cls._approver = cls._ensure_user(
            "e2e_approver@test.qms", "E2E Approver", ["DMS Approver"], "Test@1234"
        )
        cls._creator_emp = cls._ensure_employee(cls._creator, "E2E Creator")
        frappe.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls._wf_patch.stop()
        super().tearDownClass()

    def setUp(self):
        frappe.set_user("Administrator")

    @classmethod
    def _ensure_dept(cls):
        existing = frappe.db.get_value("Department", {"department_name": "E2E Test Dept"})
        if existing:
            return existing
        d = frappe.get_doc({
            "doctype": "Department",
            "department_name": "E2E Test Dept",
            "is_group": 0,
        })
        d.insert(ignore_permissions=True)
        frappe.db.commit()
        return frappe.db.get_value("Department", {"department_name": "E2E Test Dept"})

    @classmethod
    def _ensure_category(cls):
        name = "E2E Test Category"
        if not frappe.db.exists("Document Category", name):
            frappe.get_doc({"doctype": "Document Category", "category_name": name}).insert(
                ignore_permissions=True
            )
            frappe.db.commit()
        return name

    @classmethod
    def _ensure_user(cls, email, first_name, roles, password):
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "send_welcome_email": 0,
                "roles": [{"role": r} for r in roles],
            })
            user.insert(ignore_permissions=True)
        else:
            user = frappe.get_doc("User", email)
            existing = {r.role for r in user.roles}
            for role in roles:
                if role not in existing:
                    user.append("roles", {"role": role})
            user.save(ignore_permissions=True)

        frappe.utils.password.update_password(email, password)
        frappe.db.commit()
        return email

    @classmethod
    def _ensure_employee(cls, user_id, first_name):
        emp = frappe.db.get_value("Employee", {"user_id": user_id})
        if emp:
            return emp
        e = frappe.get_doc({
            "doctype": "Employee",
            "first_name": first_name,
            "user_id": user_id,
            "status": "Active",
            "date_of_joining": nowdate(),
            "gender": "Male",
            "date_of_birth": "1990-01-01",
        })
        e.insert(ignore_permissions=True)
        frappe.db.commit()
        return e.name

    def _make_doc(self, status="Draft"):
        doc = frappe.get_doc({
            "doctype": "Document Library",
            "title": f"E2E Doc {frappe.generate_hash(length=6)}",
            "status": status,
            "version": "1.0",
            "department": self._dept,
            "category": self._cat,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc

    def _set_state(self, docname, status, workflow_state=None):
        values = {"status": status}
        if workflow_state:
            values["workflow_state"] = workflow_state
        frappe.db.set_value("Document Library", docname, values)
        frappe.db.commit()

    # ── tests ──────────────────────────────────────────────────────────────────

    def test_01_creator_creates_draft_document(self):
        """Employee can insert a new Document Library in Draft status."""
        frappe.set_user(self._creator)
        doc = frappe.get_doc({
            "doctype": "Document Library",
            "title": f"Creator Draft {frappe.generate_hash(length=6)}",
            "status": "Draft",
            "version": "1.0",
            "department": self._dept,
            "category": self._cat,
        })
        doc.insert()
        frappe.db.commit()

        self.assertEqual(doc.status, "Draft")
        self.assertTrue(frappe.db.exists("Document Library", doc.name))
        self.assertEqual(
            frappe.db.get_value("Document Library", doc.name, "owner"), self._creator
        )

    def test_02_full_lifecycle_draft_to_published(self):
        """Document moves through Draft → Review → Approved → Published."""
        doc = self._make_doc(status="Draft")
        self.assertEqual(doc.status, "Draft")

        self._set_state(doc.name, "Review", "Pending Review")
        doc.reload()
        self.assertEqual(doc.status, "Review")

        self._set_state(doc.name, "Approved", "Pending Approval")
        doc.reload()
        self.assertEqual(doc.status, "Approved")

        self._set_state(doc.name, "Published", "Published")
        doc.reload()
        self.assertEqual(doc.status, "Published")

    def test_03_acknowledge_creates_training_record(self):
        """acknowledge_document creates exactly one DMS Training Record."""
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(self._creator)
        from quality_dms.dms.api import acknowledge_document
        result = acknowledge_document(doc.name, e_signature=_DUMMY_SIG)
        frappe.db.commit()

        self.assertTrue(result)
        records = frappe.get_all("DMS Training Record", filters={"document": doc.name})
        self.assertEqual(len(records), 1)

    def test_04_acknowledge_marks_employee_row(self):
        """Acknowledged employee row has acknowledged=1 and acknowledged_on set."""
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(self._creator)
        from quality_dms.dms.api import acknowledge_document
        acknowledge_document(doc.name, e_signature=_DUMMY_SIG)
        frappe.db.commit()

        frappe.set_user("Administrator")
        tr = frappe.get_doc(
            "DMS Training Record",
            frappe.get_all("DMS Training Record", filters={"document": doc.name})[0].name,
        )
        emp_row = next((r for r in tr.employees if r.employee == self._creator_emp), None)
        self.assertIsNotNone(emp_row)
        self.assertEqual(emp_row.acknowledged, 1)
        self.assertIsNotNone(emp_row.acknowledged_on)

    def test_05_acknowledge_stores_e_signature(self):
        """E-Signature value is persisted on the Document Acknowledgement child row."""
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(self._creator)
        from quality_dms.dms.api import acknowledge_document
        acknowledge_document(doc.name, e_signature=_DUMMY_SIG)
        frappe.db.commit()

        frappe.set_user("Administrator")
        tr = frappe.get_doc(
            "DMS Training Record",
            frappe.get_all("DMS Training Record", filters={"document": doc.name})[0].name,
        )
        emp_row = next((r for r in tr.employees if r.employee == self._creator_emp), None)
        self.assertIsNotNone(emp_row)
        self.assertEqual(emp_row.e_signature, _DUMMY_SIG)

    def test_06_double_acknowledge_is_idempotent(self):
        """Second call to acknowledge_document returns True without creating duplicates."""
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(self._creator)
        from quality_dms.dms.api import acknowledge_document
        acknowledge_document(doc.name, e_signature=_DUMMY_SIG)
        frappe.db.commit()

        result = acknowledge_document(doc.name, e_signature=_DUMMY_SIG)
        frappe.db.commit()

        self.assertTrue(result)
        records = frappe.get_all("DMS Training Record", filters={"document": doc.name})
        self.assertEqual(len(records), 1, "Must not create a second Training Record")

    def test_07_acknowledge_fails_without_employee_record(self):
        """acknowledge_document raises ValidationError when user has no Employee record."""
        no_emp = self._ensure_user(
            "e2e_no_emp@test.qms", "No Employee User", ["Employee"], "Test@1234"
        )
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(no_emp)
        from quality_dms.dms.api import acknowledge_document
        with self.assertRaises(frappe.ValidationError):
            acknowledge_document(doc.name, e_signature=_DUMMY_SIG)

    def test_08_request_revision_from_published_document(self):
        """request_revision creates a Document Request of type Revision."""
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(self._creator)
        qdoc = frappe.get_doc("Document Library", doc.name)
        req_name = qdoc.request_revision(reason="Regulatory references need updating")
        frappe.db.commit()

        self.assertIsNotNone(req_name)
        req = frappe.get_doc("Document Request", req_name)
        self.assertEqual(req.request_type, "Revision")
        self.assertEqual(req.reference_document, doc.name)

    def test_09_request_revision_blocked_on_draft(self):
        """request_revision raises ValidationError for a Draft document."""
        doc = self._make_doc(status="Draft")

        frappe.set_user(self._creator)
        qdoc = frappe.get_doc("Document Library", doc.name)
        with self.assertRaises(frappe.ValidationError):
            qdoc.request_revision(reason="Should be blocked")

    def test_10_document_can_be_rejected(self):
        """A document in Review status can be moved to Rejected."""
        doc = self._make_doc(status="Review")
        self._set_state(doc.name, "Rejected", "Rejected")
        doc.reload()
        self.assertEqual(doc.status, "Rejected")

    def test_11_reviewer_has_permission_for_review_document(self):
        """has_permission returns True for DMS Approver on a Review-status document."""
        doc = self._make_doc(status="Review")
        frappe.db.commit()

        from quality_dms.dms.api import has_permission
        self.assertTrue(has_permission(doc, user=self._reviewer, ptype="read"))

    def test_12_creator_cannot_read_another_users_draft(self):
        """Employee cannot read a Draft document they do not own."""
        doc = self._make_doc(status="Draft")
        frappe.db.commit()
        # Owner is Administrator; creator should be denied
        from quality_dms.dms.api import has_permission
        self.assertFalse(has_permission(doc, user=self._creator, ptype="read"))

    def test_13_creator_can_read_own_draft(self):
        """Employee can read a Draft document they own."""
        frappe.set_user(self._creator)
        doc = frappe.get_doc({
            "doctype": "Document Library",
            "title": f"Own Draft {frappe.generate_hash(length=6)}",
            "status": "Draft",
            "version": "1.0",
            "department": self._dept,
            "category": self._cat,
        })
        doc.insert()
        frappe.db.commit()

        from quality_dms.dms.api import has_permission
        self.assertTrue(has_permission(doc, user=self._creator, ptype="read"))

    def test_14_verify_and_log_signature_creates_cfr_log(self):
        """verify_and_log_signature creates a CFR Part 11 Signature Log entry with checksum."""
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(self._creator)
        from quality_dms.dms.api import verify_and_log_signature
        result = verify_and_log_signature(
            doctype="Document Library",
            docname=doc.name,
            password="Test@1234",
            meaning=f"I authorize publication of {doc.name}",
        )
        frappe.db.commit()

        self.assertEqual(result.get("status"), "success")

        logs = frappe.get_all(
            "CFR Part 11 Signature Log",
            filters={"reference_doctype": "Document Library", "reference_name": doc.name},
        )
        self.assertEqual(len(logs), 1)
        log = frappe.get_doc("CFR Part 11 Signature Log", logs[0].name)
        self.assertEqual(log.signer, self._creator)
        self.assertIsNotNone(log.document_checksum)
        self.assertTrue(len(log.document_checksum) == 64, "SHA-256 checksum must be 64 hex chars")

    def test_15_verify_and_log_signature_rejects_wrong_password(self):
        """verify_and_log_signature raises ValidationError on incorrect password."""
        doc = self._make_doc(status="Published")
        self._set_state(doc.name, "Published", "Published")

        frappe.set_user(self._creator)
        from quality_dms.dms.api import verify_and_log_signature
        with self.assertRaises(frappe.ValidationError):
            verify_and_log_signature(
                doctype="Document Library",
                docname=doc.name,
                password="WrongPassword!",
                meaning="Should fail",
            )
