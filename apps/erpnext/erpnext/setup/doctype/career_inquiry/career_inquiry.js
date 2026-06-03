frappe.ui.form.on("Career Inquiry", {
	refresh(frm) {
		frm.toggle_display("other_source", frm.doc.how_did_you_hear === "Other");
	},
	how_did_you_hear(frm) {
		frm.toggle_display("other_source", frm.doc.how_did_you_hear === "Other");
		if (frm.doc.how_did_you_hear !== "Other") {
			frm.set_value("other_source", "");
		}
	},
	years_of_experience(frm) {
		const val = frm.doc.years_of_experience;
		if (val && isNaN(parseFloat(val))) {
			frappe.msgprint("Years of Relevant Experience must be a number.");
			frm.set_value("years_of_experience", "");
		}
	}
});
