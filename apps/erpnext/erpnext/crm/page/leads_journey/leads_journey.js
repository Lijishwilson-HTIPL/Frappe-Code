frappe.pages['leads-journey'].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Leads Journey'),
		single_column: true,
	});

	const page = wrapper.page;
	page.main.addClass('frappe-card');

	const JOURNEY_STAGES = ['New', 'Contacted', 'Interested', 'Replied', 'Opportunity', 'Converted'];
	const TERMINAL = ['Do Not Contact', 'Junk'];
	const STATUS_COLORS = {
		'New': '#7c3aed',
		'Contacted': '#2563eb',
		'Interested': '#d97706',
		'Replied': '#0891b2',
		'Opportunity': '#16a34a',
		'Converted': '#15803d',
		'Do Not Contact': '#6b7280',
		'Junk': '#6b7280',
	};

	let currentPage = 1;
	let selectedStatus = null;
	let data = {};

	function getInitials(name) {
		if (!name) return '?';
		return name.split(' ').slice(0, 2).map(w => (w[0] || '').toUpperCase()).join('');
	}

	function timeAgo(dateStr) {
		if (!dateStr) return '—';
		const diff = Date.now() - new Date(dateStr).getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 1) return __('just now');
		if (mins < 60) return mins + __('m ago');
		const hours = Math.floor(mins / 60);
		if (hours < 24) return hours + __('h ago');
		const days = Math.floor(hours / 24);
		if (days < 30) return days + __('d ago');
		return Math.floor(days / 30) + __('mo ago');
	}

	function stepIndex(status) {
		return JOURNEY_STAGES.indexOf(status);
	}

	function renderPipeline(status) {
		const cur = stepIndex(status);
		const isTerminal = TERMINAL.includes(status);
		return JOURNEY_STAGES.map((stage, idx) => {
			let dotClass = 'lj-dot';
			let labelClass = 'lj-label';
			if (isTerminal) {
				dotClass += ' lj-dot-inactive';
			} else if (idx < cur) {
				dotClass += ' lj-dot-done';
			} else if (idx === cur) {
				dotClass += ' lj-dot-active';
				labelClass += ' lj-label-active';
			} else {
				dotClass += ' lj-dot-inactive';
			}
			const connector = idx < JOURNEY_STAGES.length - 1
				? `<div class="lj-connector ${!isTerminal && idx < cur ? 'lj-connector-done' : ''}"></div>`
				: '';
			return `
				<div class="lj-step">
					<div class="${dotClass}"></div>
					<span class="${labelClass}">${__(stage)}</span>
				</div>
				${connector}
			`;
		}).join('');
	}

	function renderStatusBadge(status) {
		const color = STATUS_COLORS[status] || '#6b7280';
		const bg = color + '22';
		return `<span style="background:${bg};color:${color};padding:2px 8px;border-radius:999px;font-size:11px;font-weight:500;">${status}</span>`;
	}

	function renderStats(stats) {
		return `
			<div class="lj-stats-grid">
				<div class="lj-stat-card"><div class="lj-stat-label">${__('Total Leads')}</div><div class="lj-stat-value">${stats.total ?? '—'}</div></div>
				<div class="lj-stat-card"><div class="lj-stat-label">${__('Qualified')}</div><div class="lj-stat-value">${stats.qualified ?? '—'}</div></div>
				<div class="lj-stat-card"><div class="lj-stat-label">${__('Converted')}</div><div class="lj-stat-value">${stats.converted ?? '—'}</div></div>
				<div class="lj-stat-card"><div class="lj-stat-label">${__('Conversion Rate')}</div><div class="lj-stat-value">${stats.total ? stats.conversion_rate + '%' : '—'}</div></div>
			</div>
		`;
	}

	function renderFilters(statuses) {
		const allStatuses = ['New', 'Contacted', 'Interested', 'Replied', 'Opportunity', 'Converted', 'Do Not Contact', 'Junk'];
		const pills = allStatuses.map(s => {
			const active = selectedStatus === s;
			return `<button class="lj-pill ${active ? 'lj-pill-active' : ''}" data-status="${s}">${__(s)}</button>`;
		});
		return `<div class="lj-filter-bar">
			<button class="lj-pill ${!selectedStatus ? 'lj-pill-active' : ''}" data-status="">${__('All')}</button>
			${pills.join('')}
		</div>`;
	}

	function renderLeads(leads) {
		if (!leads.length) {
			return `<div class="lj-empty">${__('No leads found')}</div>`;
		}
		return leads.map(lead => `
			<div class="lj-card">
				<div class="lj-card-body">
					<div class="lj-lead-info">
						<div class="lj-avatar">${getInitials(lead.lead_name)}</div>
						<div class="lj-lead-text">
							<div class="lj-lead-name">${lead.lead_name || lead.name}</div>
							<div class="lj-lead-org">${lead.company_name || '—'}</div>
							${renderStatusBadge(lead.status)}
						</div>
					</div>
					<div class="lj-pipeline">
						<div class="lj-pipeline-inner">${renderPipeline(lead.status)}</div>
					</div>
				</div>
				<div class="lj-card-footer">
					<span class="lj-meta">${__('Last Activity')}: ${timeAgo(lead.modified)}</span>
					<div class="lj-actions">
						<button class="btn btn-default btn-xs lj-view-btn" data-name="${lead.name}">${__('View')}</button>
						<button class="btn btn-primary btn-xs lj-update-btn" data-name="${lead.name}" style="background:#7c3aed;border-color:#7c3aed;">${__('Update Status')}</button>
					</div>
				</div>
			</div>
		`).join('');
	}

	function renderPagination(total, pageSize) {
		const totalPages = Math.ceil(total / pageSize);
		if (totalPages <= 1) return '';
		const start = (currentPage - 1) * pageSize + 1;
		const end = Math.min(currentPage * pageSize, total);
		let pages = '';
		for (let p = Math.max(1, currentPage - 2); p <= Math.min(totalPages, currentPage + 2); p++) {
			pages += `<button class="lj-page-btn ${p === currentPage ? 'lj-page-active' : ''}" data-page="${p}">${p}</button>`;
		}
		return `
			<div class="lj-pagination">
				<span class="lj-page-info">${__('Showing')} ${start}–${end} ${__('of')} ${total}</span>
				<div class="lj-page-nav">
					<button class="lj-page-btn" data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>‹</button>
					${pages}
					<button class="lj-page-btn" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>›</button>
				</div>
			</div>
		`;
	}

	function render() {
		const s = data.stats || {};
		const leads = data.leads || [];
		const total = data.total || 0;
		const pageSize = data.page_size || 20;

		page.main.html(`
			<style>
				.lj-stats-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; padding:16px 16px 8px; }
				.lj-stat-card { background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:16px; }
				.lj-stat-label { font-size:12px; color:#6b7280; margin-bottom:4px; }
				.lj-stat-value { font-size:24px; font-weight:700; color:#111827; }
				.lj-filter-bar { display:flex; flex-wrap:wrap; gap:8px; padding:8px 16px 12px; }
				.lj-pill { padding:4px 14px; border-radius:999px; border:1px solid #e5e7eb; background:#fff; font-size:13px; font-weight:500; color:#6b7280; cursor:pointer; }
				.lj-pill-active { background:#7c3aed; color:#fff; border-color:#7c3aed; }
				.lj-card { background:#fff; border:1px solid #e5e7eb; border-radius:12px; margin:0 16px 10px; padding:16px; }
				.lj-card-body { display:flex; align-items:center; gap:24px; }
				.lj-lead-info { display:flex; align-items:flex-start; gap:12px; width:200px; flex-shrink:0; }
				.lj-avatar { width:40px; height:40px; border-radius:8px; background:#7c3aed; color:#fff; font-weight:600; font-size:14px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
				.lj-lead-name { font-size:13px; font-weight:600; color:#111827; }
				.lj-lead-org { font-size:12px; color:#6b7280; margin:2px 0 4px; }
				.lj-pipeline { flex:1; }
				.lj-pipeline-inner { display:flex; align-items:center; }
				.lj-step { display:flex; flex-direction:column; align-items:center; }
				.lj-dot { width:12px; height:12px; border-radius:50%; border:2px solid #d1d5db; background:#fff; }
				.lj-dot-done { border-color:#7c3aed; background:#7c3aed; }
				.lj-dot-active { width:16px; height:16px; border-color:#7c3aed; background:#fff; }
				.lj-dot-inactive { border-color:#d1d5db; background:#f3f4f6; }
				.lj-label { font-size:10px; color:#9ca3af; margin-top:6px; text-align:center; white-space:nowrap; }
				.lj-label-active { color:#7c3aed; font-weight:600; }
				.lj-connector { height:2px; flex:1; background:#e5e7eb; margin-bottom:20px; }
				.lj-connector-done { background:#7c3aed; }
				.lj-card-footer { display:flex; align-items:center; justify-content:space-between; margin-top:12px; padding-top:12px; border-top:1px solid #f3f4f6; }
				.lj-meta { font-size:12px; color:#9ca3af; }
				.lj-actions { display:flex; gap:8px; }
				.lj-empty { text-align:center; color:#9ca3af; padding:60px 0; font-size:15px; }
				.lj-pagination { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; border-top:1px solid #e5e7eb; margin-top:4px; }
				.lj-page-info { font-size:13px; color:#6b7280; }
				.lj-page-nav { display:flex; gap:4px; }
				.lj-page-btn { min-width:32px; height:32px; padding:0 8px; border-radius:6px; border:1px solid #e5e7eb; background:#fff; font-size:13px; cursor:pointer; color:#374151; }
				.lj-page-active { background:#7c3aed; color:#fff; border-color:#7c3aed; }
				.lj-page-btn:disabled { opacity:0.4; cursor:default; }
			</style>
			${renderStats(s)}
			${renderFilters()}
			<div id="lj-leads-list">${renderLeads(leads)}</div>
			${renderPagination(total, pageSize)}
		`);

		// Bind events
		page.main.find('.lj-pill').on('click', function () {
			selectedStatus = $(this).data('status') || null;
			currentPage = 1;
			load();
		});

		page.main.find('.lj-view-btn, .lj-update-btn').on('click', function () {
			const name = $(this).data('name');
			frappe.set_route('Form', 'Lead', name);
		});

		page.main.find('.lj-page-btn').on('click', function () {
			const p = parseInt($(this).data('page'));
			if (!p || p < 1) return;
			currentPage = p;
			load();
		});
	}

	function load() {
		page.main.find('#lj-leads-list').html(
			'<div style="text-align:center;padding:60px 0;color:#9ca3af;">Loading…</div>'
		);
		frappe.call({
			method: 'crm_unify.crm_unify.page.leads_journey.leads_journey.get_leads_journey',
			args: { page: currentPage, status: selectedStatus },
			callback(r) {
				data = r.message || {};
				render();
			},
		});
	}

	load();
};
