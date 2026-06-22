import frappe
import json


def execute():
    ws = frappe.get_doc("Workspace", "CRM")

    # Check the content field
    content = ws.content
    if content:
        try:
            data = json.loads(content)
            print(f"Content type: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'list len=' + str(len(data))}")
            print(f"Content preview: {str(data)[:500]}")
        except Exception as e:
            print(f"Content parse error: {e}, raw: {str(content)[:200]}")
    else:
        print("No content field set")

    # Check shortcuts field
    print(f"\nShortcuts count: {len(ws.shortcuts)}")
    for s in ws.shortcuts:
        print(f"  [{s.idx}] {s.label} -> {s.link_to} ({s.type})")
