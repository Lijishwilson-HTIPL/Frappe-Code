# Frappe Development Rules

## DocType Change Rule

**Any time a DocType is created or modified, export it to JSON immediately.**

The database is not the source of truth — the JSON file is.

---

## Why

Frappe stores DocType definitions in the database after you save them in the UI. If you only save to the database and never export to JSON, the change:

- Will not survive a fresh `bench restore`
- Will not be visible in `git diff`
- Will not be applied on another machine via `bench migrate`
- Cannot be code-reviewed or rolled back

Exporting to JSON makes the schema part of the codebase, not just the database.

---

## The Rule

After every DocType change — new field, removed field, renamed field, changed fieldtype, changed options, permission update, naming rule change, anything — run:

```bash
bench --site mysite.local export-doc "DocType" "<DocType Name>"
```

Example:

```bash
bench --site mysite.local export-doc "DocType" "SBIQ Lead"
bench --site mysite.local export-doc "DocType" "SBIQ Deal"
```

This overwrites the JSON file at:

```
apps/<app>//<module>/doctype/<doctype_folder>/<doctype_name>.json
```

Then commit the JSON file to git.

---

## Step-by-Step Workflow

1. Open the DocType in the Frappe desk and make your changes
2. Click **Save** in the UI
3. In the terminal, export the DocType to JSON:
   ```bash
   bench --site mysite.local export-doc "DocType" "<DocType Name>"
   ```
4. Confirm the JSON changed:
   ```bash
   git diff apps/<app>/
   ```
5. Commit the JSON:
   ```bash
   git add apps/<app>/path/to/doctype.json
   git commit -m "feat(DocType): describe what changed and why"
   ```

---

## Applying Changes on Another Machine

When someone pulls the repo and runs:

```bash
bench --site <site> migrate
```

Frappe reads every DocType JSON and syncs the database to match. This is why the JSON must always be up to date — `migrate` reads JSON, not whatever is in someone else's database.

---

## Exporting Multiple DocTypes at Once

To export all DocTypes in an app at once:

```bash
bench --site mysite.local export-fixtures --app <app_name>
```

To export all DocTypes in a module:

```bash
bench --site mysite.local export-doc "DocType" "DocType 1"
bench --site mysite.local export-doc "DocType" "DocType 2"
```

---

## Checklist Before Every Commit

- [ ] Every modified DocType has been exported to JSON
- [ ] `git diff` shows only intentional changes in the JSON
- [ ] No DocType was changed only in the database with no JSON update
- [ ] The commit message names which DocTypes were changed

---

## Custom Fields and Property Setters

Custom Fields and Property Setters added via **Customize Form** also live in the database. Export them as fixtures:

Add to `hooks.py`:

```python
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Your Module"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Your Module"]]},
]
```

Then export:

```bash
bench --site mysite.local export-fixtures --app <app_name>
```

---

## What Happens If You Skip This

| Action | Without JSON export | With JSON export |
|---|---|---|
| `bench migrate` on fresh install | Change is missing | Change is applied |
| `git diff` review | Nothing shows | Change is visible |
| Rollback via `git revert` | Not possible | Works cleanly |
| Another developer pulls the branch | Gets a broken schema | Gets the correct schema |
| DB restore from backup | Change depends on backup date | Change is always in code |

---

## Backup mysite.local

When asked to "backup mysite", run:

```bash
bench --site mysite.local backup --with-files
```

Backup files are saved to:
```
~/frappe-bench/sites/mysite.local/private/backups/
```

Also accessible from Windows at:
```
\\wsl.localhost\Ubuntu-22.04\home\paul\frappe-bench\sites\mysite.local\private\backups\
```

---

## Quick Reference

```bash
# Export one DocType
bench --site mysite.local export-doc "DocType" "<DocType Name>"

# Export all fixtures for an app
bench --site mysite.local export-fixtures --app <app_name>

# Check what changed
git diff apps/

# Apply JSON changes to a database
bench --site mysite.local migrate
```
## rules 