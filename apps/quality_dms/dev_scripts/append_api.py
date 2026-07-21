import os

api_path = "/home/james/frappe-bench/apps/quality_dms/quality_dms/quality_dms/api.py"

code_to_append = """

def get_permission_query_conditions(user):
    if not user: user = frappe.session.user
    if user == "Administrator": return ""
    
    roles = frappe.get_roles(user)
    if "DMS Admin" in roles or "DMS Manager" in roles:
        return ""
        
    conditions = []
    
    if "DMS Approver" in roles:
        conditions.append("`tabQuality Document`.workflow_state IN ('Pending Approval', 'Published')")
    elif "DMS Reviewer" in roles:
        conditions.append("`tabQuality Document`.workflow_state IN ('Pending Review', 'Published')")
    elif "DMS Creator" in roles:
        conditions.append(f"(`tabQuality Document`.owner = '{user}' OR `tabQuality Document`.workflow_state = 'Published')")
        
    if conditions:
        return "(" + " OR ".join(conditions) + ")"
        
    return ""

def has_permission(doc, user=None, ptype="read"):
    if not user: user = frappe.session.user
    if user == "Administrator": return True
    
    roles = frappe.get_roles(user)
    if "DMS Admin" in roles or "DMS Manager" in roles:
        return True
        
    if "DMS Approver" in roles:
        if doc.workflow_state in ["Pending Approval", "Published"]: return True
    elif "DMS Reviewer" in roles:
        if doc.workflow_state in ["Pending Review", "Published"]: return True
    elif "DMS Creator" in roles:
        if doc.owner == user or doc.workflow_state == "Published": return True
        
    return False
"""

with open(api_path, "a") as f:
    f.write(code_to_append)

print("Appended permission logic to api.py")
