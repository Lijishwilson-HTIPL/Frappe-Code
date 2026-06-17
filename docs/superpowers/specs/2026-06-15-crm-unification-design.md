# CRM Unification Layer — Design Spec

**Date:** 2026-06-15
**Status:** Approved (brainstorming complete)
**Author:** Claude (ultracode brainstorming session)
**App:** `crm_unify` (new, separate custom app — zero core edits to `erpnext` or `crm`)

---

## 0. Decisions locked

| Decision | Choice | Consequence |
|---|---|---|
| Frontend strategy | **Option B** — new Vue 3 SPA in `crm_unify`, ERPNext-native | Custom app ships its own Vite/frappe-ui build, mounted on an ERPNext workspace. Delivered incrementally (vanilla dashboard first, Vue last). |
| Data direction | **Bidirectional** — keep CRM→ERPNext conversion + add targeted ERPNext→CRM write-back | Narrow, explicit doc-event hooks keyed on the existing `crm_deal` link. **Not** a general sync engine. |
| Duplicate matching | **Auto-match on shared Contact email/phone** | No schema change; person/account identity keyed on Frappe `Contact.email_ids`/`phone_nos`. |

**Hard constraints:** no ERPNext core edits, no Frappe CRM core edits, all customization in `crm_unify`, upgrade-safe, future-compatible.

---

## 1. Gap Analysis (evidence-backed)

Verified ground truth: `crm` and `erpnext` are installed on **one site** (`mysite.local`) backed by **one MariaDB schema** (`_c059e81fe917cb98`). Every table is joinable in a single `frappe.db` transaction → **a replication/sync engine is unjustified and would be an anti-pattern.**

| Capability | ERPNext | Frappe CRM | Gap / action |
|---|---|---|---|
| Lead | `Lead`: single Select `status`, no `converted`, separate `qualification_status`, owner `lead_owner` | `CRM Lead`: `status`→`CRM Lead Status` master (position/color/type) + `converted` checkbox + bench-local inquiry fields | Two un-linked Lead populations; show side-by-side with source badges, de-dup on Contact email/phone. Confirm bench-local CRM Lead fields are committed to JSON. |
| Opportunity / Deal | `Opportunity`: `status` (Open/Quotation/Converted/Lost/Replied/Closed) **+** `sales_stage`→`Sales Stage` master; owner `opportunity_owner` | `CRM Deal`: `status`→`CRM Deal Status` master (position/color/type/probability); owner `deal_owner`; `deal_value`/`expected_deal_value`, multi-currency | Map `sales_stage`↔`CRM Deal Status`. **No `Won` status exists on Opportunity** — fix the dashboard's won metric. Standardize owner = `opportunity_owner`/`deal_owner`. **No join key Opportunity↔CRM Deal** (write-back out of scope unless a key is added). |
| Account / company | `Prospect` (aggregates leads/opps/notes); `Customer` links upstream via `lead_name`+`prospect_name` | `CRM Organization` (website/industry/territory/revenue/address) | No link between `CRM Organization` and `Prospect`/`Customer`. Account-360 joins heuristically on company_name/website/industry. |
| Bridge / join keys | `crm_deal` Data field on Customer/Quotation/Sales Invoice + `Prospect.crm_deal` — **created at runtime, absent from JSON** | `erpnext_customer` + `erpnext_invoice` on CRM Deal — added imperatively + via patch, **not in JSON**, not fixtures | **Risk:** fresh `migrate` without enabling the Single = fields missing → joins break. `crm_unify` MUST ship these as Custom Field fixtures. |
| Activity / timeline | `crm-dashboard` page merges `Communication` (Lead/Opportunity/CRM Lead/CRM Deal); legacy charts ERPNext-only | `activities.py` merges 8 sources: Version, Comment, Communication, File, CRM Call Log, FCRM Note, CRM Task, status_change_log + lead→deal carry-over | Unified timeline replicates the 8-source merge + folds in ERPNext-side Communication/ToDo on the same Contact. Scope Call Log/Note to references (currently global). |
| Sync / resilience | None — on-demand reads; bridge writes run inline in deal save | None dedicated; conversion synchronous on `CRM Deal.on_update` | No retry/queue; **no idempotency guard → duplicate Sales Invoices** on re-saving a Won deal. This is conversion hardening, not a sync engine. |
| Frontend stack | No Vue/Vite/frappe-ui (esbuild plain JS); `crm-dashboard` is vanilla JS | Standalone Vue 3 SPA (Vite, Pinia, vue-router base `/crm`, frappe-ui 0.1.261, socket.io) at `/crm` | A custom app must introduce its own Vite build + explicitly wire the bundle (`page_js`/`app_include_js`). Reuse **frappe-ui library**, never CRM composite `.vue` components (not upgrade-safe). |

