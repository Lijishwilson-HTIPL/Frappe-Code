"""
engine.py — Multi-tenant provisioning engine for SBIQ.

Environment-aware: reads `is_production` from frappe.conf (default False).
- Local mode: creates site, installs apps, updates /etc/hosts
- Production mode: creates site, installs apps, writes Nginx conf (stubbed)
"""

import subprocess
import traceback
from datetime import datetime

import frappe
from frappe import _

from sbiqc_provisioning.provisioner.seeder import seed_tenant
from sbiqc_provisioning.sbiqc_provisioning.doctype.provisioning_log.provisioning_log import (
	complete_log,
	create_log,
	update_log_step,
)


def provision_tenant(tenant_name):
	"""Main entry point — called by the background job queue."""
	frappe.init(site=frappe.local.site)
	frappe.connect()

	tenant = frappe.get_doc("Tenant", tenant_name)
	bench_path = frappe.utils.get_bench_path()
	is_production = frappe.conf.get("is_production", False)
	site_name = tenant.site_name
	db_root_password = frappe.conf.get("db_root_password", "root")
	admin_password = frappe.conf.get("tenant_admin_password", "Admin@123")

	log_name = create_log(tenant_name, site_name)

	try:
		_update_status(tenant, "Provisioning")
		update_log_step(log_name, "Initializing", 5)

		# Step 1: Create the new site (skip if it already exists)
		import os
		site_path = os.path.join(bench_path, "sites", site_name)
		if os.path.isdir(site_path):
			update_log_step(log_name, f"Site {site_name} already exists — reusing", 25)
		else:
			update_log_step(log_name, "Creating site: " + site_name, 10)
			_run(
				[
					"bench", "new-site", site_name,
					"--mariadb-root-password", db_root_password,
					"--admin-password", admin_password,
				],
				cwd=bench_path,
				timeout=600,
			)
			update_log_step(log_name, "Site created", 25)
		frappe.publish_progress(25, title=_("Provisioning {0}").format(site_name))

		# Step 2: Install apps — skip already-installed, erpnext first
		app_names = [row.app_name for row in tenant.apps_to_install]
		if "erpnext" in app_names:
			app_names.remove("erpnext")
		install_order = ["erpnext"] + sorted(app_names)

		_clear_stale_locks(site_name, bench_path)
		already_installed = _get_installed_apps(site_name, bench_path)
		to_install = [a for a in install_order if a not in already_installed]

		if not to_install:
			update_log_step(log_name, "All apps already installed", 65)
		else:
			for i, app in enumerate(to_install):
				update_log_step(log_name, f"Installing {app}", 25 + int((i + 1) / len(to_install) * 40))
				_install_app(site_name, app, bench_path)
				pct = 25 + int((i + 1) / len(to_install) * 40)
				frappe.publish_progress(pct, title=_("Installing {0}").format(app))
			update_log_step(log_name, "All apps installed", 65)

		# Step 3: Seed company defaults
		update_log_step(log_name, "Seeding company defaults", 70)
		seed_tenant(
			site_name=site_name,
			client_name=tenant.client_name,
			plan=tenant.plan,
			currency=getattr(tenant, "currency", "INR") or "INR",
			timezone=getattr(tenant, "timezone", "Asia/Kolkata") or "Asia/Kolkata",
			admin_email=getattr(tenant, "admin_email", None) or None,
		)
		frappe.publish_progress(75, title=_("Seeding defaults"))
		update_log_step(log_name, "Defaults configured", 75)

		# Step 4: Routing — environment switch
		update_log_step(log_name, "Configuring routing", 80)
		if is_production:
			_setup_production_routing(site_name)
		else:
			_setup_local_routing(site_name)
		frappe.publish_progress(90, title=_("Configuring routing"))
		update_log_step(log_name, "Routing configured", 90)

		# Step 5: Clear cache
		update_log_step(log_name, "Clearing cache", 95)
		_run(["bench", "--site", site_name, "clear-cache"], cwd=bench_path)

		# Step 6: Mark active
		_update_status(tenant, "Active")
		tenant.reload()
		tenant.db_set("provisioned_at", datetime.now())
		frappe.db.commit()

		# Step 7: Send welcome email (non-blocking)
		_send_welcome_email(tenant)

		frappe.publish_progress(100, title=_("Done"))
		complete_log(log_name)

	except Exception:
		tb = traceback.format_exc()
		_update_status(tenant, "Error")
		tenant.reload()
		tenant.db_set("error_log", tb[:10000])
		frappe.db.commit()
		frappe.log_error(
			title=f"Tenant provisioning failed: {tenant_name}",
			message=tb,
		)
		complete_log(log_name, failed=True, error=tb)
		raise


def _update_status(tenant, status):
	tenant.reload()
	tenant.db_set("status", status)
	frappe.db.commit()


