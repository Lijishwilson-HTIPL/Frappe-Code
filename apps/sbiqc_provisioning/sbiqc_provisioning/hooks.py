app_name = "sbiqc_provisioning"
app_title = "SBIQC Provisioning"
app_publisher = "https://hephzibahtech.com"
app_description = "Multi-tenant SaaS provisioning engine"
app_email = "lijish.wilson@hephzibahtech.com"
app_license = "mit"

# ── Apps Drawer Registration ──
# Route points to /app/sbiqc-provisioning (our custom Page).
# The slug "sbiqc-provisioning" does NOT match the workspace slug "sbiq-provisioner",
# so Frappe's router falls through to the Page DocType.
add_to_apps_screen = [
	{
		"name": "sbiqc_provisioning",
		"logo": "/assets/sbiqc_provisioning/images/provisioner-icon.svg",
		"title": "SBIQC Provisioning",
		"route": "/app/sbiqc-provisioning",
	}
]

# ── Desk Asset Includes ──
app_include_css = ["/assets/sbiqc_provisioning/css/sbiqc_provisioning.css"]
