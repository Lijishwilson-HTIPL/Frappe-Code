frappe.listview_settings["Task"] = {
	hide_name_column: true,
	add_fields: [
		"project", "status", "priority", "subject",
		"exp_end_date", "progress", "_assign", "owner",
		"is_group", "parent_task",
	],
	filters: [["status", "=", "Open"]],

	onload: function (listview) {
		// Hide Frappe's default "Add Task" button — the quick-bar handles creation
		// (re-hidden inside the MutationObserver below on every list re-render)
		setTimeout(() => listview.page.btn_primary && listview.page.btn_primary.hide(), 100);

		// Shortcut button — navigates to Task Assignment Board, carrying active project filter
		listview.page.add_button(__("Assignment Board"), () => {
			const project = get_active_project_id();
			if (project) frappe.route_options = { project: project };
			frappe.set_route("task-assignment-board");
		}, { icon: "arrow-right" });

		// ── Jira CSS ───────────────────────────────────────────────────
		{
			let s = document.getElementById("jira-task-list-css");
			if (!s) { s = document.createElement("style"); s.id = "jira-task-list-css"; document.head.appendChild(s); }
			s.textContent = `
				[data-doctype="Task"] .layout-main-section { background:#fff !important; }

				/* The jira-quick-bar pushes $result down ~52px, so Frappe's dynamic
				   set_result_height() makes the list 52px too short and clips bottom rows.
				   Remove the max-height so .page-wrapper scroll handles everything. */
				[data-doctype="Task"] .frappe-list,
				[data-doctype="Task"] .list-result {
					max-height: none !important;
					height: auto !important;
				}

				/* indent page title to match content area — page-head container has padding:0 */
				[data-doctype="Task"] .page-head .page-title,
				[data-doctype="Task"] .page-head .title-area {
					padding-left: 15px !important;
				}

				/* push sidebar down so it starts below the page title, eliminating the overlap.
				   padding-left: 15px counteracts Bootstrap .row margin-left:-15px that clips
				   sidebar text against overflow-x:hidden on .page-wrapper */
				[data-doctype="Task"] .layout-side-section {
					padding-top: 52px !important;
					padding-left: 15px !important;
				}

				/* fix Bootstrap .row negative margins that push .layout-main left by 15px */
				[data-doctype="Task"] .layout-main.row {
					margin-left: 0 !important;
					margin-right: 0 !important;
				}

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

				/* ── Subject column: wider + wraps on hover ── */
				[data-doctype="Task"] .list-row .list-subject,
				[data-doctype="Task"] .list-row-head .list-subject {
					min-width:260px !important;
					flex:3 !important;
				}
				[data-doctype="Task"] .list-row .level-item.bold {
					white-space:nowrap !important;
					overflow:hidden !important;
					text-overflow:ellipsis !important;
					max-width:420px !important;
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

				/* ── Task type badges — solid colors that survive any theme ── */
				[data-doctype="Task"] .jira-task-badge {
					display:inline-block !important;
					font-size:10px !important; font-weight:700 !important;
					border-radius:3px !important; padding:2px 6px !important;
					letter-spacing:0.05em !important; vertical-align:middle !important;
					flex-shrink:0 !important; margin-left:6px !important;
					line-height:1.4 !important;
				}
				[data-doctype="Task"] .jira-task-badge.jira-badge-parent {
					background:#0052cc !important;
					color:#ffffff !important;
					-webkit-text-fill-color:#ffffff !important;
				}
				[data-doctype="Task"] .jira-task-badge.jira-badge-subtask {
					background:#505f79 !important;
					color:#ffffff !important;
					-webkit-text-fill-color:#ffffff !important;
				}

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

				/* Multi-assignee select */
				.jira-multi-select-wrap { position:relative; display:inline-block; }
				.jira-multi-select-trigger {
					height:32px; border:1px solid #dfe1e6; border-radius:3px;
					padding:0 10px; font-size:13px; color:#97a0af;
					background:#fff; display:flex; align-items:center; gap:6px;
					cursor:pointer; min-width:150px; white-space:nowrap;
					transition:border-color 0.15s, box-shadow 0.15s; user-select:none;
				}
				.jira-multi-select-trigger:hover { border-color:#4c9aff; }
				.jira-multi-select-trigger.has-value { color:#172b4d; }
				.jira-multi-select-arrow { margin-left:auto; font-size:10px; color:#97a0af; }
				.jira-multi-select-menu {
					position:absolute; top:calc(100% + 4px); left:0; z-index:9999;
					background:#fff; border:1px solid #dfe1e6; border-radius:4px;
					box-shadow:0 4px 16px rgba(0,0,0,0.15); min-width:220px; max-width:280px;
				}
				.jira-multi-select-search { padding:8px 8px 4px; border-bottom:1px solid #f0f0f0; }
				.jira-multi-select-search input {
					width:100%; height:28px; border:1px solid #dfe1e6; border-radius:3px;
					padding:0 8px; font-size:12px; outline:none; box-sizing:border-box;
				}
				.jira-multi-select-search input:focus { border-color:#4c9aff; }
				.jira-multi-select-list { max-height:200px; overflow-y:auto; padding:4px 0; }
				.jira-multi-select-item {
					display:flex; align-items:center; gap:8px; padding:6px 12px;
					font-size:13px; color:#172b4d; cursor:pointer; transition:background 0.1s;
				}
				.jira-multi-select-item:hover { background:#f4f5f7; }
				.jira-multi-select-item input[type="checkbox"] { cursor:pointer; }

				/* Assignment board shortcut button */
				[data-doctype="Task"] .page-actions .btn:has(.icon-arrow-right) {
					border-color: #0052cc;
					color: #0052cc;
					font-weight: 600;
				}
				[data-doctype="Task"] .page-actions .btn:has(.icon-arrow-right):hover {
					background: #deebff;
				}
			`;
		}

		// ── Fix sidebar clipping — Bootstrap .row margin-left:-15px pushes .layout-main
		//    left of its container; overflow-x:hidden on .page-wrapper clips the sidebar text.
		//    JS inline style beats all CSS specificity issues.
		setTimeout(() => {
			const sideSec = document.querySelector('.layout-side-section');
			if (sideSec) {
				sideSec.style.setProperty('padding-left', '15px', 'important');
				const layoutMain = sideSec.parentElement;
				if (layoutMain) {
					layoutMain.style.setProperty('margin-left', '0', 'important');
					layoutMain.style.setProperty('margin-right', '0', 'important');
				}
			}
		}, 50);

		// ── Build project autocomplete list ───────────────────────────
		// Remove any datalist left behind by a previous onload to avoid duplicates
		$("#jira-project-list").remove();
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
				<div class="jira-multi-select-wrap" id="jira-assignee-wrap">
					<div class="jira-multi-select-trigger" id="jira-task-assignee">
						<span id="jira-assignee-label">👤 Assign To *</span>
						<span class="jira-multi-select-arrow">▾</span>
					</div>
					<div class="jira-multi-select-menu" id="jira-assignee-menu" style="display:none;">
						<div class="jira-multi-select-search">
							<input type="text" placeholder="🔍 Search members..." id="jira-assignee-search" />
						</div>
						<div class="jira-multi-select-list" id="jira-assignee-list"></div>
					</div>
				</div>
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

			// Frappe sets list result max-height inline via JS: window.innerHeight - $result.offsetTop - 16.
			// The quick-bar pushes $result down, making Frappe clip the bottom rows.
			// Inline jQuery .css() beats CSS !important, so we override the method itself.
			if (typeof listview.set_result_height === "function") {
				const _orig = listview.set_result_height.bind(listview);
				listview.set_result_height = function () {
					_orig();
					const barEl = document.getElementById("jira-quick-bar");
					const barH = barEl ? barEl.offsetHeight : 52;
					const cur = parseInt(listview.$result && listview.$result.css("max-height")) || 0;
					if (cur > 0) listview.$result.css("max-height", (cur + barH) + "px");
				};
			}

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

		// Populate assignee checkbox list
		frappe.call({
			method: "frappe.client.get_list",
			args: { doctype: "User", filters: { enabled: 1, user_type: "System User" }, fields: ["name", "full_name"], limit_page_length: 100 },
			callback: function (r) {
				if (!r.message) return;
				r.message.forEach(u => {
					const label = frappe.utils.escape_html(u.full_name || u.name);
					const val = frappe.utils.escape_html(u.name);
					$("#jira-assignee-list").append(
						`<label class="jira-multi-select-item">
							<input type="checkbox" value="${val}" />
							<span>${label}</span>
						</label>`
					);
				});
			},
		});

		// Toggle dropdown
		$("#jira-task-assignee").on("click", function (e) {
			e.stopPropagation();
			const $menu = $("#jira-assignee-menu");
			const open = $menu.is(":visible");
			$menu.toggle(!open);
			if (!open) { $("#jira-assignee-search").val("").trigger("input").focus(); }
		});

		// Search filter (namespaced + de-duplicated)
		$(document).off("input.jira-assignee-search").on("input.jira-assignee-search", "#jira-assignee-search", function () {
			const q = $(this).val().toLowerCase();
			$("#jira-assignee-list .jira-multi-select-item").each(function () {
				$(this).toggle($(this).text().toLowerCase().includes(q));
			});
		});

		// Update trigger label when selection changes (namespaced + de-duplicated)
		$(document).off("change.jira-assignee-check").on("change.jira-assignee-check", "#jira-assignee-list input[type='checkbox']", function () {
			const checked = $("#jira-assignee-list input:checked");
			const $trigger = $("#jira-task-assignee");
			$trigger.removeClass("jira-field-required");
			if (!checked.length) {
				$("#jira-assignee-label").text("👤 Assign To *");
				$trigger.removeClass("has-value");
			} else if (checked.length === 1) {
				const name = checked.first().closest("label").find("span").text();
				$("#jira-assignee-label").text("👤 " + name);
				$trigger.addClass("has-value");
			} else {
				$("#jira-assignee-label").text("👤 " + checked.length + " members");
				$trigger.addClass("has-value");
			}
		});

		// Close on click outside
		$(document).off("click.jira-assignee").on("click.jira-assignee", function (e) {
			if (!$(e.target).closest("#jira-assignee-wrap").length) {
				$("#jira-assignee-menu").hide();
			}
		});

		// ── Submit handler ────────────────────────────────────────────
		function create_task() {
			const subject  = $("#jira-task-subject").val().trim();
			const projectId = get_active_project_id();
			const assignees = $("#jira-assignee-list input:checked").map((_, el) => el.value).get();
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
			if (!assignees.length) {
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
						if (assignees.length) {
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
									assign_to: assignees,
									notify: 1,
									description: emailBody,
								},
								callback: function () {
									// Sync task_assignees child table now that _assign is written
									frappe.call({
										method: "erpnext.projects.doctype.task.task.sync_task_assignees",
										args: { name: res.message.name },
									});
								},
								error: function () {
									frappe.show_alert({
										message: __("Task created but assignment failed — open the task to assign manually."),
										indicator: "orange",
									}, 5);
								},
							});
						}
						frappe.show_alert({ message: __("Task <b>{0}</b> created", [subject]), indicator: "green" }, 3);
						$("#jira-task-subject").val("").attr("placeholder", "+ What needs to be done?");
						$("#jira-assignee-list input[type='checkbox']").prop("checked", false);
						$("#jira-assignee-label").text("👤 Assign To *");
						$("#jira-task-assignee").removeClass("has-value");
						$("#jira-task-priority").val("");
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

		// ── Project link: click to filter list by project (namespaced + de-duplicated) ──
		$(document).off("click.jira-project-link").on("click.jira-project-link", ".jira-project-link", function (e) {
			e.preventDefault();
			const project = $(this).data("project");
			// clear existing project filter then add new one
			listview.filter_area.add([[listview.doctype, "project", "=", project]]);
			listview.refresh();
			// show a "Showing tasks for: X" indicator
			frappe.show_alert({ message: __("Showing tasks for project <b>{0}</b>", [project]), indicator: "blue" }, 3);
		});

		// ── Filter chips (skip if already injected on this page) ──────
		const $chips = $(`<span class="jira-task-chips" style="margin-left:12px;"></span>`);
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

		if (!$(listview.page.body).find(".jira-task-chips").length) {
			$chips.append($mine).append($dueW);
			$(listview.page.body).find(".page-head .page-title").after($chips);
		}

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

				// ── Subject type badge (parent / subtask) ──────────────────
				const $subjectLink = $container.find('.list-subject a, .level-item.bold a').first();
				if ($subjectLink.length && !$container.find('.jira-task-badge').length) {
					const subjectText = $subjectLink.text().trim();
					$subjectLink.attr("title", subjectText);
					if (task.is_group) {
						$subjectLink.before(
							'<svg viewBox="0 0 16 16" width="13" height="13" fill="#0052cc" style="flex-shrink:0;margin-right:4px;vertical-align:middle;" title="Parent Task">' +
							'<path d="M1 3.5A1.5 1.5 0 0 1 2.5 2h3.764c.415 0 .813.165 1.107.46l.647.646A1.5 1.5 0 0 0 9.125 3.5H13.5A1.5 1.5 0 0 1 15 5v7.5A1.5 1.5 0 0 1 13.5 14h-11A1.5 1.5 0 0 1 1 12.5z"/></svg>'
						);
						$subjectLink.after(
							'<span class="jira-task-badge jira-badge-parent" title="This is a parent task">PARENT</span>'
						);
					} else if (task.parent_task) {
						$subjectLink.before(
							'<span style="color:#97a0af;font-size:14px;margin-right:4px;vertical-align:middle;line-height:1;" title="Subtask of ' + frappe.utils.escape_html(task.parent_task) + '">↳</span>'
						);
						$subjectLink.after(
							'<span class="jira-task-badge jira-badge-subtask" title="Subtask of ' + frappe.utils.escape_html(task.parent_task) + '">SUBTASK</span>'
						);
					}
				}

				// Assigner — task owner
				let assigner = "—";
				if (task.owner) {
					const info = frappe.user_info(task.owner);
					assigner = (info && info.fullname) ? info.fullname : task.owner.split("@")[0];
				}

				// Assigned To — _assign JSON array
				let assignedTo = "—";
				let assignedToTitle = "";
				if (task._assign && task._assign !== "[]" && task._assign !== "null") {
					try {
						const users = JSON.parse(task._assign);
						if (users && users.length) {
							const names = users.map(function (u) {
								const info = frappe.user_info(u);
								return (info && info.fullname) ? info.fullname : u.split("@")[0];
							});
							assignedToTitle = names.join(", ");
							if (names.length === 1) {
								assignedTo = names[0];
							} else {
								assignedTo = names[0] + " +" + (names.length - 1);
							}
						}
					} catch (_) { /* show — */ }
				}

				function safe(v) {
					return String(v || "—").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
				}

				const assignedToHtml = assignedToTitle
					? '<span style="font-size:12px;color:#172b4d;" title="' + safe(assignedToTitle) + '">' + safe(assignedTo) + '</span>'
					: '<span style="font-size:12px;color:#172b4d;">—</span>';

				$container.find('.level-right').first().before(
					'<div class="jira-assign-col"><span style="font-size:12px;color:#172b4d;">' + safe(assigner) + '</span></div>' +
					'<div class="jira-assign-col">' + assignedToHtml + '</div>'
				);
			});
		}

		// ── Group subtasks under their parent tasks ──────────────────────
		function reorder_subtasks_under_parents() {
			if (!listview.data || !listview.data.length) return;
			const $result = listview.$result;
			if (!$result || !$result.length) return;

			const $containers = $result.find('.list-row-container');
			if ($containers.length < 2) return;

			// rowName → $container
			const rowMap = {};
			$containers.each(function () {
				const n = $(this).find('.list-row-checkbox').data('name');
				if (n) rowMap[n] = $(this);
			});

			// rowName → task data
			const taskMap = {};
			(listview.data || []).forEach(function (d) { taskMap[d.name] = d; });

			const ordered = [];
			const placed = new Set();

			// First pass: top-level tasks (no parent_task) followed by their subtasks
			$containers.each(function () {
				const n = $(this).find('.list-row-checkbox').data('name');
				if (!n || placed.has(n)) return;
				const task = taskMap[n];
				if (!task || task.parent_task) return; // skip subtasks in this pass

				placed.add(n);
				ordered.push(rowMap[n]);

				// Immediately append any subtasks of this task
				$containers.each(function () {
					const sn = $(this).find('.list-row-checkbox').data('name');
					if (!sn || placed.has(sn)) return;
					const sub = taskMap[sn];
					if (sub && sub.parent_task === n) {
						placed.add(sn);
						ordered.push(rowMap[sn]);
					}
				});
			});

			// Second pass: orphan subtasks whose parent is not in the current list
			$containers.each(function () {
				const n = $(this).find('.list-row-checkbox').data('name');
				if (!n || placed.has(n)) return;
				ordered.push(rowMap[n]);
			});

			// Re-insert all rows in the new order (append moves existing elements — no clone needed).
			// Disconnect observer first — appending direct children of listview.$result triggers
			// childList mutations, which would re-fire the observer and create an infinite loop.
			const $listBody = $containers.first().parent();
			if (listview.__jira_observer) listview.__jira_observer.disconnect();
			ordered.forEach(function ($el) { $listBody.append($el); });
			// Spacer so the last row has breathing room and is fully clickable
			$listBody.find('.jira-bottom-spacer').remove();
			$listBody.append('<div class="jira-bottom-spacer" style="height:60px;"></div>');
			if (listview.__jira_observer && listview.$result && listview.$result[0]) {
				listview.__jira_observer.observe(listview.$result[0], { childList: true });
			}
		}

		// Fire inject immediately on every list re-render using MutationObserver.
		// This replaces the old 400ms poll, which left a window where Frappe could
		// re-render after our inject and undo all changes before the next poll fired.
		setTimeout(() => { inject_assignment_cols(); reorder_subtasks_under_parents(); inject_col_resizer(); }, 150);
		if (!listview.__jira_observer && listview.$result && listview.$result[0]) {
			listview.__jira_observer = new MutationObserver(frappe.utils.debounce(() => {
				inject_assignment_cols();
				reorder_subtasks_under_parents();
				inject_col_resizer();
				// re-hide the default primary button after every list re-render
				listview.page.btn_primary && listview.page.btn_primary.hide();
			}, 80));
			listview.__jira_observer.observe(listview.$result[0], { childList: true });
		}

		// ── Subject column drag-to-resize ────────────────────────────────
		const COL_W_KEY = "jira_task_subject_col_width";

		function apply_subject_width(px) {
			if (!listview.$result) return;
			// .list-subject class is on BOTH header and data-row subject cells
			listview.$result.find(".list-subject").each(function () {
				this.style.setProperty("min-width", px + "px", "important");
				this.style.setProperty("max-width", px + "px", "important");
				this.style.setProperty("flex", "none", "important");
			});
			let s = document.getElementById("jira-subject-col-style");
			if (!s) { s = document.createElement("style"); s.id = "jira-subject-col-style"; document.head.appendChild(s); }
			s.textContent = `[data-doctype="Task"] .list-subject{min-width:${px}px!important;max-width:${px}px!important;flex:none!important;}`;
		}

		function inject_col_resizer() {
			if (!listview.$result || !listview.$result.length) return;
			const $head = listview.$result.find(".list-row-head");
			if (!$head.length) return;

			// The header subject cell carries the same .list-subject class as data rows
			const col = $head.find(".list-subject")[0];
			if (!col || col.__jira_resizer) return;
			col.__jira_resizer = true;

			// Hover near the right edge → blue border + col-resize cursor (16px hot zone)
			col.addEventListener("mousemove", function (e) {
				const near = e.clientX > col.getBoundingClientRect().right - 16;
				col.style.cursor = near ? "col-resize" : "";
				col.style.borderRight = near ? "2px solid #4c9aff" : "";
			});
			col.addEventListener("mouseleave", () => {
				col.style.cursor = "";
				col.style.borderRight = "";
			});

			// Mousedown near right edge → start drag via full-screen overlay
			col.addEventListener("mousedown", function (e) {
				if (e.clientX < col.getBoundingClientRect().right - 16) return;
				e.preventDefault();
				e.stopPropagation();
				col.style.borderRight = "2px solid #0052cc";
				const startX = e.clientX;
				const startW = col.getBoundingClientRect().width;
				const overlay = document.createElement("div");
				overlay.style.cssText = "position:fixed;inset:0;z-index:99999;cursor:col-resize;";
				document.body.appendChild(overlay);
				overlay.addEventListener("mousemove", ev => apply_subject_width(Math.max(120, startW + ev.clientX - startX)));
				overlay.addEventListener("mouseup", ev => {
					const w = Math.max(120, startW + ev.clientX - startX);
					apply_subject_width(w);
					localStorage.setItem(COL_W_KEY, w);
					document.body.removeChild(overlay);
					col.style.borderRight = "";
					col.style.cursor = "";
				});
			});

			const saved = localStorage.getItem(COL_W_KEY);
			if (saved) apply_subject_width(parseInt(saved, 10));
		}

		// Bulk status actions
		const method = "erpnext.projects.doctype.task.task.set_multiple_status";
		listview.page.add_menu_item(__("Set as Open"),      () => listview.call_for_selected_items(method, { status: "Open" }));
		listview.page.add_menu_item(__("Set as Completed"), () => listview.call_for_selected_items(method, { status: "Completed" }));

		// Bulk field edit — priority + due date
		listview.page.add_menu_item(__("Edit Selected Fields"), function () {
			const selected = listview.get_checked_items();
			if (!selected.length) {
				frappe.show_alert({ message: __("Select at least one task first"), indicator: "orange" }, 3);
				return;
			}
			const d = new frappe.ui.Dialog({
				title: __("Edit {0} Task(s)", [selected.length]),
				fields: [
					{
						fieldtype: "Select",
						fieldname: "priority",
						label: __("Priority"),
						options: "\nLow\nMedium\nHigh\nUrgent",
						description: __("Leave blank to keep existing priority"),
					},
					{
						fieldtype: "Date",
						fieldname: "due_date",
						label: __("Due Date"),
						description: __("Leave blank to keep existing due date"),
					},
				],
				primary_action_label: __("Apply"),
				primary_action(values) {
					if (!values.priority && !values.due_date) {
						frappe.show_alert({ message: __("Select at least one field to update"), indicator: "orange" }, 3);
						return;
					}
					frappe.call({
						method: "erpnext.projects.doctype.task.task.set_multiple_fields",
						args: {
							names: JSON.stringify(selected.map(t => t.name)),
							priority: values.priority || null,
							due_date: values.due_date || null,
						},
						callback() {
							frappe.show_alert({ message: __("Updated {0} task(s)", [selected.length]), indicator: "green" }, 3);
							listview.refresh();
						},
					});
					d.hide();
				},
			});
			d.show();
		});

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
						label: __("Assign To (User)"),
						options: "User",
						reqd: 1,
						get_query: () => ({ filters: { enabled: 1, user_type: "System User" } }),
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
								user: values.assignee,
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
			try {
				const users = JSON.parse(task._assign);
				if (Array.isArray(users) && users.length) {
					html += `<br><small>Assigned: ${users.map(u => (frappe.user_info(u) || {}).fullname || u).join(", ")}</small>`;
				}
			} catch(e) {}
		}
		return `<div class="p-3" style="min-width:220px">${html}</div>`;
	},
};
