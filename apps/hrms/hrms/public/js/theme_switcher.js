frappe.provide("hrms.theme");

hrms.theme.themes = ["uichange1", "uichange2", "uichange3", "uichange4"];
hrms.theme.labels = {
	uichange1: "Theme 1",
	uichange2: "Theme 2",
	uichange3: "Theme 3",
	uichange4: "Theme 4",
};
hrms.theme.storage_key = "hrms_ui_theme";

hrms.theme.get_current = function () {
	return localStorage.getItem(hrms.theme.storage_key) || "uichange1";
};

hrms.theme.apply = function (theme) {
	if (!hrms.theme.themes.includes(theme)) return;
	let link = document.getElementById("hrms-theme-override");
	if (!link) {
		link = document.createElement("link");
		link.rel = "stylesheet";
		link.id = "hrms-theme-override";
		document.head.appendChild(link);
	}
	link.href = `/assets/hrms/css/${theme}.css?v=${Date.now()}`;
	localStorage.setItem(hrms.theme.storage_key, theme);
	document.documentElement.setAttribute("data-hrms-theme", theme);
};

hrms.theme.show_picker = function () {
	const current = hrms.theme.get_current();
	const d = new frappe.ui.Dialog({
		title: __("Switch Theme"),
		fields: [
			{
				fieldname: "theme",
				fieldtype: "Select",
				label: __("Theme"),
				options: hrms.theme.themes.map((t) => ({
					label: hrms.theme.labels[t],
					value: t,
				})),
				default: current,
			},
		],
		primary_action_label: __("Apply"),
		primary_action(values) {
			hrms.theme.apply(values.theme);
			frappe.show_alert({
				message: __("Theme switched to {0}", [hrms.theme.labels[values.theme]]),
				indicator: "green",
			});
			d.hide();
		},
	});
	d.show();
};

hrms.theme.add_button = function () {
	if (document.getElementById("hrms-theme-switcher")) return true;
	const navbar =
		document.querySelector(".navbar .navbar-nav.navbar-right") ||
		document.querySelector(".navbar .navbar-nav.ml-auto") ||
		document.querySelector(".navbar .navbar-nav");
	if (!navbar) return false;

	const li = document.createElement("li");
	li.className = "nav-item";
	li.id = "hrms-theme-switcher";
	li.innerHTML = `
		<a class="nav-link" href="#" title="${frappe.utils.escape_html(__("Switch Theme"))}" style="display:flex;align-items:center;gap:4px;">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="10.5" r="2.5"/><circle cx="8.5" cy="7.5" r="2.5"/><circle cx="6.5" cy="12.5" r="2.5"/><path d="M12 2a10 10 0 1 0 0 20 1.5 1.5 0 0 0 1.06-2.56 1.5 1.5 0 0 1 1.06-2.56H16a6 6 0 0 0 6-6c0-5.52-4.48-10-10-10z"/></svg>
			<span>${frappe.utils.escape_html(__("Theme"))}</span>
		</a>
	`;
	navbar.prepend(li);
	li.querySelector("a").addEventListener("click", (e) => {
		e.preventDefault();
		hrms.theme.show_picker();
	});
	return true;
};

$(document).ready(() => {
	hrms.theme.apply(hrms.theme.get_current());
	let attempts = 0;
	const tryAdd = () => {
		if (hrms.theme.add_button()) return;
		if (++attempts < 30) setTimeout(tryAdd, 400);
	};
	tryAdd();
});
