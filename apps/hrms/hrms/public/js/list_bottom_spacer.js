// list_bottom_spacer.js — global fix for all Frappe list views
// Frappe's set_result_height() sets max-height inline via jQuery, clipping the last row
// right at the bottom edge with no breathing room. This override adds 60px to every
// list result so the last row is always fully visible and clickable.
frappe.after_ajax(function () {
	if (
		frappe.views &&
		frappe.views.ListView &&
		frappe.views.ListView.prototype &&
		typeof frappe.views.ListView.prototype.set_result_height === "function"
	) {
		const _orig = frappe.views.ListView.prototype.set_result_height;
		frappe.views.ListView.prototype.set_result_height = function () {
			_orig.apply(this, arguments);
			if (this.$result) {
				const cur = parseInt(this.$result.css("max-height")) || 0;
				if (cur > 0) this.$result.css("max-height", (cur + 60) + "px");
			}
		};
	}
});
