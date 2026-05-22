"""
Creates a professional custom print format for Sales Invoice.

Run via:
    bench --site mysite.local execute crm.demo.create_invoice_print_format.run
"""

import frappe


def run():
    frappe.set_user("Administrator")

    name = "SBIQ Professional Invoice"

    if frappe.db.exists("Print Format", name):
        pf = frappe.get_doc("Print Format", name)
    else:
        pf = frappe.new_doc("Print Format")
        pf.name = name

    pf.doc_type = "Sales Invoice"
    pf.module = "Accounts"
    pf.custom_format = 1
    pf.print_format_type = "Jinja"
    pf.standard = "No"
    pf.html = get_html()

    pf.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"Print format '{name}' saved.")


def get_html():
    return r"""
{%- set company = frappe.get_doc("Company", doc.company) -%}
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 13px;
    color: #1a202c;
    background: #fff;
    padding: 0;
  }

  /* ── Page wrapper ── */
  .page {
    max-width: 860px;
    margin: 0 auto;
    padding: 48px 52px;
    background: #fff;
  }

  /* ── Header ── */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 40px;
    padding-bottom: 32px;
    border-bottom: 2px solid #1e3a5f;
  }

  .brand-block {}
  .brand-name {
    font-size: 26px;
    font-weight: 700;
    color: #1e3a5f;
    letter-spacing: -0.5px;
    line-height: 1;
  }
  .brand-tagline {
    font-size: 11px;
    color: #718096;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .company-details {
    text-align: right;
    font-size: 12px;
    color: #4a5568;
    line-height: 1.7;
  }
  .company-details strong {
    display: block;
    font-size: 13px;
    color: #1a202c;
    font-weight: 600;
    margin-bottom: 2px;
  }

  /* ── Invoice title band ── */
  .invoice-band {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #1e3a5f;
    color: #fff;
    border-radius: 10px;
    padding: 18px 26px;
    margin-bottom: 32px;
  }
  .invoice-band h1 {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  .invoice-band .inv-meta {
    text-align: right;
  }
  .invoice-band .inv-meta p {
    font-size: 12px;
    color: #a0aec0;
    line-height: 1.6;
  }
  .invoice-band .inv-meta span {
    color: #fff;
    font-weight: 600;
  }

  /* ── Status badge ── */
  .status-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-left: 12px;
    vertical-align: middle;
  }
  .status-paid    { background: #c6f6d5; color: #276749; }
  .status-unpaid  { background: #fed7d7; color: #9b2c2c; }
  .status-draft   { background: #e2e8f0; color: #4a5568; }

  /* ── Bill to / from ── */
  .parties {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 32px;
  }
  .party-box {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 20px;
  }
  .party-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #718096;
    margin-bottom: 10px;
  }
  .party-name {
    font-size: 15px;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 4px;
  }
  .party-detail {
    font-size: 12px;
    color: #4a5568;
    line-height: 1.7;
  }

  /* ── Dates row ── */
  .dates-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 32px;
  }
  .date-box {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: center;
  }
  .date-box .date-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #718096;
    font-weight: 600;
    margin-bottom: 4px;
  }
  .date-box .date-value {
    font-size: 13px;
    font-weight: 700;
    color: #1e3a5f;
  }

  /* ── Items table ── */
  .items-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 28px;
  }
  .items-table thead tr {
    background: #1e3a5f;
    color: #fff;
  }
  .items-table thead th {
    padding: 11px 14px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    text-align: left;
  }
  .items-table thead th:last-child,
  .items-table thead th.right { text-align: right; }
  .items-table thead th.center { text-align: center; }

  .items-table tbody tr { border-bottom: 1px solid #edf2f7; }
  .items-table tbody tr:nth-child(even) { background: #f7fafc; }
  .items-table tbody tr:hover { background: #ebf8ff; }

  .items-table tbody td {
    padding: 13px 14px;
    font-size: 12.5px;
    color: #2d3748;
    vertical-align: top;
  }
  .items-table tbody td.right { text-align: right; }
  .items-table tbody td.center { text-align: center; }
  .items-table tbody td .item-name { font-weight: 600; color: #1a202c; }
  .items-table tbody td .item-desc { font-size: 11.5px; color: #718096; margin-top: 2px; }

  /* ── Totals ── */
  .totals-section {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 32px;
  }
  .totals-box {
    width: 320px;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
  }
  .totals-row {
    display: flex;
    justify-content: space-between;
    padding: 10px 18px;
    font-size: 13px;
    border-bottom: 1px solid #e2e8f0;
  }
  .totals-row:last-child { border-bottom: none; }
  .totals-row .label { color: #718096; }
  .totals-row .value { font-weight: 600; color: #1a202c; }
  .totals-row.grand {
    background: #1e3a5f;
    padding: 14px 18px;
  }
  .totals-row.grand .label,
  .totals-row.grand .value { color: #fff; font-weight: 700; font-size: 15px; }

  /* ── Payment / Bank details ── */
  .payment-section {
    background: #f0f7ff;
    border: 1px solid #bee3f8;
    border-radius: 10px;
    padding: 20px 22px;
    margin-bottom: 28px;
  }
  .payment-section h3 {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #2b6cb0;
    margin-bottom: 12px;
  }
  .payment-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 24px;
    font-size: 12px;
  }
  .payment-grid .key { color: #718096; }
  .payment-grid .val { color: #1a202c; font-weight: 600; }

  /* ── Notes / Terms ── */
  .notes-section {
    background: #fffbeb;
    border-left: 4px solid #f6ad55;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-bottom: 28px;
    font-size: 12px;
    color: #7b341e;
    line-height: 1.7;
  }
  .notes-section strong { display: block; color: #c05621; margin-bottom: 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; }

  /* ── Stripe reference ── */
  .stripe-ref {
    background: #f0e7ff;
    border: 1px solid #d6bcfa;
    border-radius: 8px;
    padding: 12px 18px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
  }
  .stripe-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #805ad5; flex-shrink: 0;
  }
  .stripe-ref .ref-label { color: #553c9a; font-weight: 600; margin-right: 8px; }
  .stripe-ref .ref-value { color: #44337a; font-family: monospace; font-size: 11.5px; }

  /* ── Footer ── */
  .footer {
    border-top: 1px solid #e2e8f0;
    padding-top: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .footer-left { font-size: 11px; color: #a0aec0; line-height: 1.6; }
  .footer-right { text-align: right; font-size: 11px; color: #a0aec0; }
  .footer-brand { font-weight: 700; color: #1e3a5f; }

  /* ── Print ── */
  @media print {
    body { padding: 0; }
    .page { padding: 28px 32px; }
  }
</style>
</head>
<body>
<div class="page">

  <!-- ── HEADER ── -->
  <div class="header">
    <div class="brand-block">
      <div class="brand-name">{{ doc.company }}</div>
      <div class="brand-tagline">Official Tax Invoice</div>
      {% if company.website %}
        <div style="font-size:11px;color:#718096;margin-top:6px;">{{ company.website }}</div>
      {% endif %}
    </div>
    <div class="company-details">
      <strong>{{ doc.company }}</strong>
      {% if company.phone_no %}📞 {{ company.phone_no }}<br>{% endif %}
      {% if company.email %}✉ {{ company.email }}<br>{% endif %}
      {% if company.default_currency %}Currency: {{ company.default_currency }}{% endif %}
    </div>
  </div>

  <!-- ── INVOICE TITLE BAND ── -->
  <div class="invoice-band">
    <div>
      <h1>
        Invoice
        {%- set status_map = {"Paid": "status-paid", "Unpaid": "status-unpaid", "Draft": "status-draft", "Return": "status-unpaid", "Overdue": "status-unpaid"} -%}
        {%- set badge_class = status_map.get(doc.status, "status-draft") -%}
        <span class="status-badge {{ badge_class }}">{{ doc.status or "Draft" }}</span>
      </h1>
    </div>
    <div class="inv-meta">
      <p>Invoice No. <span>{{ doc.name }}</span></p>
      {% if doc.po_no %}<p>PO / Ref. <span>{{ doc.po_no }}</span></p>{% endif %}
      <p>Currency <span>{{ doc.currency }}</span></p>
    </div>
  </div>

  <!-- ── PARTIES ── -->
  <div class="parties">
    <!-- Bill From -->
    <div class="party-box">
      <div class="party-label">From</div>
      <div class="party-name">{{ doc.company }}</div>
      <div class="party-detail">
        {% if company.phone_no %}{{ company.phone_no }}<br>{% endif %}
        {% if company.email %}{{ company.email }}{% endif %}
      </div>
    </div>

    <!-- Bill To -->
    <div class="party-box">
      <div class="party-label">Bill To</div>
      <div class="party-name">{{ doc.customer_name or doc.customer }}</div>
      <div class="party-detail">
        {% if doc.contact_email %}{{ doc.contact_email }}<br>{% endif %}
        {% if doc.contact_mobile %}{{ doc.contact_mobile }}<br>{% endif %}
        {% if doc.customer_address %}{{ doc.customer_address }}{% endif %}
      </div>
    </div>
  </div>

  <!-- ── DATES ── -->
  <div class="dates-row">
    <div class="date-box">
      <div class="date-label">Invoice Date</div>
      <div class="date-value">{{ frappe.format(doc.posting_date, {"fieldtype": "Date"}) }}</div>
    </div>
    <div class="date-box">
      <div class="date-label">Due Date</div>
      <div class="date-value">{{ frappe.format(doc.due_date, {"fieldtype": "Date"}) if doc.due_date else "On Receipt" }}</div>
    </div>
    <div class="date-box">
      <div class="date-label">Payment Terms</div>
      <div class="date-value">{{ doc.payment_terms_template or "Net 30" }}</div>
    </div>
  </div>

  <!-- ── ITEMS TABLE ── -->
  <table class="items-table">
    <thead>
      <tr>
        <th style="width:36px;">#</th>
        <th>Item / Description</th>
        <th class="center" style="width:70px;">Qty</th>
        <th class="right" style="width:110px;">Rate ({{ doc.currency }})</th>
        {% if doc.items and doc.items[0].discount_percentage %}
          <th class="right" style="width:80px;">Disc %</th>
        {% endif %}
        <th class="right" style="width:120px;">Amount ({{ doc.currency }})</th>
      </tr>
    </thead>
    <tbody>
      {% for item in doc.items %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>
          <div class="item-name">{{ item.item_name or item.item_code }}</div>
          {% if item.description and item.description != item.item_name %}
            <div class="item-desc">{{ item.description | striptags }}</div>
          {% endif %}
        </td>
        <td class="center">{{ item.qty | int if item.qty == (item.qty | int) else item.qty }}</td>
        <td class="right">{{ frappe.format(item.rate, {"fieldtype": "Currency", "options": doc.currency}) }}</td>
        {% if doc.items and doc.items[0].discount_percentage %}
          <td class="right">{{ item.discount_percentage or "—" }}{% if item.discount_percentage %}%{% endif %}</td>
        {% endif %}
        <td class="right" style="font-weight:600;">{{ frappe.format(item.amount, {"fieldtype": "Currency", "options": doc.currency}) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <!-- ── TOTALS ── -->
  <div class="totals-section">
    <div class="totals-box">
      <div class="totals-row">
        <span class="label">Subtotal</span>
        <span class="value">{{ frappe.format(doc.total, {"fieldtype": "Currency", "options": doc.currency}) }}</span>
      </div>
      {% if doc.discount_amount and doc.discount_amount > 0 %}
      <div class="totals-row">
        <span class="label">Discount</span>
        <span class="value" style="color:#e53e3e;">− {{ frappe.format(doc.discount_amount, {"fieldtype": "Currency", "options": doc.currency}) }}</span>
      </div>
      {% endif %}
      {% for tax in doc.taxes %}
        {% if tax.tax_amount %}
        <div class="totals-row">
          <span class="label">{{ tax.description or tax.account_head }}</span>
          <span class="value">{{ frappe.format(tax.tax_amount, {"fieldtype": "Currency", "options": doc.currency}) }}</span>
        </div>
        {% endif %}
      {% endfor %}
      <div class="totals-row grand">
        <span class="label">Total Due</span>
        <span class="value">{{ frappe.format(doc.grand_total, {"fieldtype": "Currency", "options": doc.currency}) }}</span>
      </div>
      {% if doc.outstanding_amount is defined and doc.outstanding_amount != doc.grand_total %}
      <div class="totals-row" style="background:#f0fff4;">
        <span class="label" style="color:#276749;">Outstanding</span>
        <span class="value" style="color:#276749;">{{ frappe.format(doc.outstanding_amount, {"fieldtype": "Currency", "options": doc.currency}) }}</span>
      </div>
      {% endif %}
    </div>
  </div>

  <!-- ── STRIPE PAYMENT REFERENCE ── -->
  {% if doc.remarks and "Stripe Payment ID" in doc.remarks %}
  <div class="stripe-ref">
    <div class="stripe-dot"></div>
    <span class="ref-label">Stripe Payment</span>
    <span class="ref-value">{{ doc.remarks | replace("Stripe Payment ID: ", "") }}</span>
  </div>
  {% endif %}

  <!-- ── NOTES / TERMS ── -->
  {% if doc.terms %}
  <div class="notes-section">
    <strong>Terms &amp; Conditions</strong>
    {{ doc.terms }}
  </div>
  {% endif %}

  {% if doc.remarks and "Stripe Payment ID" not in doc.remarks %}
  <div class="notes-section">
    <strong>Remarks</strong>
    {{ doc.remarks }}
  </div>
  {% endif %}

  <!-- ── FOOTER ── -->
  <div class="footer">
    <div class="footer-left">
      <span class="footer-brand">{{ doc.company }}</span><br>
      This is a computer-generated invoice and does not require a signature.
    </div>
    <div class="footer-right">
      Generated by <strong>Frappe CRM</strong><br>
      {{ frappe.format(frappe.utils.now_datetime(), {"fieldtype": "Datetime"}) }}
    </div>
  </div>

</div>
</body>
</html>
"""
