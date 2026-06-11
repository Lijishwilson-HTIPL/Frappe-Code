frappe.pages["task-assignment-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Task Assignment Board"),
		single_column: true,
	});
	wrapper._tab = new TaskAssignmentBoard(page);
};

frappe.pages["task-assignment-board"].on_page_show = function (wrapper) {
	if (!wrapper._tab) return;
	const opts = frappe.route_options || {};
	if (opts.project) {
		wrapper._tab._project_field.set_value(opts.project);
		wrapper._tab.project = opts.project;
		frappe.route_options = {};
	}
	wrapper._tab.refresh();
};

const TASK_STATUSES = ["Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled"];

class TaskAssignmentBoard {
	constructor(page) {
		this.page = page;
		this.project = null;
		this.sprint = null;
		this.department = null;
		this.status = null;
		this.show_completed = false;
		this.all_collapsed = false;
		this._tasks = [];
		this._users = [];
		this._user_map = {};
		this._task_map = {};
		this._setup_filters();
		this._setup_menu();
		this._inject_css();
		this.$board = $('<div class="tab-board"></div>').appendTo($(page.body));
		this.refresh();
	}

	_setup_filters() {
		this._project_field = this.page.add_field({
			fieldtype: "Link",
			fieldname: "project",
			label: __("Project"),
			options: "Project",
			change: () => { this.project = this._project_field.get_value(); this.refresh(); },
		});

		this._sprint_field = this.page.add_field({
			fieldtype: "Link",
			fieldname: "sprint",
			label: __("Sprint"),
			options: "Sprint",
			change: () => { this.sprint = this._sprint_field.get_value(); this.refresh(); },
		});

		this._department_field = this.page.add_field({
			fieldtype: "Link",
			fieldname: "department",
			label: __("Department"),
			options: "Department",
			change: () => { this.department = this._department_field.get_value(); this.refresh(); },
		});

		this._status_field = this.page.add_field({
			fieldtype: "Select",
			fieldname: "status",
			label: __("Status"),
			options: [
				{ label: __("All Active"), value: "" },
				{ label: __("Open"), value: "Open" },
				{ label: __("Working"), value: "Working" },
				{ label: __("Pending Review"), value: "Pending Review" },
				{ label: __("Overdue"), value: "Overdue" },
			],
			default: "",
			change: () => { this.status = this._status_field.get_value(); this.refresh(); },
		});

		this.page.add_button(__("Refresh"), () => this.refresh(), { icon: "refresh" });
	}

	_setup_menu() {
		this.page.add_menu_item(__("Export to CSV"), () => this._export_csv());
		this.page.add_menu_item(__("Clear Filters"), () => this._clear_filters());
		this.page.add_menu_item(__("Collapse All Columns"), () => this._toggle_collapse());
		this.page.add_menu_item(__("Show Completed Tasks"), () => this._toggle_completed());
	}

	refresh() {
		this.$board.html(`<div class="tab-loading"><span class="tab-spinner"></span> ${__("Loading…")}</div>`);
		frappe.call({
			method: "erpnext.projects.page.task_assignment_board.task_assignment_board.get_board_data",
			args: {
				project: this.project || "",
				sprint: this.sprint || "",
				department: this.department || "",
				status: this.status || "",
				show_completed: this.show_completed ? 1 : 0,
			},
			callback: (r) => {
				if (r.message) {
					this._tasks = r.message.tasks;
					this._users = r.message.users;
					this._user_map = {};
					this._task_map = {};
					this._users.forEach(u => this._user_map[u.name] = u);
					this._tasks.forEach(t => this._task_map[t.name] = t);
					this._render(this._tasks, this._users);
				}
			},
		});
	}

