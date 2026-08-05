frappe.pages["training-analytics"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Training Analytics"),
		single_column: true,
	});

	new TrainingAnalytics(page);
};

class TrainingAnalytics {
	constructor(page) {
		this.page = page;
		this.$body = $(page.body);
		this.render_shell();
		this.load();
	}

	render_shell() {
		this.$body.html(`
			<div class="ta-root">
				<style>${this.styles()}</style>
				<div class="ta-loading">${__("Loading training analytics...")}</div>
			</div>
		`);
		this.$root = this.$body.find(".ta-root");
	}

	load() {
		frappe.call({
			method: "quality_dms.dms.api.get_training_analytics",
			callback: (r) => {
				if (!r.message) return;
				this.render(r.message);
			},
			error: () => {
				this.$root.html(`
					<style>${this.styles()}</style>
					<div class="ta-empty">${__("You do not have permission to view training analytics.")}</div>
				`);
			},
		});
	}

	render(data) {
		const totalCompleted = data.completion_by_department.reduce((s, d) => s + d.completed, 0);
		const totalAssigned = data.completion_by_department.reduce((s, d) => s + d.total, 0);
		const overallCompletionPct = totalAssigned ? Math.round((totalCompleted / totalAssigned) * 1000) / 10 : 0;
		const lastMonth = data.score_trend.length ? data.score_trend[data.score_trend.length - 1] : null;

		const scoreBand = (score) => {
			if (score === null || score === undefined) return "none";
			if (score >= 80) return "good";
			if (score >= 60) return "fair";
			return "poor";
		};
		const completionBand = (pct) => (pct >= 80 ? "good" : pct >= 50 ? "fair" : "poor");

		const icon = (path) => `<svg class="ta-title-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">${path}</svg>`;
		const icons = {
			attempts: icon('<path d="M9 11l3 3L22 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'),
			trend: icon('<path d="M3 17l6-6 4 4 8-8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M15 7h6v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'),
			check: icon('<path d="M4 12l5 5L20 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'),
			bars: icon('<path d="M5 21V10M12 21V3M19 21v-7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'),
			dept: icon('<path d="M3 21h18M6 21V7l6-4 6 4v14M9 9h1M9 13h1M9 17h1M14 9h1M14 13h1M14 17h1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'),
		};

		this.$root.html(`
			<style>${this.styles()}</style>
			<div class="ta-tiles">
				<div class="ta-tile ta-accent-blue">
					<div class="ta-tile-label">${icons.attempts}${__("Total Graded Attempts")}</div>
					<div class="ta-tile-value">${data.total_attempts}</div>
				</div>
				<div class="ta-tile ta-accent-${scoreBand(lastMonth ? lastMonth.avg_score : null)}">
					<div class="ta-tile-label">${icons.trend}${__("Latest Monthly Avg Score")}</div>
					<div class="ta-tile-value ta-value-${scoreBand(lastMonth ? lastMonth.avg_score : null)}">${lastMonth ? lastMonth.avg_score + "%" : "—"}</div>
				</div>
				<div class="ta-tile ta-accent-${completionBand(overallCompletionPct)}">
					<div class="ta-tile-label">${icons.check}${__("Overall Completion Rate")}</div>
					<div class="ta-tile-value ta-value-${completionBand(overallCompletionPct)}">${overallCompletionPct}%</div>
				</div>
			</div>

			<div class="ta-grid">
				<div class="ta-card ta-trend-card ta-accent-blue">
					<div class="ta-card-title">${icons.trend}${__("Org Average Score Trend (Monthly)")}</div>
					${this.trend_chart(data.score_trend)}
				</div>

				<div class="ta-card ta-accent-amber">
					<div class="ta-card-title">${icons.bars}${__("Score Distribution")}</div>
					${this.distribution_chart(data.distribution)}
				</div>

				<div class="ta-card ta-dept-card ta-accent-violet">
					<div class="ta-card-title">${icons.dept}${__("Completion Rate by Department")}</div>
					${this.department_table(data.completion_by_department)}
				</div>
			</div>
		`);
	}

