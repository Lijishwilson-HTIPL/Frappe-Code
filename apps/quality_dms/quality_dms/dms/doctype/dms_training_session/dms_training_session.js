frappe.ui.form.on("DMS Training Session", {
	refresh(frm) {
		if (frm.doc.__islocal || frm.doc.status === "Completed") return;

		const is_manager = frappe.user.has_role(["System Manager"]);
		const is_trainer = frappe.session.user === frm.doc.trainer;
		if (!is_manager && !is_trainer) return;

		frm.add_custom_button(__("Mark Attendance"), () => {
			frm.call("mark_attendance").then((r) => {
				frm.reload_doc();
				const updated = r && r.message ? r.message.updated : 0;
				frappe.show_alert({
					message: __("Attendance recorded. {0} training row(s) marked acknowledged.", [updated]),
					indicator: "green",
				});
			});
		});
	},
});