	_render(tasks, users) {
		this.$board.empty();

		const byUser = { __unassigned__: [] };
		users.forEach(u => byUser[u.name] = []);

		tasks.forEach(t => {
			if (!t.assignees || t.assignees.length === 0) {
				byUser["__unassigned__"].push(t);
			} else {
				let placed = false;
				t.assignees.forEach(uid => {
					if (byUser[uid] !== undefined) {
						byUser[uid].push(t);
						placed = true;
					}
				});
				if (!placed) byUser["__unassigned__"].push(t);
			}
		});

		const unassignedCol = { name: "__unassigned__", full_name: __("Unassigned"), user_image: null };
		const sortedUsers = [...users].sort((a, b) => (byUser[b.name] || []).length - (byUser[a.name] || []).length);
		const columns = [...sortedUsers, unassignedCol];
		const $scroll = $('<div class="tab-scroll"></div>').appendTo(this.$board);

		columns.forEach(user => {
			const colTasks = byUser[user.name] || [];
			const $col = $(`
				<div class="tab-col" data-user="${frappe.utils.escape_html(user.name)}">
					<div class="tab-col-header">
						${this._avatar(user)}
						<span class="tab-col-name">${frappe.utils.escape_html(user.full_name)}</span>
						<span class="tab-col-count badge">${colTasks.length}</span>
						<button class="tab-col-toggle btn btn-xs" title="${__("Collapse")}">▲</button>
					</div>
					<div class="tab-col-body"></div>
				</div>
			`).appendTo($scroll);

			const $body = $col.find(".tab-col-body");
			const $toggle = $col.find(".tab-col-toggle");

			colTasks.forEach(t => $body.append(this._card(t)));

			// collapse/expand single column
			$toggle.on("click", () => {
				const collapsed = $col.hasClass("tab-col-collapsed");
				$col.toggleClass("tab-col-collapsed", !collapsed);
				$toggle.text(collapsed ? "▲" : "▼");
				$toggle.attr("title", collapsed ? __("Collapse") : __("Expand"));
			});

			// drag-drop
			$body[0].addEventListener("dragover", e => { e.preventDefault(); $body.addClass("tab-drop-target"); });
			$body[0].addEventListener("dragleave", (e) => {
				if (!$body[0].contains(e.relatedTarget)) {
					$body.removeClass("tab-drop-target");
				}
			});
			$body[0].addEventListener("drop", e => {
				e.preventDefault();
				$body.removeClass("tab-drop-target");
				const taskName = e.dataTransfer.getData("text/plain");
				this._confirm_reassign(taskName, user);
			});
		});

		// Auto-scroll the board horizontally when dragging near edges
		const scrollEl = $scroll[0];
		let _scrollRAF = null;
		const _stopScroll = () => { if (_scrollRAF) { cancelAnimationFrame(_scrollRAF); _scrollRAF = null; } };
		const _autoScroll = (dir) => { scrollEl.scrollLeft += dir * 8; _scrollRAF = requestAnimationFrame(() => _autoScroll(dir)); };
		scrollEl.addEventListener("dragover", e => {
			const rect = scrollEl.getBoundingClientRect();
			const threshold = 80;
			if (e.clientX > rect.right - threshold) { _stopScroll(); _autoScroll(1); }
			else if (e.clientX < rect.left + threshold) { _stopScroll(); _autoScroll(-1); }
			else { _stopScroll(); }
		});
		scrollEl.addEventListener("dragleave", e => { if (!scrollEl.contains(e.relatedTarget)) _stopScroll(); });
		scrollEl.addEventListener("drop", _stopScroll);

		// restore collapsed state
		if (this.all_collapsed) {
			this.$board.find(".tab-col").addClass("tab-col-collapsed");
			this.$board.find(".tab-col-toggle").text("▼");
		}
	}

	_card(task) {
		const priority_class = {
			Urgent: "tab-priority-urgent",
			High: "tab-priority-high",
			Medium: "tab-priority-medium",
			Low: "tab-priority-low",
		}[task.priority] || "";

		const due = task.exp_end_date
			? `<span class="tab-due ${frappe.datetime.get_diff(task.exp_end_date) < 0 ? "tab-overdue" : ""}">
				${frappe.datetime.str_to_user(task.exp_end_date)}
			   </span>`
			: "";

		const progress = task.progress || 0;
		const progress_color = progress >= 100 ? "#38a169" : progress >= 50 ? "#d69e2e" : "#4490f1";

		// assignee avatars on card (all assignees)
		const assigneeAvatar = task.assignees && task.assignees.length
			? task.assignees.map(uid => this._mini_avatar(uid)).join("")
			: "";

		// status dropdown
		const statusOptions = TASK_STATUSES.map(s =>
			`<option value="${s}" ${s === task.status ? "selected" : ""}>${s}</option>`
		).join("");

		const $card = $(`
			<div class="tab-card ${priority_class}" draggable="true" data-task="${frappe.utils.escape_html(task.name)}">
				<div class="tab-card-top">
					<div class="tab-card-subject">${frappe.utils.escape_html(task.subject)}</div>
					${assigneeAvatar ? `<div class="tab-card-assignee">${assigneeAvatar}</div>` : ""}
				</div>
				<div class="tab-card-meta">
					<select class="tab-status-select tab-status-${(task.status || "").toLowerCase().replace(/ /g, "-")}">
						${statusOptions}
					</select>
					${due}
				</div>
				<div class="tab-progress-bar">
					<div class="tab-progress-fill" style="width:${progress}%;background:${progress_color};"></div>
				</div>
				<div class="tab-card-footer">
					${task.project ? `<span class="tab-card-project">${frappe.utils.escape_html(task.project)}</span>` : ""}
					<span class="tab-card-progress-text">${progress}%</span>
				</div>
			</div>
		`);

		// status change
		$card.find(".tab-status-select").on("change", e => {
			e.stopPropagation();
			const newStatus = $(e.target).val();
			frappe.call({
				method: "erpnext.projects.page.task_assignment_board.task_assignment_board.update_task_status",
				args: { task_name: task.name, status: newStatus },
				callback: r => {
					if (r.message && r.message.success) {
						frappe.show_alert({ message: __("Status updated"), indicator: "green" });
						// update local state
						task.status = newStatus;
						$(e.target).attr("class", `tab-status-select tab-status-${newStatus.toLowerCase().replace(/ /g, "-")}`);
					}
				},
				error: () => {
					// server rejected the change (validation/permission) — revert the select
					$(e.target).val(task.status);
				},
			});
		});

		$card[0].addEventListener("dragstart", e => {
			e.dataTransfer.setData("text/plain", task.name);
			$card.addClass("tab-dragging");
		});
		$card[0].addEventListener("dragend", () => $card.removeClass("tab-dragging"));
		$card.on("click", e => {
			if ($(e.target).hasClass("tab-status-select")) return;
			frappe.set_route("Form", "Task", task.name);
		});

		return $card;
	}