### Confirmed defects (to fix in Phase 1–2)
1. **Won metric always 0** — `crm_dashboard.py` filters `Opportunity.status == "Won"`, but `Won` is not a valid option (Open/Quotation/Converted/Lost/Replied/Closed).
2. **Owner mis-attribution** — pipeline renders document `owner`, not `opportunity_owner`.
3. **Unscoped activity** — CRM Call Log / FCRM Note pulled globally, leaking unrelated rows.
4. **Bridge fields not in JSON** — violates CLAUDE.md rule #1/#4; breaks on fresh migrate.
5. **Duplicate Sales Invoices** — `create_invoice_in_erpnext` writes back via `set_value` with no existing-invoice guard; `CRM Deal.on_update` re-enters on every save where `status == deal_status`.

---

## 2. Unified CRM Architecture

```
                ┌─────────────────────────────────────────────┐
                │   crm_unify (custom app — zero core edits)    │
                │                                               │
  ERPNext desk  │  ┌─────────────┐   ┌──────────────────────┐  │
  workspace ────┼─▶│ Vue 3 SPA   │──▶│ Whitelisted services │  │
  shortcut      │  │ (Vite +     │   │  - DashboardService  │  │
                │  │  frappe-ui  │   │  - LeadJourneyService│  │
                │  │  + Pinia)   │   │  - AnalyticsService  │  │
                │  └─────────────┘   │  - CommunicationSvc  │  │
                │        ▲           │  - Customer360Svc    │  │
                │        │ realtime  │  - ConversionService │  │
                │        │ (socket)  └──────────┬───────────┘  │
                │  ┌─────┴───────────┐          │ frappe.db    │
                │  │ doc_events:     │          ▼ (single txn) │
                │  │  CRM Deal→ERPN  │   ┌──────────────────┐  │
                │  │  ERPN→CRM Deal  │   │  ONE MariaDB      │  │
                │  │ (write-back)    │   │  schema           │  │
                │  └─────────────────┘   │  tabCRM Lead/Deal │  │
                │  Fixtures: bridge      │  tabLead/Opp/...  │  │
                │  custom fields + PS    │  tabContact/Addr  │  │
                └────────────────────────┴──────────────────┴──┘
                Reuses (does NOT rebuild): ERPNext CRM Settings write bridge,
                get_dashboard_data read contract, shared Contact/Address graph.
```

**Principle:** read directly from the shared DB; write only at explicit conversion moments; never replicate.

---

## 3. Data Synchronization Strategy (reframed)

There is **no replication**. "Sync" reduces to two explicit, bounded mechanisms:

### 3a. CRM → ERPNext (already ships — reuse + harden)
- Trigger: `CRM Deal.on_update` where `status == ERPNext CRM Settings.deal_status` (currently `Won`).
- Effect: create/locate ERPNext `Customer` (+ contacts/address, deduped) and (local customization) a `Sales Invoice`.
- **Harden:** idempotency guard (skip if `CRM Deal.erpnext_invoice` set or a Sales Invoice with that `crm_deal` exists); optional `frappe.enqueue` with retry; audit via new `CRM Conversion Log`.

### 3b. ERPNext → CRM write-back (NEW — targeted, bounded)
Keyed on the existing `crm_deal` link. Enqueued (non-blocking), idempotent (write only on change), guarded. New read-only Custom Fields on `CRM Deal` shipped as fixtures.

| Source doc (filter `crm_deal` set) | Event | Fields mirrored → CRM Deal |
|---|---|---|
| `Customer` | `on_update` | `territory`, `customer_group`, `website`, `default_currency` → Deal/Organization |
| `Sales Invoice` | `on_update`/`on_submit` | `status` → `erpnext_invoice_status`; `outstanding_amount` → `erpnext_invoice_outstanding` |
| `Quotation` | `on_submit`/`on_update` | `name` → `erpnext_quotation`; `status` → `erpnext_quotation_status`; `grand_total` |

Every write-back sets `erpnext_last_synced` (Datetime) on the Deal and only writes when a value actually changed (prevents save loops).

**Out of scope:** `Opportunity`↔`CRM Deal` write-back — no join key exists. Adding one (an `opportunity`/`crm_deal` link) is a documented future option, not in this spec.

### 3c. Duplicate matching
- Person identity = shared Frappe `Contact` (`email_ids`/`phone_nos`). The two Lead populations and CRM Organization vs Prospect/Customer are associated by matching on Contact email/phone at read time.
- Automatic association (no manual queue). False-match safety: exact email match preferred; phone normalized; company name only as a tiebreaker.

---

## 4. Entity Mapping

