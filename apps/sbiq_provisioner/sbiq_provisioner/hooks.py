app_name = "sbiq_provisioner"
app_title = "SBIQC Provisioner"
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
		"name": "sbiq_provisioner",
		"logo": "/assets/sbiq_provisioner/images/provisioner-icon.svg",
		"title": "SBIQC Provisioner",
		"route": "/app/sbiqc-provisioning",
	}
]

# ── Desk Asset Includes ──
app_include_css = ["/assets/sbiq_provisioner/css/sbiq_provisioner.css"]
