# Copyright (c) 2026, Quality Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DocumentType(Document):
	def validate(self):
		self._normalize_prefix()

	def _normalize_prefix(self):
		"""Prefixes are used verbatim in document numbers (e.g. SOP-0001), so
		normalize to uppercase and strip surrounding whitespace. Reject anything
		that isn't a short alphanumeric token so it stays URL/name-safe."""
		if not self.prefix:
			return
		self.prefix = self.prefix.strip().upper()
		if not self.prefix.isalnum():
			frappe.throw("Document Number Prefix must be alphanumeric (letters/digits only), e.g. SOP, WI, TD, POL.")
		if len(self.prefix) > 10:
			frappe.throw("Document Number Prefix must be 10 characters or fewer.")
