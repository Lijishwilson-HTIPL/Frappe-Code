# Coffee Shop — Post-Inventory Full Roadmap Design Spec

**Date:** 2026-06-17
**Author:** Hilton Paul
**Status:** Approved
**Builds on:** `2026-06-16-coffee-shop-inventory-design.md` (Phase 1 — complete)

---

## 1. Overview

This spec defines the 5 phases that follow the completed inventory system for Namibian Coffee Roasters. Together they deliver a full multi-branch coffee shop management platform: drink recipes (BOM), counter sales with automatic ingredient deduction (POS), multi-branch stock isolation, a smart 5-tier sourcing hierarchy that minimises purchasing costs, and a consolidated reporting dashboard for the owner.

**Payment methods:** Cash and Card (generic) for now. Stripe integration is deferred — a teammate is implementing it separately and will be wired in once complete.

---

## 2. Architecture Overview

```
Phase 1 ✅  Inventory Foundation
           Items · Warehouses · Reorder Levels · Low-Stock Alert (Server Script)

Phase 2     Bill of Materials
           BOM per drink → defines raw ingredients + qty per cup

Phase 3     Point of Sale
           POS Profile per branch → barista sells drink
           Server Script on POS Invoice (on_submit) → auto Stock Entry (Manufacture)
           Stock Entry deducts raw ingredients via BOM

Phase 4     Multi-Branch
           One Warehouse per branch
           One POS Profile per branch
           Stock Transfer between branches

Phase 5     Smart Sourcing Hierarchy
           Low-stock alert extended:
             1. Check company head warehouse (free transfer)
             2. Check other branches with surplus (free transfer)
             3. Draft PO → Wholesale Store (cheapest external)
             4. Draft PO → Supermarket (mid-tier fallback)
             5. Draft PO → Small Shop (emergency last resort)

Phase 6     Reporting Dashboard
           6 Script Reports + Custom Workspace + 4 Number Cards
```

Every phase builds on the previous. BOM must exist before POS can deduct ingredients. Multi-branch multiplies the warehouse + POS pattern. Smart sourcing extends the Phase 1 alert script. Reports read from data all prior phases generate.

---

## 3. Phase 2 — Bill of Materials

### 3.1 What it is

A BOM defines the recipe for each finished drink: which raw ingredients and what quantity goes into one cup. Uses the built-in ERPNext `BOM` DocType. No new DocTypes needed.

### 3.2 One BOM per drink (sample)

| Finished Product | Ingredient | Qty | UOM |
|---|---|---|---|
| Espresso (1 cup) | Coffee Beans - Arabica | 0.018 | Kg |
| Espresso (1 cup) | Paper Cups (8oz) | 1 | Nos |
| Latte (1 cup) | Coffee Beans - Arabica | 0.018 | Kg |
| Latte (1 cup) | Full Cream Milk | 0.2 | Litre |
| Latte (1 cup) | Paper Cups (8oz) | 1 | Nos |

Additional drinks follow the same pattern. Every BOM has:
- `Item` = finished drink
- `Quantity` = 1 (one cup)
- `Items` table = raw ingredients + quantities
- `Is Default` = ✓
- `Is Active` = ✓

### 3.3 How Phase 3 uses it

When POS sells 1 Latte, a Server Script reads the default BOM for Latte, multiplies ingredient quantities by qty sold, and creates a `Stock Entry (type: Manufacture)` that consumes raw ingredients and produces the finished drink — all in one transaction.

---

## 4. Phase 3 — Point of Sale + Auto Ingredient Deduction

### 4.1 ERPNext components

- `POS Profile` — one per branch, sets warehouse, payment methods, visible items
- `POS Invoice` — created when a barista submits a sale
- `Server Script` on `POS Invoice → on_submit` — reads BOM per invoice line, creates Stock Entry

### 4.2 Auto-deduction flow

