import frappe, json

frappe.init(site='mysite.local', sites_path='sites')
frappe.connect()

hr_ws = frappe.get_doc('Workspace', 'HR')
content = json.loads(hr_ws.content)

careers_blocks = [
    {"id": "careers_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Careers</b></span>", "col": 12}},
    {"id": "careers_card", "type": "card", "data": {"card_name": "Career Inquiries", "col": 4}},
    {"id": "careers_spacer", "type": "spacer", "data": {"col": 12}}
]

# Remove any existing careers blocks
content = [b for b in content if not b.get('id', '').startswith('careers_')]

# Prepend careers blocks at the top
new_content = careers_blocks + content

frappe.db.set_value('Workspace', 'HR', 'content', json.dumps(new_content))
frappe.db.commit()
print("Done. Careers moved to top of HR workspace.")
