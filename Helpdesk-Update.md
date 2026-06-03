# Root Cause Analysis (RCA) — Frappe Helpdesk User Guide

**Module:** Frappe Helpdesk
**Feature:** Root Cause Analysis (RCA)
**Audience:** Support Agents, Team Leads, Support Managers
**Last Updated:** 2026-05-27

---

## Table of Contents

1. [Overview](#1-overview)
2. [The RCA Tab — Field by Field](#2-the-rca-tab--field-by-field)
3. [Status Flow](#3-status-flow)
4. [Auto-Detection Rules](#4-auto-detection-rules)
5. [Step-by-Step Workflow](#5-step-by-step-workflow)
6. [Integration with the Ticket Flow](#6-integration-with-the-ticket-flow)
7. [Tips and Best Practices](#7-tips-and-best-practices)

---

## 1. Overview

### What is Root Cause Analysis?

Root Cause Analysis (RCA) is a structured process for identifying **why** a support incident occurred, not just what went wrong or how it was fixed. In Frappe Helpdesk, the RCA feature is built directly into the ticket so that agents and managers can document the underlying cause, the resolution, and the steps taken to prevent the same issue from happening again — all in one place.

An RCA is not a post-mortem report you write days later in a separate document. It is a living record attached to the ticket, updated as the investigation progresses, and permanently linked to that ticket for historical reference.

### Why Does It Matter?

Without structured RCA:

- The same incident recurs because the fix addressed symptoms, not causes
- Knowledge is siloed in individual agents' heads or scattered across chat threads
- Managers have no visibility into systemic problems
- Knowledge base (KB) articles never get written, so customers keep raising the same tickets

With RCA in Helpdesk:

- Every high-impact ticket produces a documented cause-and-fix record
- KB articles are linked directly to the ticket that generated the knowledge
- Recurring issues can be grouped under a single **Problem Ticket** for trend analysis
- Managers can audit completed RCAs and identify patterns across teams

### When Is RCA Triggered Automatically?

RCA is triggered automatically when any of the following conditions are detected on a ticket:

- The ticket's **Priority** is set to **Critical** or **High**
- The ticket's **SLA Status** reaches **Failed** (resolution breach)
- The ticket's **SLA Status** reaches **Resolution Due** (approaching breach)

When auto-triggered, the system sets **RCA Required = Yes** and records the specific reason in the **RCA Trigger Reason** field so there is always an audit trail for why the flag was raised.

For tickets that do not meet these criteria (Medium or Low priority, SLA in good standing), an agent or manager can still enable RCA manually by checking **RCA Required**.

### Where to Find the RCA Tab

The RCA tab lives inside the **right sidebar** of every ticket.

1. Open any ticket in Helpdesk.
2. Look at the right-hand side panel.
3. Click the **RCA** tab (alongside Details, Conversations, etc.).

The tab is always present. For tickets where RCA has not been triggered, most fields will be empty and **RCA Required** will be unchecked.

---

## 2. The RCA Tab — Field by Field

This section describes every field in the RCA tab, its purpose, who fills it, and any auto-population behavior.

---

### RCA Required

| Attribute | Value |
|-----------|-------|
| Type | Checkbox |
| Set by | System (auto) or Agent / Manager (manual) |
| Editable | Yes — can be toggled manually |

This checkbox is the master switch for the RCA process on a ticket. When checked, it signals that a formal RCA must be completed before or alongside ticket closure.

The system checks trigger conditions (priority and SLA status) whenever a ticket is saved or its status changes. If a condition is met, this checkbox is enabled automatically. If the checkbox is already enabled, the system does not clear it — it can only be unchecked manually by an agent or manager.

> **Note:** Even if the auto-trigger conditions later resolve (e.g., SLA breach is reset), the RCA Required flag remains set. This is intentional — if RCA was warranted at any point during the ticket's lifecycle, the investigation should still be completed.

---

### RCA Status

| Attribute | Value |
|-----------|-------|
| Type | Select (single choice) |
| Options | Pending / In Progress / Completed / Waived |
| Default | Pending (when RCA Required is enabled) |
| Set by | Agent or Manager |

Tracks the current state of the RCA investigation. See [Section 3 — Status Flow](#3-status-flow) for a detailed explanation of each status and the expected transitions.

---

### RCA Trigger Reason

| Attribute | Value |
|-----------|-------|
| Type | Read-only text |
| Set by | System (auto-populated) |
| Editable | No |

A human-readable explanation of why RCA was flagged. The system writes this automatically when it enables **RCA Required**. Example values:

- `Priority is Critical`
- `Priority is High`
- `SLA Status is Failed`
- `SLA Status is Resolution Due`

If RCA was enabled manually (not by the system), this field remains empty. Managers can interpret an empty trigger reason as "manually flagged" rather than auto-detected.

> **Note:** This field is intentionally read-only. It is an audit record, not an editable note. If additional context is needed, use the Escalation Reason or Root Cause fields.

---

### Root Cause

| Attribute | Value |
|-----------|-------|
| Type | Long text / rich-text editor |
| Set by | Agent investigating the ticket |
| Required for completion | Yes |

The core of the RCA. Describe **what fundamentally caused the issue**, not just what the surface symptom was.

Good root causes are specific and actionable:

- "The payment gateway timeout threshold was set to 3 seconds; under high load the gateway takes 5-8 seconds, causing all payment submissions to fail silently."
- "The nightly sync job assumes the source database is online. No retry logic exists, so a 10-minute maintenance window caused 48 hours of stale data."

Avoid vague descriptions like "user error" or "system issue" unless you can explain precisely what the user did wrong or which system component failed and why.

---

### Fix / Workaround

| Attribute | Value |
|-----------|-------|
| Type | Long text / rich-text editor |
| Set by | Agent who resolved the ticket |
| Required for completion | Yes |

Describe **what was done to resolve this specific incident**. This may be a permanent fix or a temporary workaround. Be explicit about which one it is.

Examples:

- **Permanent fix:** "Timeout threshold increased to 15 seconds in `payment_gateway.conf`. Deployed to production at 14:32 UTC."
- **Workaround:** "Customer's account was manually re-synced via the admin panel. A permanent fix for the sync retry logic is tracked in JIRA-1042."

If a workaround was applied, link the KB article (see **KB Article** field below) so other agents know how to handle the same situation.

---

### Preventive Measures

| Attribute | Value |
|-----------|-------|
| Type | Long text / rich-text editor |
| Set by | Agent or Team Lead |
| Required for completion | Recommended, not enforced |

Document **what changes will prevent this issue from recurring**. These are forward-looking actions, not descriptions of what was already done.

Examples:

- "Add alerting for payment gateway response times exceeding 4 seconds."
- "Write a runbook for the sync job and add it to the on-call guide."
- "Update the onboarding checklist to include correct timezone configuration."

Preventive measures are most valuable when they are assigned to a specific owner or linked to a task/issue tracker. Use this field to capture the intention; track completion externally.

---

### KB Article

| Attribute | Value |
|-----------|-------|
| Type | Link (Helpdesk — HD Article) |
| Set by | Agent |
| Editable | Yes |

Link to a Helpdesk Knowledge Base article that documents the fix or workaround for this type of issue. This connects the incident to reusable documentation.

If no KB article exists yet, the agent should create one and link it here once published. Linking a KB article here:

- Makes the article discoverable from the ticket history
- Helps managers identify which KB articles originated from real incidents
- Allows future tickets of the same type to be resolved faster by referencing the article

---

### Problem Ticket

| Attribute | Value |
|-----------|-------|
| Type | Link (Helpdesk — HD Ticket) |
| Set by | Agent or Team Lead |
| Editable | Yes |

Link this ticket to a **parent Problem Ticket** — a separate ticket that tracks a recurring or systemic issue that is the underlying cause of multiple individual incidents.

Use this when:

- The same root cause has appeared in 2 or more tickets
- A known infrastructure or software bug is generating repeated support tickets
- A team lead has created a dedicated problem ticket to aggregate related incidents

Linking problem tickets gives managers a consolidated view of how many customers were affected by a single underlying problem.

---

### Escalation Reason

| Attribute | Value |
|-----------|-------|
| Type | Long text |
| Set by | Agent or escalating manager |
| Editable | Yes |

Explains why this ticket was escalated (if it was). This is especially relevant when RCA Status is set to **Waived** — the escalation reason should explain why the RCA process was bypassed.

If the ticket was not escalated, this field can be left empty. However, if the ticket was transferred between teams or bumped to a higher support tier, a brief explanation here creates a complete audit trail.

---

### Completed By

| Attribute | Value |
|-----------|-------|
| Type | Link (User) |
| Set by | System (auto-stamped) |
| Editable | No |

The user account that marked the RCA as **Completed**. Auto-populated by the system when the status transitions to Completed. This cannot be manually edited, ensuring the record accurately reflects who closed out the investigation.

---

### Completed On

| Attribute | Value |
|-----------|-------|
| Type | Datetime |
| Set by | System (auto-stamped) |
| Editable | No |

The date and time at which the RCA was marked **Completed**. Auto-populated alongside **Completed By**. Useful for measuring how long RCAs take from ticket creation to investigation closure.

---

## 3. Status Flow

The **RCA Status** field follows a defined set of states. Agents move through these states as the investigation progresses.

```
[Not triggered]  →  Pending  →  In Progress  →  Completed
                                              ↘  Waived
```

---

### Pending (amber)

RCA has been flagged — either automatically by the system or manually by an agent or manager — but the investigation has not started yet. The agent can see an amber indicator on the RCA tab to draw attention.

**What to do:** Assign the RCA to the appropriate agent and move to In Progress as soon as the investigation begins. Tickets should not sit in Pending for extended periods after being closed.

---

### In Progress (blue)

The agent is actively investigating and filling in the RCA fields. The Root Cause, Fix/Workaround, and Preventive Measures fields should be populated during this phase.

**What to do:** Fill in all required fields. Link the KB Article and Problem Ticket if applicable. When documentation is complete, mark as Completed.

---

### Completed (green)

The RCA is fully documented. Root Cause, Fix/Workaround, and Preventive Measures have all been filled in. The system automatically stamps **Completed By** and **Completed On** at this moment.

**What to do:** No further action required on the RCA itself. The ticket can be closed. The manager may review completed RCAs during team retrospectives or quality audits.

---

### Waived

The RCA was deliberately skipped. This is a legitimate option when, for example:

- The ticket was a duplicate of an already-RCA'd ticket
- The issue was a one-off user configuration error with no systemic implications
- Management made a deliberate decision that an RCA was not warranted

> **Important:** Waiving an RCA should never be done silently. Always fill in the **Escalation Reason** field with a clear explanation of why the RCA was waived. A waived RCA with no explanation is indistinguishable from a skipped one and will flag in audits.

---

## 4. Auto-Detection Rules

The system evaluates the following conditions each time a ticket is saved or its status/priority changes. If any condition is true, **RCA Required** is set to Yes and the **RCA Trigger Reason** is recorded.

| Condition | Triggers Auto-RCA? | Trigger Reason Recorded |
|-----------|-------------------|-------------------------|
| Priority = **Critical** | Yes | `Priority is Critical` |
| Priority = **High** | Yes | `Priority is High` |
| SLA Status = **Failed** | Yes | `SLA Status is Failed` |
| SLA Status = **Resolution Due** | Yes | `SLA Status is Resolution Due` |
| Priority = Medium, SLA OK | No | — (manual only) |
| Priority = Low, SLA OK | No | — (manual only) |
| Any priority, SLA = Fulfilled | No | — (manual only) |

### Important Behaviors

- **Multiple conditions can be true at the same time.** For example, a Critical priority ticket that also breaches SLA. In this case, the trigger reason records the first condition detected. The RCA flag is still set only once.
- **The flag is sticky.** Once RCA Required is enabled, changing the priority or SLA status back to a non-triggering value does not automatically unset it. The flag must be manually unchecked if you determine RCA is no longer needed.
- **Manual override is always available.** An agent or manager can check RCA Required on any ticket at any time, regardless of priority or SLA status.

---

## 5. Step-by-Step Workflow

This section walks through the complete RCA process from ticket intake to completed investigation.

---

### Step 1 — Ticket Arrives and Is Assessed

A new ticket is created by a customer or by an agent on the customer's behalf. During triage, the agent sets the ticket **Priority**.

- If priority is set to **Critical** or **High**, the system immediately sets RCA Required = Yes and records the trigger reason.
- If priority is Medium or Low, no auto-flag is set at this point.

---

### Step 2 — Agent Notices the RCA Flag

When a ticket has RCA Required = Yes, the **RCA** tab in the right sidebar shows an amber indicator. The agent sees the tab is active and can click it to view:

- The **RCA Trigger Reason** explaining why it was flagged
- The **RCA Status** defaulted to Pending

At this stage, the agent acknowledges the flag and can begin investigation immediately or queue it for after resolution.

---

### Step 3 — Agent Sets Status to "In Progress"

Once the agent begins the RCA investigation (typically after the immediate issue is resolved for the customer), they set **RCA Status = In Progress**.

This signals to the team lead and manager that the investigation is actively running. Tickets with In Progress RCAs should appear in team dashboards so managers can track progress.

---

### Step 4 — Fill In the Core RCA Fields

The agent completes the investigation and documents findings in the following order:

1. **Root Cause** — What fundamentally caused this incident?
2. **Fix / Workaround** — What was done to resolve it? Is this permanent or temporary?
3. **Preventive Measures** — What should be done to stop this recurring?

All three fields should be filled before moving to Completed status. Rich-text formatting is supported — use bullet points and headers to keep the documentation readable.

---

### Step 5 — Link Related Resources

After filling the core fields, the agent links any relevant resources:

- **KB Article** — If a knowledge base article exists for this issue type, link it. If one needs to be created, create it in Helpdesk Articles and then link it here.
- **Problem Ticket** — If this incident is part of a recurring pattern, link the parent problem ticket. If no problem ticket exists yet but the issue is recurring, create one and link it.
- **Escalation Reason** — If the ticket was escalated, document why.

---

### Step 6 — Mark RCA Complete

When all fields are filled and reviewed, the agent sets **RCA Status = Completed**.

The system automatically:

- Records the current user in **Completed By**
- Records the current timestamp in **Completed On**
- Updates the tab indicator to green

> **Note:** Once Completed is set, the RCA fields become a permanent record of the investigation. Edits are still technically possible, but should only be made with manager awareness to preserve the integrity of the audit trail.

---

### Step 7 — Manager Reviews Completed RCAs

Team leads and support managers should periodically audit completed RCAs to:

- Verify the quality and specificity of root cause documentation
- Identify recurring root causes across multiple tickets
- Confirm that preventive measures have been actioned
- Check that KB articles are being written and linked
- Flag any waived RCAs that lack a written reason

This review process is the feedback loop that makes RCA valuable. Without it, the documentation is produced but never acted on.

---

## 6. Integration with the Ticket Flow

### The Refined Helpdesk Ticket Flow

The full ticket lifecycle in Frappe Helpdesk follows this cycle:

```
Intake → Triage → Resolve / Escalate → Close → Improve
```

RCA sits at the **intersection of Close and Improve**. Here is how it fits into each phase:

---

### Intake

Customer submits a ticket via portal, email, or agent creation. The ticket enters the queue in **Open** status. Priority is not yet set (or defaults to Medium).

RCA is not involved at this stage.

---

### Triage

The assigned agent or triaging team reviews the ticket, sets **Priority**, assigns it to the right team, and determines urgency.

**RCA involvement:** If Priority is set to Critical or High, RCA Required is automatically enabled. The agent sees the RCA tab flag. This early flag ensures that agents know from the moment of triage that an investigation will be required — not just a quick fix and close.

---

### Resolve / Escalate

The agent works on the ticket. They may resolve it directly, or escalate it to a higher tier, a specialist team, or a third-party vendor.

**RCA involvement:** During or immediately after resolution, the agent should begin filling the RCA tab. The resolution of the customer's issue and the investigation of the root cause are parallel activities. Waiting until the ticket is closed to start RCA often means context is lost.

If the ticket breaches SLA during this phase, the auto-trigger fires again (if not already fired), now with `SLA Status is Failed` as the trigger reason.

---

### Close

The ticket is marked **Resolved** and then **Closed** after customer confirmation or after the auto-close timer expires.

**RCA involvement:** A ticket can be closed even if RCA is still In Progress or Pending. Closing a ticket does not enforce RCA completion. However, managers should monitor the queue of closed tickets with outstanding RCAs and follow up with agents to complete them. A completed ticket with a Pending RCA is an incomplete record.

> **Note:** If your team wants to enforce RCA completion before closure, this can be configured as a validation rule at the team lead level. By default, the system does not block ticket closure for incomplete RCAs.

---

### Improve

This is the phase where completed RCA data drives systemic improvement. Actions taken here include:

- Publishing KB articles based on the Fix/Workaround documentation
- Grouping related tickets under Problem Tickets for trend analysis
- Acting on Preventive Measures (bug fixes, configuration changes, process updates, training)
- Updating SLA policies or escalation rules based on patterns seen in RCA data

**RCA involvement:** This phase is entirely powered by the data in the RCA tab. The quality of the Improve phase is directly proportional to the quality of the RCA documentation in the previous phases. Vague root causes produce vague preventive measures and no lasting change.

---

## 7. Tips and Best Practices

### Always Link a KB Article If a Workaround Was Documented

If the Fix/Workaround field describes a repeatable procedure — steps an agent can follow to fix a recurring issue — that content belongs in a KB article, not just buried in a closed ticket. Create the article, publish it, and link it in the **KB Article** field.

Other agents will benefit. The next time the same issue comes in, the ticket can be resolved faster. Customers using the self-service portal can potentially resolve it themselves.

---

### Use Problem Tickets to Link Recurring Issues Together

When you notice the same root cause appearing across multiple tickets, do not treat each ticket in isolation. Create a dedicated **Problem Ticket** that tracks the underlying systemic issue. Link each individual incident ticket to that problem ticket.

This gives managers a single place to track how many customers have been affected, how many times the issue has recurred, and whether preventive measures have actually stopped the recurrence.

---

### Waive Only With a Written Escalation Reason

Waiving an RCA is legitimate. Not every ticket that auto-triggers needs a full investigation. Duplicate tickets, clearly isolated user errors, and one-off configuration mistakes may not warrant the same depth of investigation.

However, a waived RCA with no written reason looks identical to an accidentally skipped one during an audit. Always fill in **Escalation Reason** when waiving. Even a single sentence is enough:

- "Duplicate of Ticket #4821 which has a completed RCA."
- "Isolated user error, no systemic cause. Customer confirmed misconfiguration on their end."
- "One-off hardware failure at customer's site, outside our control. No preventive measures applicable."

---

### Start RCA During Resolution, Not After Closure

The best time to fill the Root Cause and Fix fields is while you are actively working on the ticket — when the details are fresh and the investigation context is in your head. Agents who defer RCA to after ticket closure often find they have forgotten the specifics, leading to generic, low-quality documentation.

Get into the habit of treating the RCA tab as a live investigation log, not an after-action report.

---

### Keep Root Cause Descriptions Specific and Actionable

The root cause field is the most important field in the RCA. A vague root cause leads to vague preventive measures and no real improvement.

| Poor root cause | Better root cause |
|-----------------|-------------------|
| "System error" | "Null pointer exception in the invoice generation service when the customer's address has no postcode set" |
| "User didn't know how to use the feature" | "The export button requires a date range to be set first, but no validation message is shown — the button silently does nothing, leading users to think the feature is broken" |
| "Network issue" | "The API call to the payment processor has a hardcoded 3-second timeout. Under peak load, the processor takes 5-8 seconds to respond, causing all payment submissions to fail" |

The test of a good root cause: could an engineer or product manager read it and know exactly what to fix, even with no other context?

---

### Monitor RCA Completion Rates as a Team Metric

Support managers should track the ratio of:

- Tickets where RCA was triggered (auto or manual)
- Tickets where RCA Status = Completed vs. Pending / In Progress

A growing backlog of Pending RCAs is an early warning sign that the team is under-resourced, that RCA is being deprioritized, or that agents need better tooling or training.

A healthy team should be completing RCAs within 2-3 business days of ticket resolution for Critical tickets, and within 5 business days for High priority.

---

### Review RCA Data in Retrospectives

Completed RCAs are the raw material for team retrospectives. At the end of each sprint or monthly review cycle, pull all completed RCAs and look for:

- Which root causes appeared more than once?
- Which preventive measures were promised but not delivered?
- Which KB articles were created as a result of RCA findings?
- Are there problem tickets with a high number of linked incidents?

This review closes the loop from **Improve** back to **Triage** — the insights from last month's incidents shape how this month's incidents are handled.

---

## Appendix A — Field Reference Summary

| Field | Type | Auto-Populated | Required for Completion |
|-------|------|---------------|------------------------|
| RCA Required | Checkbox | Yes (on trigger) | — |
| RCA Status | Select | No (default: Pending) | — |
| RCA Trigger Reason | Read-only text | Yes | — |
| Root Cause | Long text | No | Yes |
| Fix / Workaround | Long text | No | Yes |
| Preventive Measures | Long text | No | Recommended |
| KB Article | Link | No | No |
| Problem Ticket | Link | No | No |
| Escalation Reason | Long text | No | Required if Waived |
| Completed By | Link (User) | Yes (on Complete) | — |
| Completed On | Datetime | Yes (on Complete) | — |

---

## Appendix B — Quick-Start Checklist for Agents

When you pick up a ticket with the RCA tab flagged:

- [ ] Read the **RCA Trigger Reason** to understand why it was flagged
- [ ] Set **RCA Status = In Progress** when you begin the investigation
- [ ] Fill **Root Cause** — be specific, describe the underlying cause
- [ ] Fill **Fix / Workaround** — note whether this is permanent or temporary
- [ ] Fill **Preventive Measures** — describe what should stop this recurring
- [ ] Link a **KB Article** if a workaround procedure was documented
- [ ] Link a **Problem Ticket** if this is a recurring issue
- [ ] If waiving, fill **Escalation Reason** with the reason
- [ ] Set **RCA Status = Completed** — system stamps Completed By and Completed On

---

*This guide covers the RCA feature as built into Frappe Helpdesk. For questions about the implementation or for reporting issues with the RCA tab behavior, contact the development team.*