```
Barista sells 2 Lattes + 1 Espresso at POS
        │
        └── POS Invoice submitted
                  │
                  └── Server Script fires (on_submit)
                            │
                            ├── For each line item on the invoice:
                            │     1. Find default BOM for that item
                            │     2. Multiply BOM quantities × qty sold
                            │     3. Create Stock Entry (Manufacture):
                            │           Source Warehouse: branch warehouse
                            │           Consumes: raw ingredients (calculated qty)
                            │           Produces: finished drinks (matches invoice qty)
                            │
                            └── Phase 1 low-stock alert fires automatically
                                if any ingredient drops below reorder level
                                → triggers Phase 5 sourcing hierarchy
```

### 4.3 Key rules

- If no BOM exists for a sold item, skip the Stock Entry — just record the sale
- Stock Entry is linked back to the POS Invoice via `custom_pos_invoice` field for traceability
- If Stock Entry fails (ingredient out of stock), the error is logged but does NOT roll back the POS Invoice — sale goes through, shortfall flagged for manager

### 4.4 POS Profile configuration per branch

| Field | Value |
|---|---|
| POS Profile Name | `Coffee Shop - [Branch Name]` |
| Warehouse | `Coffee Shop - [Branch Name] - [Abbr]` |
| Company | Namibian Coffee Roasters |
| Payment Methods | Cash, Card |

### 4.5 Payment methods

Cash and Card (generic) are configured now. Stripe will be added as a third payment method once the teammate's integration is complete — no changes to POS Profile structure required, just add the Stripe Payment Gateway Account as an additional row.

---

## 5. Phase 4 — Multi-Branch

### 5.1 One set of components per branch

| Component | Example — Branch 1 | Example — Branch 2 |
|---|---|---|
| Warehouse | `Coffee Shop - Branch 1 - NCR` | `Coffee Shop - Branch 2 - NCR` |
| POS Profile | `POS - Coffee Shop - Branch 1` | `POS - Coffee Shop - Branch 2` |

### 5.2 Key rules

- Each POS Profile is locked to its branch warehouse — baristas only see and deduct their own branch's stock
- BOMs are shared across all branches — one recipe applies everywhere
- Reorder levels are set per item **per warehouse** — branches with higher traffic get higher reorder thresholds
- The Phase 1 alert script reads `doc.warehouse` from the Stock Ledger Entry — fires per branch automatically, no script changes needed

### 5.3 Stock Transfer between branches

Manager creates a `Stock Entry (type: Material Transfer)` in ERPNext UI — deducts from source branch warehouse, adds to destination branch warehouse. Built into ERPNext, no custom code.

### 5.4 Branch naming convention

```
Warehouse:   Coffee Shop - [City/Branch Name] - [Company Abbr]
POS Profile: POS - Coffee Shop - [City/Branch Name]
```

---

## 6. Phase 5 — Smart Sourcing Hierarchy

### 6.1 The business rule

Before spending money externally, check internal sources first — cheapest and fastest first, emergency fallback last.

### 6.2 Five-tier sourcing flow

```
Stock drops below reorder level at any branch
        │
        ▼
Step 1 — Company central warehouse (Head Office)
        Has enough qty? → Stock Transfer (free, no purchase)
        NO ↓
        ▼
Step 2 — Other company branches
        Any branch has surplus above (reorder_level × 1.5)?
        → Stock Transfer from that branch (free, no purchase)
        NO ↓
        ▼
Step 3 — Big Discount / Wholesale Store
        Best external price — bulk buying
        → Create Draft Purchase Order to Wholesale supplier
        NO / not enough ↓
        ▼
Step 4 — Supermarket
        Mid-price, quicker availability
        → Create Draft Purchase Order to Supermarket supplier
        NO / not enough ↓
        ▼
Step 5 — Small Shop
        Last resort — most expensive, emergency only
        → Create Draft Purchase Order to Small Shop supplier
        + Alert: "Emergency sourcing — all preferred sources exhausted"
```

### 6.3 ERPNext setup

