// Quality DMS theme scoping — adds .dms-theme to <body> on every DMS page
// (DMS workspace + all its child workspaces, all quality_dms doctypes in any
// view, and the DMS reports), so the blue theme in quality_dms.css never
// touches other apps' pages. UI-only: no workflow or data logic here.
(function () {
	const DMS_DOCTYPES = new Set([
		"Document Library",
		"Document Request",
		"Document Revision",
		"Document Acknowledgement",
		"Document Category",
		"Document Type",
		"Approval Matrix",
		"DMS Audit Log",
		"DMS Curriculum",
		"DMS Curriculum Document",
		"DMS Project",
		"DMS Quiz",
		"DMS Quiz Question",
		"DMS Training Assignment Rule",
		"DMS Training Record",
		"DMS Training Session",
		"DMS Training Session Attendee",
		"Training Settings",
		"CFR Part 11 Signature Log",
		// core doctypes reached from the DMS workspace sidebar
		"File",
		"Workflow",
		"Workflow Action",
	]);
	const DMS_REPORTS = new Set([
		"Audit Trail Report",
		"Master Document List",
		"Overdue Training Report",
		"Training Compliance Report",
		"Training Matrix Report",
	]);

	// The ERPNext Projects module reuses the same navy/blue theme so its
	// workspace, lists, and forms match the DMS look.
	const PROJECT_DOCTYPES = new Set([
		"Project",
		"Task",
		"Timesheet",
		"Project Template",
		"Project Type",
		"Project Update",
		"Activity Type",
		"Activity Cost",
		"Task Type",
		"Issue",
	]);
	const PROJECT_REPORTS = new Set([
		"Project Summary",
		"Daily Timesheet Summary",
		"Timesheet Billing Summary",
		"Project wise Stock Tracking",
		"Delayed Tasks Summary",
	]);

	function slug(txt) {
		return (txt || "").toString().toLowerCase().replace(/[\s_]+/g, "-");
	}

	// All workspaces belonging to the DMS module / quality_dms app,
	// including child workspaces (Folder Management, Compliance & Logs, …).
	function dms_workspace_slugs() {
		const pages =
			(frappe.boot && (frappe.boot.allowed_workspaces || frappe.boot.sidebar_pages?.pages)) || [];
		const slugs = new Set(["dms"]);
		for (const ws of pages) {
			const module = slug(ws.module);
			const app = slug(ws.app);
			const parent = slug(ws.parent_page);
			if (module === "dms" || app === "quality-dms" || app === "quality_dms" || parent === "dms" || slugs.has(parent)) {
				slugs.add(slug(ws.name));
				slugs.add(slug(ws.title));
			}
		}
		return slugs;
	}

	function is_dms_route() {
		const route = (frappe.get_route && frappe.get_route()) || [];
		if (!route.length) return false;
		const view = route[0];
		const target = route[1] || "";
		if (view === "Workspaces") return dms_workspace_slugs().has(slug(target));
		if (view === "query-report") return DMS_REPORTS.has(target);
		if (slug(view) === "module-onboarding") return slug(target) === "dms";
		// any view of a DMS doctype: List, Form, Tree, Report, Kanban,
		// Calendar, Dashboard, Image, print…
		if (DMS_DOCTYPES.has(target)) return true;
		return false;
	}

	function is_projects_route() {
		const route = (frappe.get_route && frappe.get_route()) || [];
		if (!route.length) return false;
		const view = route[0];
		const target = route[1] || "";
		if (view === "Workspaces") return slug(target) === "projects";
		if (view === "query-report") return PROJECT_REPORTS.has(target);
		// any view of a Projects doctype: List, Form, Kanban, Gantt, Report, …
		if (PROJECT_DOCTYPES.has(target)) return true;
		return false;
	}

	function apply() {
		document.body.classList.toggle("dms-theme", is_dms_route() || is_projects_route());
	}

	// Curated Document Library entry points (Repository, Workbench, the
	// "Published Documents" Key Metrics card) should land on a pre-scoped view
	// that reads as the default list for that purpose, not as "a filter someone
	// applied and could remove." Hides just the clear-all-filters (X) button --
	// scoped to when the ONLY active filter is exactly one of these curated
	// ones, so a user's own manual filtering elsewhere is completely unaffected.
	const LOCKED_FILTER_SIGNATURES = [
		{ fieldname: "is_in_progress", value: "1" },
		{ fieldname: "workflow_state", value: "Published" },
	];

	function apply_locked_filter_ui() {
		const route = (frappe.get_route && frappe.get_route()) || [];
		const is_doc_library_list = route[0] === "List" && route[1] === "Document Library";
		if (!is_doc_library_list) {
			document.body.classList.remove("dms-locked-filter");
			return;
		}
		setTimeout(() => {
			try {
				const filters = (cur_list && cur_list.filter_area && cur_list.filter_area.get()) || [];
				const locked =
					filters.length === 1 &&
					LOCKED_FILTER_SIGNATURES.some(
						(sig) => filters[0][1] === sig.fieldname && String(filters[0][3]) === sig.value
					);
				document.body.classList.toggle("dms-locked-filter", locked);
			} catch (e) {
				document.body.classList.remove("dms-locked-filter");
			}
		}, 400);
	}

	$(document).ready(function () {
		apply();
		apply_locked_filter_ui();
		if (frappe.router && frappe.router.on) {
			frappe.router.on("change", apply);
			frappe.router.on("change", apply_locked_filter_ui);
		} else {
			$(window).on("hashchange", apply);
			$(window).on("hashchange", apply_locked_filter_ui);
		}
	});

	// Key Metrics cards: each Number Card doctype record already has its own
	// `color` field (set in the fixture JSON) but the stock widget only uses
	// it to tint the number text, not the card itself. Mirror that same
	// color onto the card wrapper as a CSS variable so quality_dms.css can
	// render a colored bottom accent, matching the Project Summary tab's
	// per-status stat cards. Matched by label text (not by patching
	// NumberCardWidget, which is bundled internally and not reachable from
	// an app_include_js script) via a MutationObserver, since cards render
	// asynchronously after their data fetch completes.
	const CARD_ACCENTS = {
		Documents: "#4C7CF3",
		Published: "#36AE7C",
		Review: "#E8A317",
		Approved: "#26A69A",
		Draft: "#ECAD4B",
		Obsolete: "#CB4B4B",
		"Pending Revision": "#FF6B6B",
		Revisions: "#6C63FF",
	};

	function apply_card_accents(root) {
		root.querySelectorAll(".number-widget-box").forEach((el) => {
			if (el.style.getPropertyValue("--card-accent")) return;
			const title_el = el.querySelector(".widget-title [title], .widget-title .ellipsis");
			const label = title_el && (title_el.getAttribute("title") || title_el.textContent).trim();
			if (label && CARD_ACCENTS[label]) {
				el.style.setProperty("--card-accent", CARD_ACCENTS[label]);
			}
		});
	}

	// "Documents by Status" donut chart: recolor to match the Key Metrics
	// palette above. Frappe Charts renders each slice as an SVG <path
	// class="donut-path"> with its color in an inline `stroke` style, and
	// each legend entry as a <rect fill="..."> immediately followed by a
	// text node with the status label -- both in the same index order, but
	// that order isn't stable (ties on count reshuffle it), so match by the
	// legend's own label text rather than assuming position.
	const STATUS_COLORS = {
		Draft: "#F4A623",
		"Documents in Review": "#4C7CF3",
		Review: "#4C7CF3",
		Approved: "#2E9E6C",
		Published: "#6C5CE7",
		Obsolete: "#D64550",
		Archived: "#6C757D",
		Rejected: "#A8324F",
	};

	function apply_status_chart_colors(root) {
		root.querySelectorAll(".widget-head").forEach((head) => {
			if (!head.textContent.includes("Documents by Status")) return;
			const widget = head.closest(".widget");
			if (!widget) return;

			const paths = Array.from(widget.querySelectorAll("svg path.donut-path"));
			const rects = Array.from(widget.querySelectorAll("svg rect"));
			if (!paths.length || !rects.length) return;

			// No "already done" guard: frappe-charts redraws the SVG (fresh
			// nodes) at least once after the first paint (ResizeObserver-
			// driven), which would silently revert a one-time recolor. This
			// runs on every relevant mutation instead -- cheap for 5 slices,
			// and a no-op once colors already match.
			rects.forEach((rect, i) => {
				const label = rect.nextSibling && rect.nextSibling.textContent && rect.nextSibling.textContent.trim();
				const color = label && STATUS_COLORS[label];
				if (!color) return;
				if (rect.getAttribute("fill") !== color) rect.setAttribute("fill", color);
				const path = paths[i];
				if (path) {
					const style = (path.getAttribute("style") || "");
					if (!style.includes(`stroke: ${color};`)) {
						path.setAttribute("style", style.replace(/stroke:\s*[^;]+;?/, `stroke: ${color};`));
					}
				}
			});
		});
	}

	const card_observer = new MutationObserver((mutations) => {
		for (const m of mutations) {
			if (m.addedNodes.length) {
				apply_card_accents(document.body);
				apply_status_chart_colors(document.body);
			}
		}
	});
	card_observer.observe(document.body, { childList: true, subtree: true });
})();
