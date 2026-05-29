frappe.listview_settings["Project"] = {
	add_fields: [
		"status", "priority", "percent_complete",
		"expected_end_date", "project_name", "customer", "_assign"
	],
	filters: [["status", "=", "Open"]],

	onload: function (listview) {
		// ── Jira-like CSS ──────────────────────────────────────────────
		if (!document.getElementById("jira-project-list-css")) {
			const s = document.createElement("style");
			s.id = "jira-project-list-css";
			s.textContent = `
				/* === JIRA LIST SKIN FOR PROJECTS === */

				/* page background */
				.layout-main-section { background: #fff !important; }

				/* header row */
				[data-doctype="Project"] .list-row-head {
					background: #f4f5f7 !important;
					border-top: 2px solid #dfe1e6 !important;
					border-bottom: 2px solid #dfe1e6 !important;
				}
				[data-doctype="Project"] .list-row-head .list-col,
				[data-doctype="Project"] .list-row-head span {
					font-size: 11px !important;
					font-weight: 700 !important;
					color: #5e6c84 !important;
					text-transform: uppercase !important;
					letter-spacing: 0.06em !important;
				}

				/* data rows */
				[data-doctype="Project"] .list-row {
					border-left: 3px solid transparent !important;
					border-bottom: 1px solid #ebecf0 !important;
					background: #fff !important;
					transition: background 0.1s, border-left-color 0.1s !important;
				}
				[data-doctype="Project"] .list-row:hover {
					background: #f4f5f7 !important;
					border-left-color: #0052cc !important;
				}

				/* cells */
				[data-doctype="Project"] .list-row .list-col,
				[data-doctype="Project"] .list-row-head .list-col {
					padding: 9px 14px !important;
					vertical-align: middle !important;
				}

				/* title / project name */
				[data-doctype="Project"] .list-row .level-item.bold a,
				[data-doctype="Project"] .list-row .list-subject a {
					font-size: 14px !important;
					font-weight: 500 !important;
					color: #172b4d !important;
				}
				[data-doctype="Project"] .list-row .level-item.bold a:hover,
				[data-doctype="Project"] .list-row .list-subject a:hover {
					color: #0052cc !important;
					text-decoration: underline !important;
				}

				/* hide the default indicator dot — we replace it with a badge */
				[data-doctype="Project"] .list-row .indicator-pill { display:none !important; }

				/* "Assigned to me" / "Due this week" chips */
				.jira-filter-chip {
					display: inline-block;
					padding: 3px 12px;
					border: 1px solid #dfe1e6;
					border-radius: 14px;
					font-size: 12px;
					font-weight: 500;
					color: #42526e;
					cursor: pointer;
					margin-left: 6px;
					background: #fff;
					transition: background 0.15s, border-color 0.15s;
				}
				.jira-filter-chip:hover {
					background: #ebecf0;
					border-color: #b3bac5;
				}
				.jira-filter-chip.active {
					background: #deebff;
					border-color: #4c9aff;
					color: #0052cc;
				}
			`;
			document.head.appendChild(s);
		}

		// ── "Assigned to me" chip ──────────────────────────────────────
		const $bar = $(listview.page.page_actions || listview.page.$title_area);
		const $chips = $(`<span style="margin-left:12px;"></span>`);

		const $assigned = $(`<button class="jira-filter-chip" data-filter="assigned">👤 Assigned to me</button>`);
		const $due      = $(`<button class="jira-filter-chip" data-filter="due">📅 Due this week</button>`);

		$assigned.on("click", function () {
			const active = $(this).hasClass("active");
			$(this).toggleClass("active");
			if (!active) {
				listview.filter_area.add([[listview.doctype, "_assign", "like", "%" + frappe.session.user + "%"]]);
			} else {
				listview.filter_area.remove_filter(listview.doctype, "_assign");
			}
			listview.refresh();
		});

		$due.on("click", function () {
			const active = $(this).hasClass("active");
			$(this).toggleClass("active");
			const today = frappe.datetime.get_today();
			const end   = frappe.datetime.add_days(today, 7);
			if (!active) {
				listview.filter_area.add([
					[listview.doctype, "expected_end_date", ">=", today],
					[listview.doctype, "expected_end_date", "<=", end],
				]);
			} else {
				listview.filter_area.remove_filter(listview.doctype, "expected_end_date");
			}
			listview.refresh();
		});

		$chips.append($assigned).append($due);
		$(listview.page.body).find(".page-head .page-title").after($chips);
	},

	button: {
		show: function (doc) {
			return true;
		},
		get_label: function () {
			return __("View Tasks");
		},
		get_description: function (doc) {
			return __("View tasks for {0}", [doc.project_name || doc.name]);
		},
		action: function (doc) {
			frappe.route_options = { project: doc.name };
			frappe.set_route("List", "Task", "List");
		},
	},

	// keep indicator for Kanban / sidebar colour strip
	get_indicator: function (doc) {
		const map = { Open: "blue", Completed: "green", Cancelled: "red" };
		if (doc.status === "Open" && doc.percent_complete) {
			return [__("{0}%", [cint(doc.percent_complete)]), "orange", "percent_complete,>,0|status,=,Open"];
		}
		return [__(doc.status), map[doc.status] || frappe.utils.guess_colour(doc.status), "status,=," + doc.status];
	},

	formatters: {
		// ── Status badge (exact Jira pill style) ────────────────────────
		status: function (value) {
			if (!value) return "";
			const cfg = {
				Open:      { bg: "#0052CC", color: "#fff", label: "IN PROGRESS" },
				Completed: { bg: "#00875A", color: "#fff", label: "DONE"        },
				Cancelled: { bg: "#97a0af", color: "#fff", label: "CANCELLED"   },
			};
			const c = cfg[value] || { bg: "#dfe1e6", color: "#42526e", label: value.toUpperCase() };
			return `<span style="
				background:${c.bg};
				color:${c.color};
				padding:2px 8px;
				border-radius:3px;
				font-size:11px;
				font-weight:700;
				display:inline-block;
				white-space:nowrap;
				letter-spacing:0.04em;
			">${c.label}</span>`;
		},

		// ── Priority with Jira arrow icons ──────────────────────────────
		priority: function (value) {
			if (!value) return "";
			const p = {
				High:   { color: "#CD5A1B", icon: `<svg viewBox="0 0 16 16" width="14" height="14" fill="#CD5A1B"><path d="M8 3 2 11h12z"/></svg>` },
				Medium: { color: "#0065FF", icon: `<svg viewBox="0 0 16 16" width="14" height="14" fill="#0065FF"><rect x="2" y="5" width="12" height="2"/><rect x="2" y="9" width="12" height="2"/></svg>` },
				Low:    { color: "#2D8738", icon: `<svg viewBox="0 0 16 16" width="14" height="14" fill="#2D8738"><path d="M8 13 2 5h12z"/></svg>` },
			};
			const s = p[value] || { color: "#6b7280", icon: "•" };
			return `<span style="display:inline-flex;align-items:center;gap:4px;color:${s.color};font-weight:600;font-size:13px;">${s.icon}${__(value)}</span>`;
		},

		// ── Due date — red if overdue ────────────────────────────────────
		expected_end_date: function (value) {
			if (!value) return "";
			const today   = frappe.datetime.get_today();
			const overdue = value < today;
			return `<span style="color:${overdue ? "#DE350B" : "#42526E"};font-weight:${overdue ? 600 : 400};">
				${overdue ? "⚠ " : ""}${frappe.datetime.str_to_user(value)}
			</span>`;
		},

	},
};
