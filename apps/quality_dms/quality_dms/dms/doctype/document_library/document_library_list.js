frappe.listview_settings['Document Library'] = {
	// Pull the fields the indicator / formatters need, even if a user hides the column.
	add_fields: ["status", "version", "document_number", "effective_date", "review_date"],

	// Show the meaningful lifecycle status (not docstatus) as the row indicator.
	// The third element makes the colored badge a one-click filter for that status.
	get_indicator(doc) {
		const map = {
			"Draft":     [__("Draft"),     "gray",   "status,=,Draft"],
			"Review":    [__("In Review"), "orange", "status,=,Review"],
			"Approved":  [__("Approved"),  "blue",   "status,=,Approved"],
			"Published": [__("Published"), "green",  "status,=,Published"],
			"Obsolete":  [__("Obsolete"),  "red",    "status,=,Obsolete"],
			"Archived":  [__("Archived"),  "gray",   "status,=,Archived"],
			"Rejected":  [__("Rejected"),  "red",    "status,=,Rejected"],
		};
		return map[doc.status] || [__(doc.status || "—"), "gray", null];
	},

	formatters: {
		// Version as a compact pill so it reads as a tag, not loose text.
		version(value) {
			if (!value) return "";
			return `<span class="indicator-pill blue" style="font-weight:600;">v${frappe.utils.escape_html(value)}</span>`;
		},
		// Version-specific number in monospace so the code stands out from prose.
		document_number(value) {
			if (!value) return `<span class="text-muted">${__("Not published")}</span>`;
			return `<span style="font-family:var(--font-stack-monospace,monospace);">${frappe.utils.escape_html(value)}</span>`;
		},
	},

	onload(listview) {
		// Always open the full, unfiltered document register.
		// Frappe otherwise restores each user's last-used filter (saved in
		// __UserSettings), which made the list open pre-filtered (e.g. stuck on
		// workflow_state=Draft). We discard that restored filter on a direct open.
		// A Key Metrics number-card drill-down passes frappe.route_options (applied
		// later in ListView.before_refresh), so those targeted views still work; and
		// users can still filter freely during the session — only the *remembered*
		// filter is ignored at open time.
		const arrived_via_card =
			frappe.route_options && Object.keys(frappe.route_options).length > 0;
		if (!arrived_via_card) {
			listview.filters = [];
		}

		// Compact "Status" quick-filter dropdown in the list toolbar.
		const quick = ["Published", "Review", "Approved", "Draft", "Obsolete", "Archived"];
		quick.forEach((s) => {
			listview.page.add_inner_button(
				s === "Review" ? __("In Review") : __(s),
				() => {
					listview.filter_area.clear();
					listview.filter_area.add([["Document Library", "status", "=", s]]);
				},
				__("Status"),
			);
		});
		listview.page.add_inner_button(
			__("Show all"),
			() => listview.filter_area.clear(),
			__("Status"),
		);
	},
};