| Concept | Frappe CRM | ERPNext | Shared / join |
|---|---|---|---|
| Person | (denormalized fields) + `CRM Contacts` child → `Contact` | `Contact` via Dynamic Link `links` | **`Contact`** (`email_ids`/`phone_nos`) |
| Address | `CRM Organization.address` → `Address` | `Address` via Dynamic Link `links` | **`Address`** |
| Lead | `CRM Lead` (status master + `converted`) | `Lead` (Select status) | Contact email/phone (no FK) |
| Deal / Opportunity | `CRM Deal` (status master, `deal_value`) | `Opportunity` (status + `sales_stage`) | none (no FK) |
| Account / company | `CRM Organization` | `Prospect` → `Customer` | heuristic: company_name/website/industry |
| Won-deal endpoint | `CRM Deal` (status Won) | `Customer` + `Sales Invoice` | **`crm_deal`** field (bridge) |
| Stage master | `CRM Deal Status` / `CRM Lead Status` (position/color/type) | `Sales Stage`; `Lead.status` options | — |
| Activity primitives | `CRM Call Log`, `FCRM Note`, `CRM Task`, `status_change_log` | `Communication`, `ToDo` | `Communication`, `Comment`, `Version`, `File` (core) |

---

## 5. Frontend Architecture (Phase 4)

- **Stack:** Vue 3 (Composition API) + Vite + frappe-ui + Pinia + vue-router (`createWebHistory('/crm-unify')`).
- **Mount:** `<app>.bundle.js` built via `bench build --app crm_unify`, **explicitly** loaded through `hooks.page_js` (or `app_include_js`) and mounted onto `.layout-main-section` in `on_page_load`. *(The orphaned `sbiq_provisioner.bundle.js` proves a bundle that is built but not wired never loads.)*
- **Auth/realtime:** free — same `sid` cookie + `window.csrf_token`; replicate `socket.js` wiring (`socketio_port` from `common_site_config`) to subscribe to `crm_customer_created`, `crm_invoice_created`, and new write-back events.
- **Upgrade safety:** depend on the **frappe-ui library** only; never import CRM Pinia stores, the `@` alias, or CRM `.vue` composites (unpinned internal `frappe-ui 0.1.261`, ~92 `createResource` calls coupled to CRM doctypes).
- **Reusable components:** `CRMStatCard`, `LeadJourneyTimeline`, `PipelineBoard` (drag via `sortablejs`), `Customer360Panel`, `ActivityFeed`, `CommunicationPanel`, `AnalyticsWidgets`, `FollowUpWidget`, `LeadSummaryDrawer`.

---

## 6. Backend Architecture

Service modules under `crm_unify/api/`, each a set of `@frappe.whitelist()` methods:

