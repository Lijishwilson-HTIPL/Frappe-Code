import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today, add_days, add_months, now_datetime, getdate
from unittest.mock import patch


EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = [
    "Department",
    "Document Category",
    "Document Type",
    "DMS Project",
    "Document Library",
    "Employee",
    "Company",
]


class IntegrationTestDMSTrainingRecord(IntegrationTestCase):

    # ── fixtures ──────────────────────────────────────────────────────────────

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        cls._dept = cls._ensure_department()
        cls._cat = cls._ensure_category()
        cls._company = cls._ensure_company()
        cls._emp1 = cls._ensure_employee("Test DMS Emp Alpha")
        cls._emp2 = cls._ensure_employee("Test DMS Emp Beta")
        cls._qdoc = cls._ensure_qdoc()

    def setUp(self):
        frappe.set_user("Administrator")

    @classmethod
    def _ensure_department(cls):
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

    @classmethod
    def _ensure_company(cls):
        existing = frappe.db.get_value("Company", {}, "name")
        if existing:
            return existing
        doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test DMS Company",
            "abbr": "TDC",
            "default_currency": "USD",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    @classmethod
    def _ensure_employee(cls, name):
        existing = frappe.db.get_value("Employee", {"employee_name": name}, "name")
        if existing:
            return existing
        doc = frappe.get_doc({
            "doctype": "Employee",
            "employee_name": name,
            "first_name": name.split()[0],
            "last_name": name.split()[-1],
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2020-01-01",
            "company": cls._company,
            "status": "Active",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    @classmethod
    def _ensure_qdoc(cls):
        existing = frappe.db.get_value(
            "Document Library", {"title": "Test DMS Training Doc"}, "name"
        )
        if existing:
            return existing
        with patch(
            "frappe.workflow.doctype.workflow_action.workflow_action.send_workflow_action_email"
        ):
            doc = frappe.get_doc({
                "doctype": "Document Library",
                "title": "Test DMS Training Doc",
                "status": "Draft",
                "version": "1.0",
                "department": cls._dept,
                "category": cls._cat,
            })
            doc.flags.ignore_workflow = True
            doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    def _make_qdoc(self, status="Draft", version="1.0"):
        # Patch workflow email to prevent wkhtmltopdf PDF generation:
        # process_workflow_actions runs send_workflow_action_email synchronously
        # in test mode (enqueue uses now=frappe.in_test), which calls get_pdf via
        # attach_print and fails when erp.local:8000 is not running.
        with patch(
            "frappe.workflow.doctype.workflow_action.workflow_action.send_workflow_action_email"
        ):
            doc = frappe.get_doc({
                "doctype": "Document Library",
                "title": f"Test QDoc {frappe.generate_hash(length=6)}",
                "status": status,
                "version": version,
                "department": self._dept,
                "category": self._cat,
            })
            doc.flags.ignore_workflow = True
            doc.insert(ignore_permissions=True)
        return doc

    def _make_trn(self, **kwargs):
        defaults = {
            "doctype": "DMS Training Record",
            "document": self._qdoc,
            "version": "1.0",
            "status": "Draft",
        }
        defaults.update(kwargs)
        doc = frappe.get_doc(defaults)
        doc.insert(ignore_permissions=True)
        return doc

    # ── T-01: Auto-creation on publish ────────────────────────────────────────

    def test_create_training_record_creates_draft(self):
        qdoc = self._make_qdoc(version="1.0")
        qdoc.workflow_state = "Published"
        qdoc._create_training_record()

        trn_name = frappe.db.get_value(
            "DMS Training Record", {"document": qdoc.name, "version": "1.0"}, "name"
        )
        self.assertIsNotNone(trn_name, "Training record must be created on publish")
        trn = frappe.get_doc("DMS Training Record", trn_name)
        self.assertEqual(trn.status, "Draft")
        self.assertEqual(trn.version, "1.0")

    def test_create_training_record_is_idempotent(self):
        """Calling _create_training_record twice must not produce a duplicate."""
        qdoc = self._make_qdoc(version="2.0")
        qdoc.workflow_state = "Published"
        qdoc._create_training_record()
        qdoc._create_training_record()

        count = frappe.db.count(
            "DMS Training Record", {"document": qdoc.name, "version": "2.0"}
        )
        self.assertEqual(count, 1, "Only one training record must exist for a given document+version")

    def test_create_training_record_links_correct_document(self):
        qdoc = self._make_qdoc(version="3.0")
        qdoc.workflow_state = "Published"
        qdoc._create_training_record()

        trn_name = frappe.db.get_value(
            "DMS Training Record", {"document": qdoc.name}, "name"
        )
        trn = frappe.get_doc("DMS Training Record", trn_name)
        self.assertEqual(trn.document, qdoc.name)

    # ── T-02: New record defaults ─────────────────────────────────────────────

    def test_new_training_record_defaults_to_draft(self):
        trn = self._make_trn()
        self.assertEqual(trn.status, "Draft")
        self.assertEqual(trn.total_assigned, 0)
        self.assertEqual(trn.total_completed, 0)

    # ── T-03: Status transition enforcement ───────────────────────────────────

    def test_invalid_transition_draft_to_completed_raises(self):
        trn = self._make_trn()
        trn.status = "Completed"
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_invalid_transition_draft_to_verified_raises(self):
        trn = self._make_trn()
        trn.status = "Verified"
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_invalid_transition_draft_to_closed_raises(self):
        trn = self._make_trn()
        trn.status = "Closed"
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_invalid_transition_assigned_to_closed_raises(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.status = "Closed"
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_invalid_transition_assigned_to_verified_raises(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.status = "Verified"
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_invalid_transition_closed_to_draft_raises(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Closed")
        trn.reload()
        trn.status = "Draft"
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_invalid_transition_cancelled_to_draft_raises(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Cancelled")
        trn.reload()
        trn.status = "Draft"
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_valid_transition_draft_to_cancelled(self):
        trn = self._make_trn()
        trn.status = "Cancelled"
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "Cancelled")

    def test_valid_transition_assigned_to_overdue(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.status = "Overdue"
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "Overdue")

    def test_valid_transition_overdue_to_cancelled(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Overdue")
        trn.reload()
        trn.status = "Cancelled"
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "Cancelled")

    # ── T-04: assign_employees whitelist method ───────────────────────────────

    def test_assign_employees_transitions_draft_to_assigned(self):
        trn = self._make_trn()
        trn.assign_employees(
            employee_ids=[self._emp1],
            due_date=add_days(today(), 14),
        )
        trn.reload()
        self.assertEqual(trn.status, "Assigned")

    def test_assign_employees_adds_correct_rows(self):
        trn = self._make_trn()
        trn.assign_employees(
            employee_ids=[self._emp1, self._emp2],
            due_date=add_days(today(), 14),
        )
        trn.reload()
        self.assertEqual(trn.total_assigned, 2)
        emp_ids = {row.employee for row in trn.employees}
        self.assertIn(self._emp1, emp_ids)
        self.assertIn(self._emp2, emp_ids)

    def test_assign_employees_sets_assigned_by_and_date(self):
        trn = self._make_trn()
        trn.assign_employees(employee_ids=[self._emp1])
        trn.reload()
        self.assertEqual(trn.assigned_by, "Administrator")
        self.assertEqual(str(trn.assigned_date), today())

    def test_assign_employees_skips_duplicates(self):
        trn = self._make_trn()
        trn.assign_employees(employee_ids=[self._emp1])
        result = trn.assign_employees(employee_ids=[self._emp1, self._emp2])
        trn.reload()
        self.assertEqual(result["added"], 1, "Duplicate employee must not be added again")
        self.assertEqual(trn.total_assigned, 2)

    def test_assign_employees_propagates_due_date_to_rows(self):
        due = add_days(today(), 21)
        trn = self._make_trn()
        trn.assign_employees(employee_ids=[self._emp1], due_date=due)
        trn.reload()
        row = trn.employees[0]
        self.assertEqual(str(row.due_date), due)

    def test_assign_employees_row_status_is_pending(self):
        trn = self._make_trn()
        trn.assign_employees(employee_ids=[self._emp1])
        trn.reload()
        row = trn.employees[0]
        self.assertEqual(row.status, "Pending")

    def test_assign_employees_raises_when_in_progress(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "In Progress")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.assign_employees(employee_ids=[self._emp1])

    def test_assign_employees_raises_when_completed(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Completed")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.assign_employees(employee_ids=[self._emp1])

    def test_assign_employees_returns_added_and_total_counts(self):
        trn = self._make_trn()
        result = trn.assign_employees(employee_ids=[self._emp1, self._emp2])
        self.assertIn("added", result)
        self.assertIn("total", result)
        self.assertEqual(result["added"], 2)
        self.assertEqual(result["total"], 2)

    # ── T-05: Progress sync (totals + auto-advance) ───────────────────────────

    def test_progress_totals_computed_on_save(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1, "acknowledged_on": now_datetime()})
        trn.append("employees", {"employee": self._emp2, "acknowledged": 0})
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.total_assigned, 2)
        self.assertEqual(trn.total_completed, 1)
        self.assertAlmostEqual(float(trn.completion_percentage), 50.0, places=1)

    def test_progress_auto_advances_assigned_to_in_progress(self):
        """First acknowledgement must advance status from Assigned → In Progress."""
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1, "acknowledged_on": now_datetime()})
        trn.append("employees", {"employee": self._emp2, "acknowledged": 0})
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "In Progress")

    def test_progress_auto_advances_in_progress_to_completed(self):
        """All employees acknowledged must advance status from In Progress → Completed."""
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "In Progress")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1, "acknowledged_on": now_datetime()})
        trn.append("employees", {"employee": self._emp2, "acknowledged": 1, "acknowledged_on": now_datetime()})
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "Completed")
        self.assertAlmostEqual(float(trn.completion_percentage), 100.0, places=1)

    def test_progress_overdue_auto_advances_to_completed_when_all_acknowledge(self):
        """If all employees acknowledge while status is Overdue, advance to Completed."""
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Overdue")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1, "acknowledged_on": now_datetime()})
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "Completed")

    def test_acknowledged_row_gets_status_completed_and_completion_date(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1, "acknowledged_on": now_datetime()})
        trn.save(ignore_permissions=True)
        trn.reload()
        row = next(r for r in trn.employees if r.employee == self._emp1)
        self.assertEqual(row.status, "Completed")
        self.assertIsNotNone(row.completion_date)

    def test_unacknowledged_past_due_row_gets_status_overdue(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {
            "employee": self._emp1,
            "acknowledged": 0,
            "due_date": add_days(today(), -5),
        })
        trn.save(ignore_permissions=True)
        trn.reload()
        row = next(r for r in trn.employees if r.employee == self._emp1)
        self.assertEqual(row.status, "Overdue")

    def test_due_date_propagates_to_rows_without_due_date(self):
        due = add_days(today(), 10)
        trn = self._make_trn(due_date=due)
        trn.append("employees", {"employee": self._emp1, "acknowledged": 0})
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(str(trn.employees[0].due_date), due)

    def test_rows_with_existing_due_date_not_overwritten(self):
        """Rows that already have a due_date must keep their own value."""
        parent_due = add_days(today(), 10)
        row_due = add_days(today(), 5)
        trn = self._make_trn(due_date=parent_due)
        trn.append("employees", {"employee": self._emp1, "acknowledged": 0, "due_date": row_due})
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(str(trn.employees[0].due_date), row_due)

    # ── T-06: verify_completion whitelist method ──────────────────────────────

    def test_verify_completion_transitions_completed_to_verified(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Completed")
        trn.reload()
        trn.verify_completion(notes="Reviewed and confirmed.")
        trn.reload()
        self.assertEqual(trn.status, "Verified")

    def test_verify_completion_sets_verified_by_and_date(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Completed")
        trn.reload()
        trn.verify_completion(notes="All good.")
        trn.reload()
        self.assertEqual(trn.verified_by, "Administrator")
        self.assertEqual(str(trn.verified_date), today())
        self.assertEqual(trn.verification_notes, "All good.")

    def test_verify_completion_raises_when_assigned(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.verify_completion()

    def test_verify_completion_raises_when_in_progress(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "In Progress")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.verify_completion()

    def test_verify_completion_raises_when_draft(self):
        trn = self._make_trn()
        with self.assertRaises(frappe.ValidationError):
            trn.verify_completion()

    # ── T-07: close_record whitelist method ───────────────────────────────────

    def test_close_record_transitions_verified_to_closed(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Verified")
        trn.reload()
        trn.close_record(notes="Compliance cycle complete.")
        trn.reload()
        self.assertEqual(trn.status, "Closed")

    def test_close_record_sets_closed_by_date_and_notes(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Verified")
        trn.reload()
        trn.close_record(notes="Cycle complete.")
        trn.reload()
        self.assertEqual(trn.closed_by, "Administrator")
        self.assertEqual(str(trn.closed_date), today())
        self.assertEqual(trn.closure_notes, "Cycle complete.")

    def test_close_record_raises_when_completed_not_verified(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Completed")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.close_record()

    def test_close_record_raises_when_assigned(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.close_record()

    # ── T-08: cancel_record whitelist method ──────────────────────────────────

    def test_cancel_record_from_draft(self):
        trn = self._make_trn()
        trn.cancel_record(reason="Not required.")
        trn.reload()
        self.assertEqual(trn.status, "Cancelled")
        self.assertEqual(trn.closure_notes, "Not required.")

    def test_cancel_record_from_assigned(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.cancel_record(reason="Project cancelled.")
        trn.reload()
        self.assertEqual(trn.status, "Cancelled")

    def test_cancel_record_from_overdue(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Overdue")
        trn.reload()
        trn.cancel_record()
        trn.reload()
        self.assertEqual(trn.status, "Cancelled")

    def test_cancel_raises_when_already_closed(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Closed")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.cancel_record()

    def test_cancel_raises_when_already_cancelled(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Cancelled")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.cancel_record()

    # ── T-09: Overdue scheduler ───────────────────────────────────────────────

    def test_scheduler_marks_assigned_past_due_record_overdue(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            mark_overdue_training_records,
        )
        trn = self._make_trn()
        frappe.db.set_value(
            "DMS Training Record",
            trn.name,
            {"status": "Assigned", "due_date": add_days(today(), -3)},
        )
        frappe.db.commit()

        with patch.object(frappe, "sendmail", return_value=None):
            mark_overdue_training_records()

        trn.reload()
        self.assertEqual(trn.status, "Overdue")

    def test_scheduler_marks_in_progress_past_due_record_overdue(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            mark_overdue_training_records,
        )
        trn = self._make_trn()
        frappe.db.set_value(
            "DMS Training Record",
            trn.name,
            {"status": "In Progress", "due_date": add_days(today(), -1)},
        )
        frappe.db.commit()

        with patch.object(frappe, "sendmail", return_value=None):
            mark_overdue_training_records()

        trn.reload()
        self.assertEqual(trn.status, "Overdue")

    def test_scheduler_does_not_mark_future_due_record_overdue(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            mark_overdue_training_records,
        )
        trn = self._make_trn()
        frappe.db.set_value(
            "DMS Training Record",
            trn.name,
            {"status": "Assigned", "due_date": add_days(today(), 7)},
        )
        frappe.db.commit()

        mark_overdue_training_records()

        trn.reload()
        self.assertEqual(trn.status, "Assigned", "Future due date must NOT be marked Overdue")

    def test_scheduler_does_not_affect_completed_records(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            mark_overdue_training_records,
        )
        trn = self._make_trn()
        frappe.db.set_value(
            "DMS Training Record",
            trn.name,
            {"status": "Completed", "due_date": add_days(today(), -5)},
        )
        frappe.db.commit()

        mark_overdue_training_records()

        trn.reload()
        self.assertEqual(
            trn.status,
            "Completed",
            "Completed records must not be touched by the overdue scheduler",
        )

    def test_scheduler_does_not_affect_draft_records(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            mark_overdue_training_records,
        )
        trn = self._make_trn()
        frappe.db.set_value(
            "DMS Training Record",
            trn.name,
            {"status": "Draft", "due_date": add_days(today(), -5)},
        )
        frappe.db.commit()

        mark_overdue_training_records()

        trn.reload()
        self.assertEqual(trn.status, "Draft", "Draft records with past due date must not be touched")

    # ── T-10: Permission query conditions ────────────────────────────────────

    def test_permission_administrator_returns_empty(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            get_permission_query_conditions,
        )
        result = get_permission_query_conditions("Administrator")
        self.assertEqual(result, "", "Administrator must have unrestricted access")

    def test_permission_system_manager_returns_empty(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            get_permission_query_conditions,
        )
        with patch("frappe.get_roles", return_value=["System Manager", "All"]):
            result = get_permission_query_conditions("manager@example.com")
        self.assertEqual(result, "")

    def test_permission_dms_manager_returns_empty(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            get_permission_query_conditions,
        )
        with patch("frappe.get_roles", return_value=["DMS Admin", "All"]):
            result = get_permission_query_conditions("dmsmanager@example.com")
        self.assertEqual(result, "")

    def test_permission_dms_approver_returns_empty(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            get_permission_query_conditions,
        )
        with patch("frappe.get_roles", return_value=["DMS Approver", "All"]):
            result = get_permission_query_conditions("approver@example.com")
        self.assertEqual(result, "")

    def test_permission_user_with_no_employee_and_no_special_role_returns_no_access(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            get_permission_query_conditions,
        )
        # The new implementation joins tabEmployee in SQL (no Python-side lookup).
        # A user with no DMS role gets an EXISTS clause scoped to their user_id.
        # In practice this returns no rows if they have no matching employee,
        # which is functionally equivalent to "1=0".
        with patch("frappe.get_roles", return_value=["All"]):
            result = get_permission_query_conditions("nobody@example.com")
        self.assertIn("EXISTS", result)
        self.assertIn("emp.user_id", result)
        self.assertIn("nobody@example.com", result)

    def test_permission_dms_reviewer_with_employee_returns_exists_clause(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            get_permission_query_conditions,
        )
        # New implementation joins tabEmployee directly via emp.user_id — no Python lookup.
        with patch("frappe.get_roles", return_value=["DMS Approver", "All"]):
            result = get_permission_query_conditions("reviewer@example.com")
        self.assertIn("EXISTS", result)
        self.assertIn("tabDocument Acknowledgement", result)
        self.assertIn("tabEmployee", result)
        self.assertIn("emp.user_id", result)
        self.assertIn("reviewer@example.com", result)

    # ── T-11: Full lifecycle integration ──────────────────────────────────────

    def test_full_draft_to_closed_lifecycle(self):
        """Draft → assign → first ack (In Progress) → all ack (Completed) → Verified → Closed."""
        # 1. Create training record
        trn = self._make_trn(due_date=add_days(today(), 30))
        self.assertEqual(trn.status, "Draft")

        # 2. Manager assigns employees
        trn.assign_employees(
            employee_ids=[self._emp1, self._emp2],
            due_date=add_days(today(), 30),
        )
        trn.reload()
        self.assertEqual(trn.status, "Assigned")
        self.assertEqual(trn.total_assigned, 2)
        self.assertEqual(trn.assigned_by, "Administrator")

        # 3. Employee 1 acknowledges → In Progress
        for row in trn.employees:
            if row.employee == self._emp1:
                row.acknowledged = 1
                row.acknowledged_on = now_datetime()
                break
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "In Progress")
        self.assertEqual(trn.total_completed, 1)

        # 4. Employee 2 acknowledges → Completed
        for row in trn.employees:
            if row.employee == self._emp2:
                row.acknowledged = 1
                row.acknowledged_on = now_datetime()
                break
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "Completed")
        self.assertEqual(trn.total_completed, 2)
        self.assertAlmostEqual(float(trn.completion_percentage), 100.0, places=1)

        # 5. Manager verifies
        trn.verify_completion(notes="Confirmed by QA Lead.")
        trn.reload()
        self.assertEqual(trn.status, "Verified")
        self.assertIsNotNone(trn.verified_by)

        # 6. Manager closes
        trn.close_record(notes="Archived.")
        trn.reload()
        self.assertEqual(trn.status, "Closed")
        self.assertIsNotNone(trn.closed_by)
        self.assertIsNotNone(trn.closed_date)

    def test_cannot_close_without_verifying_first(self):
        """Completing training must not allow skipping the Verified step."""
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Completed")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.close_record()

    # ── T-12: Quiz gating ──────────────────────────────────────────────────────

    def _make_quiz(self, pass_percentage=80):
        title = f"Test Quiz {frappe.generate_hash(length=6)}"
        quiz = frappe.get_doc({
            "doctype": "DMS Quiz",
            "title": title,
            "pass_percentage": pass_percentage,
            "questions": [{
                "question_text": "2 + 2 = ?",
                "option_1": "3",
                "option_2": "4",
                "correct_option": "2",
                "marks": 1,
            }],
        })
        quiz.insert(ignore_permissions=True)
        return quiz

    def test_acknowledged_row_below_pass_percentage_raises(self):
        quiz = self._make_quiz(pass_percentage=80)
        qdoc = self._make_qdoc()
        qdoc.training_quiz = quiz.name
        qdoc.save(ignore_permissions=True)

        trn = self._make_trn(document=qdoc.name)
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {
            "employee": self._emp1,
            "acknowledged": 1,
            "assessment_score": 50,
        })
        with self.assertRaises(frappe.ValidationError):
            trn.save(ignore_permissions=True)

    def test_acknowledged_row_meeting_pass_percentage_succeeds(self):
        quiz = self._make_quiz(pass_percentage=80)
        qdoc = self._make_qdoc()
        qdoc.training_quiz = quiz.name
        qdoc.save(ignore_permissions=True)

        trn = self._make_trn(document=qdoc.name)
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {
            "employee": self._emp1,
            "acknowledged": 1,
            "assessment_score": 90,
        })
        trn.save(ignore_permissions=True)
        trn.reload()
        row = trn.employees[0]
        self.assertEqual(row.status, "Completed")
        self.assertEqual(row.quiz_passed, 1)

    def test_no_quiz_attached_does_not_gate_completion(self):
        """Documents without a training_quiz must behave exactly as before."""
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1})
        trn.save(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.employees[0].status, "Completed")

    def test_new_record_with_employees_auto_assigns_on_first_save(self):
        """Creating a training record with employee rows in a single save must
        transition Draft -> Assigned immediately, not stay stuck in Draft."""
        trn = frappe.get_doc({
            "doctype": "DMS Training Record",
            "document": self._qdoc,
            "version": "1.0",
            "status": "Draft",
            "employees": [{"employee": self._emp1, "status": "Pending"}],
        })
        trn.insert(ignore_permissions=True)
        trn.reload()
        self.assertEqual(trn.status, "Assigned")
        self.assertEqual(trn.total_assigned, 1)

    # ── T-12b: Failing quiz submissions + admin-gated retake ───────────────────

    def _setup_quiz_trn(self, pass_percentage=80):
        quiz = self._make_quiz(pass_percentage=pass_percentage)
        qdoc = self._make_qdoc()
        qdoc.training_quiz = quiz.name
        qdoc.save(ignore_permissions=True)
        trn = self._make_trn(document=qdoc.name)
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "status": "Pending"})
        trn.save(ignore_permissions=True)
        trn.reload()
        return trn, trn.employees[0].name

    def test_failing_quiz_is_recorded_not_rejected(self):
        """A failing attempt must be recorded (score + attempt count) instead of
        being thrown away, and must NOT acknowledge the row."""
        trn, row_name = self._setup_quiz_trn(pass_percentage=80)
        # correct_option is 2; answer wrong (option 1) -> 0%
        res = trn.submit_quiz_and_sign(row_name, {"0": "1"}, password="irrelevant")
        self.assertFalse(res["passed"])
        self.assertEqual(res["attempts"], 1)
        trn.reload()
        row = trn.employees[0]
        self.assertEqual(row.quiz_attempts, 1)
        self.assertEqual(row.quiz_passed, 0)
        self.assertFalse(row.acknowledged)
        self.assertEqual(row.assessment_score, 0)
        self.assertEqual(row.status, "Failed")

    def test_second_attempt_blocked_until_retake_allowed(self):
        trn, row_name = self._setup_quiz_trn(pass_percentage=80)
        trn.submit_quiz_and_sign(row_name, {"0": "1"}, password="x")
        trn.reload()
        with self.assertRaises(frappe.ValidationError):
            trn.submit_quiz_and_sign(row_name, {"0": "1"}, password="x")

    def test_allow_retake_reopens_a_single_attempt(self):
        trn, row_name = self._setup_quiz_trn(pass_percentage=80)
        trn.submit_quiz_and_sign(row_name, {"0": "1"}, password="x")
        trn.reload()
        trn.allow_quiz_retake(row_name)
        trn.reload()
        self.assertEqual(trn.employees[0].retake_allowed, 1)
        self.assertEqual(trn.employees[0].status, "In Progress")
        # A new (still failing) attempt is now allowed and consumes the grant.
        res = trn.submit_quiz_and_sign(row_name, {"0": "1"}, password="x")
        self.assertFalse(res["passed"])
        self.assertEqual(res["attempts"], 2)
        trn.reload()
        self.assertEqual(trn.employees[0].retake_allowed, 0)

    def test_allow_retake_requires_manager(self):
        trn, row_name = self._setup_quiz_trn(pass_percentage=80)
        trn.submit_quiz_and_sign(row_name, {"0": "1"}, password="x")
        trn.reload()
        user_id = frappe.db.get_value("Employee", self._emp1, "user_id")
        if not user_id:
            self.skipTest("emp1 has no linked user to test non-manager path")
        frappe.set_user(user_id)
        try:
            with self.assertRaises(frappe.PermissionError):
                trn.allow_quiz_retake(row_name)
        finally:
            frappe.set_user("Administrator")

    # ── T-13: Retraining / expiry ─────────────────────────────────────────────

    def test_completed_row_gets_expires_on_using_default_retraining_months(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1})
        trn.save(ignore_permissions=True)
        trn.reload()
        row = trn.employees[0]
        self.assertIsNotNone(row.expires_on)
        expected = add_months(getdate(row.completion_date), 12)
        self.assertEqual(getdate(row.expires_on), expected)

    def test_completed_row_uses_record_level_retraining_override(self):
        trn = self._make_trn(retraining_months=1)
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1})
        trn.save(ignore_permissions=True)
        trn.reload()
        row = trn.employees[0]
        expected = add_months(getdate(row.completion_date), 1)
        self.assertEqual(getdate(row.expires_on), expected)

    def test_scheduler_reopens_expired_row_and_record(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            check_training_expiry,
        )
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1})
        trn.save(ignore_permissions=True)
        trn.reload()

        row_name = trn.employees[0].name
        frappe.db.set_value("Document Acknowledgement", row_name, "expires_on", add_days(today(), -1))
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Closed")

        with patch.object(frappe, "sendmail", return_value=None):
            check_training_expiry()

        trn.reload()
        self.assertEqual(trn.status, "Assigned")
        row = trn.employees[0]
        self.assertEqual(row.acknowledged, 0)
        self.assertEqual(row.status, "Pending")
        self.assertIsNone(row.expires_on)

    def test_scheduler_does_not_reopen_cancelled_record(self):
        from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
            check_training_expiry,
        )
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 1})
        trn.save(ignore_permissions=True)
        trn.reload()

        row_name = trn.employees[0].name
        frappe.db.set_value("Document Acknowledgement", row_name, "expires_on", add_days(today(), -1))
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Cancelled")

        check_training_expiry()

        trn.reload()
        self.assertEqual(trn.status, "Cancelled", "Cancelled records must not be reopened by retraining")

    # ── T-14: Offboarding ──────────────────────────────────────────────────────

    def test_departed_employee_open_rows_get_excused(self):
        from quality_dms.dms.api import handle_employee_status_change

        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Assigned")
        trn.reload()
        trn.append("employees", {"employee": self._emp1, "acknowledged": 0})
        trn.save(ignore_permissions=True)

        class _Stub:
            def __init__(self, name):
                self.name = name
                self.status = "Left"

            def is_new(self):
                return False

            def has_value_changed(self, field):
                return True

        handle_employee_status_change(_Stub(self._emp1), "on_update")

        trn.reload()
        row = next(r for r in trn.employees if r.employee == self._emp1)
        self.assertEqual(row.status, "Excused")

    # ── T-15: Certificate attachment ──────────────────────────────────────────

    def test_verify_completion_attaches_certificate(self):
        trn = self._make_trn()
        frappe.db.set_value("DMS Training Record", trn.name, "status", "Completed")
        trn.reload()

        with (
            patch("frappe.get_print", return_value=b"%PDF-1.4 fake pdf content"),
            patch("frappe.core.doctype.file.file.pdf_contains_js", return_value=False),
        ):
            trn.verify_completion(notes="Reviewed.")

        attached = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "DMS Training Record", "attached_to_name": trn.name},
            fields=["file_name"],
        )
        self.assertTrue(
            any(f.file_name.endswith("-certificate.pdf") for f in attached),
            "Verifying completion must attach a Training Certificate PDF",
        )
