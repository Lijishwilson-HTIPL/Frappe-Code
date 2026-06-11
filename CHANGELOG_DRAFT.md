# Changelog Draft

## 2026-06-11 — Projects Module Fix-Batch (pipeline run; NOT committed, release-manager not invoked)

Delegation log (Team Lead). No subagent runtime was available in this session, so the pipeline roles (Developer -> Tester -> Compliance) were executed sequentially by the Team Lead under the stated constraints: file edits only, no bench/DB/git.

- Dev task 1 (A, B, H): Task doctype JSON gains sprint/is_blocked/cancel_reason/resolution_note/sb_subtasks+subtasks_html; stale "Closed" depends_on fixed; task.py TYPE_CHECKING block updated; share_with_project_members batched + called from on_update only on project change; set_tasks_as_overdue rewritten as bulk qb update + per-project rollup; task.js persists resolution_note; cleanup patch v15_0.delete_task_db_only_custom_fields registered at end of patches.txt.
- Dev task 2 (C, F): deleted duplicate fixtures/Workspace.json (hooks.py had no fixtures entry to remove); module workspace Dashboard shortcut replaced by Sprint (shortcuts + serialized content string); Sprint DocType link added under Projects card; Sprint Summary report link added under Reports card; sprint.py date + single-active-sprint validation; new Sprint Summary script report (json/py/js/__init__).
- Dev task 3 (D, E, G): task_assignment_board.py rewritten — frappe.get_list for permission-aware reads, _assign as primary assignee source, sprint filter, doc.save() with check_permission, document-API child-table writes, no frappe.db.commit, queued + HTML-escaped notification email; board JS — XSS escape in confirm dialog, Sprint filter field, status select reverts on server error; task_summary_report.py — _assign primary + child-table fallback, assignee filter on union, dead __style keys removed.
- Dev task 4 (I, J, K, L): task_list.js handler namespacing/de-dup, chips/datalist/observer duplicate guards, set_primary_action monkeypatch removed (hide kept in setTimeout + observer); project_list.js layout background rule scoped to [data-doctype="Project"], chips guard, Open badge label "OPEN"; tasks web form status Closed->Completed; Task Completion Trend based_on completed_on; Overdue Tasks number card now computes overdue dynamically; new static tests for board endpoints and Sprint validation.

## 2026-06-08

- feat(helpdesk/portal): fix support-tracker UI visibility, add activity timeline, register HD Ticket after_insert hook — CSS override added to Web Page HTML so authShell hero text is visible (#ffffff) against Frappe theme injection; portal_api.py updated: get_ticket_detail now returns HD Ticket Activity records as "activity" key; new methods portal_logout, get_user_tickets (alias), get_ticket_details (alias) added; renderActivityTimeline JS function added to portal page slide-over; doc_events in hooks.py updated to register send_ticket_acknowledgment as HD Ticket after_insert; all existing HD Ticket, HD Ticket Activity, and HD Ticket Comment records deleted per user request.
- feat(apps-drawer): add Logo upload per app in Apps Drawer — new `Attach Image` field `logo` added to `Website Apps Drawer App` child DocType JSON; `apps.py` reads the logo column from drawer config and overrides the hook-defined logo for that tile on `/apps`; apps without a drawer logo fall back to the existing hook value unchanged; `bench migrate` applied cleanly; branch: Lijish-up.

## 2026-06-04

- feat(hrms): send welcome email on new Employee creation — added `send_welcome_email` doc-event handler to `hrms/overrides/employee_master.py`; registered as additional `after_insert` handler in `hooks.py`; email priority: `prefered_email` > `personal_email` > `company_email`; silently skips if no email; exceptions are logged via `frappe.log_error` and never propagate so employee creation is never blocked.



- fix(task-assignment-board): resolve 11 bugs — C-1 add `task_assignees` Table field to Task DocType JSON + migrate; C-2 fix show_completed filter logic (was using identical branches); C-4 replace doc.save() with frappe.db.delete/insert in reassign_task to skip full validation chain; C-5 guard Gantt popup JSON.parse against null _assign and missing user info; M-1 add VALID_STATUSES whitelist + close_all_assignments on Completed in update_task_status; M-2 add frappe.has_permission write-check to both reassign_task and update_task_status; M-3 validate user exists before child table write and move _assign clear after write succeeds; M-8 remove def __(msg) shim and replace with frappe._(); L-2 quote Task ID in CSV export; L-5 guard dragleave handler with relatedTarget check.

## 2026-06-02

- feat(website-settings): Add "Apps Drawer" tab to Website Settings — new child DocType `Website Apps Drawer App` allows admins to set a display name and control app ordering/visibility on the `/apps` page; `/apps` controller updated to read from Website Settings first for company name and apply drawer config ordering and hiding; favicon pipeline verified as already correct (no change needed).
- [2026-06-02] feat(frappe): add Apps Drawer tab to Website Settings + app ordering (branch: Lijish-up)
