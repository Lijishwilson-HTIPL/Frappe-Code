frappe.listview_settings["Project"] = {
	add_fields: ["status", "priority", "is_active", "percent_complete", "expected_end_date", "project_name"],
	filters: [["status", "=", "Open"]],
	get_indicator: function (doc) {
		if (doc.status == "Open" && doc.percent_complete) {
			return [__("{0}%", [cint(doc.percent_complete)]), "orange", "percent_complete,>,0|status,=,Open"];
		} else {
			return [__(doc.status), frappe.utils.guess_colour(doc.status), "status,=," + doc.status];
		}
	},
	button: {
		show: () => true,
		get_label: () => __("View Tasks"),
		get_description: (doc) => __("View tasks for {0}", [doc.project_name || doc.name]),
		action: (doc) => {
			frappe.set_route("List", "Task", { project: doc.name });
		},
	},
};
