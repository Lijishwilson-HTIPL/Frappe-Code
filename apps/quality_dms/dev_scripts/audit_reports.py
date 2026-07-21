import traceback

import frappe
from frappe.desk.query_report import run


def run_all():
    frappe.set_user("Administrator")
    for name in ["Training Matrix Report", "Training Compliance Report", "Overdue Training Report"]:
        try:
            res = run(name, filters={})
            print(f"{name}: OK rows={len(res.get('result') or [])}")
        except Exception:
            print(f"{name}: FAIL")
            traceback.print_exc()
