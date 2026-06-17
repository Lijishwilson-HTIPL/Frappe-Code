import frappe, json

frappe.init(site='mysite.local', sites_path='sites')
frappe.connect()

hr_ws = frappe.get_doc('Workspace', 'HR')

# Remove any existing career links to avoid duplicates
hr_ws.links = [l for l in hr_ws.links if 'career' not in l.get('label', '').lower() and 'career' not in (l.get('link_to') or '').lower()]

# Prepend Career Inquiries Card Break + Career Inquiry Link at the top
career_card_break = frappe.new_doc('Workspace Link')
career_card_break.update({
    'type': 'Card Break',
    'label': 'Career Inquiries',
    'hidden': 0,
    'is_query_report': 0,
    'onboard': 0,
    'link_count': 0,
    'link_type': 'DocType',
})

career_link = frappe.new_doc('Workspace Link')
career_link.update({
    'type': 'Link',
    'label': 'Career Inquiry',
    'link_to': 'Career Inquiry',
    'link_type': 'DocType',
    'hidden': 0,
    'is_query_report': 0,
    'onboard': 1,
    'link_count': 0,
})

hr_ws.links = [career_card_break, career_link] + hr_ws.links

# Re-index idx
for i, l in enumerate(hr_ws.links):
    l.idx = i + 1

hr_ws.save(ignore_permissions=True)
frappe.db.commit()
print("Done. Career Inquiries links added to HR workspace.")
