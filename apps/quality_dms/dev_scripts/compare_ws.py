import frappe

def compare():
    w1 = frappe.get_doc("Workspace", "Accounting") if frappe.db.exists("Workspace", "Accounting") else None
    w2 = frappe.get_doc("Workspace", "Quality DMS")
    
    if w1:
        print(f"Accounting: module={w1.module}, hidden={getattr(w1, 'is_hidden', 'N/A')}, public={w1.public}, parent={w1.parent_page}, roles={[r.role for r in w1.roles]}")
    else:
        print("Accounting workspace not found!")
        
    print(f"Quality DMS: module={w2.module}, hidden={getattr(w2, 'is_hidden', 'N/A')}, public={w2.public}, parent={w2.parent_page}, roles={[r.role for r in w2.roles]}")
    
