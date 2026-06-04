# Changelog Draft

## 2026-06-04

- feat(hrms): send welcome email on new Employee creation — added `send_welcome_email` doc-event handler to `hrms/overrides/employee_master.py`; registered as additional `after_insert` handler in `hooks.py`; email priority: `prefered_email` > `personal_email` > `company_email`; silently skips if no email; exceptions are logged via `frappe.log_error` and never propagate so employee creation is never blocked.



- fix(task-assignment-board): resolve 11 bugs — C-1 add `task_assignees` Table field to Task DocType JSON + migrate; C-2 fix show_completed filter logic (was using identical branches); C-4 replace doc.save() with frappe.db.delete/insert in reassign_task to skip full validation chain; C-5 guard Gantt popup JSON.parse against null _assign and missing user info; M-1 add VALID_STATUSES whitelist + close_all_assignments on Completed in update_task_status; M-2 add frappe.has_permission write-check to both reassign_task and update_task_status; M-3 validate user exists before child table write and move _assign clear after write succeeds; M-8 remove def __(msg) shim and replace with frappe._(); L-2 quote Task ID in CSV export; L-5 guard dragleave handler with relatedTarget check.

## 2026-06-02

- feat(website-settings): Add "Apps Drawer" tab to Website Settings — new child DocType `Website Apps Drawer App` allows admins to set a display name and control app ordering/visibility on the `/apps` page; `/apps` controller updated to read from Website Settings first for company name and apply drawer config ordering and hiding; favicon pipeline verified as already correct (no change needed).
- [2026-06-02] feat(frappe): add Apps Drawer tab to Website Settings + app ordering (branch: Lijish-up)
