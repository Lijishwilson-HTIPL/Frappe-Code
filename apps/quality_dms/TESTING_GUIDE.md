# Quality DMS — Manual Testing Guide (post-fix regression pass)

Run these after any change to permissions, workflow, or certificates. Each
section maps to a fix applied on 2026-07-08. **Test as the named role, not as
Administrator** — Administrator bypasses every permission check and will hide
regressions.

## Test accounts (site: erp.local)

| Role | Login | Password |
|---|---|---|
| DMS Approver + Employee | alice.manager@hephzibahtech.com | Alice@1234 |
| Employee | bob.reyes@hephzibahtech.com | Bob@1234 |
| Employee | carla.nunes@hephzibahtech.com | Carla@1234 |
| Employee | david.kim@hephzibahtech.com | David@1234 |
| Employee | dms.trainee1@hephzibahtech.com | Trainee@1234 |

> After code changes: hard-refresh the browser (Ctrl+Shift+R) so updated form
> scripts load. Log out/in to refresh cached permissions.

---

## 1. Document publish workflow (submit permissions)
**Why:** publishing sets docstatus=1; previously no role had submit permission,
so only Administrator could publish.

1. As **Administrator**, create a Document Library record, attach a file, and take
   it through the workflow to **Pending Approval**.
2. Log in as **alice.manager** (DMS Approver). Open the record.
3. Use the workflow action **Publish Document**.
   - **Expect:** it publishes (status → Published, docstatus → 1), no
     "not permitted / no submit permission" error.
4. Confirm on-publish side effects ran: a **DMS Training Record** was created for
   the document, and the previous version was retired.

## 2. Quiz cannot be bypassed
**Why:** the score used to be accepted from the client.

1. As **Administrator**, attach an active **DMS Quiz** to a document and assign
   training on it to bob.
2. As **bob**, open the training record → **Sign My Acknowledgement**.
   - **Expect:** the quiz dialog appears; you must answer and pass to sign.
3. **Negative check (optional, technical):** calling `sign_acknowledgement` with
   an `assessment_score` on a quiz document must be rejected with a message
   telling you to use the quiz flow. (Verified server-side.)

## 3. Uploaded document files get organized
**Why:** the organizing hook (`after_save`) never fired; renamed to `on_update`.

1. As **Administrator**, create/edit a Document Library record and upload a file.
2. Check the File Manager / folder structure — the file should be organized into
   the DMS folder tree (not left loose). No error in the console.

## 4. Certificate regenerates on retraining
**Why:** the retraining reset kept the old certificate.

1. Verify a training record so a certificate is generated for an employee.
2. Simulate expiry (set the row's `expires_on` to a past date) and run the daily
   job `check_training_expiry`.
   - **Expect:** the row resets to Pending, the **old certificate file is
     deleted**, and `certificate_file` is cleared.
3. Have the employee re-complete; verify again.
   - **Expect:** a **new** certificate is generated with the current date/version.
4. Confirm a **Cancelled** record's rows are NOT reopened by the expiry job.

## 5. Ungated endpoints
**Why:** `acknowledge_document` allowed forging completion on any document.

1. As **carla**, try to acknowledge a document she is **not** assigned to
   (via the Acknowledge button on a document she can't see, or API).
   - **Expect:** blocked ("not assigned to you" / not permitted).
2. As **bob**, acknowledge a document he **is** assigned to.
   - **Expect:** works normally.

## 6. XSS escaping in document panels
**Why:** file names / audit fields were injected into HTML unescaped.

1. As **Administrator**, upload a file to a document with a name containing HTML,
   e.g. `test<img src=x onerror=alert(1)>.pdf`.
2. Open the document as any user and view the Version History / preview panel.
   - **Expect:** the name renders as literal text; **no** alert/script runs.

## 7. Check-out / check-in
**Why:** the buttons errored for non-admins; the lock bypassed write permission
and had a race.

1. As **alice** (approver — a DMS role), open a Published document → **Check Out**.
   - **Expect:** works (no permission error), lock shows her name.
2. As **bob**, try to check the same document out.
   - **Expect:** "already checked out by …" message; he cannot steal the lock.
3. As **alice** (or an admin) → **Check In**. Lock clears.

## 8. Certificate privacy (approver included)
**Why:** approvers could list other employees' personal certificates.

1. As **alice** (DMS Approver), open **File Storage / File list**.
   - **Expect:** she does **not** see other employees' `*-certificate.pdf` files
     (only her own, if any). Non-certificate files are still visible to her.
2. As **bob**, confirm he sees only his own certificate(s).
3. Direct URL: as bob, open another employee's certificate
   `/private/files/TRN-...-HR-EMP-<other>-certificate.pdf`.
   - **Expect:** HTTP 403.

## 9. Document Request lifecycle
**Why:** terminal requests could be resurrected; revision approval could silently
create nothing.

1. As **alice**, approve then try to set an **Approved** or **Rejected** request
   back to **Pending**.
   - **Expect:** blocked ("already Approved/Rejected … raise a new request").
2. Raise a **Revision** request against a document, then **delete/obsolete** that
   document, then approve the request.
   - **Expect:** approval is rejected with a clear message (not a silent no-op);
     the request does **not** end up Approved-with-nothing-created.
3. **New Document** / **Revision** approval still auto-creates the draft and the
   requester can open it (see section 11).

## 10. Workspace home page
1. Open **DMS** workspace. All shortcut count badges load; the two Work Queue
   quick lists render.
   - **Expect:** no broken **Training Gap Analysis** link (removed); all report
     links open.

## 11. Employee document visibility (regression)
**Why:** employees must see only assigned / requested / own documents.

1. As **carla**, open **Document Library**.
   - **Expect:** only her assigned + requested documents; not the whole library.
2. Open her assigned document → the file renders embedded in the training record.
3. Try a direct URL to an unassigned document.
   - **Expect:** "Not permitted".

## 12. Personal certificate (regression)
1. As **bob**, on a Verified training record click **My Certificate**.
   - **Expect:** opens **his** certificate, showing his name + Employee ID.
2. He cannot open another employee's certificate (section 8.3).

---

### Quick automated re-check
A scripted check of the highest-risk fixes lives in the review notes; re-run the
equivalent of `verify_fixes.py` (submit perms, acknowledge gate, approver cert
scoping, request terminal guard, quiz bypass) in `bench console` after upgrades.
