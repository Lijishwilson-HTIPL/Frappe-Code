frappe.pages["task-assignment-board"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Task Assignment Board",
		single_column: true,
	});

	var board = new TaskAssignmentBoard(page);
	$(wrapper).data("task_assignment_board", board);
};

frappe.pages["task-assignment-board"].on_page_show = function (wrapper) {
	$(wrapper).data("task_assignment_board").refresh();
};

class TaskAssignmentBoard {
	constructor(page) {
		this.page = page;
		this.setup_filters();
		this.setup_styles();
		this.$wrapper = $('<div class="tab-board-wrap">').appendTo(page.main);
	}

	setup_filters() {
		this.project_filter = this.page.add_field({
			fieldtype: "Link",
			fieldname: "project",
			options: "Project",
			label: __("Project"),
			change: () => this.refresh(),
		});

		this.page.set_secondary_action(__("Refresh"), () => this.refresh(), "refresh");
	}

	setup_styles() {
		frappe.dom.set_style(`
			.tab-board-wrap { padding: 0; overflow: hidden; display: flex; flex-direction: column; height: calc(100vh - 140px); }
			.tab-board-cols { display: flex; gap: 14px; align-items: flex-start; min-width: max-content; overflow-x: auto; overflow-y: hidden; padding: 12px 15px; flex: 1; height: 100%; }
			.tab-board-col { background: var(--card-bg, #fff); border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; width: 270px; flex-shrink: 0; display: flex; flex-direction: column; max-height: 100%; transition: border-color 0.15s; }
			.tab-board-col.drag-over { border-color: var(--primary, #5e64ff); background: var(--blue-50, #f0f1ff); }
			.tab-board-col-head { padding: 10px 14px; font-weight: 600; font-size: 13px; border-bottom: 1px solid var(--border-color, #d1d8dd); display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-shrink: 0; background: var(--card-bg, #fff); border-radius: 8px 8px 0 0; position: sticky; top: 0; z-index: 2; }
			.tab-board-col-body { padding: 8px; overflow-y: auto; flex: 1; min-height: 60px; }
			.tab-task-card { background: var(--card-bg, #fff); border: 1px solid var(--border-color, #d1d8dd); border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; cursor: grab; transition: box-shadow 0.15s ease, opacity 0.15s; }
			.tab-task-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.10); border-color: var(--primary, #5e64ff); }
			.tab-task-card.dragging { opacity: 0.4; cursor: grabbing; }
			.tab-task-title { font-size: 13px; font-weight: 500; margin-bottom: 5px; line-height: 1.4; }
			.tab-task-meta { font-size: 11px; color: var(--text-muted, #8d99a6); display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
			.tab-priority { padding: 1px 7px; border-radius: 10px; font-size: 10px; font-weight: 700; letter-spacing: 0.3px; }
			.tab-priority-Urgent { background: #fde8e8; color: #c0392b; }
			.tab-priority-High { background: #fde8e8; color: #c0392b; }
			.tab-priority-Medium { background: #fff8e1; color: #856404; }
			.tab-priority-Low { background: #e8f5e9; color: #2e7d32; }
			.tab-status-badge { padding: 1px 7px; border-radius: 10px; font-size: 10px; font-weight: 600; background: var(--gray-100, #f4f5f6); color: var(--text-muted, #8d99a6); }
			.tab-status-Overdue { background: #fde8e8; color: #c0392b; }
			.tab-status-Open { background: #e8f5e9; color: #2e7d32; }
			.tab-status-Working { background: #e3f2fd; color: #1565c0; }
			.tab-board-empty { text-align: center; padding: 24px 10px; color: var(--text-muted, #8d99a6); font-size: 12px; }
			.tab-board-loading { padding: 30px; text-align: center; color: var(--text-muted, #8d99a6); }
			.tab-user-badge { display: inline-flex; align-items: center; gap: 5px; min-width: 0; overflow: hidden; }
			.tab-user-badge span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
		`);
	}

	refresh() {
		this.$wrapper.html(`<div class="tab-board-loading">${__("Loading...")}</div>`);
		let project = this.project_filter.get_value();

		frappe.call({
			method: "erpnext.projects.page.task_assignment_board.task_assignment_board.get_task_data",
			args: { project: project || "" },
			callback: (r) => {
				if (r.message) {
					this.render(r.message);
				}
			},
		});
	}

