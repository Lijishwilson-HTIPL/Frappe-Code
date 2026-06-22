# File: apps/helpdesk/helpdesk/overrides/hd_ticket_hooks.py
# ---------------------------------------------------------------------------
# after_insert hook for HD Ticket — sends a branded acknowledgment email to
# the ticket reporter (raised_by) immediately after a new ticket is created.
# ---------------------------------------------------------------------------

import frappe


def send_ticket_acknowledgment(doc, method):
    """
    Fires on HD Ticket after_insert.
    Sends a branded acknowledgment email to doc.raised_by.
    Skipped when:
      - raised_by is blank or is a system/administrator account
      - ticket was created by an internal split (ticket_split_from set)
      - frappe.flags.initial_sync is active (bulk import)
    """
    # --- guard rails --------------------------------------------------------
    if not doc.raised_by:
        return

    if doc.ticket_split_from:
        # Split tickets are internal; the original reporter was already notified
        return

    if frappe.flags.initial_sync:
        # Bulk import — do not flood inboxes
        return

    # Guard against sending to system/anonymous accounts
    skip_accounts = {"Administrator", "Guest", ""}
    if doc.raised_by in skip_accounts:
        return

    # --- build email content ------------------------------------------------
    tracker_url = f"{frappe.utils.get_url()}/support-tracker"

    subject = f"We received your support request - {doc.name}"

    body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Support Request Received</title>
  <style>
    body {{
      font-family: Arial, Helvetica, sans-serif;
      background-color: #f4f4f7;
      margin: 0;
      padding: 0;
      color: #333333;
    }}
    .wrapper {{
      max-width: 600px;
      margin: 40px auto;
      background-color: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    .header {{
      background-color: #1a5276;
      padding: 28px 32px;
    }}
    .header h1 {{
      color: #ffffff;
      margin: 0;
      font-size: 22px;
      font-weight: 600;
      letter-spacing: 0.3px;
    }}
    .content {{
      padding: 32px;
    }}
    .content p {{
      font-size: 15px;
      line-height: 1.7;
      margin: 0 0 16px 0;
    }}
    .ticket-box {{
      background-color: #eaf0fb;
      border-left: 4px solid #1a5276;
      border-radius: 4px;
      padding: 16px 20px;
      margin: 24px 0;
    }}
    .ticket-box p {{
      margin: 0;
      font-size: 15px;
      color: #1a3a5c;
    }}
    .ticket-box .ticket-id {{
      font-size: 18px;
      font-weight: 700;
      color: #1a5276;
      margin-bottom: 4px;
    }}
    .btn-wrap {{
      text-align: center;
      margin: 32px 0 24px 0;
    }}
    .btn {{
      display: inline-block;
      background-color: #1a5276;
      color: #ffffff !important;
      text-decoration: none;
      padding: 13px 32px;
      border-radius: 5px;
      font-size: 15px;
      font-weight: 600;
      letter-spacing: 0.2px;
    }}
    .note {{
      font-size: 13px;
      color: #666666;
      text-align: center;
      margin: 0 0 24px 0;
    }}
    .footer {{
      background-color: #f0f0f0;
      border-top: 1px solid #e0e0e0;
      text-align: center;
      padding: 20px 32px;
    }}
    .footer p {{
      margin: 0;
      font-size: 12px;
      color: #888888;
    }}
    .footer .brand {{
      font-size: 14px;
      font-weight: 700;
      color: #1a5276;
      margin-bottom: 4px;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <!-- Header -->
    <div class="header">
      <h1>Support Request Received</h1>
    </div>

    <!-- Body -->
    <div class="content">
      <p>Dear Customer,</p>

      <p>Thank you for reaching out to us. We have received your support ticket and our team is on it.</p>

      <div class="ticket-box">
        <p class="ticket-id">Ticket {doc.name}</p>
        <p>{frappe.utils.escape_html(doc.subject or "")}</p>
      </div>

      <p>Our team will review it and get back to you shortly. You can track the status of your request at any time using the button below.</p>

      <div class="btn-wrap">
        <a href="{tracker_url}" class="btn">Track Your Ticket</a>
      </div>

      <p class="note">
        If this is your first visit, you will be asked to verify your email and set a password.
      </p>
    </div>

    <!-- Footer -->
    <div class="footer">
      <p class="brand">Hephzibah Technologies</p>
      <p>Quality Control</p>
    </div>
  </div>
</body>
</html>
""".strip()

    # --- send ---------------------------------------------------------------
    try:
        frappe.sendmail(
            recipients=[doc.raised_by],
            subject=subject,
            message=body,
            reference_doctype="HD Ticket",
            reference_name=doc.name,
            now=True,
            expose_recipients="header",
            email_headers={"X-Auto-Generated": "hd-ticket-ack-hti"},
        )
    except Exception:
        # Log but do not raise — a failed acknowledgment must never block ticket creation
        frappe.log_error(
            title=f"HD Ticket acknowledgment email failed for {doc.name}",
            message=frappe.get_traceback(),
        )
