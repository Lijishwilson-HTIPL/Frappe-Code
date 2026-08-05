# Visual-only override of the login page (see www/login.html in this app).
# Frappe pairs a www template with a same-named .py in the *same* app/folder
# for its context -- reuse the core logic unchanged instead of duplicating it,
# so behavior (redirects, social login, LDAP, etc.) never drifts from core.
from frappe.www.login import get_context  # noqa: F401

# `set_pymodule_properties` reads module-level attrs like this one directly
# off *this* module, not the one get_context came from -- must be repeated.
no_cache = True
