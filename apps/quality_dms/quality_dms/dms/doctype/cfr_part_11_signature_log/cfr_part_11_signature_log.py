# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CFRPart11SignatureLog(Document):
    def validate(self):
        if not self.is_new():
            frappe.throw("21 CFR compliance constraint: Signature Log records are immutable and cannot be modified.")

    def on_trash(self):
        frappe.throw("21 CFR compliance constraint: Signature Log records are permanent and cannot be deleted.")
