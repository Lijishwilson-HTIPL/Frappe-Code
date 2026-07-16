import frappe
from frappe.utils import now_datetime

_ALLOWED_SIGN_DOCTYPES = {"Document Library", "DMS Training Record"}


def _require_document_read(document):
    """Guard shared by the whitelisted document endpoints: the document must
    exist AND the caller must be allowed to read it. Prevents non-permitted
    users from using these endpoints as an existence oracle or to pollute the
    audit / signature trail for documents they cannot see."""
    if not frappe.db.exists("Document Library", document):
        frappe.throw("Document not found")
    if not frappe.has_permission("Document Library", doc=document, ptype="read"):
        raise frappe.PermissionError(f"Not permitted to access {document}")


@frappe.whitelist()
def log_file_download(document):
    """Log a file download event for the audit trail."""
    if not frappe.db.exists("Document Library", document):
        return
    if not frappe.has_permission("Document Library", doc=document, ptype="read"):
        return
    version = frappe.db.get_value("Document Library", document, "version")
    try:
        frappe.get_doc({
            "doctype": "DMS Audit Log",
            "document": document,
            "action": f"File Downloaded (v{version})" if version else "File Downloaded",
            "user": frappe.session.user,
            "timestamp": now_datetime(),
            "ip_address": getattr(frappe.local, "request_ip", ""),
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DMS: Failed to log file download")


@frappe.whitelist()
def log_file_preview(document):
    """Log a file preview event for the audit trail."""
    if not frappe.db.exists("Document Library", document):
        return
    if not frappe.has_permission("Document Library", doc=document, ptype="read"):
        return
    version = frappe.db.get_value("Document Library", document, "version")
    try:
        frappe.get_doc({
            "doctype": "DMS Audit Log",
            "document": document,
            "action": f"File Previewed (v{version})" if version else "File Previewed",
            "user": frappe.session.user,
            "timestamp": now_datetime(),
            "ip_address": getattr(frappe.local, "request_ip", ""),
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DMS: Failed to log file preview")

@frappe.whitelist()
def acknowledge_document(document, e_signature=None):
    # Must exist and be readable by the caller (i.e. actually assigned to them).
    _require_document_read(document)

    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if not employee:
        frappe.throw("User is not linked to any Employee record. Cannot acknowledge.")

    doc_version = frappe.db.get_value("Document Library", document, "version")

    training_record = frappe.db.get_value(
        "DMS Training Record", {"document": document, "version": doc_version}, "name"
    )
    # No self-service creation of training records and no self-append of rows:
    # an employee can only acknowledge a training that was actually assigned to
    # them. Otherwise anyone could fabricate a completed compliance record.
    if not training_record:
        frappe.throw(
            "No training has been assigned to you for this document. "
            "Please contact your DMS administrator."
        )

    training_record_doc = frappe.get_doc("DMS Training Record", training_record)
    row = next((r for r in training_record_doc.employees
                if r.employee == employee and r.status != "Suggested"), None)
    if not row:
        frappe.throw("This document's training has not been assigned to you.")

    if row.acknowledged:
        frappe.msgprint("You have already acknowledged this document.")
        return True

    row.acknowledged = 1
    row.acknowledged_on = now_datetime()
    row.status = "Completed"
    row.completion_date = now_datetime().date()
    if e_signature:
        row.e_signature = e_signature
    training_record_doc.save(ignore_permissions=True)
    return True


def _insert_audit_log(action, document=None, request=None):
    """Single insertion point for all DMS Audit Log entries."""
    try:
        frappe.get_doc({
            "doctype": "DMS Audit Log",
            "document": document,
            "request": request,
            "action": action,
            "user": frappe.session.user,
            "timestamp": now_datetime(),
            "ip_address": getattr(frappe.local, "request_ip", ""),
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DMS: Failed to write audit log")


def log_audit_event(doc, method):
    if doc.is_new():
        return

    if method == "on_trash":
        action = "Deleted"
    elif method == "on_cancel":
        action = "Cancelled"
    elif method == "on_submit":
        action = f"Submitted / Published (v{doc.version})" if doc.version else "Submitted / Published"
    elif doc.has_value_changed("status"):
        action = f"Status changed to {doc.status}"
    else:
        action = "Updated"

    _insert_audit_log(action=action, document=doc.name)


def log_request_audit_event(doc, method):
    if doc.is_new():
        return

    if method == "on_trash":
        action = "Deleted"
    elif doc.has_value_changed("status"):
        action = f"Status changed to {doc.status}"
    else:
        action = "Updated"

    _insert_audit_log(action=action, request=doc.name)


_INACTIVE_EMPLOYEE_STATUSES = frozenset({"Left", "Inactive", "Suspended"})


def handle_employee_status_change(doc, method):
    """Excuse an Employee's open training assignments once they leave the
    company, so departed staff stop counting against compliance reports and
    stop receiving overdue reminders."""
    if doc.is_new() or not doc.has_value_changed("status"):
        return
    if doc.status not in _INACTIVE_EMPLOYEE_STATUSES:
        return

    from quality_dms.dms.doctype.dms_training_record.dms_training_record import (
        excuse_departed_employee,
    )
    excuse_departed_employee(doc.name)


def notify_upcoming_reviews():
    # Lower bound (today) prevents repeat emails for already-overdue documents.
    today = frappe.utils.today()
    docs = frappe.get_all("Document Library", filters={
        "status": "Published",
        "review_date": ("between", [today, frappe.utils.add_days(today, 30)]),
    }, fields=["name", "title", "review_date", "owner"])

    if not docs:
        return

    owners = list({d.owner for d in docs})
    email_map = {
        row.name: row.email
        for row in frappe.get_all("User", filters={"name": ("in", owners)}, fields=["name", "email"])
        if row.email
    }

    for d in docs:
        email = email_map.get(d.owner)
        if not email:
            continue
        frappe.sendmail(
            recipients=[email],
            subject=f"Upcoming Review for Document: {d.title}",
            message=f"The document {d.title} is due for review on {d.review_date}. Please initiate a revision request if needed.",
            delayed=True
        )


def get_permission_query_conditions(user):
    if not user: user = frappe.session.user
    if user == "Administrator": return ""

    roles = frappe.get_roles(user)
    if "System Manager" in roles:
        return ""

    conditions = []

    if "Employee" in roles:
        escaped_user = frappe.db.escape(user)
        # Employees see only documents assigned to them through a DMS Training
        # Record, documents they created themselves, or documents created from
        # a Document Request they raised or that was raised for them.
        assigned_via_training = (
            "EXISTS ("
            "SELECT 1 FROM `tabDMS Training Record` tr "
            "INNER JOIN `tabDocument Acknowledgement` da "
            "ON da.parent = tr.name AND da.parenttype = 'DMS Training Record' "
            "INNER JOIN `tabEmployee` emp ON emp.name = da.employee "
            f"WHERE tr.document = `tabDocument Library`.name AND emp.user_id = {escaped_user}"
            ")"
        )
        via_request = (
            "EXISTS ("
            "SELECT 1 FROM `tabDocument Request` dr "
            "WHERE dr.linked_document = `tabDocument Library`.name "
            f"AND (dr.requested_for = {escaped_user} OR dr.requested_by = {escaped_user})"
            ")"
        )
        conditions.append(
            f"(`tabDocument Library`.owner = {escaped_user} "
            f"OR {assigned_via_training} "
            f"OR {via_request})"
        )

    if conditions:
        return "(" + " OR ".join(conditions) + ")"

    # Authenticated user holds no DMS role — deny list access entirely.
    # Returning "" (no filter) would grant full read access; "1=0" returns an empty list.
    return "1=0"


def has_permission(doc, user=None, ptype="read"):
    if not user: user = frappe.session.user
    if user == "Administrator": return True

    roles = frappe.get_roles(user)
    if "System Manager" in roles:
        return True

    # A controller has_permission hook can only DENY; it must return a truthy
    # value to defer to the doctype's role permissions. Returning None is treated
    # as denial by Frappe's has_controller_permissions, so return True to defer.
    if not doc:
        return True

    # Row-level restrictions below apply to reads only. Create/write/delete are
    # governed by DocPerm — defer to it rather than denying here.
    if ptype != "read":
        return True

    if "Employee" in roles:
        if doc.owner == user:
            return True
        if _is_assigned_via_training(doc.name, user):
            return True
        if _is_linked_via_request(doc.name, user):
            return True

    return False


def _is_linked_via_request(document, user):
    """True if this document was created from a Document Request the user
    raised, or that was raised on their behalf (requested_for)."""
    return bool(
        frappe.db.exists(
            "Document Request",
            {
                "linked_document": document,
                "requested_for": user,
            },
        )
        or frappe.db.exists(
            "Document Request",
            {
                "linked_document": document,
                "requested_by": user,
            },
        )
    )


def _is_assigned_via_training(document, user):
    """True if the user is assigned to this document through a DMS Training Record."""
    return bool(
        frappe.db.sql(
            """
            SELECT 1 FROM `tabDMS Training Record` tr
            INNER JOIN `tabDocument Acknowledgement` da
                ON da.parent = tr.name AND da.parenttype = 'DMS Training Record'
            INNER JOIN `tabEmployee` emp ON emp.name = da.employee
            WHERE tr.document = %s AND emp.user_id = %s
            LIMIT 1
            """,
            (document, user),
        )
    )


# Roles that may see the whole File list. Personal training certificates are
# private to the employee they belong to.
_FILE_UNRESTRICTED_ROLES = {"System Manager"}
_CERT_SUFFIX = "-certificate.pdf"


def file_permission_query_conditions(user):
    """Restrict the File list: employees see only their own uploads and files on
    their assigned documents/training; approvers see everything except other
    employees' personal certificates; admins see everything."""
    if not user:
        user = frappe.session.user
    if user == "Administrator":
        return ""

    roles = set(frappe.get_roles(user))
    if roles & _FILE_UNRESTRICTED_ROLES:
        return ""

    escaped_user = frappe.db.escape(user)

    assigned_doc_files = (
        "(`tabFile`.attached_to_doctype = 'Document Library' AND EXISTS ("
        "SELECT 1 FROM `tabDMS Training Record` tr "
        "INNER JOIN `tabDocument Acknowledgement` da "
        "ON da.parent = tr.name AND da.parenttype = 'DMS Training Record' "
        "INNER JOIN `tabEmployee` emp ON emp.name = da.employee "
        f"WHERE tr.document = `tabFile`.attached_to_name AND emp.user_id = {escaped_user}"
        "))"
    )
    # Files on the employee's own training records — but personal certificates
    # (…-<employee>-certificate.pdf) are only visible to the employee they name.
    emp_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
    # (avoid LIKE/% here: permission conditions go through %-string formatting)
    is_cert = "RIGHT(`tabFile`.file_name, 16) = '-certificate.pdf'"
    if emp_id:
        own_cert_frag = frappe.db.escape(f"-{emp_id}-certificate.pdf")
        cert_scope = f"(NOT {is_cert} OR INSTR(`tabFile`.file_name, {own_cert_frag}) > 0)"
    else:
        cert_scope = f"NOT {is_cert}"
    my_training_files = (
        "(`tabFile`.attached_to_doctype = 'DMS Training Record' AND EXISTS ("
        "SELECT 1 FROM `tabDocument Acknowledgement` da "
        "INNER JOIN `tabEmployee` emp ON emp.name = da.employee "
        "WHERE da.parent = `tabFile`.attached_to_name "
        "AND da.parenttype = 'DMS Training Record' "
        f"AND emp.user_id = {escaped_user}"
        f") AND {cert_scope})"
    )
    return (
        f"(`tabFile`.owner = {escaped_user} "
        f"OR {assigned_doc_files} "
        f"OR {my_training_files})"
    )


def file_has_permission(doc, user=None, ptype="read"):
    """Deny employees direct access to files outside their own uploads and
    their assigned documents / training records. Defers (returns True) for
    privileged roles and for non-read permission types."""
    if not user:
        user = frappe.session.user
    if user == "Administrator":
        return True

    roles = set(frappe.get_roles(user))
    if roles & _FILE_UNRESTRICTED_ROLES:
        return True

    if not doc or ptype != "read":
        return True

    if doc.owner == user:
        return True

    is_certificate = (doc.file_name or "").endswith(_CERT_SUFFIX)

    if is_certificate:
        # personal training certificate: only the employee it names may read it
        emp_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
        return bool(emp_id) and f"-{emp_id}{_CERT_SUFFIX}" in doc.file_name

    if doc.attached_to_doctype and doc.attached_to_name:
        # visible if the employee can read the document the file belongs to
        return bool(
            frappe.has_permission(doc.attached_to_doctype, doc=doc.attached_to_name, ptype="read", user=user)
        )

    return False


@frappe.whitelist()
def get_current_user_info():
    user = frappe.session.user
    full_name = frappe.db.get_value("User", user, "full_name") or user
    employee = frappe.db.get_value(
        "Employee", {"user_id": user}, ["designation", "employee_name"], as_dict=True
    )
    return {
        "full_name": full_name,
        "designation": employee.designation if employee else ""
    }


@frappe.whitelist()
def verify_and_log_signature(doctype, docname, password, meaning, position=None):
    import hashlib
    import json
    from frappe.utils.password import check_password

    if doctype not in _ALLOWED_SIGN_DOCTYPES:
        frappe.throw(f"Electronic signatures are not supported for {doctype}.")

    try:
        check_password(frappe.session.user, password)
    except Exception:
        frappe.throw("Invalid password. Electronic signature verification failed.")

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw("Not permitted", frappe.PermissionError)

    if not frappe.db.exists(doctype, docname):
        frappe.throw(f"Document {docname} of type {doctype} not found.")

    doc = frappe.get_doc(doctype, docname)

    exclude_fields = {"modified", "modified_by", "creation", "owner", "_user_tags", "_comments", "_liked_by", "docstatus", "idx"}
    doc_dict = {k: v for k, v in doc.as_dict().items() if k not in exclude_fields}
    doc_json = json.dumps(doc_dict, sort_keys=True, default=str)
    checksum = hashlib.sha256(doc_json.encode('utf-8')).hexdigest()

    user_fullname = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
    signer_email = frappe.db.get_value("User", frappe.session.user, "email") or ""

    log_doc = frappe.get_doc({
        "doctype": "CFR Part 11 Signature Log",
        "reference_doctype": doctype,
        "reference_name": docname,
        "signer": frappe.session.user,
        "signer_name": user_fullname,
        "signer_email": signer_email,
        "position": position or "",
        "timestamp": now_datetime(),
        "meaning": meaning,
        "ip_address": getattr(frappe.local, "request_ip", ""),
        "document_checksum": checksum
    })
    log_doc.insert(ignore_permissions=True)
    # No explicit commit — Frappe commits after the request completes. An explicit
    # commit here would permanently flush any other dirty state in the same transaction
    # even if a later step fails, leaving the DB in a partial state.

    return {"status": "success", "message": "Electronic signature verified and logged successfully."}
