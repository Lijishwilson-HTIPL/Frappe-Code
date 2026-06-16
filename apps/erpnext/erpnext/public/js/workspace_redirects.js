// Direct sidebar navigation: child workspace pages redirect immediately to their target
(function () {
	'use strict';

	var REDIRECTS = {
		'Tasks': function () { frappe.set_route('List', 'Task'); },
		'Project List': function () { frappe.set_route('List', 'Project'); },
		'Assignment Board': function () { frappe.set_route('task-assignment-board'); },
		'Task Summary Report': function () { frappe.set_route('query-report', 'Task Summary Report'); },
	};

	$(document).on('page-change', function () {
		var route = frappe.get_route();
		if (!route || !route.length) return;

		// Frappe v14: route is ['WorkspaceName'] or ['Workspaces', 'WorkspaceName']
		var name = (route[0] === 'Workspaces' && route[1]) ? route[1] : route[0];
		if (REDIRECTS[name]) {
			REDIRECTS[name]();
		}
	});
})();
