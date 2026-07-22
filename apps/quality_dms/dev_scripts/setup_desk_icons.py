import frappe
import json

def setup_desk_icons():
    frappe.set_user("Administrator")

    # 1. Clean up old DMS workspaces' parent_page if they are 'None'
    workspaces = frappe.get_all("Workspace", filters={"parent_page": "None"})
    for ws in workspaces:
        doc = frappe.get_doc("Workspace", ws.name)
        doc.parent_page = ""
        doc.save(ignore_permissions=True)
    
    # 2. Create the Workspace Sidebar for DMS (the main sidebar we want)
    sidebar_name = "DMS"
    if frappe.db.exists("Workspace Sidebar", sidebar_name):
        frappe.delete_doc("Workspace Sidebar", sidebar_name, ignore_permissions=True)
    
    sidebar = frappe.new_doc("Workspace Sidebar")
    sidebar.name = sidebar_name
    sidebar.title = "DMS"
    sidebar.header_icon = "archive"
    sidebar.standard = 1
    sidebar.module = "Quality DMS"
    
    sidebar_items = [
        # Home Link (top-level)
        {
            "type": "Link",
            "label": "Home",
            "link_type": "Workspace",
            "link_to": "DMS",
            "icon": "home",
            "child": 0,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        # Section Break: Document Management
        {
            "type": "Section Break",
            "label": "Document Management",
            "icon": "file-text",
            "child": 0,
            "indent": 1,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Document Explorer",
            "link_type": "Page",
            "link_to": "dms-explorer",
            "icon": "folder-open",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Quality Documents",
            "link_type": "DocType",
            "link_to": "Quality Document",
            "icon": "file-text",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Document Requests",
            "link_type": "DocType",
            "link_to": "Document Request",
            "icon": "file-plus",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        # Section Break: Folder Management
        {
            "type": "Section Break",
            "label": "Folder Management",
            "icon": "folder",
            "child": 0,
            "indent": 1,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Departments",
            "link_type": "DocType",
            "link_to": "Department",
            "icon": "users",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Document Categories",
            "link_type": "DocType",
            "link_to": "Document Category",
            "icon": "tag",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Document Types",
            "link_type": "DocType",
            "link_to": "Document Type",
            "icon": "file",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        # Section Break: Workflow & Approvals
        {
            "type": "Section Break",
            "label": "Workflow & Approvals",
            "icon": "check-square",
            "child": 0,
            "indent": 1,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Approval Matrix",
            "link_type": "DocType",
            "link_to": "Approval Matrix",
            "icon": "grid",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Workflows",
            "link_type": "DocType",
            "link_to": "Workflow",
            "icon": "git-branch",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        # Acknowledgements
        {
            "type": "Section Break",
            "label": "Acknowledgements",
            "icon": "award",
            "child": 0,
            "indent": 1,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Training Records",
            "link_type": "DocType",
            "link_to": "DMS Training Record",
            "icon": "users",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        # Section Break: Compliance & History
        {
            "type": "Section Break",
            "label": "Compliance & History",
            "icon": "history",
            "child": 0,
            "indent": 1,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Document Revisions",
            "link_type": "DocType",
            "link_to": "Document Revision",
            "icon": "clock",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Audit Logs",
            "link_type": "DocType",
            "link_to": "DMS Audit Log",
            "icon": "shield",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        # Reports
        {
            "type": "Section Break",
            "label": "Reports",
            "icon": "bar-chart",
            "child": 0,
            "indent": 1,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Master Document List",
            "link_type": "Report",
            "link_to": "Master Document List",
            "icon": "list",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        },
        {
            "type": "Link",
            "label": "Audit Trail Report",
            "link_type": "Report",
            "link_to": "Audit Trail Report",
            "icon": "shield-alert",
            "child": 1,
            "indent": 0,
            "keep_closed": 0,
            "collapsible": 1,
            "show_arrow": 0
        }
    ]
    
    for item in sidebar_items:
        sidebar.append("items", item)
        
    sidebar.insert(ignore_permissions=True)
    print("Created Workspace Sidebar: DMS")

    # 3. Create dummy/empty Workspace Sidebar named 'Quality DMS'
    dummy_sidebar_name = "Quality DMS"
    if frappe.db.exists("Workspace Sidebar", dummy_sidebar_name):
        frappe.delete_doc("Workspace Sidebar", dummy_sidebar_name, ignore_permissions=True)
        
    dummy = frappe.new_doc("Workspace Sidebar")
    dummy.name = dummy_sidebar_name
    dummy.title = "Quality DMS"
    dummy.standard = 1
    dummy.module = "Quality DMS"
    dummy.items = []  # No items!
    dummy.insert(ignore_permissions=True)
    print("Created Empty/Dummy Workspace Sidebar: Quality DMS")

    # 4. Create or update the Desktop Icon for DMS
    desktop_icon_name = "DMS"
    if frappe.db.exists("Desktop Icon", desktop_icon_name):
        frappe.delete_doc("Desktop Icon", desktop_icon_name, ignore_permissions=True)
        
    desktop_icon = frappe.new_doc("Desktop Icon")
    desktop_icon.name = desktop_icon_name
    desktop_icon.label = "DMS"  # The label shown on the card
    desktop_icon.icon = "archive"  # The icon shown on the card
    desktop_icon.icon_type = "Link"
    desktop_icon.link_type = "Workspace Sidebar"
    desktop_icon.link_to = "DMS"
    desktop_icon.parent_icon = "ERPNext"
    desktop_icon.app = "quality_dms"
    desktop_icon.hidden = 0
    desktop_icon.standard = 1
    desktop_icon.idx = 10  # Put it somewhere in the list
    
    desktop_icon.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Created Desktop Icon: DMS")

    # 5. Clear cache to make sure UI gets updated
    frappe.cache.delete_key("desktop_icons")
    frappe.cache.delete_key("bootinfo")
    print("Cleared Desktop Icon and bootinfo caches!")

if __name__ == "__main__":
    setup_desk_icons()