	_confirm_reassign(taskName, newUser) {
		const task = this._task_map[taskName];
		if (!task) return;
		const taskSubject = frappe.utils.escape_html(task.subject || taskName);
		const displayName = frappe.utils.escape_html(
			newUser.name === "__unassigned__" ? __("Unassigned") : newUser.full_name
		);

		frappe.confirm(
			__(`Reassign <b>"${taskSubject}"</b> to <b>${displayName}</b>?`),
			() => {
				frappe.call({
					method: "erpnext.projects.page.task_assignment_board.task_assignment_board.reassign_task",
					args: { task_name: taskName, new_user: newUser.name },
					callback: r => {
						if (r.message && r.message.success) {
							frappe.show_alert({ message: __("Task reassigned"), indicator: "green" });
							this.refresh();
						}
					},
				});
			}
		);
	}

	_clear_filters() {
		this._project_field.set_value("");
		this._sprint_field.set_value("");
		this._department_field.set_value("");
		this._status_field.set_value("");
		this.project = null;
		this.sprint = null;
		this.department = null;
		this.status = null;
		this.refresh();
	}

	_toggle_collapse() {
		this.all_collapsed = !this.all_collapsed;
		this.$board.find(".tab-col").toggleClass("tab-col-collapsed", this.all_collapsed);
		this.$board.find(".tab-col-toggle").text(this.all_collapsed ? "▼" : "▲");
	}

	_toggle_completed() {
		this.show_completed = !this.show_completed;
		// update menu item label
		const $menuItems = $(".dropdown-menu a:contains('Completed')");
		$menuItems.filter((_, el) => $(el).text().includes("Completed")).text(
			this.show_completed ? __("Hide Completed Tasks") : __("Show Completed Tasks")
		);
		this.refresh();
	}

	_export_csv() {
		if (!this._tasks.length) {
			frappe.show_alert({ message: __("No tasks to export"), indicator: "orange" });
			return;
		}

		const headers = ["Task ID", "Subject", "Project", "Status", "Priority", "Assignee", "Due Date", "Progress %"];
		const rows = this._tasks.map(t => {
			const assigneeName = t.assignees && t.assignees.length
				? (this._user_map[t.assignees[0]] ? this._user_map[t.assignees[0]].full_name : t.assignees[0])
				: "Unassigned";
			return [
				`"${(t.name || "").replace(/"/g, '""')}"`,
				`"${(t.subject || "").replace(/"/g, '""')}"`,
				`"${(t.project || "").replace(/"/g, '""')}"`,
				t.status || "",
				t.priority || "",
				`"${assigneeName.replace(/"/g, '""')}"`,
				t.exp_end_date ? `"${t.exp_end_date}"` : "",
				t.progress || 0,
			].join(",");
		});

		const csv = [headers.join(","), ...rows].join("\n");
		const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `task_assignment_board_${frappe.datetime.nowdate()}.csv`;
		a.click();
		URL.revokeObjectURL(url);
		frappe.show_alert({ message: __("CSV exported"), indicator: "green" });
	}

