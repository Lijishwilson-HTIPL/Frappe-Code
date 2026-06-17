"""
patch_portal_page.py — One-time patch for the support-tracker Web Page.

Applies three changes:
  1. CSS fix: overrides Frappe website theme text-color injection so the
     authShell hero heading and subtitle are visible (#ffffff, not overridden).
  2. JS update: renderTicketDetail receives the full API response object so the
     new activity timeline data (res.activity) is accessible.
  3. JS addition: adds renderActivityTimeline() helper that renders HD Ticket
     Activity records as a vertical dot-timeline in the detail slide-over.

Run once via:
  bench --site mysite.local execute helpdesk.helpdesk.patch_portal_page.run
"""

import frappe


def run():
    """Patch the support-tracker Web Page HTML."""
    html = frappe.db.get_value("Web Page", "support-tracker", "main_section_html") or ""

    if not html:
        frappe.throw("Web Page 'support-tracker' not found or has no main_section_html.")

    changed = False

    # ------------------------------------------------------------------
    # PATCH 1 — CSS visibility fix for authShell hero text
    # ------------------------------------------------------------------
    CSS_MARKER = "/* FIX: Portal branding visibility"
    if CSS_MARKER not in html:
        css_fix = """
    /* FIX: Portal branding visibility — override Frappe website theme color injection - 2026-06-08 */
    #authShell h1,
    #authShell h1 * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    #authShell .text-white,
    #authShell .text-white * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    #authShell .text-blue-200,
    #authShell .text-blue-200 * { color: #bfdbfe !important; -webkit-text-fill-color: #bfdbfe !important; }
    /* END FIX: Portal branding visibility */"""
        # Insert before the closing </style> tag
        html = html.replace(
            "    [x-cloak] { display: none !important; }\n  </style>",
            "    [x-cloak] { display: none !important; }\n" + css_fix + "\n  </style>"
        )
        changed = True

    # ------------------------------------------------------------------
    # PATCH 2 — renderTicketDetail: pass full response as 3rd arg
    # ------------------------------------------------------------------
    OLD_OPEN_TICKET_RENDER = (
        "          renderTicketDetail(ticket, d.conversation || d.comments || d.messages || d.thread || []);"
    )
    NEW_OPEN_TICKET_RENDER = (
        "          renderTicketDetail(ticket, d.conversation || d.comments || d.messages || d.thread || [], d);"
    )
    if OLD_OPEN_TICKET_RENDER in html:
        html = html.replace(OLD_OPEN_TICKET_RENDER, NEW_OPEN_TICKET_RENDER)
        changed = True

    # ------------------------------------------------------------------
    # PATCH 3 — renderTicketDetail function signature accepts fullResponse
    # ------------------------------------------------------------------
    OLD_FN_SIG = "    function renderTicketDetail(t, conversation) {"
    NEW_FN_SIG = "    function renderTicketDetail(t, conversation, fullResponse) {"
    if OLD_FN_SIG in html:
        html = html.replace(OLD_FN_SIG, NEW_FN_SIG)
        changed = True

    # ------------------------------------------------------------------
    # PATCH 4 — renderTicketDetail body: inject activity section
    # ------------------------------------------------------------------
    OLD_SOBODY = (
        '      $(\"soBody\").innerHTML = meta + descBlock +\n'
        '        \'<p class=\"text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3\">Conversation</p>\' + conv;'
    )
    NEW_SOBODY = (
        '      var activitySection = renderActivityTimeline(fullResponse && fullResponse.activity || []);\n'
        '      $(\"soBody\").innerHTML = meta + descBlock +\n'
        '        (activitySection ? \'<p class=\"text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3 mt-5\">Activity Timeline</p>\' + activitySection + \'<div class=\"my-4 border-t border-slate-100\"></div>\' : \'\') +\n'
        '        \'<p class=\"text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3\">Conversation</p>\' + conv;'
    )
    if OLD_SOBODY in html:
        html = html.replace(OLD_SOBODY, NEW_SOBODY)
        changed = True

    # ------------------------------------------------------------------
    # PATCH 5 — Add renderActivityTimeline function
    # ------------------------------------------------------------------
    ACTIVITY_MARKER = "function renderActivityTimeline"
    if ACTIVITY_MARKER not in html:
        activity_fn = """
    // ============ ACTIVITY TIMELINE ============
    function renderActivityTimeline(items) {
      if (!items || !items.length) return '';
      var rows = items.map(function (a) {
        var action = a.action || a.content || '';
        var when = a.creation || '';
        var actor = a.owner || '';
        return '<div class=\"flex items-start gap-3 py-1.5\">' +
          '<span class=\"mt-1.5 shrink-0 w-2 h-2 rounded-full bg-primary/40 ring-2 ring-primary/10\"></span>' +
          '<div class=\"flex-1 min-w-0\">' +
            '<p class=\"text-sm text-slate-700\">' + esc(action) + '</p>' +
            '<p class=\"text-[10px] text-slate-400 mt-0.5\">' +
              (actor ? esc(actor) + ' \\u00b7 ' : '') + relative(when) +
            '</p>' +
          '</div>' +
          '</div>';
      }).join('');
      return '<div class=\"space-y-0.5 pl-1\">' + rows + '</div>';
    }

"""
        html = html.replace(
            "    function closeSlide() {",
            activity_fn + "    function closeSlide() {"
        )
        changed = True

    # ------------------------------------------------------------------
    # Write back
    # ------------------------------------------------------------------
    if changed:
        frappe.db.set_value("Web Page", "support-tracker", "main_section_html", html)
        frappe.db.commit()
        frappe.clear_cache()
        return "Patched successfully — 5 patches applied."
    else:
        return "No changes needed — all patches already applied."
