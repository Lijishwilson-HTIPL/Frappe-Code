"""
portal_api.py — Customer-facing Support Tracker Portal API
All methods are whitelisted for guest access and use their own token-based auth.
"""

import re
import secrets
import random
from datetime import datetime, timedelta

import frappe
from frappe import _
from werkzeug.security import generate_password_hash, check_password_hash


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_STATUS_LABEL_MAP = {
    "Open": "Open",
    "Replied": "Awaiting Your Reply",
    "Resolved": "Resolved",
    "Closed": "Closed",
    "On Hold": "On Hold",
}

_IN_PROGRESS_STATUSES = {"Open", "On Hold", "Replied"}
_AWAITING_STATUSES = {"Replied"}
_RESOLVED_STATUSES = {"Resolved", "Closed"}


def _now():
    return datetime.now()


def _get_portal_user(email):
    """Return the Support Portal User doc or None."""
    name = frappe.db.get_value("Support Portal User", {"email": email}, "name")
    if not name:
        return None
    return frappe.get_doc("Support Portal User", name)


def _days_open(creation):
    if not creation:
        return 0
    if isinstance(creation, str):
        try:
            creation = datetime.strptime(creation, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            creation = datetime.strptime(creation, "%Y-%m-%d %H:%M:%S")
    return max(0, (_now() - creation).days)


# ---------------------------------------------------------------------------
# 1. check_email
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def check_email(email=None):
    """Check if a Support Portal User exists for this email."""
    try:
        email = (email or "").strip().lower()
        if not email:
            return {"exists": False, "verified": False}
        user = _get_portal_user(email)
        if not user:
            return {"exists": False, "verified": False}
        return {"exists": True, "verified": bool(user.is_verified)}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 2. send_otp
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def send_otp(email=None):
    """Generate and email a 6-digit OTP to the customer."""
    try:
        email = (email or "").strip().lower()
        if not _EMAIL_RE.match(email):
            return {"success": False, "message": "Invalid email format."}

        # Create user if not exists
        user = _get_portal_user(email)
        if not user:
            user = frappe.get_doc({
                "doctype": "Support Portal User",
                "email": email,
                "is_verified": 0,
            })
            user.insert(ignore_permissions=True)
            frappe.db.commit()
            user = _get_portal_user(email)

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        expiry = (_now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

        user.otp = otp
        user.otp_expiry = expiry
        user.save(ignore_permissions=True)
        frappe.db.commit()

        # Send email
        frappe.sendmail(
            recipients=[email],
            subject="Your OTP for Hephzibah Support Portal",
            message=(
                f"Your OTP is: <strong>{otp}</strong>. "
                "Valid for 10 minutes.<br><br>"
                "If you did not request this, please ignore this email."
            ),
            now=True,
        )

        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.send_otp")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 3. verify_otp
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def verify_otp(email=None, otp=None):
    """Check OTP matches and is not expired."""
    try:
        email = (email or "").strip().lower()
        otp = (otp or "").strip()

        user = _get_portal_user(email)
        if not user:
            return {"valid": False, "message": "No account found for this email."}

        if not user.otp or user.otp != otp:
            return {"valid": False, "message": "Invalid OTP."}

        if not user.otp_expiry:
            return {"valid": False, "message": "OTP has expired."}

        expiry = user.otp_expiry
        if isinstance(expiry, str):
            try:
                expiry = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                expiry = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")

        if _now() > expiry:
            return {"valid": False, "message": "OTP has expired."}

        return {"valid": True, "message": "OTP verified."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.verify_otp")
        return {"valid": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 4. set_password
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def set_password(email=None, otp=None, new_password=None):
    """Verify OTP then set a new password and issue a session token."""
    try:
        email = (email or "").strip().lower()

        otp_result = verify_otp(email, otp)
        if not otp_result.get("valid"):
            return {"success": False, "message": otp_result.get("message", "OTP verification failed.")}

        if not new_password or len(new_password) < 6:
            return {"success": False, "message": "Password must be at least 6 characters."}

        user = _get_portal_user(email)
        if not user:
            return {"success": False, "message": "Account not found."}

        token = secrets.token_hex(32)
        token_expiry = (_now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        user.password_hash = generate_password_hash(new_password)
        user.is_verified = 1
        user.otp = None
        user.otp_expiry = None
        user.session_token = token
        user.token_expiry = token_expiry
        user.save(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "token": token, "email": email}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.set_password")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 5. portal_login
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def portal_login(email=None, password=None):
    """Authenticate with email + password and return a session token."""
    try:
        email = (email or "").strip().lower()

        user = _get_portal_user(email)
        if not user:
            return {"success": False, "message": "No account found for this email."}

        if not user.is_verified:
            return {"success": False, "message": "Account not verified. Please complete OTP verification."}

        if not user.password_hash:
            return {"success": False, "message": "Password not set. Please use OTP to set a password."}

        if not check_password_hash(user.password_hash, password):
            return {"success": False, "message": "Invalid credentials."}

        token = secrets.token_hex(32)
        token_expiry = (_now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        user.session_token = token
        user.token_expiry = token_expiry
        user.save(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "token": token, "email": email}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.portal_login")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 6. validate_token
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def validate_token(email=None, token=None):
    """Check token matches and has not expired."""
    try:
        email = (email or "").strip().lower()
        token = (token or "").strip()

        user = _get_portal_user(email)
        if not user:
            return {"valid": False}

        if not user.session_token or user.session_token != token:
            return {"valid": False}

        if not user.token_expiry:
            return {"valid": False}

        expiry = user.token_expiry
        if isinstance(expiry, str):
            try:
                expiry = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                expiry = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")

        if _now() > expiry:
            return {"valid": False}

        return {"valid": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.validate_token")
        return {"valid": False}


# ---------------------------------------------------------------------------
# 7. get_my_tickets
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_my_tickets(email=None, token=None):
    """Return all tickets raised by this email with summary stats."""
    try:
        email = (email or "").strip().lower()

        token_check = validate_token(email, token)
        if not token_check.get("valid"):
            return {"success": False, "message": "Invalid or expired session. Please log in again."}

        tickets_raw = frappe.get_list(
            "HD Ticket",
            filters=[["raised_by", "=", email]],
            fields=[
                "name", "subject", "status", "priority",
                "creation", "modified", "_assign as agent",
                "custom_product", "custom_submitter_name",
            ],
            order_by="modified desc",
            limit_page_length=50,
            ignore_permissions=True,
        )

        stats = {"total": 0, "awaiting_reply": 0, "in_progress": 0, "resolved": 0}
        tickets = []

        for t in tickets_raw:
            status = t.get("status") or "Open"
            status_label = _STATUS_LABEL_MAP.get(status, status)
            days = _days_open(t.get("creation"))

            stats["total"] += 1
            if status in _AWAITING_STATUSES:
                stats["awaiting_reply"] += 1
            elif status in _IN_PROGRESS_STATUSES:
                stats["in_progress"] += 1
            elif status in _RESOLVED_STATUSES:
                stats["resolved"] += 1

            agent_raw = t.get("agent")
            agent_name = None
            if agent_raw:
                try:
                    import json as _json
                    assigned = _json.loads(agent_raw)
                    if assigned:
                        agent_name = assigned[0]
                except Exception:
                    agent_name = agent_raw

            tickets.append({
                "name": t.get("name"),
                "subject": t.get("subject"),
                "status": status,
                "status_label": status_label,
                "priority": t.get("priority"),
                "creation": str(t.get("creation") or ""),
                "modified": str(t.get("modified") or ""),
                "days_open": days,
                "agent": agent_name,
                "product": t.get("custom_product"),
                "submitter_name": t.get("custom_submitter_name"),
            })

        return {"tickets": tickets, "stats": stats}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.get_my_tickets")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 8. get_ticket_detail
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_ticket_detail(email=None, token=None, ticket_name=None):
    """Return full ticket detail plus comments."""
    try:
        email = (email or "").strip().lower()

        token_check = validate_token(email, token)
        if not token_check.get("valid"):
            return {"success": False, "message": "Invalid or expired session. Please log in again."}

        ticket = frappe.get_doc("HD Ticket", ticket_name, ignore_permissions=True)

        if (ticket.raised_by or "").strip().lower() != email:
            return {"success": False, "message": "Access denied."}

        comments_raw = frappe.get_list(
            "HD Ticket Comment",
            filters=[["reference_ticket", "=", ticket_name]],
            fields=["content", "commented_by", "creation"],
            order_by="creation asc",
            ignore_permissions=True,
        )

        comments = []
        for c in comments_raw:
            comments.append({
                "content": c.get("content"),
                "commented_by": c.get("commented_by"),
                "creation": str(c.get("creation") or ""),
            })

        status = ticket.status or "Open"
        ticket_data = {
            "name": ticket.name,
            "subject": ticket.subject,
            "status": status,
            "status_label": _STATUS_LABEL_MAP.get(status, status),
            "priority": ticket.priority,
            "creation": str(ticket.creation or ""),
            "modified": str(ticket.modified or ""),
            "days_open": _days_open(ticket.creation),
            "description": ticket.description,
            "resolution_details": ticket.resolution_details,
            "product": ticket.custom_product,
            "submitter_name": ticket.custom_submitter_name,
            "phone": ticket.custom_phone,
            "sla": ticket.sla,
            "agreement_status": ticket.agreement_status,
            "response_by": str(ticket.response_by or ""),
            "resolution_by": str(ticket.resolution_by or ""),
            "feedback_rating": ticket.feedback_rating,
            "feedback_extra": ticket.feedback_extra,
            "rca_status": ticket.rca_status,
        }

        # HD Ticket Activity records — status/assignment timeline
        activity_raw = frappe.get_list(
            "HD Ticket Activity",
            filters=[["ticket", "=", ticket_name]],
            fields=["name", "ticket", "action", "creation", "owner"],
            order_by="creation asc",
            ignore_permissions=True,
        )
        activity = []
        for a in activity_raw:
            activity.append({
                "name": a.get("name"),
                "ticket": a.get("ticket"),
                "action": a.get("action"),
                "creation": str(a.get("creation") or ""),
                "owner": a.get("owner"),
            })

        return {"ticket": ticket_data, "comments": comments, "activity": activity}
    except frappe.DoesNotExistError:
        return {"success": False, "message": f"Ticket {ticket_name} not found."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.get_ticket_detail")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 9. submit_reply
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def submit_reply(email=None, token=None, ticket_name=None, message=None):
    """Post a customer reply comment on a ticket."""
    try:
        email = (email or "").strip().lower()
        message = (message or "").strip()

        token_check = validate_token(email, token)
        if not token_check.get("valid"):
            return {"success": False, "message": "Invalid or expired session. Please log in again."}

        if not message:
            return {"success": False, "message": "Reply message cannot be empty."}

        ticket = frappe.get_doc("HD Ticket", ticket_name, ignore_permissions=True)

        if (ticket.raised_by or "").strip().lower() != email:
            return {"success": False, "message": "Access denied."}

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": ticket_name,
            "content": message,
            "commented_by": email,
        })
        comment.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True}
    except frappe.DoesNotExistError:
        return {"success": False, "message": f"Ticket {ticket_name} not found."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.submit_reply")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 10. raise_ticket
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def raise_ticket(email, token, subject, description, priority=None):
    """Create a new HD Ticket on behalf of the authenticated portal user."""
    try:
        email = (email or "").strip().lower()
        subject = (subject or "").strip()
        description = (description or "").strip()

        token_check = validate_token(email, token)
        if not token_check.get("valid"):
            return {"success": False, "message": "Invalid or expired session. Please log in again."}

        if not subject:
            return {"success": False, "message": "Subject is required."}

        if not description:
            return {"success": False, "message": "Description is required."}

        doc_data = {
            "doctype": "HD Ticket",
            "subject": subject,
            "description": description,
            "raised_by": email,
            "via_customer_portal": 1,
        }
        if priority:
            doc_data["priority"] = priority

        doc = frappe.get_doc(doc_data)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "ticket_name": doc.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.raise_ticket")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 11. portal_logout
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def portal_logout(email=None, token=None):
    """Invalidate the session token for the portal user."""
    try:
        email = (email or "").strip().lower()

        user = _get_portal_user(email)
        if not user:
            return {"success": True}

        # Only clear token if it matches (don't allow arbitrary session clearing)
        if user.session_token == token:
            user.session_token = None
            user.token_expiry = None
            user.save(ignore_permissions=True)
            frappe.db.commit()

        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "portal_api.portal_logout")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# 12. get_user_tickets  (alias for JS compatibility)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_user_tickets(email=None, session_token=None):
    """
    Alias of get_my_tickets that accepts session_token parameter.
    Returns tickets for the authenticated portal user.
    """
    return get_my_tickets(email=email, token=session_token)


# ---------------------------------------------------------------------------
# 13. get_ticket_details  (with HD Ticket Activity timeline)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_ticket_details(ticket_name=None, email=None, session_token=None):
    """
    Alias of get_ticket_detail that accepts session_token parameter.
    Returns ticket + comments + activity timeline.
    """
    return get_ticket_detail(email=email, token=session_token, ticket_name=ticket_name)
