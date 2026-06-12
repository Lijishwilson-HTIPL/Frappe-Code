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
`;
		const $style = $(`<style id="ph-page-css">${css}</style>`);
		$("head").append($style);
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
