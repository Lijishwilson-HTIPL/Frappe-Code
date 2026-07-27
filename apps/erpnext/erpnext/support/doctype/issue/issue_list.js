// The "+ Add Defect" button opens the standard Quick Entry dialog, which
// otherwise titles itself "New Issue" from the raw DocType name. Frappe looks
// for a "<Doctype>QuickEntryForm" class before falling back to the generic
// one, so this override only changes the dialog title — everything else
// (fields, save behavior) is inherited unchanged.
frappe.ui.form.IssueQuickEntryForm = class IssueQuickEntryForm extends frappe.ui.form.QuickEntryForm {
	get_title() {
		return __("New {0}", [__("Defect")]);
	}
};

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

		// Page title (set once, before onload runs, so a single override here
		// sticks) and the breadcrumb, which frappe.breadcrumbs re-renders on
		// every route change — patch it once, globally, but only relabel when
		// the crumb is actually for Issue so no other doctype is affected.
		listview.page.set_title(__("Defect"));
		if (!frappe.breadcrumbs.__issue_defect_patched) {
			frappe.breadcrumbs.__issue_defect_patched = true;
			const original_set_list_breadcrumb = frappe.breadcrumbs.set_list_breadcrumb.bind(frappe.breadcrumbs);
			frappe.breadcrumbs.set_list_breadcrumb = function (breadcrumbs) {
				original_set_list_breadcrumb(breadcrumbs);
				if (breadcrumbs.doctype === "Issue") {
					this.$breadcrumbs.find("li a.title-text").text(__("Defect"));
				}
			};
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
