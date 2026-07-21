import frappe
from frappe.tests import IntegrationTestCase
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


class IntegrationTestDMSTrainingAssignmentRule(IntegrationTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        cls._dept = cls._ensure_department("Test TAR Department")
        cls._other_dept = cls._ensure_department("Test TAR Other Department")
        # Dedicated department for onboarding tests, kept separate from _dept so
        # employees created there don't inflate employee counts asserted by the
        # document-publish auto-assignment tests (all tests share one DB
        # transaction for the duration of this test class run).
        cls._onboard_dept = cls._ensure_department("Test TAR Onboarding Department")
        cls._cat = cls._ensure_category("Test TAR Category")
        cls._company = cls._ensure_company()
        cls._emp1 = cls._ensure_employee("Test TAR Emp One", cls._dept)
        cls._emp2 = cls._ensure_employee("Test TAR Emp Two", cls._other_dept)

    def setUp(self):
        frappe.set_user("Administrator")

    @classmethod
    def _ensure_department(cls, name):
        existing = frappe.db.get_value("Department", {"department_name": name}, "name")
        if existing:
            return existing
        doc = frappe.get_doc({"doctype": "Department", "department_name": name})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    @classmethod
    def _ensure_category(cls, name):
        existing = frappe.db.get_value("Document Category", {"category_name": name}, "name")
        if existing:
            return existing
        doc = frappe.get_doc({"doctype": "Document Category", "category_name": name})
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
            "company_name": "Test TAR Company",
            "abbr": "TTC",
            "default_currency": "USD",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    @classmethod
    def _ensure_employee(cls, name, department):
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
            "department": department,
            "status": "Active",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name

    def _make_qdoc(self, category=None):
        with patch(
            "frappe.workflow.doctype.workflow_action.workflow_action.send_workflow_action_email"
        ):
            doc = frappe.get_doc({
                "doctype": "Document Library",
                "title": f"Test TAR QDoc {frappe.generate_hash(length=6)}",
                "status": "Draft",
                "version": "1.0",
                "department": self._dept,
                "category": category or self._cat,
            })
            doc.flags.ignore_workflow = True
            doc.insert(ignore_permissions=True)
        return doc

    def _make_rule(self, **kwargs):
        defaults = {"doctype": "DMS Training Assignment Rule", "active": 1}
        defaults.update(kwargs)
        doc = frappe.get_doc(defaults)
        doc.insert(ignore_permissions=True)
        return doc

    def test_rule_matching_category_assigns_department_employees(self):
        self._make_rule(document_category=self._cat, department=self._dept)
        qdoc = self._make_qdoc()
        qdoc.workflow_state = "Published"
        qdoc._create_training_record()

        trn_name = frappe.db.get_value(
            "DMS Training Record", {"document": qdoc.name}, "name"
        )
        trn = frappe.get_doc("DMS Training Record", trn_name)
        emp_ids = {row.employee for row in trn.employees}
        self.assertIn(self._emp1, emp_ids)
        self.assertNotIn(self._emp2, emp_ids, "Employee outside the rule's department must not be assigned")
        self.assertEqual(trn.status, "Assigned")

    def test_rule_with_no_department_matches_all_active_employees(self):
        self._make_rule(document_category=self._cat)
        qdoc = self._make_qdoc()
        qdoc.workflow_state = "Published"
        qdoc._create_training_record()

        trn_name = frappe.db.get_value(
            "DMS Training Record", {"document": qdoc.name}, "name"
        )
        trn = frappe.get_doc("DMS Training Record", trn_name)
        emp_ids = {row.employee for row in trn.employees}
        self.assertIn(self._emp1, emp_ids)
        self.assertIn(self._emp2, emp_ids)

    def test_inactive_rule_does_not_assign(self):
        self._make_rule(document_category=self._cat, department=self._dept, active=0)
        qdoc = self._make_qdoc()
        qdoc.workflow_state = "Published"
        qdoc._create_training_record()

        trn_name = frappe.db.get_value(
            "DMS Training Record", {"document": qdoc.name}, "name"
        )
        trn = frappe.get_doc("DMS Training Record", trn_name)
        self.assertEqual(trn.status, "Draft")
        self.assertEqual(len(trn.employees), 0)

    def test_republish_does_not_double_assign(self):
        from quality_dms.dms.doctype.dms_training_assignment_rule.dms_training_assignment_rule import (
            apply_rules,
        )
        self._make_rule(document_category=self._cat, department=self._dept)
        qdoc = self._make_qdoc()
        qdoc.workflow_state = "Published"
        qdoc._create_training_record()

        trn_name = frappe.db.get_value(
            "DMS Training Record", {"document": qdoc.name}, "name"
        )
        trn = frappe.get_doc("DMS Training Record", trn_name)
        apply_rules(trn.name)
        trn.reload()
        self.assertEqual(len(trn.employees), 1, "Applying rules twice must not duplicate assignments")

    # ── Onboarding curricula ──────────────────────────────────────────────────

    def test_new_employee_matching_onboarding_rule_gets_curriculum_assigned(self):
        doc1 = self._make_qdoc()
        curriculum = frappe.get_doc({
            "doctype": "DMS Curriculum",
            "title": f"Test Onboarding Curriculum {frappe.generate_hash(length=6)}",
            "documents": [{"document": doc1.name}],
        })
        curriculum.insert(ignore_permissions=True)

        self._make_rule(department=self._onboard_dept, curriculum=curriculum.name)

        new_emp = frappe.get_doc({
            "doctype": "Employee",
            "employee_name": "Test TAR Onboarding Emp",
            "first_name": "Test",
            "last_name": "Onboarding",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2020-01-01",
            "company": self._company,
            "department": self._onboard_dept,
            "status": "Active",
        })
        new_emp.insert(ignore_permissions=True)

        trn_name = frappe.db.get_value("DMS Training Record", {"document": doc1.name}, "name")
        self.assertIsNotNone(trn_name, "Onboarding curriculum must create a Training Record")
        trn = frappe.get_doc("DMS Training Record", trn_name)
        emp_ids = {row.employee for row in trn.employees}
        self.assertIn(new_emp.name, emp_ids)

    def test_new_employee_in_other_department_not_assigned(self):
        doc1 = self._make_qdoc()
        curriculum = frappe.get_doc({
            "doctype": "DMS Curriculum",
            "title": f"Test Onboarding Curriculum Other {frappe.generate_hash(length=6)}",
            "documents": [{"document": doc1.name}],
        })
        curriculum.insert(ignore_permissions=True)

        self._make_rule(department=self._onboard_dept, curriculum=curriculum.name)

        new_emp = frappe.get_doc({
            "doctype": "Employee",
            "employee_name": "Test TAR Other Dept Emp",
            "first_name": "Test",
            "last_name": "OtherDept",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "date_of_joining": "2020-01-01",
            "company": self._company,
            "department": self._other_dept,
            "status": "Active",
        })
        new_emp.insert(ignore_permissions=True)

        trn_name = frappe.db.get_value("DMS Training Record", {"document": doc1.name}, "name")
        self.assertIsNone(trn_name, "Employee outside the rule's department must not trigger curriculum assignment")
