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

	show_task_defect_summary_tab: function (frm) {
		// Full Task + Defect (Issue) summary report on the form's own "Summary"
		// tab — same numbers as the sidebar panel, plus a per-status breakdown.
		// Every number is clickable and opens the filtered Task / Defect list
		// for exactly that slice (e.g. clicking "Completed" opens the list
		// filtered to this project + completed statuses).
		const $wrapper = frm.fields_dict.task_defect_summary_html?.$wrapper;
		if (!$wrapper) return;

		$wrapper.html(`<div class="text-muted" style="padding: 12px 0;">${__("Loading summary...")}</div>`);

		// Status sets behind each aggregate bucket — mirrors the grouping
		// done server-side in get_task_summary / get_defect_summary.
		const STATUS_GROUPS = {
			Task: {
				completed: ["Completed"],
				pending: ["Open", "Working", "Pending Review", "Overdue", "Hold"],
				cancelled: ["Cancelled"],
			},
			Issue: {
				completed: ["Resolved", "Closed"],
				pending: ["Open", "Replied", "On Hold"],
			},
		};

		// One individual card per stat — same visual language as the
		// workspace's "Active Projects / Open Tasks" overview tiles, each
		// tile clickable to open the matching filtered list.
		const stat_card = (doctype, project, label, value, color, statuses) => `
			<a class="summary-stat-card" data-doctype="${doctype}" data-project="${frappe.utils.escape_html(
				project
			)}" data-statuses='${statuses ? JSON.stringify(statuses) : ""}'
				style="flex: 1; min-width: 150px; background: var(--card-bg, #fff); border: 1px solid var(--border-color, #d1d8dd);
					border-radius: 10px; padding: 14px 16px; cursor: pointer; text-decoration: none !important;
					box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.06)); transition: box-shadow 0.15s ease, transform 0.15s ease;">
				<div class="text-muted" style="font-size: 12px; margin-bottom: 4px;">${__(label)}</div>
				<div style="font-size: 26px; font-weight: 700; color: ${color};">${value}</div>
			</a>`;

		const status_rows = (doctype, project, by_status) =>
			Object.keys(by_status)
				.sort()
				.map((status) => stat_card(doctype, project, status, by_status[status], "var(--text-color, #1f272e)", [status]))
				.join("");

		const section = (title, icon, doctype, project, s, view_route) => `
			<div>
				<div class="flex justify-between align-items-center" style="margin-bottom: 10px;">
					<div class="flex align-items-center" style="gap: 8px; font-weight: 650; font-size: 15px;">
						${frappe.utils.icon(icon, "sm")} ${__(title)}
					</div>
					<a href="${view_route}" style="font-size: 12px;">${__("View All")}</a>
				</div>
				<div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 10px;">
					${stat_card(doctype, project, "Total", s.total, "var(--text-color, #1f272e)", null)}
					${stat_card(
						doctype,
						project,
						"Completed",
						s.completed,
						"var(--text-color, #1f272e)",
						STATUS_GROUPS[doctype].completed
					)}
					${stat_card(
						doctype,
						project,
						"Pending",
						s.pending,
						"var(--text-color, #1f272e)",
						STATUS_GROUPS[doctype].pending
					)}
				</div>
				<div style="display: flex; gap: 12px; flex-wrap: wrap;">
					${status_rows(doctype, project, s.by_status) || `<span class="text-muted" style="font-size: 12px;">${__("No records yet")}</span>`}
				</div>
			</div>`;

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
					}
				</style>
				<div style="display: flex; flex-direction: column; gap: 22px; margin-top: 8px;">
					${section("Tasks", "bullet-list", "Task", frm.doc.name, task_r.message, task_route)}
					${section("Defects", "alert-triangle", "Issue", frm.doc.name, defect_r.message, defect_route)}
				</div>
			`);

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
