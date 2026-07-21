frappe.listview_settings["Issue"] = {
	colwidths: { subject: 6 },
	add_fields: ["priority"],
	filters: [["status", "=", "Open"]],
	onload: function (listview) {
		var method = "erpnext.support.doctype.issue.issue.set_multiple_status";

		listview.page.add_action_item(__("Set as Open"), function () {
			listview.call_for_selected_items(method, { status: "Open" });
		});

		listview.page.add_action_item(__("Set as Closed"), function () {
			listview.call_for_selected_items(method, { status: "Closed" });
		});

		// Issue is shown as "Defect" throughout the Projects/Support workspace
		// sidebars and its own fields (Defect Priority, Defect Summary);
		// relabel just this list view's primary action to match, without a
		// global translation of the word "Issue" elsewhere in the system.
		//
		// list_view.js calls set_primary_action() again on every refresh
		// (route change, filter change, etc.), which would silently put the
		// default "Add Issue" label back — so the method itself is wrapped
		// here rather than relabelling once in onload.
		if (!listview.__defect_label_patched) {
			listview.__defect_label_patched = true;
			const original_set_primary_action = listview.set_primary_action.bind(listview);
			listview.set_primary_action = function () {
				original_set_primary_action();
				const label_span = listview.page.btn_primary.find("span.hidden-xs");
				if (label_span.length) {
					label_span.text(" " + __("Add Defect") + " ");
				} else {
					listview.page.btn_primary.text(__("Add Defect"));
				}
			};
			listview.set_primary_action();
		}
	},
	get_indicator: function (doc) {
		if (doc.status === "Open") {
			const color = {
				Low: "yellow",
				Medium: "orange",
				High: "red",
			};
			return [__(doc.status), color[doc.priority] || "red", `status,=,Open`];
		} else if (doc.status === "Closed") {
			return [__(doc.status), "green", "status,=," + doc.status];
		} else {
			return [__(doc.status), "gray", "status,=," + doc.status];
		}
	},
};
