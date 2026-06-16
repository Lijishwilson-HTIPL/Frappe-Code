"""
seeder.py — Seed a newly provisioned tenant site with defaults.
"""

import json
import os
import shutil
import subprocess

import frappe


def _bench_bin():
    """Return absolute path to bench binary (works when ~/.local/bin is absent from PATH)."""
    found = shutil.which("bench")
    if found:
        return found
    import pwd
    try:
        real_home = pwd.getpwuid(os.getuid()).pw_dir
    except Exception:
        real_home = os.path.expanduser("~")
    candidates = [
        os.path.join(real_home, ".local", "bin", "bench"),
        "/usr/local/bin/bench",
        os.path.join(frappe.utils.get_bench_path(), "env", "bin", "bench"),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return "bench"


def seed_tenant(site_name, client_name, plan="Starter", currency="INR", timezone="Asia/Kolkata", admin_email=None):
    bench_path = frappe.utils.get_bench_path()
    bench_cmd = _bench_bin()

    setup_data = {
        "app_name": client_name,
        "company_name": client_name,
        "company_abbr": _abbreviate(client_name),
        "currency": currency,
        "timezone": timezone,
        "country": "India",
    }

    for key, val in setup_data.items():
        _run(
            [bench_cmd, "--site", site_name, "set-config", key, str(val)],
            cwd=bench_path,
        )

    _set_site_branding(site_name, client_name, bench_path)

    if admin_email:
        _create_admin_user(site_name, admin_email, bench_path)


def _create_admin_user(site_name, admin_email, bench_path):
    import json as _json
    safe_site = _json.dumps(site_name)
    safe_email = _json.dumps(admin_email)
    script = (
        "import frappe;"
        f"frappe.init(site={safe_site});"
        "frappe.connect();"
        f"em={safe_email};"
        "u=frappe.db.exists('User',em);"
        "( None if u else ("
        "  frappe.get_doc({"
        "    'doctype':'User','email':em,'first_name':'Admin',"
        "    'send_welcome_email':0,'user_type':'System User'"
        "  }).insert(ignore_permissions=True),"
        f"  frappe.get_doc('User',em).add_roles('System Manager')"
        ") );"
        "frappe.db.commit();frappe.destroy()"
    )
    python = os.path.join(bench_path, "env", "bin", "python")
    _run(
        [python, "-c", script],
        cwd=os.path.join(bench_path, "sites"),
    )


def _set_site_branding(site_name, client_name, bench_path):
    """Set Website Settings and System Settings branding fields on the tenant site."""
    safe_name = json.dumps(client_name)
    safe_site = json.dumps(site_name)
    script = (
        "import frappe;"
        f"frappe.init(site={safe_site});"
        "frappe.connect();"
        f"frappe.db.set_single_value('Website Settings','app_name',{safe_name});"
        f"frappe.db.set_single_value('System Settings','app_name',{safe_name});"
        f"frappe.db.set_single_value('System Settings','system_name',{safe_name});"
        "frappe.db.commit();"
        "frappe.destroy()"
    )
    python = os.path.join(bench_path, "env", "bin", "python")
    _run(
        [python, "-c", script],
        cwd=os.path.join(bench_path, "sites"),
    )


def _abbreviate(name):
    words = name.strip().split()
    if len(words) >= 2:
        return "".join(w[0].upper() for w in words[:3])
    return name[:4].upper()


def _run(argv, cwd=None):
    try:
        result = subprocess.run(
            argv, cwd=cwd,
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        # `from None` suppresses chaining so TimeoutExpired (which embeds the full
        # argv) never appears in traceback.format_exc(). argv carries no credentials
        # here today, but keep the guard symmetric with engine._run.
        raise RuntimeError(
            f"Command timed out after 120s: {' '.join(argv)}"
        ) from None
    if result.returncode != 0:
        # Redact inline script arguments (-c ...) to prevent PII leaking into error logs
        _redacted = []
        _skip_next = False
        for _a in argv:
            if _skip_next:
                _redacted.append("[script redacted]")
                _skip_next = False
            elif _a == "-c":
                _redacted.append(_a)
                _skip_next = True
            else:
                _redacted.append(_a)
        cmd_display = " ".join(_redacted)
        raise RuntimeError(
            f"Command failed: {cmd_display}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout
