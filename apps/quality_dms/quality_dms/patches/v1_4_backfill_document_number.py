# Copyright (c) 2026, Quality Team and contributors
# Patch: Back-fill Document Number so every version in a revision_of lineage
# shares the same stable identifier (the root document's original name).

import frappe


def execute():
	rows = frappe.get_all(
		"Document Library",
		fields=["name", "revision_of", "document_number"],
	)
	by_name = {r.name: r for r in rows}

	def root_document_number(name, seen=None):
		seen = seen or set()
		if name in seen:
			return name  # revision_of cycle guard, should not happen
		seen.add(name)

		row = by_name.get(name)
		if not row:
			return name
		if row.document_number:
			return row.document_number
		if row.revision_of and row.revision_of in by_name:
			return root_document_number(row.revision_of, seen)
		return name

	for row in rows:
		if row.document_number:
			continue
		frappe.db.set_value(
			"Document Library", row.name, "document_number", root_document_number(row.name)
		)

	frappe.db.commit()
