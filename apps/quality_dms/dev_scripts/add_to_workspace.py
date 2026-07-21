import frappe

def add_dashboard_link():
    ws = frappe.get_doc("Workspace", "DMS")
    
    # Check if link already exists
    for link in ws.links:
        if link.label == "Quality Dashboard":
            print("Link already exists")
            return
            
    # Prepend it to the top of the links by adding it and then sorting or just appending
    ws.append("links", {"type": "Link", "label": "Quality Dashboard", "link_to": "quality_dashboard", "link_type": "Page"})
    
    # Re-order the other indices
    idx = 2
    for link in ws.links:
        if link.label != "Quality Dashboard":
            link.idx = idx
            idx += 1
            
    ws.save(ignore_permissions=True)
    print("Added Quality Dashboard link to DMS workspace!")

add_dashboard_link()