	render(data) {
		let { tasks } = data;

		let groups = {};
		tasks.forEach((task) => {
			let users = task.assigned_to && task.assigned_to.length ? task.assigned_to : ["__unassigned__"];
			users.forEach((user) => {
				if (!groups[user]) groups[user] = [];
				groups[user].push(task);
			});
		});

		let user_keys = Object.keys(groups)
			.filter((u) => u !== "__unassigned__")
			.sort((a, b) => groups[b].length - groups[a].length);
		if (groups["__unassigned__"]) user_keys.push("__unassigned__");

		if (!user_keys.length) {
			this.$wrapper.html(`<div class="tab-board-empty">${__("No open tasks found.")}</div>`);
			return;
		}

		let cols_html = user_keys.map((user) => {
			let user_tasks = groups[user];
			let label = user === "__unassigned__"
				? __("Unassigned")
				: frappe.user_info(user).fullname || user;
			let avatar = user === "__unassigned__"
				? `<span class="avatar avatar-small"><i class="fa fa-user-o"></i></span>`
				: frappe.avatar(user, "avatar-small");

			let cards = user_tasks.map((t) => this.card_html(t)).join("");
			return `
				<div class="tab-board-col" data-user="${frappe.utils.escape_html(user)}">
					<div class="tab-board-col-head">
						<span class="tab-user-badge">${avatar}<span>${frappe.utils.escape_html(label)}</span></span>
						<span class="badge badge-pill badge-secondary">${user_tasks.length}</span>
					</div>
					<div class="tab-board-col-body" data-user="${frappe.utils.escape_html(user)}">
						${cards || `<div class="tab-board-empty">${__("No tasks")}</div>`}
					</div>
				</div>`;
		}).join("");

		this.$wrapper.html(`<div class="tab-board-cols">${cols_html}</div>`);

		this.bind_drag_drop();
	}

	bind_drag_drop() {
		const self = this;

		// Make cards draggable
		this.$wrapper.find(".tab-task-card").each(function () {
			this.setAttribute("draggable", "true");

			this.addEventListener("dragstart", function (e) {
				e.dataTransfer.setData("task_name", this.dataset.name);
				e.dataTransfer.setData("from_user", $(this).closest(".tab-board-col-body").data("user"));
				e.dataTransfer.effectAllowed = "move";
				$(this).addClass("dragging");
			});

			this.addEventListener("dragend", function () {
				$(this).removeClass("dragging");
				self.$wrapper.find(".drag-over").removeClass("drag-over");
			});

			// Click to open
			this.addEventListener("click", function () {
				frappe.set_route("Form", "Task", this.dataset.name);
			});
		});

		// Column drop zones
		this.$wrapper.find(".tab-board-col-body").each(function () {
			this.addEventListener("dragover", function (e) {
				e.preventDefault();
				e.dataTransfer.dropEffect = "move";
				$(this).closest(".tab-board-col").addClass("drag-over");
			});

			this.addEventListener("dragleave", function (e) {
				if (!this.contains(e.relatedTarget)) {
					$(this).closest(".tab-board-col").removeClass("drag-over");
				}
			});

			this.addEventListener("drop", function (e) {
				e.preventDefault();
				$(this).closest(".tab-board-col").removeClass("drag-over");

				let task_name = e.dataTransfer.getData("task_name");
				let from_user = e.dataTransfer.getData("from_user");
				let to_user = this.dataset.user;

				if (from_user === to_user) return;

				self.reassign_task(task_name, from_user, to_user);
			});
		});
	}

	reassign_task(task_name, from_user, to_user) {
		frappe.call({
			method: "erpnext.projects.page.task_assignment_board.task_assignment_board.reassign_task",
			args: {
				task_name: task_name,
				from_user: from_user === "__unassigned__" ? "" : from_user,
				to_user: to_user === "__unassigned__" ? "" : to_user,
			},
			freeze: false,
			callback: (r) => {
				if (!r.exc) {
					frappe.show_alert({
						message: __("Task reassigned"),
						indicator: "green",
					}, 2);
					this.refresh();
				}
			},
		});
	}

	card_html(task) {
		let priority = task.priority || "Medium";
		let due = task.exp_end_date
			? `<span>Due: ${frappe.datetime.str_to_user(task.exp_end_date)}</span>`
			: "";
		let project = task.project
			? `<span style="color:var(--text-muted,#8d99a6)">${frappe.utils.escape_html(task.project)}</span>`
			: "";
		let status_cls = (task.status || "").replace(/\s+/g, "");
		let status = task.status
			? `<span class="tab-status-badge tab-status-${frappe.utils.escape_html(status_cls)}">${frappe.utils.escape_html(task.status)}</span>`
			: "";

		return `
			<div class="tab-task-card" data-name="${frappe.utils.escape_html(task.name)}" title="${frappe.utils.escape_html(task.subject)}">
				<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:6px;margin-bottom:5px;">
					<div class="tab-task-title" style="margin-bottom:0;flex:1">${frappe.utils.escape_html(task.subject)}</div>
					${status}
				</div>
				<div class="tab-task-meta">
					${project}${due}
					<span class="tab-priority tab-priority-${priority}">${priority}</span>
				</div>
			</div>`;
	}
}