| Service | Methods (indicative) | Notes |
|---|---|---|
| DashboardService | `get_unified_crm_data()` | Preserves the existing `get_dashboard_data` contract (`kpis`, `erpnext_opportunities`, `crm_deals`, `*_statuses`, `*_leads`, `crm_tasks`, `activities`). Fixes Won/owner/scoping bugs. |
| LeadJourneyService | `get_lead_journey(name)` | Kanban columns from `CRM Lead Status`/`Lead.status` dynamically. |
| AnalyticsService | `get_funnel()`, `get_owner_territory()` | Combined metrics computed in Python (single-app Number Cards can't aggregate). |
| CommunicationService | `get_timeline(doctype, name)` | 8-source merge + ERPNext-side Communication/ToDo. |
| Customer360Service | `get_account_360()`, `get_contact_360()` | Joins CRM Organization↔Prospect/Customer; Contact-keyed. |
| ConversionService | `convert_deal()`, idempotency + audit | Wraps/hardens existing bridge; writes `CRM Conversion Log`. |

**Every API:** role check (`Sales Manager`/`Sales User`/`CRM User`/`System Manager`), `frappe.has_permission` per doctype, pagination (`limit_start`/`limit_page_length`), cached status masters, no PII (no raw phone/email senders) in feed payloads.

---

## 7. Workspace Design

App-owned `crm_unify/workspace/crm_unify/crm_unify.json` (JSON, no fixtures needed) with shortcuts: **CRM Dashboard, Leads, Lead Journey, Pipeline, Customer 360, Communications, Activities, Analytics**. Surfaced in the ERPNext apps drawer.

---

## 8–10. Lead Journey / Dashboard / Customer 360
Vue views over §6 endpoints. Lead Journey = horizontal timeline driven by `status_change_log` + status masters. Dashboard = KPI strip + tabs (Pipeline/Lead Journey/Leads/Tasks/Activity), extended with Accounts + Funnel. Customer 360 = account header (CRM Organization⋈Prospect/Customer) + contacts + deals/opps + invoices + unified timeline.

## 11. Realtime Event Architecture
Reuse `crm_customer_created`/`crm_invoice_created`; emit new `crm_unify_writeback` on each ERPNext→CRM mirror. Vue subscribes for live KPI/board refresh.

## 12. Security Design
Role-gated whitelisted methods; per-doctype `has_permission`; no PII in aggregated feeds; write-back hooks run with explicit permission context; `CRM Conversion Log` is the audit trail. No new public/guest endpoints.

## 13. Performance Optimization
Single-roundtrip unified endpoint; pagination on all lists; status masters cached; write-backs enqueued (non-blocking ERPNext saves); idempotent guards prevent redundant writes.

## 14. Deployment Strategy
`crm_unify` installed on `mysite.local`; **`bench build --app crm_unify` wired into the deploy flow** (esbuild glob is per-app); fixtures auto-import on `bench migrate`. Machine-specific files untouched (CLAUDE.md rule 3b). `site_config.json` never touched (rule 3).

## 15. Migration Strategy
Bridge Custom Fields + Property Setter shipped as **fixtures** (JSON source of truth) so a fresh `migrate`/`restore` reproduces them **without** enabling the Single. Reconcile with `ERPNext CRM Settings.create_custom_fields` (Custom Field creation is idempotent by name) so they don't double-create.

## 16. Implementation Roadmap

| Phase | Goal | Key deliverables | Depends |
|---|---|---|---|
| **0 — Foundation** | Scaffold app + durable bridge schema (no UI) | `bench new-app crm_unify`; hooks shell; bridge Custom Fields + Quotation Property Setter as fixtures; new write-back read-only fields on CRM Deal; `bench build` wired; verify Single enabled/same-site | — |
| **1 — Unified read + bug fixes** | Cross-app command center, correctness | `get_unified_crm_data` in app; fix Won metric, owner, activity scoping; dynamic Kanban columns; app workspace | 0 |
| **2 — Conversion + write-back** | Idempotent, resilient, bidirectional at conversion points | Invoice idempotency guard; optional enqueue+retry; `CRM Conversion Log`; ERPNext→CRM write-back doc_events (§3b) | 1 |
| **3 — Auto-match** | De-dup across apps | Contact email/phone matching service; surfaced in lists/360 | 1 |
| **4 — Vue SPA + 360/analytics** | Modern ERPNext-native UI | Vite/frappe-ui/Pinia SPA; Pipeline/Lead Journey/Customer 360/Analytics/Activity; realtime; cross-app funnel + owner/territory | 1 (uses 2/3 data) |

---

## Phase 0 — detailed acceptance criteria (implementing now)

1. **App scaffolded:** `apps/crm_unify` created via `bench new-app crm_unify`, added to `apps.txt`, installed on `mysite.local`. `modules.txt`, `hooks.py` present.
2. **Bridge fields as fixtures** (`crm_unify/fixtures/custom_field.json`, `property_setter.json`):
   - ERPNext side: `crm_deal` (Data, read-only) on **Customer, Quotation, Sales Invoice, Prospect**.
   - CRM side on **CRM Deal**: `erpnext_customer` (Data, RO), `erpnext_invoice` (Data, RO) — reconciled with existing imperative creation.
   - **New write-back fields on CRM Deal:** `erpnext_invoice_status` (Data, RO), `erpnext_invoice_outstanding` (Currency, RO), `erpnext_quotation` (Data, RO), `erpnext_quotation_status` (Data, RO), `erpnext_last_synced` (Datetime, RO).
   - Property Setter: `Quotation.quotation_to` link_filters include CRM Deal.
3. **Reconciliation:** enabling `ERPNext CRM Settings` after a fresh migrate does not create duplicates (idempotent by field name).
4. **Build wired:** `bench build --app crm_unify` succeeds and is documented in the deploy flow.
5. **Verified:** `ERPNext CRM Settings` on `mysite.local` is `enabled=1`, `is_erpnext_in_different_site=0`; documented.
6. **Clean diff:** `git diff` shows only the new `crm_unify` app + fixtures. No core edits to `erpnext`/`crm`. `site_config.json`, `Procfile`, `config/redis_*` untouched.
7. **Fresh-migrate proof:** on a fresh `bench migrate` (setting NOT enabled), all bridge fields exist (because fixtures import).

---

## Risks (carried from audit)
- Bridge join-keys absent from JSON → must ship as fixtures (Phase 0). ✔ addressed.
- Duplicate-invoice risk → Phase 2 idempotency. 
- Won-counter = 0 bug → Phase 1.
- Vue bundle builds but doesn't auto-load → explicit `page_js` wiring (Phase 4).
- Reusing CRM `.vue` composites unsafe → frappe-ui library only.
- Deploy must run `bench build --app crm_unify` → Phase 0 deliverable.
- `crm` version discrepancy (Installed 2.0.0-dev vs apps.json 1.69.1) → confirm before relying on conversion features.
- Bench-local CRM Lead fields + local Sales-Invoice flow are non-upstream → confirm committed to JSON before treating as first-class.
