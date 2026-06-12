(function () {
    'use strict';

    var _injected = false;
    var _current_status = 'All';
    var _current_search = '';

    var CSS = [
        '#pw-projects-section { padding: 8px 0 24px; }',
        '#pw-projects-section .pw-section-head { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:12px; }',
        '#pw-projects-section .pw-section-head h4 { margin:0; font-size:15px; font-weight:700; color:var(--text-color,#1a202c); }',
        '.pw-filter-bar { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; align-items:center; }',
        '.pw-status-btn { font-size:12px; padding:3px 12px; border-radius:12px; border:1px solid var(--border-color,#e2e8f0); cursor:pointer; background:var(--bg-color,#fff); color:var(--text-muted,#6b7280); transition:background .15s,color .15s; }',
        '.pw-status-btn.active { background:var(--primary,#2563eb); color:#fff; border-color:var(--primary,#2563eb); }',
        '.pw-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; }',
        '.pw-card { background:var(--card-bg,#fff); border:1px solid var(--border-color,#e2e8f0); border-radius:8px; padding:14px 16px; transition:box-shadow .15s,transform .15s; }',
        '.pw-card:hover { box-shadow:0 4px 14px rgba(0,0,0,.10); transform:translateY(-2px); }',
        '.pw-card-title { font-weight:600; font-size:14px; color:var(--text-color,#1a202c); text-decoration:none; display:block; margin-bottom:7px; }',
        '.pw-card-title:hover { color:var(--primary,#2563eb); text-decoration:underline; }',
        '.pw-badge-row { display:flex; gap:5px; flex-wrap:wrap; margin-bottom:8px; }',
        '.pw-badge { font-size:10px; font-weight:700; padding:2px 7px; border-radius:10px; text-transform:uppercase; letter-spacing:.4px; }',
        '.pw-badge-Open { background:#dbeafe; color:#1d4ed8; }',
        '.pw-badge-Completed { background:#dcfce7; color:#15803d; }',
        '.pw-badge-Cancelled { background:#fee2e2; color:#b91c1c; }',
        '.pw-badge-High { background:#fef9c3; color:#b45309; }',
        '.pw-badge-Medium { background:#e0f2fe; color:#0369a1; }',
        '.pw-badge-Low { background:#f0fdf4; color:#166534; }',
        '.pw-badge-other { background:#f3f4f6; color:#374151; }',
        '.pw-progress-label { font-size:11px; color:var(--text-muted,#6b7280); margin-bottom:2px; }',
        '.pw-progress-bg { background:var(--border-color,#e2e8f0); border-radius:4px; height:5px; overflow:hidden; margin-bottom:8px; }',
        '.pw-progress-fill { height:5px; border-radius:4px; background:var(--primary,#2563eb); }',
        '.pw-meta { font-size:11px; color:var(--text-muted,#6b7280); display:flex; gap:10px; flex-wrap:wrap; }',
        '.pw-empty { grid-column:1/-1; text-align:center; padding:40px 0; color:var(--text-muted,#6b7280); }'
    ].join('\n');

    function isProjectsWorkspace() {
        return window.location.pathname === '/app/projects';
    }

    function injectCSS() {
        if (document.getElementById('pw-css')) return;
        var style = document.createElement('style');
        style.id = 'pw-css';
        style.textContent = CSS;
        document.head.appendChild(style);
    }

    function buildSectionHTML() {
        var statuses = ['All', 'Open', 'Completed', 'Cancelled'];
        var btns = statuses.map(function (s) {
            return '<button class="pw-status-btn' + (s === _current_status ? ' active' : '') +
                '" data-status="' + s + '">' + (frappe && frappe.__ ? frappe.__(s) : s) + '</button>';
        }).join('');
        return '<div id="pw-projects-section">' +
            '<div class="pw-section-head">' +
            '<h4>' + (frappe && frappe.__ ? frappe.__('All Projects') : 'All Projects') + '</h4>' +
            '<input id="pw-search" type="text" class="form-control form-control-sm" placeholder="' +
            (frappe && frappe.__ ? frappe.__('Search projects…') : 'Search projects…') +
            '" style="max-width:180px;">' +
            '</div>' +
            '<div class="pw-filter-bar">' + btns + '</div>' +
            '<div id="pw-grid" class="pw-grid">' +
            '<div class="pw-empty">' + (frappe && frappe.__ ? frappe.__('Loading…') : 'Loading…') + '</div>' +
            '</div>' +
            '</div>';
    }

    function attachHandlers() {
        $(document).on('click.pw_filter', '.pw-status-btn', function () {
            $('.pw-status-btn').removeClass('active');
            $(this).addClass('active');
            _current_status = $(this).data('status');
            fetchAndRender();
        });
        $(document).on('input.pw_search', '#pw-search', frappe.utils.debounce(function () {
            _current_search = $(this).val();
            fetchAndRender();
        }, 400));
    }

    function detachHandlers() {
        $(document).off('click.pw_filter');
        $(document).off('input.pw_search');
    }

    function fetchAndRender() {
        frappe.call({
            method: 'erpnext.projects.page.project_home.project_home.get_projects',
            args: { status: _current_status, search: _current_search },
            callback: function (r) { renderCards(r.message || []); }
        });
    }

    function cardHTML(p) {
        var statusCls = 'pw-badge-' + frappe.utils.escape_html(p.status || 'other');
        var priCls = 'pw-badge-' + frappe.utils.escape_html(p.priority || 'other');
        var pct = parseFloat(p.percent_complete) || 0;
        var endDate = p.expected_end_date && frappe.datetime
            ? frappe.datetime.str_to_user(p.expected_end_date) : (p.expected_end_date || '—');
        var taskText = p.total_tasks
            ? (p.open_tasks + ' open' + (p.overdue_tasks
                ? ' · <span style="color:#b91c1c">' + p.overdue_tasks + ' overdue</span>'
                : ''))
            : (frappe && frappe.__ ? frappe.__('No tasks') : 'No tasks');
        var priHtml = p.priority
            ? '<span class="pw-badge ' + priCls + '">' + (frappe && frappe.__ ? frappe.__(p.priority) : p.priority) + '</span>'
            : '';
        return '<div class="pw-card">' +
            '<a class="pw-card-title" href="/app/project/' + encodeURIComponent(p.name) + '">' +
            frappe.utils.escape_html(p.project_name || p.name) + '</a>' +
            '<div class="pw-badge-row">' +
            '<span class="pw-badge ' + statusCls + '">' + (frappe && frappe.__ ? frappe.__(p.status || '—') : (p.status || '—')) + '</span>' +
            priHtml +
            '</div>' +
            '<div class="pw-progress-label">' + (frappe && frappe.__ ? frappe.__('Progress') : 'Progress') + ': ' + pct + '%</div>' +
            '<div class="pw-progress-bg"><div class="pw-progress-fill" style="width:' + pct + '%"></div></div>' +
            '<div class="pw-meta">' +
            '<span>📅 ' + endDate + '</span>' +
            '<span>📋 ' + taskText + '</span>' +
            '</div>' +
            '</div>';
    }

    function renderCards(projects) {
        var $grid = $('#pw-grid');
        if (!$grid.length) return;
        $grid.empty();
        if (!projects.length) {
            $grid.html('<div class="pw-empty">' + (frappe && frappe.__ ? frappe.__('No projects found.') : 'No projects found.') + '</div>');
            return;
        }
        projects.forEach(function (p) { $grid.append(cardHTML(p)); });
    }

    function tryInject() {
        if (_injected || !isProjectsWorkspace()) return false;
        var $main = $('.layout-main-section');
        if (!$main.length) return false;
        if (!$main.find('.widget-group, .widget, .workspace-container').length) return false;
        if ($('#pw-projects-section').length) { _injected = true; return true; }

        injectCSS();
        $main.append(buildSectionHTML());
        _injected = true;
        attachHandlers();
        fetchAndRender();
        return true;
    }

    function startWatching() {
        if (!isProjectsWorkspace()) return;
        if (tryInject()) return;

        var attempts = 0;
        var id = setInterval(function () {
            attempts++;
            if (!isProjectsWorkspace() || attempts > 40) { clearInterval(id); return; }
            if (tryInject()) clearInterval(id);
        }, 100);
    }

    function teardown() {
        $('#pw-projects-section').remove();
        detachHandlers();
        _injected = false;
        _current_status = 'All';
        _current_search = '';
    }

    $(document).on('page-change', function () {
        teardown();
        startWatching();
    });

    $(document).ready(function () {
        if (isProjectsWorkspace()) startWatching();
    });

}());
