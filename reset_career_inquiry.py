import frappe

# Delete all existing Career Inquiry records
names = frappe.get_all("Career Inquiry", pluck="name")
print("Deleting Career Inquiry records:", len(names))
for name in names:
    frappe.delete_doc("Career Inquiry", name, force=True)
frappe.db.commit()

# Insert a single fully populated candidate
candidate = frappe.get_doc({
    "doctype": "Career Inquiry",
    "first_name": "Alex",
    "last_name": "Morgan",
    "email": "alex.morgan@example.com",
    "phone_number": "+1-555-123-4567",
    "role_applying_for": "Senior AI/ML Engineer",
    "years_of_experience": 8.5,
    "linkedin_profile_url": "https://www.linkedin.com/in/alexmorgan",
    "resume_link": "https://drive.google.com/file/d/EXAMPLE_RESUME",
    "resume_file": None,
    "portfolio_site": "https://www.alexmorgan.dev",
    "tell_us_about_yourself": "Experienced AI/ML engineer with a strong track record building scalable models for customer-facing products. Passionate about machine learning, product delivery, and mentoring teams.",
    "how_did_you_hear": "LinkedIn",
})

candidate.insert(ignore_permissions=True)
frappe.db.commit()
print("Inserted candidate:", candidate.name)
import sys
sys.exit(0)
