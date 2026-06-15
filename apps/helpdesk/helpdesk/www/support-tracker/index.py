import frappe
from frappe.sessions import get_csrf_token

no_cache = 1
login_required = 0
no_breadcrumbs = 1
no_header = 1
no_sidebar = 1
no_footer = 1


def get_context(context):
    # frappe.sessions.get_csrf_token() is Frappe's own API — it reads
    # frappe.local.session.data.csrf_token and auto-generates one if missing.
    # This is the exact value validate_csrf_token() checks on every POST.
    try:
        context.csrf_token = get_csrf_token()
    except Exception:
        context.csrf_token = ""
