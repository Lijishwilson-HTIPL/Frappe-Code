frappe.pages["project-home"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("All Projects"),
		single_column: true,
	});
	new ProjectHome(wrapper);
};

class ProjectHome {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.status_filter = "All";
		this.search_value = "";
		this._setup_filters();
		this._inject_css();
		this._render_heatmap();
		this.$grid = $('<div class="ph-grid"></div>').appendTo(
			$(this.page.main)
		);
		this.refresh();
	}

	_setup_filters() {
		// Status filter buttons
		const statuses = ["All", "Open", "Completed", "Cancelled"];
		const $filter_bar = $(
			'<div class="ph-filter-bar" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;"></div>'
		).prependTo($(this.page.main));

		statuses.forEach((s) => {
			const $btn = $(
				`<button class="btn btn-default btn-sm ph-status-btn" data-status="${s}">${__(s)}</button>`
			).appendTo($filter_bar);
			if (s === "All") $btn.addClass("btn-primary active");
			$btn.on("click", () => {
				$filter_bar.find(".ph-status-btn").removeClass("btn-primary active").addClass("btn-default");
				$btn.removeClass("btn-default").addClass("btn-primary active");
				this.status_filter = s;
				this.refresh();
			});
		});

		// Search input added to page
		const search_field = this.page.add_field({
			fieldname: "search",
			fieldtype: "Data",
			placeholder: __("Search projects…"),
		});
		$(search_field.input).on("input", frappe.utils.debounce(() => {
			this.search_value = $(search_field.input).val();
			this.refresh();
		}, 400));

		// New Project button
		this.page.set_primary_action(__("New Project"), () => {
			frappe.new_doc("Project");
		}, "add");
	}

	_inject_css() {
		if (document.getElementById("ph-page-css")) return;
		const css = `
.ph-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 16px;
	padding: 8px 0 24px;
}
.ph-card {
	background: var(--card-bg, #fff);
	border: 1px solid var(--border-color, #e2e8f0);
	border-radius: 8px;
	padding: 16px;
	cursor: pointer;
	transition: box-shadow 0.15s, transform 0.15s;
}
.ph-card:hover {
	box-shadow: 0 4px 16px rgba(0,0,0,0.10);
	transform: translateY(-2px);
}
.ph-card-title {
	font-weight: 600;
	font-size: 14px;
	color: var(--text-color, #1a202c);
	text-decoration: none;
	display: block;
	margin-bottom: 8px;
}
.ph-card-title:hover { text-decoration: underline; color: var(--primary, #2563eb); }
.ph-badge-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.ph-badge {
	font-size: 11px;
	font-weight: 600;
	padding: 2px 8px;
	border-radius: 12px;
	text-transform: uppercase;
	letter-spacing: 0.4px;
}
.ph-badge-open    { background:#dbeafe; color:#1d4ed8; }
.ph-badge-completed { background:#dcfce7; color:#15803d; }
.ph-badge-cancelled { background:#fee2e2; color:#b91c1c; }
.ph-badge-other   { background:#f3f4f6; color:#374151; }
.ph-badge-high    { background:#fef9c3; color:#b45309; }
.ph-badge-medium  { background:#e0f2fe; color:#0369a1; }
.ph-badge-low     { background:#f0fdf4; color:#166534; }
.ph-progress-wrap { margin: 10px 0 6px; }
.ph-progress-label { font-size: 11px; color: var(--text-muted, #6b7280); margin-bottom: 3px; }
.ph-progress-bar-bg {
	background: var(--border-color, #e2e8f0);
	border-radius: 4px;
	height: 6px;
	overflow: hidden;
}
.ph-progress-bar-fill {
	height: 6px;
	border-radius: 4px;
	background: var(--primary, #2563eb);
	transition: width 0.3s;
}
.ph-meta { font-size: 12px; color: var(--text-muted, #6b7280); margin-top: 8px; display:flex; gap:12px; flex-wrap:wrap; }
.ph-empty {
	grid-column: 1/-1;
	text-align: center;
	padding: 60px 20px;
	color: var(--text-muted, #6b7280);
	font-size: 14px;
}
/* ── Heatmap ── */
.ph-hm-wrap { padding: 16px 0 12px; }
.ph-hm-title { font-weight: 600; font-size: 13px; color: var(--text-color, #1a202c); margin-bottom: 8px; }
.ph-hm-months {
    display: grid;
    grid-template-columns: 28px repeat(53, 14px);
    gap: 2px;
    margin-bottom: 2px;
}
.ph-hm-month-lbl {
    font-size: 10px;
    color: var(--text-muted, #6b7280);
    white-space: nowrap;
    overflow: visible;
    line-height: 1;
}
.ph-hm-grid {
    display: grid;
    grid-template-columns: 28px repeat(53, 14px);
    grid-template-rows: repeat(7, 14px);
    gap: 2px;
}
.ph-hm-day-lbl {
    font-size: 9px;
    color: var(--text-muted, #6b7280);
    text-align: right;
    padding-right: 4px;
    line-height: 14px;
    white-space: nowrap;
}
.ph-hm-cell {
    width: 12px;
    height: 12px;
    border-radius: 2px;
    cursor: pointer;
    transition: opacity 0.1s;
}
.ph-hm-cell:hover { opacity: 0.75; }
.ph-hm-gap { background: transparent !important; cursor: default; pointer-events: none; }
.ph-hm-legend {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 8px;
}
.ph-hm-legend span { font-size: 11px; color: var(--text-muted, #6b7280); }
.ph-hm-tooltip {
    position: fixed;
    z-index: 9999;
    background: #1e293b;
    color: #f1f5f9;
    font-size: 12px;
    line-height: 1.6;
    padding: 8px 12px;
    border-radius: 6px;
    pointer-events: none;
    display: none;
    white-space: nowrap;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}
`;
		const $style = $(`<style id="ph-page-css">${css}</style>`);
		$("head").append($style);
	}

	_render_heatmap() {
		this.$heatmap = $('<div class="ph-hm-wrap"></div>').appendTo($(this.page.main));
		this.$heatmap.html(
			`<div class="ph-hm-title">${__("Task Activity — Last 52 Weeks")}</div>` +
			`<div style="color:var(--text-muted,#6b7280);font-size:12px;">${__("Loading…")}</div>`
		);
		frappe.call({
			method: "erpnext.projects.page.project_home.project_home.get_task_heatmap",
			callback: (r) => this._draw_heatmap(r.message || {}),
		});
	}

	_draw_heatmap(data) {
		const COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"];
		const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
		const DAY_LABELS = ["Mon","","Wed","","Fri","","Sun"];

		function cellColor(total) {
			if (total === 0)  return COLORS[0];
			if (total <= 2)   return COLORS[1];
			if (total <= 5)   return COLORS[2];
			if (total <= 9)   return COLORS[3];
			return COLORS[4];
		}

		const today = new Date();
		today.setHours(23, 59, 59, 999);

		const startRaw = new Date(today);
		startRaw.setDate(startRaw.getDate() - 364);
		startRaw.setHours(0, 0, 0, 0);
		const dow = startRaw.getDay();
		const toMonday = dow === 0 ? -6 : 1 - dow;
		startRaw.setDate(startRaw.getDate() + toMonday);

		const weeks = [];
		const cur = new Date(startRaw);
		while (cur <= today) {
			const week = [];
			for (let d = 0; d < 7; d++) {
				const dateStr = cur.toISOString().slice(0, 10);
				const inRange = cur >= startRaw && cur <= today;
				const v = (inRange && data[dateStr]) ? data[dateStr] : { created: 0, completed: 0, updated: 0 };
				const total = (v.created || 0) + (v.completed || 0) + (v.updated || 0);
				week.push({ dateStr, inRange, created: v.created || 0, completed: v.completed || 0, updated: v.updated || 0, total });
				cur.setDate(cur.getDate() + 1);
			}
			weeks.push(week);
		}

		let prevMonth = -1;
		const monthCells = weeks.map((week) => {
			const first = week.find(c => c.inRange);
			if (!first) return `<div></div>`;
			const m = new Date(first.dateStr + "T00:00:00").getMonth();
			if (m !== prevMonth) { prevMonth = m; return `<div class="ph-hm-month-lbl">${MONTHS[m]}</div>`; }
			return `<div></div>`;
		});
		const monthsHtml = `<div class="ph-hm-months"><div></div>${monthCells.join("")}</div>`;

		let gridCells = "";
		DAY_LABELS.forEach((label, ri) => {
			gridCells += `<div class="ph-hm-day-lbl" style="grid-column:1;grid-row:${ri + 1};">${label}</div>`;
		});
		weeks.forEach((week, wi) => {
			week.forEach((cell, ri) => {
				if (!cell.inRange) {
					gridCells += `<div class="ph-hm-cell ph-hm-gap" style="grid-column:${wi + 2};grid-row:${ri + 1};"></div>`;
					return;
				}
				const color = cellColor(cell.total);
				const d = new Date(cell.dateStr + "T00:00:00");
				const label = d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
				gridCells += `<div class="ph-hm-cell"
					style="grid-column:${wi + 2};grid-row:${ri + 1};background:${color};"
					data-date="${cell.dateStr}"
					data-tip="${cell.created} created · ${cell.completed} completed · ${cell.updated} updated · ${cell.total} total"
					data-label="${frappe.utils.escape_html(label)}">
				</div>`;
			});
		});
		const gridHtml = `<div class="ph-hm-grid">${gridCells}</div>`;

		const legendHtml = `<div class="ph-hm-legend">
			<span>${__("Less")}</span>
			${COLORS.map(c => `<div class="ph-hm-cell" style="background:${c};cursor:default;"></div>`).join("")}
			<span>${__("More")}</span>
		</div>`;

		this.$heatmap.html(
			`<div class="ph-hm-title">${__("Task Activity — Last 52 Weeks")}</div>` +
			monthsHtml + gridHtml + legendHtml
		);

		if (!$("#ph-hm-tip").length) {
			$('<div id="ph-hm-tip" class="ph-hm-tooltip"></div>').appendTo("body");
		}
		const $tip = $("#ph-hm-tip");

		this.$heatmap.find(".ph-hm-cell[data-date]")
			.on("mouseenter", function (e) {
				const label = $(this).data("label");
				const info  = $(this).data("tip");
				$tip.html(`<b>${label}</b><br>${info}`).show();
			})
			.on("mousemove", function (e) {
				$tip.css({ left: e.pageX + 14, top: e.pageY - 48 });
			})
			.on("mouseleave", function () { $tip.hide(); })
			.on("click", function () {
				const dateStr = $(this).data("date");
				frappe.set_route("List", "Task", {
					creation: ["Between", [dateStr + " 00:00:00", dateStr + " 23:59:59"]],
				});
			});
	}

	refresh() {
		this.$grid.html('<div style="padding:32px;text-align:center;color:var(--text-muted,#6b7280);">' + __("Loading…") + "</div>");
		frappe.call({
			method: "erpnext.projects.page.project_home.project_home.get_projects",
			args: {
				status: this.status_filter,
				search: this.search_value,
			},
			callback: (r) => {
				this._render(r.message || []);
			},
		});
	}

	_render(projects) {
		this.$grid.empty();
		if (!projects.length) {
			this.$grid.append('<div class="ph-empty">' + __("No projects found.") + "</div>");
			return;
		}
		projects.forEach((p) => this.$grid.append(this._card_html(p)));
	}

	_card_html(p) {
		const status_cls = {
			Open: "ph-badge-open",
			Completed: "ph-badge-completed",
			Cancelled: "ph-badge-cancelled",
		}[p.status] || "ph-badge-other";

		const priority_cls = {
			High: "ph-badge-high",
			Medium: "ph-badge-medium",
			Low: "ph-badge-low",
		}[p.priority] || "ph-badge-other";

		const pct = parseFloat(p.percent_complete) || 0;
		const end_date = p.expected_end_date
			? frappe.datetime.str_to_user(p.expected_end_date)
			: "—";

		const task_info = [];
		if (p.total_tasks) task_info.push(p.open_tasks + " open");
		if (p.overdue_tasks) task_info.push(`<span style="color:#b91c1c;">${p.overdue_tasks} overdue</span>`);
		if (!p.total_tasks) task_info.push(__("No tasks"));

		const priority_badge = p.priority
			? `<span class="ph-badge ${priority_cls}">${__(p.priority)}</span>`
			: "";

		return `
<div class="ph-card">
  <a class="ph-card-title" href="/app/project/${encodeURIComponent(p.name)}">${frappe.utils.escape_html(p.project_name || p.name)}</a>
  <div class="ph-badge-row">
    <span class="ph-badge ${status_cls}">${__(p.status || "—")}</span>
    ${priority_badge}
  </div>
  <div class="ph-progress-wrap">
    <div class="ph-progress-label">${__("Progress")}: ${pct}%</div>
    <div class="ph-progress-bar-bg">
      <div class="ph-progress-bar-fill" style="width:${pct}%"></div>
    </div>
  </div>
  <div class="ph-meta">
    <span>📅 ${end_date}</span>
    <span>📋 ${task_info.join(" · ")}</span>
  </div>
</div>`;
	}
}
