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

	$(document).ready(function () {
		apply();
		if (frappe.router && frappe.router.on) {
			frappe.router.on("change", apply);
		} else {
			$(window).on("hashchange", apply);
		}
	});
})();