	_avatar(user) {
		if (user.name === "__unassigned__") return `<span class="tab-avatar tab-avatar-empty">?</span>`;
		if (user.user_image) return `<img class="tab-avatar" src="${frappe.utils.escape_html(user.user_image)}" alt="">`;
		const initials = (user.full_name || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
		return `<span class="tab-avatar tab-avatar-initials">${initials}</span>`;
	}

	_mini_avatar(userEmail) {
		const user = this._user_map[userEmail];
		if (!user) return "";
		if (user.user_image) return `<img class="tab-mini-avatar" src="${frappe.utils.escape_html(user.user_image)}" title="${frappe.utils.escape_html(user.full_name)}" alt="">`;
		const initials = (user.full_name || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
		return `<span class="tab-mini-avatar tab-avatar-initials" title="${frappe.utils.escape_html(user.full_name)}">${initials}</span>`;
	}

	_inject_css() {
		if (document.getElementById("tab-board-css")) return;
		const style = document.createElement("style");
		style.id = "tab-board-css";
		style.textContent = `
		.tab-board { padding: 16px; height: calc(100vh - 120px); display: flex; flex-direction: column; }
		.tab-loading { padding: 40px; text-align: center; color: var(--text-muted); font-size: 15px; }
		.tab-spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #ccc; border-top-color: var(--primary, #4490f1); border-radius: 50%; animation: tab-spin 0.7s linear infinite; vertical-align: middle; }
		@keyframes tab-spin { to { transform: rotate(360deg); } }
		.tab-scroll { display: flex; gap: 16px; overflow-x: auto; flex: 1; padding-bottom: 12px; }

		.tab-col { min-width: 260px; max-width: 260px; background: var(--bg-color, #f4f5f6); border-radius: 8px; display: flex; flex-direction: column; border: 1px solid var(--border-color); transition: min-width 0.2s; }
		.tab-col-collapsed { min-width: 48px; max-width: 48px; overflow: hidden; }
		.tab-col-collapsed .tab-col-body { display: none; }
		.tab-col-collapsed .tab-col-name, .tab-col-collapsed .tab-col-count { display: none; }

		.tab-col-header { display: flex; align-items: center; gap: 8px; padding: 12px 12px 8px; border-bottom: 1px solid var(--border-color); font-weight: 600; }
		.tab-col-name { flex: 1; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
		.tab-col-count { background: var(--primary); color: #fff; font-size: 11px; flex-shrink: 0; }
		.tab-col-toggle { border: none; background: transparent; cursor: pointer; font-size: 10px; color: var(--text-muted); padding: 0 2px; flex-shrink: 0; }
		.tab-col-toggle:hover { color: var(--text-color); }

		.tab-col-body { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 8px; min-height: 80px; transition: background 0.15s; }
		.tab-col-body.tab-drop-target { background: var(--primary-light, #e8f4fd); outline: 2px dashed var(--primary); outline-offset: -4px; border-radius: 4px; }

		.tab-card { background: #fff; border-radius: 6px; padding: 10px 12px; border: 1px solid var(--border-color); cursor: grab; transition: box-shadow 0.15s, opacity 0.15s; border-left: 3px solid transparent; }
		.tab-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.10); }
		.tab-card.tab-dragging { opacity: 0.4; cursor: grabbing; }
		.tab-priority-urgent { border-left-color: #e53e3e; }
		.tab-priority-high { border-left-color: #dd6b20; }
		.tab-priority-medium { border-left-color: #d69e2e; }
		.tab-priority-low { border-left-color: #38a169; }

		.tab-card-top { display: flex; align-items: flex-start; gap: 6px; margin-bottom: 6px; }
		.tab-card-subject { font-size: 13px; font-weight: 500; flex: 1; }
		.tab-card-assignee { flex-shrink: 0; }

		.tab-card-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
		.tab-card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
		.tab-card-project { font-size: 11px; color: var(--text-muted); }
		.tab-card-progress-text { font-size: 11px; color: var(--text-muted); }

		.tab-progress-bar { width: 100%; height: 4px; background: #e2e8f0; border-radius: 2px; margin: 4px 0; overflow: hidden; }
		.tab-progress-fill { height: 100%; border-radius: 2px; transition: width 0.3s; }

		.tab-status-select { font-size: 10px; padding: 2px 4px; border-radius: 10px; border: 1px solid var(--border-color); background: var(--gray-100); color: var(--text-muted); cursor: pointer; max-width: 130px; }
		.tab-status-select.tab-status-working { background: #bee3f8; color: #2b6cb0; border-color: #bee3f8; }
		.tab-status-select.tab-status-open { background: #e2e8f0; color: #4a5568; border-color: #e2e8f0; }
		.tab-status-select.tab-status-pending-review { background: #fef3c7; color: #92400e; border-color: #fef3c7; }
		.tab-status-select.tab-status-overdue { background: #fed7d7; color: #c53030; border-color: #fed7d7; }
		.tab-status-select.tab-status-completed { background: #c6f6d5; color: #276749; border-color: #c6f6d5; }

		.tab-due { font-size: 11px; color: var(--text-muted); }
		.tab-overdue { color: #e53e3e; font-weight: 600; }

		.tab-avatar { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
		.tab-avatar-empty, .tab-avatar-initials { display: inline-flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; background: var(--gray-300); color: var(--gray-700); }
		.tab-mini-avatar { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; font-size: 8px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; background: var(--primary-light); color: var(--primary); }
		`;
		document.head.appendChild(style);
	}
}
