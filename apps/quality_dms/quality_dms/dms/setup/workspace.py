import frappe


def add_training_shortcuts():
	"""Add Phase 1 training-enhancement shortcuts/links to the 'DMS' workspace
	(the one used at /desk/dms) so they're reachable without a manual search.
	Idempotent — safe to run multiple times (e.g. after future migrations)."""
	w = frappe.get_doc("Workspace", "DMS")

	w.shortcuts = [s for s in w.shortcuts if s.label != "Debug Existing Report Shortcut"]

	new_shortcuts = [
		{"label": "DMS Quiz", "link_to": "DMS Quiz", "type": "DocType"},
		{"label": "DMS Training Assignment Rule", "link_to": "DMS Training Assignment Rule", "type": "DocType"},
		{"label": "Training Settings", "link_to": "Training Settings", "type": "DocType"},
		{"label": "Training Matrix Report", "link_to": "Training Matrix Report", "type": "Report"},
		{"label": "DMS Curriculum", "link_to": "DMS Curriculum", "type": "DocType"},
		{"label": "DMS Training Session", "link_to": "DMS Training Session", "type": "DocType"},
	]
	existing_shortcut_labels = {s.label for s in w.shortcuts}
	for sc in new_shortcuts:
		if sc["label"] not in existing_shortcut_labels:
			w.append("shortcuts", sc)

	new_links = [
		{"label": "DMS Quiz", "link_to": "DMS Quiz", "type": "Link", "link_type": "DocType"},
		{"label": "DMS Training Assignment Rule", "link_to": "DMS Training Assignment Rule", "type": "Link", "link_type": "DocType"},
		{"label": "Training Settings", "link_to": "Training Settings", "type": "Link", "link_type": "DocType"},
		{"label": "Training Matrix Report", "link_to": "Training Matrix Report", "type": "Link", "link_type": "Report"},
		{"label": "DMS Curriculum", "link_to": "DMS Curriculum", "type": "Link", "link_type": "DocType"},
		{"label": "DMS Training Session", "link_to": "DMS Training Session", "type": "Link", "link_type": "DocType"},
	]
	existing_link_labels = {l.label for l in w.links}
	for lk in new_links:
		if lk["label"] not in existing_link_labels:
			w.append("links", lk)

	w.save(ignore_permissions=True)
	frappe.db.commit()
	return {"shortcuts": len(w.shortcuts), "links": len(w.links)}
