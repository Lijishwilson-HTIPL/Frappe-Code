import frappe

def test_perms():
    frappe.set_user("creator@example.com")
    doc = frappe.new_doc("Quality Document")
    doc.title = "Test"
    doc.department = "Accounts - HT"
    
    from frappe.permissions import get_doc_permissions, get_role_permissions
    
    perms = get_doc_permissions(doc, frappe.session.user, "create")
    print(f"get_doc_permissions result: {perms}")
    
    role_perms = get_role_permissions(doc.meta, frappe.session.user)
    print(f"role_perms inside get_doc_permissions logic: {role_perms}")

test_perms()