	trend_chart(trend) {
		if (!trend || trend.length < 2) {
			return `<div class="ta-empty-small">${__("Not enough monthly data yet to show a trend (need at least 2 months).")}</div>`;
		}
		const width = 640;
		const height = 160;
		const padX = 30;
		const padY = 20;
		const n = trend.length;
		const xStep = (width - padX * 2) / (n - 1);
		const yFor = (score) => height - padY - (Math.min(100, Math.max(0, score)) / 100) * (height - padY * 2);

		const points = trend.map((t, i) => ({ x: padX + i * xStep, y: yFor(t.avg_score), ...t }));
		const linePoints = points.map((p) => `${p.x},${p.y}`).join(" ");
		const dots = points
			.map(
				(p) =>
					`<circle cx="${p.x}" cy="${p.y}" r="4" class="ta-trend-dot"><title>${frappe.utils.escape_html(p.month)}: ${p.avg_score}% (${p.attempts} attempts)</title></circle>`
			)
			.join("");

		return `
			<svg viewBox="0 0 ${width} ${height}" class="ta-trend-svg">
				<line x1="${padX}" y1="${yFor(70)}" x2="${width - padX}" y2="${yFor(70)}" class="ta-trend-threshold" />
				<polyline points="${linePoints}" class="ta-trend-line" />
				${dots}
			</svg>
			<div class="ta-trend-labels">
				<span>${frappe.utils.escape_html(trend[0].month)}</span>
				<span>${frappe.utils.escape_html(trend[trend.length - 1].month)}</span>
			</div>
		`;
	}

	distribution_chart(distribution) {
		if (!distribution || !distribution.some((d) => d.count > 0)) {
			return `<div class="ta-empty-small">${__("No graded attempts on record yet.")}</div>`;
		}
		const max = Math.max(...distribution.map((d) => d.count), 1);
		const rows = distribution
			.map((d) => {
				const cls = d.label === "0-59" ? "crit" : d.label === "60-69" || d.label === "70-79" ? "warn" : "good";
				return `
				<div class="ta-dist-row">
					<div class="ta-dist-label">${d.label}</div>
					<div class="ta-dist-track">
						<div class="ta-dist-fill ${cls}" style="width:${(d.count / max * 100).toFixed(1)}%"></div>
					</div>
					<div class="ta-dist-count">${d.count}</div>
				</div>`;
			})
			.join("");
		return `<div class="ta-dist-chart">${rows}</div>`;
	}

	department_table(rows) {
		if (!rows || !rows.length) {
			return `<div class="ta-empty-small">${__("No assigned trainings on record yet.")}</div>`;
		}
		const band = (pct) => (pct >= 80 ? "good" : pct >= 50 ? "fair" : "poor");
		const body = rows
			.map(
				(r) => `
				<tr>
					<td>${frappe.utils.escape_html(r.department)}</td>
					<td>${r.completed}/${r.total}</td>
					<td>
						<div class="ta-dept-bar-track">
							<div class="ta-dept-bar-fill ${band(r.completion_pct)}" style="width:${r.completion_pct}%"></div>
						</div>
					</td>
					<td><span class="ta-rate-badge ${band(r.completion_pct)}">${r.completion_pct}%</span></td>
				</tr>`
			)
			.join("");
		return `
			<table class="table ta-table">
				<thead>
					<tr>
						<th>${__("Department")}</th>
						<th>${__("Completed")}</th>
						<th>${__("Progress")}</th>
						<th>${__("Rate")}</th>
					</tr>
				</thead>
				<tbody>${body}</tbody>
			</table>
		`;
	}

