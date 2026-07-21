import frappe

def rename_workspace():
    # Update Workspace
    if frappe.db.exists("Workspace", "Quality DMS"):
        # Rename the primary key
        frappe.rename_doc("Workspace", "Quality DMS", "DMS", force=True)
        print("Renamed Workspace 'Quality DMS' to 'DMS'")
        
        # Also ensure title and label are updated
        frappe.db.set_value("Workspace", "DMS", "title", "DMS")
        frappe.db.set_value("Workspace", "DMS", "label", "DMS")
        
    frappe.db.commit()
    print("Successfully updated workspace name!")
