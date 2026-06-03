frappe.pages['job-applicant-journey'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Job Applicant Journey'),
		single_column: true,
	});

	new JobApplicantJourney(page);
};

const STAGES = ['Applied', 'Screening', 'Assessment', 'Interview', 'Offered', 'Onboard'];

class JobApplicantJourney {
	constructor(page) {
		this.page = page;
		this.active_filter = 'All';
		this.applicants = [];
		this.wrapper = $(`<div class="jaj-wrapper"></div>`).appendTo(page.body);
		this.inject_styles();
		this.refresh_btn = page.set_primary_action(__('Refresh'), () => this.load(), 'refresh');
		this.load();
	}

	inject_styles() {
		if (document.getElementById('jaj-styles')) return;
		const css = `
		.jaj-wrapper { padding: 8px 4px 32px; }
		.jaj-kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
		.jaj-kpi { background: var(--card-bg, #fff); border: 1px solid var(--border-color, #e2e6ea); border-radius: 10px; padding: 14px 16px; }
		.jaj-kpi .label { font-size: 12px; color: var(--text-muted, #6c7680); margin-bottom: 6px; }
		.jaj-kpi .value { font-size: 22px; font-weight: 600; color: var(--text-color, #1f272e); }
		.jaj-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
		.jaj-chip { padding: 6px 14px; border-radius: 999px; background: #f3f3f6; color: #4a5562; font-size: 12px; cursor: pointer; border: 1px solid transparent; user-select: none; }
		.jaj-chip.active { background: var(--uic-primary, #6e3bff); color: #fff; }
		.jaj-row { background: var(--card-bg, #fff); border: 1px solid var(--border-color, #e2e6ea); border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; }
		.jaj-row-top { display: flex; align-items: center; gap: 14px; }
		.jaj-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--uic-primary, #6e3bff); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; flex-shrink: 0; }
		.jaj-name { font-weight: 600; color: var(--text-color); }
		.jaj-sub { font-size: 12px; color: var(--text-muted, #6c7680); }
		.jaj-stage-badge { display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 11px; margin-top: 4px; background: #d2f5dc; color: #1f7a3a; }
		.jaj-steps { flex: 1; display: flex; align-items: center; padding: 0 12px; min-width: 0; }
		.jaj-step { flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; }
		.jaj-step .dot { width: 14px; height: 14px; border-radius: 50%; background: #fff; border: 2px solid #c9ccd4; z-index: 2; }
		.jaj-step.done .dot { background: var(--uic-primary, #6e3bff); border-color: var(--uic-primary, #6e3bff); }
		.jaj-step.current .dot { background: var(--uic-primary, #6e3bff); border-color: var(--uic-primary, #6e3bff); box-shadow: 0 0 0 4px rgba(0,0,0,0.08); }
		.jaj-step .lbl { font-size: 11px; color: var(--text-muted, #6c7680); margin-top: 6px; white-space: nowrap; }
		.jaj-step.done .lbl, .jaj-step.current .lbl { color: var(--text-color); }
		.jaj-step .line { position: absolute; top: 7px; left: 50%; width: 100%; height: 2px; background: #c9ccd4; z-index: 1; }
		.jaj-step.done .line, .jaj-step.current.has-prev .line { background: var(--uic-primary, #6e3bff); }
		.jaj-step:last-child .line { display: none; }
		.jaj-actions { display: flex; gap: 8px; }
		.jaj-row-bottom { display: flex; justify-content: space-between; margin-top: 10px; font-size: 12px; color: var(--text-muted); }
		.jaj-empty { text-align: center; padding: 40px; color: var(--text-muted); }
		`;
		const style = document.createElement('style');
		style.id = 'jaj-styles';
		style.textContent = css;
		document.head.appendChild(style);
	}

