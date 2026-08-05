// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
frappe.ui.form.on("Project", {
	setup(frm) {
		frm.make_methods = {
			Timesheet: () => {
				open_form(frm, "Timesheet", "Timesheet Detail", "time_logs");
			},
			"Purchase Order": () => {
				open_form(frm, "Purchase Order", "Purchase Order Item", "items");
			},
			"Purchase Receipt": () => {
				open_form(frm, "Purchase Receipt", "Purchase Receipt Item", "items");
			},
			"Purchase Invoice": () => {
				open_form(frm, "Purchase Invoice", "Purchase Invoice Item", "items");
			},
		};
	},
	onload: function (frm) {
		const so = frm.get_docfield("sales_order");
		so.get_route_options_for_new_doc = () => {
			if (frm.is_new()) return {};
			return {
				customer: frm.doc.customer,
				project_name: frm.doc.name,
			};
		};

		frm.set_query("user", "users", function () {
			return {
				query: "erpnext.projects.doctype.project.project.get_users_for_project",
			};
		});

		frm.set_query("department", function (doc) {
			return {
				filters: {
					company: doc.company,
				},
			};
		});

		// sales order
		frm.set_query("sales_order", function () {
			var filters = {
				project: ["in", frm.doc.__islocal ? [""] : [frm.doc.name, ""]],
				company: frm.doc.company,
			};

			if (frm.doc.customer) {
				filters["customer"] = frm.doc.customer;
			}

			return {
				filters: filters,
			};
		});

		frm.set_query("cost_center", () => {
			return {
				filters: {
					company: frm.doc.company,
				},
			};
		});
	},

	refresh: function (frm) {
		if (frm.doc.__islocal) {
			frm.web_link && frm.web_link.remove();
		} else {
			frm.add_web_link("/projects?project=" + encodeURIComponent(frm.doc.name));

			frm.trigger("show_dashboard");
			frm.trigger("show_task_summary");
			frm.trigger("show_task_defect_summary_tab");
			frm.trigger("relabel_issue_connection");
		}
		frm.trigger("set_custom_buttons");
	},

	dashboard_update: function (frm) {
		frm.trigger("relabel_issue_connection");
	},

	relabel_issue_connection: function (frm) {
		// The Connections widget renders one badge per linked DocType using its
		// raw name ("Issue"). Projects calls Issues "Defects" everywhere else on
		// this form, so relabel just this badge/tooltip without touching the
		// Issue DocType or its Support-module label anywhere else in the app.
		if (!frm.dashboard || !frm.dashboard.links_area || !frm.dashboard.links_area.body) return;
		frm.dashboard.links_area.body
			.find('.document-link[data-doctype="Issue"] .badge-link')
			.text(__("Defect"));
		frm.dashboard.links_area.body
			.find('.document-link[data-doctype="Issue"] .open-notification')
			.attr("title", __("Open {0}", [__("Defect")]));
	},

	show_task_summary: function (frm) {
		// Total / Completed / Pending task counts for this project, shown as
		// a sidebar panel (next to Links/Assign/Tags) so users don't have to
		// open the Connections tab or a separate report to see progress.
		if (!frm.sidebar || !frm.sidebar.sidebar) return;

		frm.sidebar.sidebar.find(".task-summary-sidebar-section").remove();

		frappe.call({
			method: "erpnext.projects.doctype.project.project.get_task_summary",
			args: { project: frm.doc.name },
			callback: function (r) {
				if (!r.message) return;
				const s = r.message;

				const row = (label, value, css_class) => `
					<div class="flex justify-between align-items-center" style="padding: 2px 0;">
						<span class="text-muted">${__(label)}</span>
						<span class="indicator-pill ${css_class}">${value}</span>
					</div>`;

				const html = `
					<div class="sidebar-section task-summary-sidebar-section border-bottom">
						<div class="form-sidebar-items">
							<div class="form-sidebar-label">
								${frappe.utils.icon("bullet-list", "sm")}
								<span class="ellipsis">${__("Task Summary")}</span>
							</div>
						</div>
						<div style="margin-top: 6px;">
							${row("Total Tasks", s.total, "gray")}
							${row("Completed", s.completed, "green")}
							${row("Pending", s.pending, "orange")}
							${s.cancelled ? row("Cancelled", s.cancelled, "red") : ""}
						</div>
					</div>`;

				frm.sidebar.sidebar.find(".sidebar-meta-details").after(html);
			},
		});
	},

	// ===========================================================================
	// ⚠️  PROTECTED — DO NOT DROP THIS WHEN RESOLVING A MERGE CONFLICT.
	//
	// This function carries deliberate UI fixes (collapsible Tasks/Defects
	// accordions, Defects closed on every login). project.js is an erpnext core
	// file, so it conflicts often. On conflict: KEEP OUR SIDE OF THIS FUNCTION and
	// take the incoming side elsewhere in the file — merge both, don't pick one
	// whole file.
	//
	// Must survive the merge: DEFAULT_COLLAPSED, the frappe.csrf_token-namespaced
	// collapse_key(), the .summary-accordion* markup, and the click + keydown
	// handlers on .summary-accordion-header.
	//
	// Do NOT "simplify" the collapsed-state storage to localStorage, to plain
	// sessionStorage, or to the sid cookie — all three have been tried and are
	// broken (sid is httponly, so JS cannot read it and the key degrades to a
	// constant). Only frappe.csrf_token resets per login.
	//
	// Full rationale + verification checklist: documents/PROJECT_UI_CHANGES.md
	// ===========================================================================
	show_task_defect_summary_tab: function (frm) {
		// Full Task + Defect (Issue) summary report on the form's own "Summary"
		// tab — same numbers as the sidebar panel, plus a per-status breakdown.
		// Every number is clickable and opens the filtered Task / Defect list
		// for exactly that slice (e.g. clicking "Completed" opens the list
		// filtered to this project + completed statuses).
		const $wrapper = frm.fields_dict.task_defect_summary_html?.$wrapper;
		if (!$wrapper) return;

		$wrapper.html(`<div class="text-muted" style="padding: 12px 0;">${__("Loading summary...")}</div>`);

		// Every status the doctype's own Select field defines, in schema order —
		// each always gets a card, even at zero, instead of only showing
		// whichever statuses happen to have records today (which duplicated
		// "Completed" against the old Total/Completed/Pending row above it).
		const ALL_STATUSES = {
			Task: ["Open", "Working", "Pending Review", "Overdue", "Hold", "Completed", "Cancelled"],
			Issue: ["Open", "Replied", "On Hold", "Resolved", "Closed"],
		};

		// Semantic accent per status — a thin bottom rule, not a left rail —
		// so the card still reads clean/flat at rest and only reveals color
		// as a footnote, matching each doctype's own list-view indicator
		// colors (task_list.js / issue_list.js) for consistency across the app.
		const STATUS_ACCENT = {
			Task: {
				Open: "var(--yellow-500, #fdd049)",
				Working: "var(--blue-500, #2490ef)",
				"Pending Review": "var(--orange-500, #f8a428)",
				Overdue: "var(--red-500, #ea4c4c)",
				Hold: "var(--gray-600, #74808b)",
				Completed: "var(--green-500, #2ec973)",
				Cancelled: "var(--gray-500, #8d99a6)",
			},
			Issue: {
				Open: "var(--yellow-500, #fdd049)",
				Replied: "var(--blue-500, #2490ef)",
				"On Hold": "var(--orange-500, #f8a428)",
				Resolved: "var(--green-500, #2ec973)",
				Closed: "var(--gray-600, #74808b)",
			},
		};

		// One individual card per stat — clickable to open the matching
		// filtered list. Total gets no accent (it's an aggregate, not a
		// status); a quiet hover lift signals interactivity without relying
		// on color alone.
		const stat_card = (doctype, project, label, value, statuses, accent) => `
			<a class="summary-stat-card" data-doctype="${doctype}" data-project="${frappe.utils.escape_html(
				project
			)}" data-statuses='${statuses ? JSON.stringify(statuses) : ""}'
				style="--accent: ${accent || "transparent"}; flex: 1 1 0; min-width: 0; background: var(--card-bg, #fff); border: 1px solid var(--border-color, #d1d8dd);
					border-bottom: 3px solid ${accent || "var(--border-color, #d1d8dd)"};
					border-radius: 8px; padding: 11px 12px 9px; cursor: pointer; text-decoration: none !important;
					box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.05)); transition: box-shadow 0.15s ease, transform 0.15s ease, background 0.15s ease;
					overflow: hidden;">
				<div class="text-muted" style="font-size: 11px; font-weight: 500; letter-spacing: 0.01em; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${__(label)}</div>
				<div class="num" style="font-size: 21px; font-weight: 650; line-height: 1; color: var(--text-color, #1f272e); font-variant-numeric: tabular-nums;">${value}</div>
			</a>`;

		// Small horizontal key so the underline colors are self-explanatory
		// on first use, instead of relying on users to learn them by trial.
		const legend = (doctype) => `
			<div class="text-muted" style="display: flex; align-items: center; justify-content: flex-end; gap: 14px; flex-wrap: wrap; font-size: 11.5px; margin: 3%;">
				${ALL_STATUSES[doctype]
					.map(
						(status) => `
					<span style="display: inline-flex; align-items: center; gap: 5px; white-space: nowrap;">
						<span style="width: 8px; height: 8px; border-radius: 50%; background: ${STATUS_ACCENT[doctype][status]}; flex-shrink: 0;"></span>
						${__(status)}
					</span>`
					)
					.join("")}
			</div>`;

		// Each block is a collapsible accordion, so a section that isn't relevant to
		// a given project can be folded away instead of taking up the tab. Tasks are
		// the primary content so they open by default; Defects start folded (they are
		// empty on most projects, and manufacturing projects never log any) — the
		// count badge in the header still shows the total while it's closed.
		// Whatever the user chooses is remembered per section per browser, so the
		// chosen layout survives reloads and route changes.
		const DEFAULT_COLLAPSED = { Tasks: false, Defects: true };

		// The stored state is scoped to the CURRENT LOGIN, so logging out always
		// resets Defects to closed.
		//
		// Two earlier attempts failed:
		//   - localStorage     -> outlived the session entirely.
		//   - sessionStorage   -> survives logout -> login in the same tab.
		//   - keying on the sid cookie -> frappe sets `sid` with httponly=True
		//     (auth.py:394), so JS can never read it; the key silently degraded to a
		//     constant and behaved exactly like plain sessionStorage.
		//
		// frappe.csrf_token (set per session in www/desk.html) IS readable from JS
		// and is reissued on every login, so a fresh login cannot match the previous
		// session's keys and the defaults apply again: Tasks open, Defects closed.
		const session_id = frappe.csrf_token || frappe.session?.user || "nosession";
		const collapse_key = (title) => `project_summary_collapsed::${session_id}::${title}`;

		const is_collapsed = (title) => {
			const saved = sessionStorage.getItem(collapse_key(title));
			if (saved !== null) return saved === "1";
			return !!DEFAULT_COLLAPSED[title];
		};
		const panel_id = (title) => `summary-panel-${frappe.scrub(title)}`;

		// Drop keys from earlier builds / previous logins so nothing stale survives:
		// an old localStorage flag could otherwise pin Tasks shut, and old per-session
		// keys would just accumulate.
		Object.keys(DEFAULT_COLLAPSED).forEach((t) => {
			localStorage.removeItem(`project_summary_collapsed::${t}`);
			sessionStorage.removeItem(`project_summary_collapsed::${t}`);
		});
		Object.keys(sessionStorage)
			.filter((k) => k.startsWith("project_summary_collapsed::") && !k.includes(session_id))
			.forEach((k) => sessionStorage.removeItem(k));

		const section = (title, icon, doctype, project, s, view_route) => {
			const collapsed = is_collapsed(title);
			const total = s.total || 0;
			return `
			<div class="summary-accordion ${collapsed ? "" : "open"}" data-section="${frappe.utils.escape_html(title)}">
				<div class="summary-accordion-header" role="button" tabindex="0"
					aria-expanded="${!collapsed}" aria-controls="${panel_id(title)}"
					title="${__("Click to show or hide this section")}">
					<div class="flex align-items-center" style="gap: 8px; font-weight: 700; font-size: 18px; color: var(--dms-blue, #1e3a5f);">
						<svg class="summary-chevron" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
							<path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" stroke-width="1.8"
								stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
						${frappe.utils.icon(icon, "md")} ${__(title)}
						<span class="summary-count-badge">${total}</span>
					</div>
					<a href="${view_route}" class="btn btn-default btn-xs summary-view-all">${__("View All {0}", [
						__(title),
					])}</a>
				</div>
				<div class="summary-accordion-panel" id="${panel_id(title)}">
					<div class="summary-accordion-panel-inner">
						<div style="padding-top: 4px;">
							<div style="margin-bottom: 16px;">${legend(doctype)}</div>
							<div style="display: flex; gap: 8px; flex-wrap: nowrap;">
								${stat_card(doctype, project, "Total", s.total, null, null)}
								${ALL_STATUSES[doctype]
									.map((status) =>
										stat_card(doctype, project, status, s.by_status[status] || 0, [status], STATUS_ACCENT[doctype][status])
									)
									.join("")}
							</div>
						</div>
					</div>
				</div>
			</div>`;
		};

		Promise.all([
			frappe.call({
				method: "erpnext.projects.doctype.project.project.get_task_summary",
				args: { project: frm.doc.name },
			}),
			frappe.call({
				method: "erpnext.projects.doctype.project.project.get_defect_summary",
				args: { project: frm.doc.name },
			}),
		]).then(([task_r, defect_r]) => {
			const task_route = `/app/task?project=${encodeURIComponent(frm.doc.name)}`;
			const defect_route = `/app/issue?project=${encodeURIComponent(frm.doc.name)}`;

			$wrapper.html(`
				<style>
					.summary-stat-card:hover {
						box-shadow: var(--shadow-md, 0 4px 12px rgba(0, 0, 0, 0.1)) !important;
						transform: translateY(-1px);
						background: color-mix(in srgb, var(--accent, transparent) 10%, var(--card-bg, #fff)) !important;
					}
					/* Collapsible section. Colours come from frappe's theme variables
					   (not fixed hex) so this stays correct in dark mode. */
					.summary-accordion-header {
						display: flex;
						align-items: center;
						justify-content: space-between;
						gap: 8px;
						padding: 8px 10px;
						margin: 0 -10px 8px;
						border-radius: 6px;
						cursor: pointer;
						user-select: none;
						transition: background 0.15s ease;
					}
					.summary-accordion-header:hover {
						background: var(--fg-hover-color, var(--control-bg, #f4f5f6));
					}
					.summary-accordion-header:focus-visible {
						outline: 2px solid var(--primary, #2490ef);
						outline-offset: 1px;
					}
					.summary-chevron {
						width: 16px;
						height: 16px;
						flex-shrink: 0;
						color: var(--text-muted, #8d99a6);
						transform: rotate(-90deg);
						transition: transform 0.25s ease;
					}
					.summary-accordion.open .summary-chevron { transform: rotate(0deg); }
					/* "View All Tasks" and "View All Defects" are different lengths, so
					   without a shared width their left edges sit ragged against each
					   other. A common min-width makes both buttons identical, so the
					   two header rows line up on both edges. */
					.summary-view-all {
						flex: 0 0 auto;
						min-width: 132px;
						text-align: center;
						font-size: 12px;
						border-radius: 6px;
						padding: 4px 12px;
						white-space: nowrap;
					}
					.summary-count-badge {
						display: inline-flex;
						align-items: center;
						justify-content: center;
						min-width: 22px;
						height: 20px;
						padding: 0 7px;
						border-radius: 999px;
						background: var(--control-bg, #f4f5f6);
						color: var(--text-muted, #8d99a6);
						font-size: 12px;
						font-weight: 700;
						font-variant-numeric: tabular-nums;
					}
					/* 0fr -> 1fr grid trick: animates to the panel's natural height
					   without hardcoding a max-height. */
					.summary-accordion-panel {
						display: grid;
						grid-template-rows: 0fr;
						transition: grid-template-rows 0.28s ease;
					}
					.summary-accordion.open .summary-accordion-panel { grid-template-rows: 1fr; }
					.summary-accordion-panel-inner { overflow: hidden; }
					@media (prefers-reduced-motion: reduce) {
						.summary-accordion-panel, .summary-chevron { transition: none; }
					}
				</style>
				<div style="display: flex; flex-direction: column; gap: 22px; margin-top: 8px;">
					${section("Tasks", "bullet-list", "Task", frm.doc.name, task_r.message, task_route)}
					${section("Defects", "alert-triangle", "Issue", frm.doc.name, defect_r.message, defect_route)}
				</div>
			`);

			// Collapse / expand a section and remember the choice. The "View All"
			// button lives inside the header, so its click must not also toggle.
			const toggle_section = ($header) => {
				const $acc = $header.closest(".summary-accordion");
				const open = $acc.toggleClass("open").hasClass("open");
				$header.attr("aria-expanded", open);
				const title = $acc.attr("data-section");
				sessionStorage.setItem(collapse_key(title), open ? "0" : "1");
			};

			// "View All" sits inside the clickable header, so its click must not also
			// toggle the section open/closed.
			$wrapper.off("click", ".summary-view-all").on("click", ".summary-view-all", function (e) {
				e.stopPropagation();
			});

			$wrapper
				.off("click", ".summary-accordion-header")
				.on("click", ".summary-accordion-header", function () {
					toggle_section($(this));
				});

			$wrapper
				.off("keydown", ".summary-accordion-header")
				.on("keydown", ".summary-accordion-header", function (e) {
					if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
						e.preventDefault();
						toggle_section($(this));
					}
				});

			$wrapper.off("click", ".summary-stat-card").on("click", ".summary-stat-card", function () {
				const $el = $(this);
				const doctype = $el.attr("data-doctype");
				const project = $el.attr("data-project");
				const statuses_raw = $el.attr("data-statuses");

				const filters = { project: project };
				if (statuses_raw) {
					const statuses = JSON.parse(statuses_raw);
					filters.status = statuses.length === 1 ? statuses[0] : ["in", statuses];
				}

				frappe.route_options = filters;
				frappe.set_route("List", doctype);
			});
		});
	},

	set_custom_buttons: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Duplicate Project with Tasks"),
				() => {
					frm.events.create_duplicate(frm);
				},
				__("Actions")
			);

			frm.add_custom_button(
				__("Update Costing and Billing"),
				() => {
					frm.events.update_costing_and_billing(frm);
				},
				__("Actions")
			);

			frm.trigger("set_project_status_button");

			if (frappe.model.can_read("Task")) {
				frm.add_custom_button(
					__("Gantt Chart"),
					function () {
						frappe.route_options = {
							project: frm.doc.name,
						};
						frappe.set_route("List", "Task", "Gantt");
					},
					__("View")
				);

				frm.add_custom_button(
					__("Kanban Board"),
					() => {
						frappe
							.call(
								"erpnext.projects.doctype.project.project.create_kanban_board_if_not_exists",
								{
									project: frm.doc.name,
								}
							)
							.then(() => {
								frappe.set_route("List", "Task", "Kanban", frm.doc.project_name);
							});
					},
					__("View")
				);
			}
		}
	},

	update_costing_and_billing: function (frm) {
		frappe.call({
			method: "erpnext.projects.doctype.project.project.update_costing_and_billing",
			args: { project: frm.doc.name },
			freeze: true,
			freeze_message: __("Updating Costing and Billing fields against this Project..."),
			callback: function (r) {
				if (r && !r.exc) {
					frappe.msgprint(__("Costing and Billing fields has been updated"));
					frm.refresh();
				}
			},
		});
	},

	set_project_status_button: function (frm) {
		frm.add_custom_button(
			__("Set Project Status"),
			() => frm.events.get_project_status_dialog(frm).show(),
			__("Actions")
		);
	},

	get_project_status_dialog: function (frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Set Project Status"),
			fields: [
				{
					fieldname: "status",
					fieldtype: "Select",
					label: "Status",
					reqd: 1,
					options: "Completed\nCancelled",
				},
			],
			primary_action: function () {
				frm.events.set_status(frm, dialog.get_values().status);
				dialog.hide();
			},
			primary_action_label: __("Set Project Status"),
		});
		return dialog;
	},

	create_duplicate: function (frm) {
		return new Promise((resolve) => {
			frappe.prompt("Project Name", (data) => {
				frappe
					.xcall("erpnext.projects.doctype.project.project.create_duplicate_project", {
						prev_doc: frm.doc,
						project_name: data.value,
					})
					.then(() => {
						frappe.set_route("Form", "Project", data.value);
						frappe.show_alert(__("Duplicate project has been created"));
					});
				resolve();
			});
		});
	},

	set_status: function (frm, status) {
		frappe.confirm(__("Set Project and all Tasks to status {0}?", [__(status).bold()]), () => {
			frappe
				.xcall("erpnext.projects.doctype.project.project.set_project_status", {
					project: frm.doc.name,
					status: status,
				})
				.then(() => {
					frm.reload_doc();
				});
		});
	},

	collect_progress: function (frm) {
		if (frm.doc.collect_progress && !frm.doc.subject) {
			frm.set_value("subject", __("For project - {0}, update your status", [frm.doc.project_name]));
		}
	},
});

function open_form(frm, doctype, child_doctype, parentfield) {
	frappe.model.with_doctype(doctype, () => {
		let new_doc = frappe.model.get_new_doc(doctype);

		// add a new row and set the project
		let new_child_doc = frappe.model.get_new_doc(child_doctype);
		new_child_doc.project = frm.doc.name;
		new_child_doc.parent = new_doc.name;
		new_child_doc.parentfield = parentfield;
		new_child_doc.parenttype = doctype;
		new_doc[parentfield] = [new_child_doc];
		new_doc.project = frm.doc.name;

		frappe.ui.form.make_quick_entry(doctype, null, null, new_doc);
	});
}
