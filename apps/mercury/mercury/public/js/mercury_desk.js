/* Mercury desk JS overrides.
 *
 * Loaded on every desk page via hooks.app_include_js. Additive only - we wrap
 * core functions instead of editing them, so removing the hook line reverts
 * everything. No frappe/erpnext file is patched.
 *
 * =========================================================================
 * PROTECTED - DO NOT DELETE OR "CLEAN UP" WHEN MERGING.
 * Full rationale + verification checklist: documents/PROJECT_UI_CHANGES.md
 * =========================================================================
 */

frappe.provide("mercury.breadcrumbs");

/* ------------------------------------------------------------------------
 * Breadcrumb destinations on desk list/form routes.
 *
 * Stock v16 builds three crumbs from three independent sources
 * (frappe/public/js/frappe/views/breadcrumbs.js):
 *
 *   1. home icon      clear() :278                 -> "/desk"
 *   2. workspace      set_workspace_breadcrumb() :136-141 -> the workspace
 *   3. doctype list   set_list_breadcrumb() :216   -> "/desk/<doctype>"
 *
 * Two problems on a Task form (/desk/task/TASK-2026-00007):
 *
 *   a. The home icon points at "/desk", which workspace.js:137-155 resolves to
 *      localStorage.current_page - the LAST WORKSPACE THE BROWSER VISITED. So it
 *      usually lands on the same page as crumb 2, and its destination is not
 *      stable across machines or browsers. On a fresh QA browser it falls back
 *      to this.workspaces[0], which is not Projects.
 *
 *   b. Crumb 2 ("Projects", the workspace) and crumb 3 ("Project"/"Task", the
 *      doctype) read as near-duplicates, and neither reaches the Project LIST
 *      from a Task form.
 *
 * Wanted instead:
 *      home icon  -> the module's workspace home  (stable, never "last visited")
 *      "Projects" -> the Project list
 *      "Task"     -> the Task list  (already correct in core, left alone)
 *
 * We do not re-implement the breadcrumbs: we let core build them, then rewrite
 * two hrefs. That way any upstream change to labels, translation, ordering or
 * the Custom-breadcrumb path keeps working.
 *
 * Keyed on the workspace ROUTE, not the visible label: the label is passed
 * through __() so it changes under a non-English locale, and the map would
 * silently stop matching.
 * ------------------------------------------------------------------------ */

// workspace route  ->  where its breadcrumb crumb should actually go.
// Add an entry per module that wants its crumb to reach a list instead of the
// workspace. No entry = stock behaviour (crumb keeps pointing at the workspace).
mercury.breadcrumbs.CRUMB_TARGETS = {
	"/desk/projects": "/desk/project",
};

mercury.breadcrumbs.retarget = function () {
	// NOTE: "worksapce-breadcrumb" is misspelled in frappe core
	// (breadcrumbs.js:140). Do NOT "correct" it here or the selector misses.
	$(".navbar-breadcrumbs").each(function () {
		const $container = $(this);
		const $workspace_crumb = $container.find("li a.worksapce-breadcrumb");

		// No workspace crumb: a Custom-breadcrumb page (breadcrumbs.js:56), or a
		// doctype whose module is blocked/hidden. Leave it entirely alone.
		if (!$workspace_crumb.length) return;

		const workspace_route = $workspace_crumb.attr("href");
		if (!workspace_route) return;

		// 1. Home icon -> the module workspace, instead of the stateful "/desk".
		//    The home icon is always the first <li> (appended by clear() :278).
		const $home = $container.find("li").first().find("a");
		if ($home.length && $home.attr("href") === "/desk") {
			$home.attr("href", workspace_route);
		}

		// 2. Workspace crumb -> the module's list page, where one is mapped.
		const target = mercury.breadcrumbs.CRUMB_TARGETS[workspace_route];
		if (target) {
			$workspace_crumb.attr("href", target);
		}
	});
};

// Wrap rather than replace: core owns the building, we only adjust the result.
// update() runs on every route change and after rename(), so this stays applied.
(function () {
	if (!frappe.breadcrumbs || frappe.breadcrumbs.__mercury_wrapped) return;

	const core_update = frappe.breadcrumbs.update;
	frappe.breadcrumbs.update = function () {
		core_update.apply(this, arguments);
		try {
			mercury.breadcrumbs.retarget();
		} catch (e) {
			// Never let a breadcrumb tweak break navigation.
			console.error("mercury: breadcrumb retarget failed", e);
		}
	};
	frappe.breadcrumbs.__mercury_wrapped = true;
})();