	async load() {
		this.applicants = await frappe.db.get_list('Job Applicant', {
			fields: ['name', 'applicant_name', 'job_title', 'status', 'recruitment_stage', 'modified', 'owner'],
			limit: 0,
			order_by: 'modified desc',
		});
		this.render();
	}

	stage_of(a) {
		return STAGES.includes(a.recruitment_stage) ? a.recruitment_stage : 'Applied';
	}

	render() {
		const total = this.applicants.length;
		const onboard = this.applicants.filter(a => this.stage_of(a) === 'Onboard').length;
		const offered = this.applicants.filter(a => this.stage_of(a) === 'Offered').length;
		const conv = total ? Math.round((onboard / total) * 100) : 0;

		const kpis = `
			<div class="jaj-kpis">
				<div class="jaj-kpi"><div class="label">Total Applicants</div><div class="value">${total}</div></div>
				<div class="jaj-kpi"><div class="label">Offered</div><div class="value">${offered}</div></div>
				<div class="jaj-kpi"><div class="label">Onboard</div><div class="value">${onboard}</div></div>
				<div class="jaj-kpi"><div class="label">Conversion Rate</div><div class="value">${conv}%</div></div>
			</div>`;

		const chips = ['All', ...STAGES].map(s => {
			const cls = s === this.active_filter ? 'jaj-chip active' : 'jaj-chip';
			return `<div class="${cls}" data-stage="${frappe.utils.escape_html(s)}">${frappe.utils.escape_html(s)}</div>`;
		}).join('');

		const filtered = this.active_filter === 'All'
			? this.applicants
			: this.applicants.filter(a => this.stage_of(a) === this.active_filter);

		const rows = filtered.length
			? filtered.map(a => this.row_html(a)).join('')
			: `<div class="jaj-empty">${__('No applicants for this stage.')}</div>`;

		this.wrapper.html(`${kpis}<div class="jaj-chips">${chips}</div><div class="jaj-rows">${rows}</div>`);

		this.wrapper.find('.jaj-chip').on('click', e => {
			this.active_filter = $(e.currentTarget).data('stage');
			this.render();
		});
		this.wrapper.find('[data-action="view"]').on('click', e => {
			const name = $(e.currentTarget).data('name');
			frappe.set_route('Form', 'Job Applicant', name);
		});
	}

	row_html(a) {
		const stage = this.stage_of(a);
		const idx = STAGES.indexOf(stage);
		const initials = (a.applicant_name || a.name || '?')
			.split(/\s+/).map(s => s[0]).slice(0, 2).join('').toUpperCase();
		const steps = STAGES.map((s, i) => {
			let cls = 'jaj-step';
			if (i < idx) cls += ' done';
			else if (i === idx) cls += ' current has-prev';
			return `<div class="${cls}"><div class="line"></div><div class="dot"></div><div class="lbl">${s}</div></div>`;
		}).join('');
		const when = a.modified ? frappe.datetime.comment_when(a.modified) : '';
		const job = a.job_title ? frappe.utils.escape_html(a.job_title) : '—';
		return `
			<div class="jaj-row">
				<div class="jaj-row-top">
					<div class="jaj-avatar">${frappe.utils.escape_html(initials)}</div>
					<div style="min-width: 180px;">
						<div class="jaj-name">${frappe.utils.escape_html(a.applicant_name || a.name)}</div>
						<div class="jaj-sub">${job}</div>
						<div class="jaj-stage-badge">${frappe.utils.escape_html(stage)}</div>
					</div>
					<div class="jaj-steps">${steps}</div>
					<div class="jaj-actions">
						<button class="btn btn-default btn-sm" data-action="view" data-name="${frappe.utils.escape_html(a.name)}">${__('View')}</button>
					</div>
				</div>
				<div class="jaj-row-bottom">
					<div>${__('Last Activity')}: ${when}</div>
					<div>${__('Owner')}: ${frappe.utils.escape_html(a.owner || '—')}</div>
				</div>
			</div>`;
	}
}
