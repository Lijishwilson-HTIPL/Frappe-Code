// posthog stub for helpdesk compatibility with frappe v16
// posthog was removed from frappe v16 public lib; this no-op prevents build failures
(function () {
	if (typeof window !== "undefined" && !window.posthog) {
		window.posthog = {
			init: function () {},
			identify: function () {},
			capture: function () {},
			reset: function () {},
			opt_out_capturing: function () {},
			opt_in_capturing: function () {},
			has_opted_out_capturing: function () { return true; },
		};
	}
})();
