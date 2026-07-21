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


class IntegrationTestDMSCurriculum(IntegrationTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        cls._dept = cls._ensure_department("Test Curriculum Department")
        cls._cat = cls._ensure_category("Test Curriculum Category")
        cls._company = cls._ensure_company()
        cls._emp1 = cls._ensure_employee("Test Curriculum Emp One", cls._dept)

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
            "company_name": "Test Curriculum Company",
            "abbr": "TCC",
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

    def _make_qdoc(self):
        with patch(
            "frappe.workflow.doctype.workflow_action.workflow_action.send_workflow_action_email"
        ):
            doc = frappe.get_doc({
                "doctype": "Document Library",
                "title": f"Test Curriculum QDoc {frappe.generate_hash(length=6)}",
                "status": "Draft",
                "version": "1.0",
                "department": self._dept,
                "category": self._cat,
            })
            doc.flags.ignore_workflow = True
            doc.insert(ignore_permissions=True)
        return doc

    def test_assign_to_employee_creates_training_records_for_each_document(self):
        doc1 = self._make_qdoc()
        doc2 = self._make_qdoc()

        curriculum = frappe.get_doc({
            "doctype": "DMS Curriculum",
            "title": f"Test Curriculum {frappe.generate_hash(length=6)}",
            "documents": [{"document": doc1.name}, {"document": doc2.name}],
        })
        curriculum.insert(ignore_permissions=True)

        trn_names = curriculum.assign_to_employee(self._emp1)
        self.assertEqual(len(trn_names), 2)

        for trn_name in trn_names:
            trn = frappe.get_doc("DMS Training Record", trn_name)
            self.assertEqual(trn.curriculum, curriculum.name)
            emp_ids = {row.employee for row in trn.employees}
            self.assertIn(self._emp1, emp_ids)

    def test_assign_to_employee_reuses_existing_training_record(self):
        doc1 = self._make_qdoc()
        existing_trn = frappe.get_doc({
            "doctype": "DMS Training Record",
            "document": doc1.name,
            "version": "1.0",
            "status": "Draft",
        })
        existing_trn.insert(ignore_permissions=True)

        curriculum = frappe.get_doc({
            "doctype": "DMS Curriculum",
            "title": f"Test Curriculum Reuse {frappe.generate_hash(length=6)}",
            "documents": [{"document": doc1.name}],
        })
        curriculum.insert(ignore_permissions=True)

        trn_names = curriculum.assign_to_employee(self._emp1)
        self.assertEqual(trn_names, [existing_trn.name], "Must reuse the existing Training Record, not duplicate it")
