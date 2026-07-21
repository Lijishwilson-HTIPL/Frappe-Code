import frappe

def check_home():
    w = frappe.get_doc("Workspace", "Home")
    print(f"Home: type={getattr(w, 'type', 'N/A')}, module={w.module}, app={w.app}, hidden={w.is_hidden}, public={w.public}, parent={w.parent_page}, roles={[r.role for r in w.roles]}")

    q = frappe.get_doc("Workspace", "Quality DMS")
    print(f"Quality DMS: type={getattr(q, 'type', 'N/A')}, module={q.module}, app={q.app}, hidden={q.is_hidden}, public={q.public}, parent={q.parent_page}, roles={[r.role for r in q.roles]}")
    
    # Try adding Administrator to roles just in case
    if not any(r.role == "System Manager" for r in q.roles):
        q.append("roles", {"role": "System Manager"})
        q.save(ignore_permissions=True)
        frappe.db.commit()
        print("Added System Manager role to Quality DMS workspace.")

check_home()
