import frappe
import json

def add_all_links():
    ws = frappe.get_doc("Workspace", "DMS")
    
    # Doctypes to add
    doctypes = [
        "Quality Document",
        "Document Request",
        "Document Revision",
        "DMS Training Record",
        "Document Acknowledgement",
        "DMS Audit Log",
        "DMS Project",
        "Document Category",
        "Document Type",
        "Approval Matrix"
    ]
    
    reports = [
        "Master Document List",
        "Audit Trail Report"
    ]
    
    pages = [
        "Document Explorer"
    ]
    
    # 1. Clear existing links and shortcuts
    ws.links = []
    ws.shortcuts = []
    
    # 2. Add Shortcuts (Top row cards)
    # Let's add the most important ones as Shortcuts
    important = ["Quality Document", "Document Request", "DMS Training Record", "DMS Audit Log"]
    for d in important:
        ws.append("shortcuts", {
            "type": "DocType",
            "label": "New " + d if d in ["Quality Document", "Document Request"] else d,
            "link_to": d,
            "color": "Grey"
        })
        
    # 3. Add Links to Sidebar
    for d in doctypes:
        ws.append("links", {
            "type": "Link",
            "link_type": "DocType",
            "label": d,
            "link_to": d
        })
        
    for r in reports:
        ws.append("links", {
            "type": "Link",
            "link_type": "Report",
            "label": r,
            "link_to": r
        })
        
    for p in pages:
        ws.append("links", {
            "type": "Link",
            "link_type": "Page",
            "label": p,
            "link_to": "dms-explorer" if p == "Document Explorer" else p
        })
        
    # 4. Rebuild Content Block
    content = []
    
    # Shortcuts Header
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {
            "text": "Shortcuts",
            "level": 3,
            "col": 12
        }
    })
    
    # Shortcut blocks
    for s in ws.shortcuts:
        content.append({
            "id": frappe.generate_hash(length=10),
            "type": "shortcut",
            "data": {
                "shortcut_name": s.label,
                "col": 4
            }
        })
        
    # Pages & Links Header
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {
            "text": "Pages & Links",
            "level": 3,
            "col": 12
        }
    })
    
    # Generate cards for all sidebar links
    for link in ws.links:
        # Avoid duplicating shortcuts
        # wait, the shortcut cards are already above.
        # But we want all the sidebar links to also appear as clickable blocks in "Pages & Links"!
        # To do that, Frappe requires them to exist in ws.shortcuts if we use 'shortcut' type block.
        # Or we can just add them to ws.shortcuts but NOT put them in the "Shortcuts" block.
        # Actually, let's just make everything a shortcut so it renders nicely in the center.
        pass
        
    # Let's add EVERYTHING to ws.shortcuts so it can be rendered as a card in the center.
    ws.shortcuts = []
    for d in doctypes:
        ws.append("shortcuts", {"type": "DocType", "label": d, "link_to": d})
    for r in reports:
        ws.append("shortcuts", {"type": "Report", "label": r, "link_to": r})
    for p in pages:
        ws.append("shortcuts", {"type": "Page", "label": p, "link_to": "dms-explorer" if p == "Document Explorer" else p})

    # Now rebuild content AGAIN based on all shortcuts
    content = []
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {"text": "Documents", "level": 3, "col": 12}
    })
    
    for d in doctypes:
        content.append({
            "id": frappe.generate_hash(length=10),
            "type": "shortcut",
            "data": {"shortcut_name": d, "col": 3}
        })
        
    content.append({
        "id": frappe.generate_hash(length=10),
        "type": "header",
        "data": {"text": "Reports & Pages", "level": 3, "col": 12}
    })
    
    for r in reports:
        content.append({
            "id": frappe.generate_hash(length=10),
            "type": "shortcut",
            "data": {"shortcut_name": r, "col": 3}
        })
        
    for p in pages:
        content.append({
            "id": frappe.generate_hash(length=10),
            "type": "shortcut",
            "data": {"shortcut_name": p, "col": 3}
        })
        
    ws.content = json.dumps(content)
    ws.save(ignore_permissions=True)
    print("Added all pages and links to Workspace!")

add_all_links()