	styles() {
		return `
			.ta-root { padding: 4px 2px 24px; }
			.ta-loading, .ta-empty { padding: 40px; text-align: center; color: var(--text-muted); }
			.ta-tiles {
				display: grid;
				grid-template-columns: repeat(3, 1fr);
				gap: 14px;
				margin-bottom: 16px;
			}
			.ta-tile {
				background: var(--card-bg, #fff);
				border: 1px solid var(--border-color, #e1e1e1);
				border-top: 3px solid transparent;
				border-radius: 10px;
				padding: 16px 18px;
				box-shadow: 0 1px 3px rgba(16,24,40,0.04), 0 1px 2px rgba(16,24,40,0.03);
				transition: box-shadow .15s ease;
			}
			.ta-tile:hover { box-shadow: 0 4px 14px rgba(16,24,40,0.08), 0 1px 3px rgba(16,24,40,0.05); }
			.ta-tile-label {
				font-size: 12px;
				color: var(--text-muted);
				margin-bottom: 6px;
				display: flex;
				align-items: center;
				gap: 6px;
			}
			.ta-tile-value { font-size: 26px; font-weight: 700; font-variant-numeric: tabular-nums; }
			.ta-value-good { color: #0ca30c; }
			.ta-value-fair { color: #b8860b; }
			.ta-value-poor { color: #d03b3b; }
			.ta-accent-blue { border-top-color: #1f4e79; }
			.ta-accent-amber { border-top-color: #fab219; }
			.ta-accent-violet { border-top-color: #7c5cbf; }
			.ta-accent-good { border-top-color: #0ca30c; }
			.ta-accent-fair { border-top-color: #fab219; }
			.ta-accent-poor { border-top-color: #d03b3b; }
			.ta-accent-none { border-top-color: var(--border-color, #e1e1e1); }
			.ta-title-icon { width: 14px; height: 14px; color: var(--text-muted); flex: 0 0 auto; }
			.ta-grid {
				display: grid;
				grid-template-columns: 1fr 1fr;
				gap: 16px;
			}
			@media (max-width: 900px) { .ta-grid, .ta-tiles { grid-template-columns: 1fr; } }
			.ta-card {
				background: var(--card-bg, #fff);
				border: 1px solid var(--border-color, #e1e1e1);
				border-top: 3px solid transparent;
				border-radius: 10px;
				padding: 18px 20px;
				box-shadow: 0 1px 3px rgba(16,24,40,0.04), 0 1px 2px rgba(16,24,40,0.03);
				transition: box-shadow .15s ease;
			}
			.ta-card:hover { box-shadow: 0 4px 14px rgba(16,24,40,0.08), 0 1px 3px rgba(16,24,40,0.05); }
			.ta-card-title {
				font-size: 13px;
				font-weight: 600;
				text-transform: uppercase;
				letter-spacing: 0.02em;
				color: var(--text-muted);
				margin-bottom: 14px;
				display: flex;
				align-items: center;
				gap: 8px;
			}
			.ta-trend-card, .ta-dept-card { grid-column: span 2; }
			.ta-trend-svg { width: 100%; height: 160px; }
			.ta-trend-line { fill: none; stroke: #1f4e79; stroke-width: 2; }
			.ta-trend-threshold { stroke: var(--border-color, #e1e1e1); stroke-width: 1; stroke-dasharray: 4 3; }
			.ta-trend-dot { fill: #1f4e79; }
			.ta-trend-labels {
				display: flex;
				justify-content: space-between;
				font-size: 11px;
				color: var(--text-muted);
				margin-top: 4px;
			}
			.ta-dist-chart { display: flex; flex-direction: column; gap: 10px; }
			.ta-dist-row { display: grid; grid-template-columns: 60px 1fr 40px; align-items: center; gap: 10px; }
			.ta-dist-label { font-size: 12px; color: var(--text-secondary, #52514e); text-align: right; }
			.ta-dist-track { height: 16px; border-radius: 4px; background: var(--border-color, #e1e1e1); overflow: hidden; }
			.ta-dist-fill { height: 100%; border-radius: 4px; }
			.ta-dist-fill.crit { background: #d03b3b; }
			.ta-dist-fill.warn { background: #fab219; }
			.ta-dist-fill.good { background: #0ca30c; }
			.ta-dist-count { font-size: 12px; font-weight: 600; text-align: right; }
			.ta-table { font-size: 13px; margin: 0; }
			.ta-table th { color: var(--text-muted); font-weight: 600; font-size: 11.5px; text-transform: uppercase; }
			.ta-table tbody tr:hover { background: rgba(31,78,121,0.03); }
			.ta-dept-bar-track { height: 8px; border-radius: 4px; background: var(--border-color, #e1e1e1); overflow: hidden; width: 120px; }
			.ta-dept-bar-fill { height: 100%; border-radius: 4px; }
			.ta-dept-bar-fill.good { background: linear-gradient(90deg, #0ca30c, #3fbf3f); }
			.ta-dept-bar-fill.fair { background: linear-gradient(90deg, #fab219, #ffc94d); }
			.ta-dept-bar-fill.poor { background: linear-gradient(90deg, #d03b3b, #e56b6b); }
			.ta-rate-badge {
				font-size: 11.5px;
				font-weight: 700;
				padding: 2px 9px;
				border-radius: 20px;
			}
			.ta-rate-badge.good { background: rgba(12,163,12,0.12); color: #0ca30c; }
			.ta-rate-badge.fair { background: rgba(250,178,25,0.18); color: #8a6100; }
			.ta-rate-badge.poor { background: rgba(208,59,59,0.12); color: #d03b3b; }
			.ta-empty-small { color: var(--text-muted); font-size: 13px; padding: 8px 0; }
		`;
	}
}
