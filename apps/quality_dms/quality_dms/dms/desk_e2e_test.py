# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt
#
# End-to-end desk tests for the Document Library module.
# Uses the same HTTP API layer as the Frappe desk browser client.
# Run with: python3 apps/quality_dms/quality_dms/quality_dms/desk_e2e_test.py

import json
import sys
import unittest

import requests

BASE_URL = "http://localhost:8000"

# Users created by the Python integration test suite
ADMIN    = ("Administrator",           "Admin@1234")
CREATOR  = ("e2e_creator@test.qms",  "Test@1234")
REVIEWER = ("e2e_reviewer@test.qms", "Test@1234")
APPROVER = ("e2e_approver@test.qms", "Test@1234")

_DUMMY_SIG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


# ── session helper ────────────────────────────────────────────────────────────

class DeskSession:
    """Thin wrapper around requests.Session that stays logged into Frappe."""

    def __init__(self, email: str, password: str):
        self.s = requests.Session()
        self.email = email
        resp = self.s.post(
            f"{BASE_URL}/api/method/login",
            json={"usr": email, "pwd": password},
            timeout=15,
        )
        resp.raise_for_status()
        msg = resp.json().get("message", "")
        if msg not in ("Logged In", "logged_in"):
            raise RuntimeError(f"Login failed for {email}: {resp.text}")

    def get(self, path: str, **kw) -> dict:
        r = self.s.get(f"{BASE_URL}{path}", timeout=15, **kw)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, **kw) -> dict:
        r = self.s.post(f"{BASE_URL}{path}", timeout=15, **kw)
        r.raise_for_status()
        return r.json()

    def put(self, path: str, **kw) -> dict:
        r = self.s.put(f"{BASE_URL}{path}", timeout=15, **kw)
        r.raise_for_status()
        return r.json()

    def resource(self, doctype: str) -> str:
        """Return the REST resource path for a doctype."""
        return f"/api/resource/{requests.utils.quote(doctype)}"


# ── setup helpers ─────────────────────────────────────────────────────────────

def _admin_execute(code: str) -> str:
    """Run a one-liner in bench execute (for setup/teardown only)."""
    import subprocess
    result = subprocess.run(
        ["bash", "-c",
         f"cd /home/james/frappe-bench && "
         f"/home/james/.local/bin/bench --site erp.local execute "
         f"frappe.db.get_value --args \"['Site Config', None, 'db_name']\" "
        ],
        capture_output=True, text=True
    )
    return result.stdout.strip()


# ── test class ────────────────────────────────────────────────────────────────

