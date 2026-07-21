import frappe

def trace_insert():
    frappe.set_user("creator@example.com")
    doc = frappe.new_doc("Quality Document")
    doc.title = "Test Create"
    doc.department = "Accounts - HT"
    doc.category = "Policy"
    doc.type = "Finance"
    
    print("Does doc have create perm?")
    print(doc.has_permission("create"))
    
    print("Why does it fail?")
    doctype = doc.doctype
    ptype = "create"
    user = frappe.session.user
    
    # 1. Check global create
    global_create = frappe.has_permission(doctype, "create", user=user)
    print(f"Global create: {global_create}")
    
    if global_create:
        print("Tracing frappe.has_permission with doc:")
        # 2. Check get_doc_permissions
        from frappe.permissions import get_doc_permissions
        perms = get_doc_permissions(doc, user=user, ptype=ptype)
        print(f"get_doc_permissions: {perms}")
        
    try:
        doc.insert()
        print("Inserted successfully!")
    except Exception as e:
        print(f"Insert failed: {e}")

trace_insert()
