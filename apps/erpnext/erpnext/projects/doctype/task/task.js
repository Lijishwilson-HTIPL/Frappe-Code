// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.projects");

frappe.ui.form.on("Task", {
	setup: function (frm) {
		frm.make_methods = {
			Timesheet: () =>
				frappe.model.open_mapped_doc({
					method: "erpnext.projects.doctype.task.task.make_timesheet",
					frm: frm,
				}),
		};
	},

	onload: function (frm) {
		frm._prev_status = frm.doc.status;

		frm.set_query("task", "depends_on", function () {
			let filters = { name: ["!=", frm.doc.name] };
			if (frm.doc.project) filters["project"] = frm.doc.project;
			return { filters: filters };
		});

		frm.set_query("parent_task", function () {
			let filters = { is_group: 1, name: ["!=", frm.doc.name] };
			if (frm.doc.project) filters["project"] = frm.doc.project;
			return { filters: filters };
		});

		frm.set_query("sprint", function () {
			if (frm.doc.project) {
				return { filters: { project: frm.doc.project } };
			}
		});
	},

	refresh: function (frm) {
		frm._prev_status = frm.doc.status;
		erpnext.projects.render_blocked_banner(frm);

		if (!frm.is_new() && frm.doc.is_group) {
			frm.add_custom_button(__("View Sub-Tasks"), function () {
				frappe.route_options = { parent_task: frm.doc.name };
				frappe.set_route("List", "Task", "List");
			}, __("View"));

			frm.add_custom_button(__("Sub-Task Tree"), function () {
				frappe.route_options = { parent_task: frm.doc.name };
				frappe.set_route("List", "Task", "Tree");
			}, __("View"));

			erpnext.projects.render_subtasks(frm);
		}
	},

	is_blocked: function (frm) {
		erpnext.projects.render_blocked_banner(frm);
	},

	status: function (frm) {
		const prev = frm._prev_status;
		const next = frm.doc.status;

		if (next === "Completed" && prev !== "Completed") {
			frm.set_value("status", prev);
			frappe.prompt([
				{
					fieldname: "completed_by",
					fieldtype: "Link",
					options: "User",
					label: __("Completed By"),
					reqd: 1,
					default: frappe.session.user,
				},
				{
					fieldname: "completed_on",
					fieldtype: "Date",
					label: __("Completed On"),
					reqd: 1,
					default: frappe.datetime.get_today(),
				},
				{
					fieldname: "resolution_note",
					fieldtype: "Small Text",
					label: __("Resolution Note"),
				},
			], (values) => {
				frm.set_value("status", "Completed");
				frm.set_value("completed_by", values.completed_by);
				frm.set_value("completed_on", values.completed_on);
				frm._prev_status = "Completed";
			}, __("Mark Task as Completed"), __("Confirm"));
			return;
		}

		if (next === "Cancelled" && prev !== "Cancelled") {
			frm.set_value("status", prev);
			frappe.prompt([
				{
					fieldname: "cancel_reason",
					fieldtype: "Small Text",
					label: __("Reason for Cancellation"),
					reqd: 1,
				},
			], (values) => {
				frm.set_value("status", "Cancelled");
				frm.set_value("cancel_reason", values.cancel_reason);
				frm._prev_status = "Cancelled";
			}, __("Cancel Task"), __("Confirm"));
			return;
		}

		if (next === "Pending Review" && prev !== "Pending Review") {
			frm.set_value("status", prev);
			frappe.prompt([
				{
					fieldname: "review_date",
					fieldtype: "Date",
					label: __("Review Date"),
					reqd: 1,
					default: frappe.datetime.get_today(),
				},
			], (values) => {
				frm.set_value("status", "Pending Review");
				frm.set_value("review_date", values.review_date);
				frm._prev_status = "Pending Review";
			}, __("Send for Review"), __("Confirm"));
			return;
		}

		if (next === "Working" && prev !== "Working") {
			frappe.show_alert({
				message: __("Task started. Remember to log time via a Timesheet."),
				indicator: "blue",
			}, 5);
		}

		frm._prev_status = next;
	},

	is_group: function (frm) {
		frappe.call({
			method: "erpnext.projects.doctype.task.task.check_if_child_exists",
			args: { name: frm.doc.name },
			callback: function (r) {
				if (r.message.length > 0) {
					let message = __(
						"Cannot convert Task to non-group because the following child Tasks exist: {0}.",
						[r.message.join(", ")]
					);
					frappe.msgprint(message);
					frm.reload_doc();
				}
			},
		});
	},

	validate: function (frm) {
		frm.doc.project && frappe.model.remove_from_locals("Project", frm.doc.project);
	},
});

