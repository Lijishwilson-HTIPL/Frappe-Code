"""Keep the Task "Assign" tab and frappe's real assignment (ToDo / _assign) in step.

WHY THIS EXISTS
---------------
frappe's "Add to ToDo" dialog (frappe/public/js/frappe/form/assign_to.js) is not a
set of Task fields: it inserts a **ToDo** row, and ToDo.on_update writes the hidden
`_assign` JSON on the Task. So the dialog's fields cannot simply be moved onto a tab.

They also cannot be made mandatory in their native form. The dialog needs a SAVED
document to attach a ToDo to, so "a Task cannot be saved without an assignee" plus
"a Task must be saved before it can be assigned" is a deadlock on every new Task.

The Assign tab is therefore real Custom Fields on Task (see mercury fixtures
custom_field.json). `custom_assign_to` is reqd, which works because it is an
ordinary field and is available before the first save. This module is what turns
that stored value into an actual assignment, so the sidebar "Assign", the
assignee's ToDo list, notifications and document sharing all behave exactly as
they do for the native dialog.

DIRECTION
---------
One way: tab field -> assignment. Assigning through the native sidebar dialog does
NOT write back into `custom_assign_to`. That is deliberate - a reverse sync would
have to guess which of several `_assign` users is "the" assignee, and the field is
mandatory anyway, so it always holds a value.
"""

import frappe
from frappe.desk.form.assign_to import _add as assign_to_add
from frappe.desk.form.assign_to import remove as assign_to_remove

ASSIGN_FIELD = "custom_assign_to"


def sync_assignment(doc, method=None):
	"""Mirror the Assign tab onto a real ToDo assignment. Hooked on Task.on_update.

	on_update (not validate) because a ToDo needs doc.name, which does not exist
	until after the insert.
	"""
	user = doc.get(ASSIGN_FIELD)
	if not user:
		# reqd=1 normally prevents this; a fixture import or a bulk update with
		# ignore_mandatory can still get here. Nothing to mirror - leave any
		# existing assignment alone rather than silently clearing someone's ToDo.
		return

	current = frappe.parse_json(doc.get("_assign") or "[]") or []
	if user in current:
		return

	# Drop assignments this field previously created, so changing the assignee
	# moves the ToDo instead of accumulating one per edit. Closing another user's
	# ToDo is the intended behaviour: the tab field is the single source of truth
	# for who owns the Task.
	for previous in current:
		try:
			assign_to_remove(doc.doctype, doc.name, previous)
		except Exception:
			# A ToDo already closed/deleted by hand must not block the save.
			frappe.log_error(
				title="Mercury: could not clear previous Task assignment",
				message=frappe.get_traceback(),
			)

	assign_to_add(
		{
			"doctype": doc.doctype,
			"name": doc.name,
			"assign_to": [user],
			"description": doc.get("custom_assign_comment") or f"Assignment for Task {doc.name}",
			"date": doc.get("custom_assign_complete_by"),
			"priority": doc.get("custom_assign_priority") or "Medium",
		},
		# The assigner is editing the Task, so they already passed its write
		# permission check; re-running it here fails for roles that can edit a
		# Task but lack explicit read on the assignee's User record.
		ignore_permissions=True,
	)