def _send_welcome_email(tenant):
	"""Send a welcome email to the tenant admin after successful provisioning.
	Email failure never raises — provisioning is already complete at this point.
	"""
	if not getattr(tenant, "admin_email", None):
		return

	try:
		is_production = frappe.conf.get("is_production", False)
		port = "" if is_production else ":8000"
		site_url = f"http://{tenant.site_name}{port}"

		subject = f"Your SBIQ instance is ready — {tenant.client_name}"

		message = f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#1f2937;">
  <div style="background:#6366f1;padding:28px 32px;border-radius:8px 8px 0 0;">
    <h1 style="color:#fff;font-size:22px;margin:0;">Welcome to SBIQ, {tenant.client_name}!</h1>
    <p style="color:#e0e7ff;margin:8px 0 0;font-size:14px;">Your Frappe ERP instance is live and ready to use.</p>
  </div>
  <div style="background:#f9fafb;padding:28px 32px;border:1px solid #e5e7eb;border-top:0;">
    <h2 style="font-size:16px;color:#374151;margin:0 0 16px;">Your login details</h2>
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <tr>
        <td style="padding:8px 0;color:#6b7280;width:140px;">Site URL</td>
        <td style="padding:8px 0;"><a href="{site_url}" style="color:#6366f1;font-weight:600;">{site_url}</a></td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6b7280;">Login Email</td>
        <td style="padding:8px 0;font-weight:600;">{tenant.admin_email}</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#6b7280;">Plan</td>
        <td style="padding:8px 0;">{tenant.plan or "Standard"}</td>
      </tr>
    </table>
    <div style="margin:20px 0;padding:14px 16px;background:#ede9fe;border-radius:6px;font-size:13px;color:#4c1d95;">
      <strong>First time logging in?</strong><br/>
      Use the default password: <code>Admin@123</code><br/>
      We recommend changing it immediately from <em>Settings &rarr; My Profile</em>.
    </div>
    <h2 style="font-size:16px;color:#374151;margin:20px 0 10px;">Getting started</h2>
    <ol style="font-size:14px;color:#374151;line-height:1.8;padding-left:18px;margin:0;">
      <li>Log in at the site URL above</li>
      <li>Complete the <strong>Setup Wizard</strong> to configure your company</li>
      <li>Invite your team members from <em>Settings &rarr; Users</em></li>
    </ol>
    <div style="margin-top:28px;padding-top:20px;border-top:1px solid #e5e7eb;font-size:12px;color:#9ca3af;text-align:center;">
      Powered by <strong>SBIQ</strong> &middot; Frappe v15<br/>
      This email was sent automatically after your instance was provisioned.
    </div>
  </div>
