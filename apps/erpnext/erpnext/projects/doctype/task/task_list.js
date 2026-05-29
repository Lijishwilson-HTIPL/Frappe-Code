frappe.listview_settings["Task"] = {
	hide_name_column: true,
	add_fields: [
		"project", "status", "priority", "subject",
		"exp_end_date", "progress", "_assign", "owner",
	],
	filters: [["status", "=", "Open"]],

	onload: function (listview) {
		// Hide Frappe's default "Add Task" button — the quick-bar handles creation
		listview.page.set_primary_action = function () {};
		setTimeout(() => listview.page.btn_primary && listview.page.btn_primary.hide(), 100);

		// ── Jira CSS ───────────────────────────────────────────────────
		{
			let s = document.getElementById("jira-task-list-css");
			if (!s) { s = document.createElement("style"); s.id = "jira-task-list-css"; document.head.appendChild(s); }
			s.textContent = `
				[data-doctype="Task"] .layout-main-section { background:#fff !important; }

				/* push sidebar down so it starts below the page title, eliminating the overlap */
				[data-doctype="Task"] .layout-side-section { padding-top: 52px !important; }

				[data-doctype="Task"] .list-row-head {
					background:#f4f5f7 !important;
					border-top:2px solid #dfe1e6 !important;
					border-bottom:2px solid #dfe1e6 !important;
				}
				[data-doctype="Task"] .list-row-head .list-col,
				[data-doctype="Task"] .list-row-head span {
					font-size:11px !important; font-weight:700 !important;
					color:#5e6c84 !important; text-transform:uppercase !important;
					letter-spacing:0.06em !important;
				}
				[data-doctype="Task"] .list-row {
					border-left:3px solid transparent !important;
					border-bottom:1px solid #ebecf0 !important;
					background:#fff !important;
					transition:background 0.1s,border-left-color 0.1s !important;
				}
				[data-doctype="Task"] .list-row:hover {
					background:#f4f5f7 !important;
					border-left-color:#0052cc !important;
				}
				[data-doctype="Task"] .list-row .list-col,
				[data-doctype="Task"] .list-row-head .list-col {
					padding:9px 14px !important; vertical-align:middle !important;
				}
				[data-doctype="Task"] .list-row .level-item.bold a,
				[data-doctype="Task"] .list-row .list-subject a {
					font-size:14px !important; font-weight:500 !important; color:#172b4d !important;
				}
				[data-doctype="Task"] .list-row .level-item.bold a:hover,
				[data-doctype="Task"] .list-row .list-subject a:hover {
					color:#0052cc !important; text-decoration:underline !important;
				}
				[data-doctype="Task"] .list-row .indicator-pill { display:none !important; }

				/* neaten column headings — no overflow truncation */
				[data-doctype="Task"] .list-row-head .list-col span {
					white-space:nowrap !important;
					overflow:visible !important;
					text-overflow:unset !important;
				}

				/* ── Prevent native column overflow ── */
				[data-doctype="Task"] .list-row-col {
					white-space:nowrap !important;
					overflow:hidden !important;
					text-overflow:ellipsis !important;
				}

				/* ── Quick-create bar ── */
				.jira-quick-bar {
					display:flex; align-items:center; gap:8px;
					padding:10px 14px; border-bottom:2px solid #0052cc;
					background:#fff; flex-wrap:wrap;
				}
				.jira-quick-bar input[type="text"],
				.jira-quick-bar input[type="date"],
				.jira-quick-bar select {
					height:32px; border:1px solid #dfe1e6; border-radius:3px;
					padding:0 10px; font-size:13px; color:#172b4d;
					outline:none; background:#fff;
					transition:border-color 0.15s, box-shadow 0.15s;
				}
				.jira-quick-bar input[type="text"] { flex:1; min-width:200px; }
				.jira-quick-bar input[type="text"]::placeholder { color:#97a0af; }
				.jira-quick-bar input[type="text"]:focus,
				.jira-quick-bar input[type="date"]:focus,
				.jira-quick-bar select:focus { border-color:#4c9aff; box-shadow:0 0 0 2px #deebff; }
				.jira-quick-bar select { min-width:110px; cursor:pointer; }
				.jira-quick-bar input[type="date"] { min-width:140px; }

				/* required field highlight */
				.jira-field-required { border-color:#DE350B !important; box-shadow:0 0 0 2px #ffebe6 !important; }
				.jira-field-required::placeholder { color:#DE350B !important; }

				.jira-quick-add-btn {
					height:32px; padding:0 16px; background:#0052cc; color:#fff;
					border:none; border-radius:3px; font-size:13px; font-weight:600;
					cursor:pointer; white-space:nowrap;
					transition:background 0.15s;
				}
				.jira-quick-add-btn:hover { background:#0065ff; }
				.jira-quick-add-btn:disabled { background:#b3bac5; cursor:default; }

				/* project link in list rows */
				.jira-project-link {
					color:#0052cc; font-weight:500; cursor:pointer;
					text-decoration:none; background:none; border:none; padding:0;
				}
				.jira-project-link:hover { text-decoration:underline; color:#003d99; }

				/* assignment columns — fixed width keeps header & row aligned */
				.jira-assign-col {
					width:120px !important; min-width:120px !important; max-width:120px !important;
					flex-shrink:0 !important; box-sizing:border-box !important;
					display:flex !important; align-items:center !important;
					padding:0 10px !important; overflow:hidden !important;
				}


				/* remove level-right from both rows — eliminates "of 1 ♡" clutter and
				   guarantees ASSIGNER / ASSIGNED TO are perfectly aligned */
				[data-doctype="Task"] .list-row .level-right,
				[data-doctype="Task"] .list-row-head .level-right { display:none !important; }

				/* filter chips */
				.jira-filter-chip {
					display:inline-block; padding:3px 12px;
					border:1px solid #dfe1e6; border-radius:14px;
					font-size:12px; font-weight:500; color:#42526e;
					cursor:pointer; margin-left:6px; background:#fff;
					transition:background 0.15s,border-color 0.15s;
				}
				.jira-filter-chip:hover { background:#ebecf0; border-color:#b3bac5; }
				.jira-filter-chip.active { background:#deebff; border-color:#4c9aff; color:#0052cc; }
			`;
		}

		// ── Build project autocomplete list ───────────────────────────
		const $datalist = $(`<datalist id="jira-project-list"></datalist>`);
		const projectMap = {}; // lowercase display label → document name (ID)
		frappe._task_project_id_to_name = {}; // ID → display label (used by formatter)
		$("body").append($datalist);

		frappe.call({
			method: "frappe.client.get_list",
			args: { doctype: "Project", fields: ["name", "project_name"], limit_page_length: 500 },
			callback: function (r) {
				if (!r.message) return;
				r.message.forEach(p => {
					const label = p.project_name || p.name;
					// store with lowercase key for case-insensitive lookup
					projectMap[label.toLowerCase()] = p.name;
					frappe._task_project_id_to_name[p.name] = label;
					$datalist.append(`<option value="${frappe.utils.escape_html(label)}">`);
				});
			},
		});

		// ── Quick-create bar HTML ─────────────────────────────────────
		const $bar = $(`
			<div class="jira-quick-bar" id="jira-quick-bar">
				<input type="text" id="jira-task-subject"  placeholder="+ What needs to be done?" />
				<select id="jira-task-assignee">
					<option value="">👤 Assign To *</option>
				</select>
				<select id="jira-task-priority">
					<option value="">⚡ Priority</option>
					<option value="Low">↓ Low</option>
					<option value="Medium">▬ Medium</option>
					<option value="High">↑ High</option>
					<option value="Urgent">⚡ Urgent</option>
				</select>
				<input type="date" id="jira-task-due" title="Expected End Date" />
				<button class="jira-quick-add-btn" id="jira-add-btn">+ Add Task</button>
			</div>
		`);

		$(listview.page.main).find(".list-row-container, .frappe-list").first().before($bar);

		// Get the project ID that is currently active as a filter (URL param OR listview filter area)
		function get_active_project_id() {
			// 1. URL query param (?project=PROJ-0003)
			const fromUrl = new URLSearchParams(window.location.search).get("project");
			if (fromUrl) return fromUrl;

			// 2. Frappe listview filter area (set via route_options or filter chip)
			try {
				const args = listview.get_filters_for_args ? listview.get_filters_for_args() : [];
				for (const f of args) {
					// f = [doctype, fieldname, operator, value]
					if (Array.isArray(f) && f[1] === "project" && (f[2] === "=" || f[2] === "equals")) {
						return f[3];
					}
				}
			} catch (_) {}

			// 3. Fallback: scan filter_area directly
			try {
				if (listview.filter_area && listview.filter_area.filters) {
					const pf = listview.filter_area.filters.find(fi => fi.fieldname === "project");
					if (pf) {
						const val = pf.get_value ? pf.get_value() : null;
						if (val && val[3]) return val[3];
					}
				}
			} catch (_) {}

			return null;
		}

		// Populate assignee dropdown
		frappe.call({
			method: "frappe.client.get_list",
			args: { doctype: "User", filters: { enabled: 1, user_type: "System User" }, fields: ["name", "full_name"], limit_page_length: 100 },
			callback: function (r) {
				if (!r.message) return;
				r.message.forEach(u => {
					$("#jira-task-assignee").append(`<option value="${u.name}">${u.full_name || u.name}</option>`);
				});
			},
		});

		// ── Submit handler ────────────────────────────────────────────
		function create_task() {
			const subject  = $("#jira-task-subject").val().trim();
			const projectId = get_active_project_id();
			const assignee  = $("#jira-task-assignee").val();
			const priority  = $("#jira-task-priority").val();
			const due_date  = $("#jira-task-due").val();

			// Validate required fields
			let valid = true;
			if (!subject) {
				$("#jira-task-subject").addClass("jira-field-required").attr("placeholder", "Title is required *");
				valid = false;
			} else {
				$("#jira-task-subject").removeClass("jira-field-required").attr("placeholder", "+ What needs to be done?");
			}
			if (!projectId) {
				frappe.show_alert({ message: __("Please open a project and view its tasks before adding a task"), indicator: "red" }, 4);
				valid = false;
			}
			if (!assignee) {
				$("#jira-task-assignee").addClass("jira-field-required");
				frappe.show_alert({ message: __("Please select who to assign this task to"), indicator: "red" }, 3);
				valid = false;
			} else {
				$("#jira-task-assignee").removeClass("jira-field-required");
			}
			if (!priority) {
				$("#jira-task-priority").addClass("jira-field-required");
				valid = false;
			} else {
				$("#jira-task-priority").removeClass("jira-field-required");
			}
			if (!due_date) {
				$("#jira-task-due").addClass("jira-field-required");
				valid = false;
			} else {
				$("#jira-task-due").removeClass("jira-field-required");
			}
			if (!valid) {
				if (subject && projectId) {
					frappe.show_alert({ message: __("Please fill all required fields"), indicator: "red" }, 3);
				}
				return;
			}

			const $btn = $("#jira-add-btn").prop("disabled", true).text("Adding…");
			const projectLabel = (frappe._task_project_id_to_name || {})[projectId] || projectId;
			const doc = { doctype: "Task", subject, project: projectId, status: "Open" };
			if (priority) doc.priority = priority;
			if (due_date) doc.exp_end_date = due_date;

			frappe.call({
				method: "frappe.client.insert",
				args: { doc },
				callback: function (res) {
					if (res.message) {
						if (assignee) {
							const emailBody = [
								__("Task: {0}", [subject]),
								__("Project: {0}", [projectLabel]),
								priority ? __("Priority: {0}", [priority]) : "",
								due_date ? __("Due Date: {0}", [due_date]) : "",
								__("Please log in to view and update the task."),
							].filter(Boolean).join("\n");

							frappe.call({
								method: "frappe.desk.form.assign_to.add",
								args: {
									doctype: "Task",
									name: res.message.name,
									assign_to: [assignee],
									notify: 1,
									description: emailBody,
								},
							});
						}
						frappe.show_alert({ message: __("Task <b>{0}</b> created", [subject]), indicator: "green" }, 3);
						$("#jira-task-subject").val("").attr("placeholder", "+ What needs to be done?");
						$("#jira-task-assignee,#jira-task-priority").val("");
						$("#jira-task-due").val("");
						listview.refresh();
					}
					$btn.prop("disabled", false).text("+ Add Task");
				},
			});
		}

		$("#jira-add-btn").on("click", create_task);
		$("#jira-task-subject").on("keydown", function (e) {
			if (e.key === "Enter") create_task();
		});

		// ── Project link: click to filter list by project ─────────────
		$(document).on("click", ".jira-project-link", function (e) {
			e.preventDefault();
			const project = $(this).data("project");
			// clear existing project filter then add new one
			listview.filter_area.add([[listview.doctype, "project", "=", project]]);
			listview.refresh();
			// show a "Showing tasks for: X" indicator
			frappe.show_alert({ message: __("Showing tasks for project <b>{0}</b>", [project]), indicator: "blue" }, 3);
		});

		// ── Filter chips ──────────────────────────────────────────────
		const $chips = $(`<span style="margin-left:12px;"></span>`);
		const $mine  = $(`<button class="jira-filter-chip">👤 Assigned to me</button>`);
		const $dueW  = $(`<button class="jira-filter-chip">📅 Due this week</button>`);

		$mine.on("click", function () {
			$(this).toggleClass("active");
			if ($(this).hasClass("active")) {
				listview.filter_area.add([[listview.doctype, "_assign", "like", "%" + frappe.session.user + "%"]]);
			} else {
				listview.filter_area.remove_filter(listview.doctype, "_assign");
			}
			listview.refresh();
		});

		$dueW.on("click", function () {
			$(this).toggleClass("active");
			const today = frappe.datetime.get_today();
			const end   = frappe.datetime.add_days(today, 7);
			if ($(this).hasClass("active")) {
				listview.filter_area.add([
					[listview.doctype, "exp_end_date", ">=", today],
					[listview.doctype, "exp_end_date", "<=", end],
				]);
			} else {
				listview.filter_area.remove_filter(listview.doctype, "exp_end_date");
			}
			listview.refresh();
		});

		$chips.append($mine).append($dueW);
		$(listview.page.body).find(".page-head .page-title").after($chips);

		// ── Assigner / Assigned To columns ───────────────────────────
		function inject_assignment_cols() {
			if (!listview.data || !listview.data.length) return;
			const $result = listview.$result;
			if (!$result || !$result.length) return;

			// Hide level-right in header and all data rows via inline important (beats Frappe flex CSS)
			$result.find('.list-row-head .level-right, .list-row .level-right').each(function () {
				this.style.setProperty('display', 'none', 'important');
			});

			// Header — insert before .level-right so cols are flex siblings (not clipped by .level-left.ellipsis)
			const $head = $result.find('.list-row-head');
			if ($head.length && !$head.find('.jira-assign-col').length) {
				$head.find('.level-right').first().before(
					'<div class="jira-assign-col">' +
					'<span style="font-size:11px;font-weight:700;color:#5e6c84;text-transform:uppercase;letter-spacing:.06em;">Assigner</span></div>' +
					'<div class="jira-assign-col">' +
					'<span style="font-size:11px;font-weight:700;color:#5e6c84;text-transform:uppercase;letter-spacing:.06em;">Assigned To</span></div>'
				);
			}

			// Data rows — inject as flex siblings (before .level-right) to avoid overflow:hidden on .level-left.ellipsis
			$result.find('.list-row-container').each(function () {
				const $container = $(this);

				// Remove Frappe's native _assign avatar (bypasses Bootstrap d-flex !important)
				$container.find('.list-row-activity > div').first().remove();

				if ($container.find('.jira-assign-col').length) return;

				// data-name lives on .list-row-checkbox, not on .list-row
				const rowName = $container.find('.list-row-checkbox').data('name');
				const task = rowName ? (listview.data || []).find(d => d.name === rowName) : null;
				if (!task) return;

				// Assigner — task owner
				let assigner = "—";
				if (task.owner) {
					const info = frappe.user_info(task.owner);
					assigner = (info && info.fullname) ? info.fullname : task.owner.split("@")[0];
				}

				// Assigned To — _assign JSON array
				let assignedTo = "—";
				if (task._assign && task._assign !== "[]" && task._assign !== "null") {
					try {
						const users = JSON.parse(task._assign);
						if (users && users.length) {
							assignedTo = users.map(function (u) {
								const info = frappe.user_info(u);
								return (info && info.fullname) ? info.fullname : u.split("@")[0];
							}).join(", ");
						}
					} catch (_) { /* show — */ }
				}

				function safe(v) {
					return String(v || "—").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
				}

				$container.find('.level-right').first().before(
					'<div class="jira-assign-col"><span style="font-size:12px;color:#172b4d;">' + safe(assigner)   + '</span></div>' +
					'<div class="jira-assign-col"><span style="font-size:12px;color:#172b4d;">' + safe(assignedTo) + '</span></div>'
				);
			});
		}

		// Fire inject immediately on every list re-render using MutationObserver.
		// This replaces the old 400ms poll, which left a window where Frappe could
		// re-render after our inject and undo all changes before the next poll fired.
		setTimeout(inject_assignment_cols, 150);
		if (listview.$result && listview.$result[0]) {
			new MutationObserver(frappe.utils.debounce(inject_assignment_cols, 80))
				.observe(listview.$result[0], { childList: true });
		}

		// Bulk status actions
		const method = "erpnext.projects.doctype.task.task.set_multiple_status";
		listview.page.add_menu_item(__("Set as Open"),      () => listview.call_for_selected_items(method, { status: "Open" }));
		listview.page.add_menu_item(__("Set as Completed"), () => listview.call_for_selected_items(method, { status: "Completed" }));

		// Reassign action
		listview.page.add_menu_item(__("Reassign Task"), function () {
			const selected = listview.get_checked_items();
			if (!selected.length) {
				frappe.show_alert({ message: __("Select at least one task first"), indicator: "orange" }, 3);
				return;
			}
			const d = new frappe.ui.Dialog({
				title: __("Reassign {0} Task(s)", [selected.length]),
				fields: [
					{
						fieldtype: "Link",
						fieldname: "assignee",
						label: __("Assign To (Employee)"),
						options: "Employee",
						reqd: 1,
					},
					{
						fieldtype: "Small Text",
						fieldname: "note",
						label: __("Note (sent in email)"),
					},
				],
				primary_action_label: __("Reassign"),
				primary_action(values) {
					const calls = selected.map(task =>
						frappe.call({
							method: "erpnext.projects.doctype.task.task.reassign_task",
							args: {
								name: task.name,
								employee: values.assignee,
								note: values.note || "",
							},
						})
					);
					Promise.all(calls).then(() => {
						frappe.show_alert({ message: __("Reassigned successfully"), indicator: "green" }, 3);
						listview.refresh();
					});
					d.hide();
				},
			});
			d.show();
		});
	},

	get_indicator: function (doc) {
		const colors = {
			Open: "blue", Working: "orange", "Pending Review": "orange",
			Overdue: "red", Completed: "green", Cancelled: "grey", Template: "blue",
		};
		return [__(doc.status), colors[doc.status] || "grey", "status,=," + doc.status];
	},

	formatters: {
		// Clickable project name — filters the list
		project: function (value) {
			if (!value) return "";
			const display = (frappe._task_project_id_to_name || {})[value] || value;
			return `<button class="jira-project-link" data-project="${frappe.utils.escape_html(value)}">${frappe.utils.escape_html(display)}</button>`;
		},

		status: function (value) {
			if (!value) return "";
			const cfg = {
				Open:             { bg: "#dfe1e6", color: "#42526e" },
				Working:          { bg: "#0052CC", color: "#fff"    },
				"Pending Review": { bg: "#ff991f", color: "#fff"    },
				Overdue:          { bg: "#DE350B", color: "#fff"    },
				Completed:        { bg: "#00875A", color: "#fff"    },
				Cancelled:        { bg: "#97a0af", color: "#fff"    },
				Template:         { bg: "#6554c0", color: "#fff"    },
			};
			const c = cfg[value] || { bg: "#dfe1e6", color: "#42526e" };
			return `<span style="background:${c.bg};color:${c.color};padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700;display:inline-block;white-space:nowrap;letter-spacing:0.04em;">${__(value).toUpperCase()}</span>`;
		},

		priority: function (value) {
			if (!value) return "";
			const p = {
				Urgent: { color: "#DE350B", icon: `<svg viewBox="0 0 16 16" width="13" height="13" fill="#DE350B"><path d="M8 2 1 13h14z"/></svg>` },
				High:   { color: "#CD5A1B", icon: `<svg viewBox="0 0 16 16" width="13" height="13" fill="#CD5A1B"><path d="M8 3 2 11h12z"/></svg>` },
				Medium: { color: "#0065FF", icon: `<svg viewBox="0 0 16 16" width="13" height="13" fill="#0065FF"><rect x="2" y="5" width="12" height="2"/><rect x="2" y="9" width="12" height="2"/></svg>` },
				Low:    { color: "#2D8738", icon: `<svg viewBox="0 0 16 16" width="13" height="13" fill="#2D8738"><path d="M8 13 2 5h12z"/></svg>` },
			};
			const s = p[value] || { color: "#6b7280", icon: "•" };
			return `<span style="display:inline-flex;align-items:center;gap:4px;color:${s.color};font-weight:600;font-size:13px;">${s.icon}${__(value)}</span>`;
		},

		exp_end_date: function (value) {
			if (!value) return "";
			const today   = frappe.datetime.get_today();
			const overdue = value < today;
			return `<span style="color:${overdue ? "#DE350B" : "#42526E"};font-weight:${overdue ? 600 : 400};">${overdue ? "⚠ " : ""}${frappe.datetime.str_to_user(value)}</span>`;
		},
	},

	gantt_custom_popup_html: function (ganttobj, task) {
		let html = `<a class="text-white mb-2 inline-block cursor-pointer" href="/app/task/${ganttobj.id}">${ganttobj.name}</a>`;
		if (task.project) html += `<p class="mb-1">${__("Project")}: <a class="text-white" href="/app/project/${task.project}">${task.project}</a></p>`;
		html += `<p class="mb-1">${__("Progress")}: <span class="text-white">${ganttobj.progress}%</span></p>`;
		if (task._assign) {
			const users = JSON.parse(task._assign);
			html += `<span>Assigned to: </span><span class="text-white">${users.map(u => frappe.user_info(u).fullname).join(", ")}</span>`;
		}
		return `<div class="p-3" style="min-width:220px">${html}</div>`;
	},
};