class TestQualityDocumentDesk(unittest.TestCase):
    """
    End-to-end desk tests.  Each test creates its own documents so tests are
    independent and can run in any order.
    """

    # Desk/list URL path under test
    DESK_DOCTYPE = "Document Library"

    @classmethod
    def setUpClass(cls):
        cls.admin    = DeskSession(*ADMIN)
        cls.creator  = DeskSession(*CREATOR)
        cls.reviewer = DeskSession(*REVIEWER)
        cls.approver = DeskSession(*APPROVER)

        # Resolve dept/category names created by the Python suite
        info = cls.creator.get("/api/method/frappe.client.get_value", params={
            "doctype": "Document Category",
            "filters": json.dumps({"category_name": "E2E Test Category"}),
            "fieldname": "name",
        })
        cls._cat = (info.get("message") or {}).get("name") or "E2E Test Category"

        info2 = cls.creator.get("/api/method/frappe.client.get_value", params={
            "doctype": "Department",
            "filters": json.dumps({"department_name": "E2E Test Dept"}),
            "fieldname": "name",
        })
        cls._dept = (info2.get("message") or {}).get("name")
        if not cls._dept:
            raise RuntimeError("E2E Test Dept not found — run the Python integration suite first")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _create_doc(self, session: DeskSession, status: str = "Draft") -> dict:
        """Create a Document Library via the desk REST API."""
        import random, string
        suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        payload = {
            "doctype": self.DESK_DOCTYPE,
            "title": f"Desk E2E {suffix}",
            "status": status,
            "version": "1.0",
            "department": self._dept,
            "category": self._cat,
        }
        resp = session.post(
            session.resource(self.DESK_DOCTYPE),
            json=payload,
        )
        return resp["data"]

    def _set_status(self, name: str, status: str, workflow_state: str = None) -> None:
        """Advance document status via the admin session.

        Uses only the `status` Select field — the permission / visibility logic
        in api.py reads `doc.status`, so workflow_state is irrelevant for these
        tests.  Setting workflow_state via the API triggers Frappe's workflow
        transition validation even for Administrator, so we skip it here.
        """
        self.admin.post("/api/method/frappe.client.set_value", json={
            "doctype": self.DESK_DOCTYPE,
            "name": name,
            "fieldname": "status",
            "value": status,
        })

    # ── tests ─────────────────────────────────────────────────────────────────

    def test_01_login_creator(self):
        """Employee login returns a valid session."""
        resp = self.creator.get("/api/method/frappe.auth.get_logged_user")
        self.assertEqual(resp["message"], CREATOR[0])

    def test_02_login_reviewer(self):
        """DMS Approver login returns a valid session."""
        resp = self.reviewer.get("/api/method/frappe.auth.get_logged_user")
        self.assertEqual(resp["message"], REVIEWER[0])

    def test_03_login_approver(self):
        """DMS Approver login returns a valid session."""
        resp = self.approver.get("/api/method/frappe.auth.get_logged_user")
        self.assertEqual(resp["message"], APPROVER[0])

    def test_04_list_view_loads(self):
        """GET /api/resource/Document Library returns a valid list response."""
        resp = self.creator.get(
            self.creator.resource(self.DESK_DOCTYPE),
            params={"limit_page_length": 5, "fields": '["name","status","title"]'},
        )
        self.assertIn("data", resp)
        self.assertIsInstance(resp["data"], list)

    def test_05_creator_creates_document(self):
        """Employee can POST a new Document Library via the desk API."""
        doc = self._create_doc(self.creator, status="Draft")
        self.assertIn("name", doc)
        self.assertTrue(doc["name"].startswith("DOC-"))
        self.assertEqual(doc["status"], "Draft")

    def test_06_form_data_loads(self):
        """GET a Document Library by name returns the full form data."""
        doc = self._create_doc(self.creator)
        form = self.creator.get(
            f"{self.creator.resource(self.DESK_DOCTYPE)}/{doc['name']}"
        )
        fetched = form["data"]
        self.assertEqual(fetched["name"], doc["name"])
        self.assertEqual(fetched["doctype"], self.DESK_DOCTYPE)
        self.assertIn("title", fetched)
        self.assertIn("status", fetched)

    def test_07_creator_can_see_own_draft_in_list(self):
        """Creator's own Draft appears in their list view."""
        doc = self._create_doc(self.creator)
        resp = self.creator.get(
            self.creator.resource(self.DESK_DOCTYPE),
            params={
                "filters": json.dumps([["name", "=", doc["name"]]]),
                "fields": '["name","status"]',
            },
        )
        names = [r["name"] for r in resp["data"]]
        self.assertIn(doc["name"], names)

    def test_08_creator_cannot_see_others_draft(self):
        """Creator cannot list a Draft owned by the Reviewer (different owner)."""
        # The reviewer session cannot create a QDoc (DMS Approver has no create
        # permission), so we verify via the filter/permission query
        # that no Draft owned by e2e_reviewer appears for the creator.
        resp = self.creator.get(
            self.creator.resource(self.DESK_DOCTYPE),
            params={
                "filters": json.dumps([
                    ["owner", "=", REVIEWER[0]],
                    ["status", "=", "Draft"],
                ]),
                "fields": '["name"]',
            },
        )
        self.assertEqual(resp["data"], [], "Creator must not see Reviewer's Drafts")

    def test_09_creator_can_update_own_draft(self):
        """PUT a field update on a Draft the creator owns."""
        doc = self._create_doc(self.creator)
        new_title = f"Updated Title {doc['name'][-4:]}"
        resp = self.creator.put(
            f"{self.creator.resource(self.DESK_DOCTYPE)}/{doc['name']}",
            json={"title": new_title},
        )
        self.assertEqual(resp["data"]["title"], new_title)

    def test_10_status_transition_draft_to_review(self):
        """Document status advances from Draft to Review."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Review")
        form = self.creator.get(
            f"{self.creator.resource(self.DESK_DOCTYPE)}/{doc['name']}"
        )
        self.assertEqual(form["data"]["status"], "Review")

    def test_11_reviewer_sees_document_in_review(self):
        """DMS Approver can GET a document that is in Review status."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Review")
        form = self.reviewer.get(
            f"{self.reviewer.resource(self.DESK_DOCTYPE)}/{doc['name']}"
        )
        self.assertEqual(form["data"]["name"], doc["name"])
        self.assertEqual(form["data"]["status"], "Review")

    def test_12_reviewer_appears_in_list_for_review_docs(self):
        """Reviewer list view returns documents in Review status."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Review")
        resp = self.reviewer.get(
            self.reviewer.resource(self.DESK_DOCTYPE),
            params={
                "filters": json.dumps([["name", "=", doc["name"]]]),
                "fields": '["name","status"]',
            },
        )
        self.assertEqual(len(resp["data"]), 1)
        self.assertEqual(resp["data"][0]["status"], "Review")

    def test_13_status_transition_review_to_approved(self):
        """Document status advances from Review to Approved."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Review")
        self._set_status(doc["name"], "Approved")
        form = self.approver.get(
            f"{self.approver.resource(self.DESK_DOCTYPE)}/{doc['name']}"
        )
        self.assertEqual(form["data"]["status"], "Approved")

    def test_14_status_transition_approved_to_published(self):
        """Document reaches Published status."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Review")
        self._set_status(doc["name"], "Approved")
        self._set_status(doc["name"], "Published")
        form = self.creator.get(
            f"{self.creator.resource(self.DESK_DOCTYPE)}/{doc['name']}"
        )
        self.assertEqual(form["data"]["status"], "Published")

    def test_15_acknowledge_document_via_api(self):
        """POST to acknowledge_document returns success=True."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Published")
        resp = self.creator.post(
            "/api/method/quality_dms.dms.api.acknowledge_document",
            json={"document": doc["name"], "e_signature": _DUMMY_SIG},
        )
        self.assertTrue(resp["message"])

    def test_16_acknowledge_creates_training_record(self):
        """After acknowledgment, a DMS Training Record exists for the document."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Published")
        self.creator.post(
            "/api/method/quality_dms.dms.api.acknowledge_document",
            json={"document": doc["name"], "e_signature": _DUMMY_SIG},
        )
        resp = self.creator.get(
            self.creator.resource("DMS Training Record"),
            params={"filters": json.dumps([["document", "=", doc["name"]]]), "fields": '["name"]'},
        )
        self.assertEqual(len(resp["data"]), 1)

    def test_17_get_current_user_info(self):
        """get_current_user_info returns full_name and designation for the creator."""
        resp = self.creator.get(
            "/api/method/quality_dms.dms.api.get_current_user_info"
        )
        info = resp["message"]
        self.assertIn("full_name", info)
        self.assertIn("designation", info)
        self.assertTrue(info["full_name"])

    def test_18_request_revision_from_desk(self):
        """request_revision whitelisted method creates a Document Request."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Published")
        resp = self.creator.post(
            "/api/method/run_doc_method",
            json={
                "dt": self.DESK_DOCTYPE,
                "dn": doc["name"],
                "method": "request_revision",
                "args": json.dumps({"reason": "Regulatory update required"}),
            },
        )
        req_name = resp.get("message")
        self.assertIsNotNone(req_name, "request_revision must return a Document Request name")
        # Verify the Document Request was created
        form = self.creator.get(
            f"{self.creator.resource('Document Request')}/{req_name}"
        )
        self.assertEqual(form["data"]["request_type"], "Revision")
        self.assertEqual(form["data"]["reference_document"], doc["name"])

    def test_19_verify_and_log_signature(self):
        """verify_and_log_signature creates a CFR Part 11 log entry via the desk."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Published")
        resp = self.creator.post(
            "/api/method/quality_dms.dms.api.verify_and_log_signature",
            json={
                "doctype": self.DESK_DOCTYPE,
                "docname": doc["name"],
                "password": CREATOR[1],
                "meaning": f"I authorize publication of {doc['name']}",
            },
        )
        self.assertEqual(resp["message"]["status"], "success")
        # Employee has no list-view permission on CFR Part 11 Signature Log
        # (C-1 fix removed the "All" role entry).  Use admin to verify the log.
        logs = self.admin.get(
            self.admin.resource("CFR Part 11 Signature Log"),
            params={
                "filters": json.dumps([
                    ["reference_doctype", "=", self.DESK_DOCTYPE],
                    ["reference_name", "=", doc["name"]],
                ]),
                "fields": '["name","signer","document_checksum"]',
            },
        )
        self.assertEqual(len(logs["data"]), 1)
        log = logs["data"][0]
        self.assertEqual(log["signer"], CREATOR[0])
        self.assertTrue(log["document_checksum"])

    def test_20_wrong_password_rejected_by_signature_api(self):
        """verify_and_log_signature returns HTTP 417 on wrong password."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Published")
        resp = self.creator.s.post(
            f"{BASE_URL}/api/method/quality_dms.dms.api.verify_and_log_signature",
            json={
                "doctype": self.DESK_DOCTYPE,
                "docname": doc["name"],
                "password": "WrongPassword!",
                "meaning": "Should fail",
            },
            timeout=15,
        )
        self.assertIn(resp.status_code, (417, 400, 403),
                      f"Expected an error status, got {resp.status_code}")

    def test_21_number_card_draft_count(self):
        """Draft documents are returned by the status=Draft filter (number card query)."""
        doc = self._create_doc(self.creator)
        # Filter by both status AND name so the query is not limited by page size
        resp = self.creator.get(
            self.creator.resource(self.DESK_DOCTYPE),
            params={
                "filters": json.dumps([
                    ["status", "=", "Draft"],
                    ["name", "=", doc["name"]],
                ]),
                "fields": '["name","status"]',
            },
        )
        self.assertEqual(len(resp["data"]), 1)
        self.assertEqual(resp["data"][0]["status"], "Draft")

    def test_22_number_card_review_count(self):
        """Documents in Review number card counts Review documents."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Review")
        resp = self.creator.get(
            self.creator.resource(self.DESK_DOCTYPE),
            params={
                "filters": json.dumps([["status", "=", "Review"]]),
                "fields": '["name"]',
            },
        )
        names = [r["name"] for r in resp["data"]]
        self.assertIn(doc["name"], names)

    def test_23_published_document_searchable_in_list(self):
        """A Published document appears in the list for all DMS roles."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Published")

        for label, session in [
            ("Creator",  self.creator),
            ("Reviewer", self.reviewer),
            ("Approver", self.approver),
        ]:
            with self.subTest(role=label):
                resp = session.get(
                    session.resource(self.DESK_DOCTYPE),
                    params={
                        "filters": json.dumps([["name", "=", doc["name"]]]),
                        "fields": '["name"]',
                    },
                )
                self.assertEqual(len(resp["data"]), 1,
                                 f"{label} should see Published document")

    def test_24_rejected_document_not_visible_to_reviewer(self):
        """A Rejected document is not returned for DMS Approver."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Review")
        self._set_status(doc["name"], "Rejected")
        resp = self.reviewer.get(
            self.reviewer.resource(self.DESK_DOCTYPE),
            params={
                "filters": json.dumps([["name", "=", doc["name"]]]),
                "fields": '["name"]',
            },
        )
        self.assertEqual(resp["data"], [], "Reviewer must not see Rejected document")

    def test_25_document_request_list_visible_to_creator(self):
        """A Document Request raised by the creator appears in their list."""
        doc = self._create_doc(self.creator)
        self._set_status(doc["name"], "Published")
        rev_resp = self.creator.post(
            "/api/method/run_doc_method",
            json={
                "dt": self.DESK_DOCTYPE,
                "dn": doc["name"],
                "method": "request_revision",
                "args": json.dumps({"reason": "Needs update"}),
            },
        )
        req_name = rev_resp.get("message")
        resp = self.creator.get(
            self.creator.resource("Document Request"),
            params={
                "filters": json.dumps([["name", "=", req_name]]),
                "fields": '["name","request_type","reference_document"]',
            },
        )
        self.assertEqual(len(resp["data"]), 1)
        self.assertEqual(resp["data"][0]["reference_document"], doc["name"])


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromTestCase(TestQualityDocumentDesk)
    runner  = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result  = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
