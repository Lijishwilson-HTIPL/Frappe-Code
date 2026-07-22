// Copyright (c) 2026, Quality Team and contributors
// For license information, please see license.txt

frappe.ui.form.on("Document Request", {

	onload(frm) {
		// Pre-fill Requested By on new documents (Python also sets this on save;
		// doing it here shows it immediately without waiting for the first save)
		if (frm.is_new() && !frm.doc.requested_by) {
			frm.set_value("requested_by", frappe.session.user);
		}
	},

	refresh(frm) {
		// Show a one-click button to open the created/revised Document Library
		if (frm.doc.linked_document) {
			frm.add_custom_button(__("Open Linked Document"), function () {
				frappe.set_route("Form", "Document Library", frm.doc.linked_document);
			}, __("Actions"));
		}
	},

});
