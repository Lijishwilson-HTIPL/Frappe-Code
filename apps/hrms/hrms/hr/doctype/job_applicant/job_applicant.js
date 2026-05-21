// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// For license information, please see license.txt

// for communication
cur_frm.email_field = "email_id";

frappe.ui.form.on("Job Applicant", {
	refresh: function (frm) {
		frm.set_query("job_title", function () {
			return {
				filters: {
					status: "Open",
				},
			};
		});
		frm.events.create_custom_buttons(frm);
		frm.events.make_dashboard(frm);
	},

	create_custom_buttons: function (frm) {
		if (!frm.doc.__islocal && frm.doc.status !== "Rejected" && frm.doc.status !== "Accepted") {
			frm.add_custom_button(
				__("Interview"),
				function () {
					frm.events.create_dialog(frm);
				},
				__("Create"),
			);
		}

		if (!frm.doc.__islocal && frm.doc.status == "Accepted") {
			if (frm.doc.__onload && frm.doc.__onload.job_offer) {
				$('[data-doctype="Employee Onboarding"]').find("button").show();
				$('[data-doctype="Job Offer"]').find("button").hide();
				frm.add_custom_button(
					__("Job Offer"),
					function () {
						frappe.set_route("Form", "Job Offer", frm.doc.__onload.job_offer);
					},
					__("View"),
				);
			} else {
				$('[data-doctype="Employee Onboarding"]').find("button").hide();
				$('[data-doctype="Job Offer"]').find("button").show();
				frm.add_custom_button(
					__("Job Offer"),
					function () {
						frappe.route_options = {
							job_applicant: frm.doc.name,
							applicant_name: frm.doc.applicant_name,
							designation: frm.doc.job_opening || frm.doc.designation,
						};
						frappe.new_doc("Job Offer");
					},
					__("Create"),
				);
			}
		}
	},

	make_dashboard: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.job_applicant.job_applicant.get_interview_details",
			args: {
				job_applicant: frm.doc.name,
			},
			callback: function (r) {
				if (r.message) {
					$("div").remove(".form-dashboard-section.custom");
					frm.dashboard.add_section(
						frappe.render_template("job_applicant_dashboard", {
							data: r.message.interviews,
							number_of_stars: r.message.stars,
						}),
						__("Interview Summary"),
					);

					const interview_map = r.message.interviews || {};
					const interview_list = Array.isArray(interview_map)
						? interview_map
						: Object.values(interview_map);
					const has_cleared = interview_list.some(
						(i) => (i && i.status ? String(i.status).toLowerCase() : "") === "cleared",
					);
					if (has_cleared) {
						setTimeout(() => frm.events.add_interview_email_button(frm), 50);
					}
				}
			},
		});
	},

	add_interview_email_button: function (frm) {
		const target = $(".form-dashboard-section.custom").filter(function () {
			return $(this).text().toLowerCase().includes("interview summary");
		}).last();
		const $section = target.length ? target : $(".form-dashboard-section.custom").last();
		if (!$section.length || $section.find(".btn-email-applicant").length) return;

		const $btn = $(
			`<button class="btn btn-primary btn-sm btn-email-applicant" style="position:absolute;top:6px;right:16px;z-index:5;">
				<svg style="width:12px;height:12px;vertical-align:-1px;margin-right:4px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
				${__("Email Applicant")}
			</button>`,
		);
		$btn.on("click", () => frm.events.choose_email_template(frm));

		$section.css("position", "relative");
		$section.prepend($btn);

		// Also add a top-toolbar button as a reliable backup
		if (!frm.custom_buttons[__("Email Applicant")]) {
			frm.add_custom_button(__("Email Applicant"), () =>
				frm.events.choose_email_template(frm),
			).addClass("btn-primary");
		}
	},

	choose_email_template: function (frm) {
		if (!frm.doc.email_id) {
			frappe.msgprint(__("Applicant has no email address on file."));
			return;
		}
		const d = new frappe.ui.Dialog({
			title: __("Choose Email Template"),
			fields: [
				{
					label: __("Email Template"),
					fieldname: "email_template",
					fieldtype: "Link",
					options: "Email Template",
					reqd: 1,
					description: __("Pick a template to pre-fill the email."),
				},
			],
			primary_action_label: __("Continue"),
			primary_action(values) {
				d.hide();
				frm.events.open_email_composer(frm, values.email_template);
			},
			secondary_action_label: __("Skip & Compose Blank"),
			secondary_action() {
				d.hide();
				frm.events.open_email_composer(frm, null);
			},
		});
		d.show();
	},

	open_email_composer: function (frm, template_name) {
		const launch = (subject, content) => {
			new frappe.views.CommunicationComposer({
				doc: frm.doc,
				frm: frm,
				subject: subject || __("Regarding your application — {0}", [frm.doc.applicant_name || ""]),
				recipients: frm.doc.email_id,
				content: content || "",
				attach_document_print: false,
			});
		};
		if (!template_name) return launch();
		frappe.db.get_doc("Email Template", template_name).then((tpl) => {
			launch(tpl.subject, tpl.response_html || tpl.response || "");
		});
	},

	create_dialog: function (frm) {
		let d = new frappe.ui.Dialog({
			title: "Enter Interview Round",
			fields: [
				{
					label: "Interview Round",
					fieldname: "interview_round",
					fieldtype: "Link",
					options: "Interview Round",
				},
			],
			primary_action_label: __("Create Interview"),
			primary_action(values) {
				frm.events.create_interview(frm, values);
				d.hide();
			},
		});
		d.show();
	},

	create_interview: function (frm, values) {
		frappe.call({
			method: "hrms.hr.doctype.job_applicant.job_applicant.create_interview",
			args: {
				doc: frm.doc,
				interview_round: values.interview_round,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},
});