</div>
"""

		frappe.sendmail(
			recipients=[tenant.admin_email],
			subject=subject,
			message=message,
			now=True,
		)
		frappe.logger().info(f"Welcome email sent to {tenant.admin_email} for tenant {tenant.name}")

	except Exception:
		frappe.logger().warning(
			f"Welcome email failed for tenant {tenant.name}: {frappe.get_traceback()}"
		)


# Argv flags whose following value must never appear in error messages or logs.
SENSITIVE_FLAGS = ("--mariadb-root-password", "--admin-password")


def _redact_argv(argv):
	"""Return a display string for argv with values of sensitive flags redacted."""
	redacted = []
	redact_next = False
	for arg in argv:
		if redact_next:
			redacted.append("[REDACTED]")
			redact_next = False
		else:
			redacted.append(arg)
			if arg in SENSITIVE_FLAGS:
				redact_next = True
	return " ".join(redacted)


def _run(argv, cwd=None, timeout=120):
	try:
		result = subprocess.run(
			argv, cwd=cwd,
			capture_output=True, text=True, timeout=timeout,
		)
	except subprocess.TimeoutExpired:
		# `from None` suppresses exception chaining: str(TimeoutExpired) embeds the
		# raw argv (including passwords), and a chained __context__/__cause__ would
		# still surface it in traceback.format_exc(). Only the redacted command may leak.
		raise RuntimeError(
			f"Command timed out after {timeout}s: {_redact_argv(argv)}"
		) from None
	if result.returncode != 0:
		raise RuntimeError(
			f"Command failed (exit {result.returncode}): {_redact_argv(argv)}\n"
			f"stdout: {result.stdout[-2000:]}\n"
			f"stderr: {result.stderr[-2000:]}"
		)
	return result.stdout


def _get_installed_apps(site_name, bench_path):
	"""Return set of apps already installed on a site."""
	result = subprocess.run(
		["bench", "--site", site_name, "list-apps"],
		cwd=bench_path,
		capture_output=True, text=True, timeout=30,
	)
	if result.returncode != 0:
		return set()
	return {line.strip() for line in result.stdout.strip().splitlines() if line.strip()}


def _clear_stale_locks(site_name, bench_path):
	"""Remove stale install_app.lock left by a crashed prior run."""
	import os
	lock_dir = os.path.join(bench_path, "sites", site_name, "locks")
	if not os.path.isdir(lock_dir):
		return
	lock_file = os.path.join(lock_dir, "install_app.lock")
	if os.path.exists(lock_file):
		os.remove(lock_file)


def _install_app(site_name, app, bench_path):
	"""Install an app on a site. Tolerates non-zero exit if the app ends up installed."""
	result = subprocess.run(
		["bench", "--site", site_name, "install-app", app],
		cwd=bench_path,
		capture_output=True, text=True, timeout=300,
	)
	if result.returncode != 0:
		verify = subprocess.run(
			["bench", "--site", site_name, "list-apps"],
			cwd=bench_path,
			capture_output=True, text=True, timeout=30,
		)
		if app in verify.stdout:
			return
		raise RuntimeError(
			f"Failed to install {app} on {site_name} (exit {result.returncode}):\n"
			f"stderr: {result.stderr[-2000:]}"
		)


def _setup_local_routing(site_name):
	"""Idempotently add 127.0.0.1 entry to both WSL /etc/hosts and Windows hosts file."""
	hosts_entry = f"127.0.0.1   {site_name}"

	# --- WSL /etc/hosts ---
	with open("/etc/hosts", "r") as f:
		content = f.read()

	if hosts_entry not in content:
		sudo_password = frappe.conf.get("sudo_password", "")
		result = subprocess.run(
			["sudo", "-S", "bash", "-c", f"echo '{hosts_entry}' >> /etc/hosts"],
			input=(sudo_password + "\n").encode(),
			shell=False,
			capture_output=True,
			text=False,
			timeout=30,
		)
		result_stderr = result.stderr.decode(errors="replace") if result.stderr else ""
		result_returncode = result.returncode
		if result_returncode != 0:
			frappe.log_error(
				title=f"Failed to update WSL /etc/hosts for {site_name}",
				message=result_stderr,
			)
			raise RuntimeError(f"Could not update WSL /etc/hosts: {result_stderr}")

	# --- Windows hosts file (for browser access) ---
	_update_windows_hosts(site_name)


def _update_windows_hosts(site_name):
	"""Idempotently add 127.0.0.1 entry to the Windows hosts file (WSL only)."""
	win_hosts = "/mnt/c/Windows/System32/drivers/etc/hosts"

	try:
		with open(win_hosts, "r") as f:
			content = f.read()
	except FileNotFoundError:
		return

	hosts_entry = f"127.0.0.1   {site_name}"
	if hosts_entry in content:
		return

	try:
		with open(win_hosts, "a") as f:
			f.write(f"\n{hosts_entry}\n")
	except PermissionError:
		frappe.log_error(
			title=f"Cannot write Windows hosts for {site_name}",
			message=(
				f"Permission denied on {win_hosts}. "
				f"Run in PowerShell as admin: icacls \"C:\\Windows\\System32\\drivers\\etc\\hosts\" /grant \"$USER:(M)\""
			),
		)
		frappe.msgprint(
			f"Could not auto-update Windows hosts file for {site_name}. "
			f"Please manually add '{hosts_entry}' to C:\\Windows\\System32\\drivers\\etc\\hosts",
			alert=True,
		)


def _setup_production_routing(site_name):
	"""
	Stub for production Nginx routing.
	Will write Nginx server block, run nginx -t, then reload.
	Not wired up yet — local dev only for now.
	"""
	pass


def provision_update(tenant_name, apps_to_add):
	"""Install additional apps on an already-Active tenant site."""
	frappe.init(site=frappe.local.site)
	frappe.connect()

	tenant = frappe.get_doc("Tenant", tenant_name)
	bench_path = frappe.utils.get_bench_path()
	site_name = tenant.site_name

	log_name = create_log(tenant_name, site_name)

	try:
		_update_status(tenant, "Provisioning")
		update_log_step(log_name, "Starting app update", 5)
		_clear_stale_locks(site_name, bench_path)
		already_installed = _get_installed_apps(site_name, bench_path)
		to_install = [a for a in apps_to_add if a not in already_installed]
		to_install = list(dict.fromkeys(to_install))  # preserve order, remove dupes

		if not to_install:
			update_log_step(log_name, "All requested apps already installed", 80)
		else:
			for i, app in enumerate(to_install):
				pct = 10 + int((i + 1) / len(to_install) * 60)
				update_log_step(log_name, f"Installing {app}", pct)
				_install_app(site_name, app, bench_path)

		update_log_step(log_name, "Running migrations", 80)
		_run(["bench", "--site", site_name, "migrate"], cwd=bench_path, timeout=300)

		update_log_step(log_name, "Clearing cache", 92)
		_run(["bench", "--site", site_name, "clear-cache"], cwd=bench_path)

		# Append new apps to Tenant.apps_to_install child table
		tenant.reload()
		existing_apps = {row.app_name for row in tenant.apps_to_install}
		for app in to_install:
			if app not in existing_apps:
				tenant.append("apps_to_install", {"app_name": app})
		if to_install:
			tenant.save(ignore_permissions=True)  # background worker has no session user context
		frappe.db.commit()

		_update_status(tenant, "Active")
		complete_log(log_name)

	except Exception:
		tb = traceback.format_exc()
		_update_status(tenant, "Error")
		tenant.reload()
		tenant.db_set("error_log", tb[:10000])
		frappe.db.commit()
		frappe.log_error(title=f"App update failed: {tenant_name}", message=tb)
		complete_log(log_name, failed=True, error=tb)
		raise