| Level | ERPNext entity | Purpose |
|---|---|---|
| Company warehouse | Warehouse `Head Office - NCR` | Central stock, free transfers |
| Branch warehouses | Warehouse per branch | Free internal transfers |
| Wholesale Store | Supplier + Warehouse `Wholesale - NCR` | Bulk external buying |
| Supermarket | Supplier + Warehouse `Supermarket - NCR` | Mid-tier external |
| Small Shop | Supplier + Warehouse `Small Shop - NCR` | Emergency fallback |

External sources (Steps 3–5) each have both a **Supplier** (for raising the PO) and a **Warehouse** (to receive goods when the PO is fulfilled).

### 6.4 Surplus rule

A branch or head warehouse is considered available to donate stock only if:
`actual_qty > (reorder_level × 1.5)`

This prevents robbing one branch to fix another, only to immediately trigger a second alert at the donor.

### 6.5 Manager notifications per outcome

| Outcome | Notification message |
|---|---|
| Transferred from Head Office | "Stock transferred from Head Office — no purchase needed" |
| Transferred from Branch X | "Stock transferred from Branch X — no purchase needed" |
| PO to Wholesale | "Draft PO raised to Wholesale Store" |
| PO to Supermarket | "Wholesale unavailable — Draft PO raised to Supermarket" |
| PO to Small Shop | "Emergency: Draft PO raised to Small Shop — review urgently" |

### 6.6 Implementation approach

The Phase 1 `Low Stock Alert - Coffee Shop` Server Script is extended with the sourcing hierarchy logic. The 24-hour dedup guard (already in Phase 1) applies equally — only one sourcing action per item per 24-hour window.

---

## 7. Phase 6 — Reporting Dashboard

### 7.1 Six Script Reports

| Report name | What it shows |
|---|---|
| Stock Levels by Branch | Current qty vs reorder level per item per warehouse — items below reorder highlighted |
| Daily Sales by Branch | Total sales per branch per day — filterable by date range, branch, item group |
| Top Selling Drinks | Finished products ranked by qty sold |
| Ingredient Cost vs Revenue | Raw material cost (Stock Entry valuation) vs POS invoice revenue per drink — margin per drink |
| Waste & Loss Tracker | Expected consumption (BOM × units sold) vs actual stock deducted — flags spoilage or theft |
| Sourcing History | Every sourcing decision log — which source was used, qty, cost — shows how often emergency sourcing was triggered |

All reports follow the standard 4-file Script Report pattern: `.json` + `.py` + `.js` + `__init__.py`.
Data sources: `Bin`, `POS Invoice`, `Stock Ledger Entry`, `Stock Entry`, `Purchase Order`. No new DocTypes.

### 7.2 Custom Workspace — "Coffee Shop Manager"

```
Namibian Coffee Roasters — Manager Dashboard
│
├── Shortcuts:
│     Stock Balance · POS · Purchase Orders · Stock Transfer
│
├── Reports:
│     Stock Levels by Branch
│     Daily Sales by Branch
│     Top Selling Drinks
│     Ingredient Cost vs Revenue
│     Waste & Loss Tracker
│     Sourcing History
│
└── Number Cards:
      Items below reorder level today (all branches)
      Total sales today (all branches)
      Open Purchase Orders
      Pending Stock Transfers
```

---

## 8. Deferred Items

| Item | Status | Owner |
|---|---|---|
| Stripe payment method in POS | Deferred — teammate implementing | Teammate |
| Stripe integration wired into POS Profile | After teammate completes | Hilton |

---

## 9. Implementation Order

| Phase | Depends on |
|---|---|
| Phase 2 — BOM | Phase 1 (items must exist) ✅ |
| Phase 3 — POS | Phase 2 (BOM must exist for deduction) |
| Phase 4 — Multi-branch | Phase 3 (POS pattern established) |
| Phase 5 — Smart sourcing | Phase 4 (all warehouses exist) |
| Phase 6 — Reporting | Phase 3+ (data must be generating) |