erpnext.projects.render_blocked_banner = function (frm) {
	frm.$wrapper.find(".blocked-banner").remove();
	if (frm.doc.is_blocked) {
		frm.$wrapper.find(".page-form.row").before(`
			<div class="blocked-banner" style="
				background:#fef2f2;border:1px solid #fecaca;border-radius:6px;
				padding:10px 16px;margin:0 0 12px 0;display:flex;
				align-items:center;gap:10px;font-weight:600;color:#dc2626;">
				<span>&#9940;</span>
				<span>${__("This task is blocked. Resolve blockers before proceeding.")}</span>
			</div>`);
	}
};

erpnext.projects.render_subtasks = function (frm) {
	const STATUS_COLOR = {
		"Open": "blue",
		"Working": "orange",
		"Pending Review": "yellow",
		"Overdue": "red",
		"Completed": "green",
		"Cancelled": "grey",
		"Template": "grey",
	};

	frappe.db.get_list("Task", {
		filters: { parent_task: frm.doc.name },
		fields: ["name", "subject", "status", "priority", "assigned_to", "progress", "exp_end_date"],
		limit: 100,
		order_by: "creation asc",
	}).then(tasks => {
		const total = tasks.length;
		const done = tasks.filter(t => t.status === "Completed" || t.status === "Cancelled").length;
		const pct = total ? Math.round((done / total) * 100) : 0;

		const progressBar = total ? `
			<div style="margin-bottom:12px;">
				<div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:4px;">
					<span>${done} of ${total} done</span><span>${pct}%</span>
				</div>
				<div style="background:#e5e7eb;border-radius:4px;height:6px;overflow:hidden;">
					<div style="background:#22c55e;width:${pct}%;height:100%;border-radius:4px;transition:width .3s;"></div>
				</div>
			</div>` : "";

		const rows = tasks.map(t => {
			const color = STATUS_COLOR[t.status] || "blue";
			const due = t.exp_end_date ? `<span style="font-size:11px;color:#9ca3af;margin-left:8px;">${frappe.datetime.str_to_user(t.exp_end_date)}</span>` : "";
			return `
				<div style="display:flex;align-items:center;padding:8px 10px;border-bottom:1px solid #f3f4f6;gap:8px;cursor:pointer;"
					class="subtask-row" data-name="${t.name}">
					<span class="indicator ${color}" style="flex-shrink:0;"></span>
					<a href="/Form/Task/${encodeURIComponent(t.name)}" onclick="event.stopPropagation();"
						style="font-size:11px;color:#6b7280;white-space:nowrap;flex-shrink:0;">${t.name}</a>
					<span style="flex:1;font-size:13px;color:#111827;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${t.subject}</span>
					${due}
					<span class="badge" style="font-size:11px;background:var(--indicator-${color});color:#fff;border-radius:4px;padding:2px 7px;flex-shrink:0;">${t.status}</span>
				</div>`;
		}).join("");

		const noTasks = !total ? `<div style="padding:16px;text-align:center;color:#9ca3af;font-size:13px;">No child issues yet</div>` : "";

		const html = `
			<div style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-top:4px;">
				<div style="padding:10px 14px;background:#f9fafb;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e5e7eb;">
					<span style="font-weight:600;font-size:13px;color:#374151;">Child Issues <span style="font-weight:400;color:#9ca3af;">(${total})</span></span>
					<button class="btn btn-xs btn-default add-subtask-btn" style="font-size:12px;">+ Create child issue</button>
				</div>
				${progressBar}
				<div class="subtask-list">${rows}${noTasks}</div>
			</div>`;

		const $wrapper = frm.fields_dict.subtasks_html.$wrapper;
		$wrapper.html(html);

		$wrapper.find(".add-subtask-btn").on("click", function () {
			frappe.new_doc("Task", {
				parent_task: frm.doc.name,
				project: frm.doc.project,
				is_group: 0,
			});
		});

		$wrapper.find(".subtask-row").on("click", function () {
			frappe.set_route("Form", "Task", $(this).data("name"));
		});
	});
};
