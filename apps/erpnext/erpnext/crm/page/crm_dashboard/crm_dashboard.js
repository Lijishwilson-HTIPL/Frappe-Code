frappe.pages["crm-dashboard"].on_page_load = function (wrapper) {
    frappe.ui.make_app_page({
        parent: wrapper,
        title: __("CRM Dashboard"),
        single_column: true,
    });
    new CRMDashboard(wrapper);
};

class CRMDashboard {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.$main = $(wrapper).find(".layout-main-section");
        this._render_skeleton();
        this._bind();
        this.load_data();
    }

    _render_skeleton() {
        frappe.require("assets/erpnext/crm/page/crm_dashboard/crm_dashboard.html")
            .then(() => {})
            .catch(() => {});

        // Inline the HTML directly
        const html = `<div id="crm-dashboard-wrapper" style="padding:0;">
  <style>
    #crm-dashboard-wrapper { font-family: var(--font-stack); color: var(--text-color); background: var(--bg-color); min-height:100vh; padding-bottom:40px; }
    .crm-db-header { display:flex; align-items:center; justify-content:space-between; padding:18px 24px 10px; border-bottom:1px solid var(--border-color); background:var(--card-bg); flex-wrap:wrap; gap:10px; }
    .crm-db-header h2 { margin:0; font-size:1.3rem; font-weight:600; color:var(--text-color); }
    .crm-db-actions { display:flex; gap:8px; flex-wrap:wrap; }
    .crm-db-actions .btn { font-size:0.8rem; padding:5px 14px; border-radius:6px; }
    .crm-kpi-strip { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; padding:20px 24px 10px; }
    .crm-kpi-card { background:var(--card-bg); border:1px solid var(--border-color); border-radius:10px; padding:18px 20px; display:flex; flex-direction:column; gap:6px; transition:box-shadow 0.15s; }
    .crm-kpi-card:hover { box-shadow:0 4px 16px rgba(0,0,0,0.08); }
    .crm-kpi-label { font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.04em; }
    .crm-kpi-value { font-size:2rem; font-weight:700; color:var(--primary); line-height:1.1; }
    .crm-kpi-sub { font-size:0.72rem; color:var(--text-muted); }
    .crm-tabs { display:flex; gap:0; padding:0 24px; border-bottom:2px solid var(--border-color); margin-top:8px; }
    .crm-tab-pill { padding:10px 22px; cursor:pointer; font-size:0.9rem; font-weight:500; color:var(--text-muted); border-bottom:3px solid transparent; margin-bottom:-2px; transition:color 0.15s,border-color 0.15s; user-select:none; }
    .crm-tab-pill:hover { color:var(--primary); }
    .crm-tab-pill.active { color:var(--primary); border-bottom-color:var(--primary); }
    .crm-tab-content { display:none; padding:20px 24px; }
    .crm-tab-content.active { display:block; }
    .crm-pipeline-section { margin-bottom:28px; }
    .crm-pipeline-section h3 { font-size:0.95rem; font-weight:600; color:var(--text-color); margin:0 0 12px; display:flex; align-items:center; gap:8px; }
    .crm-pipeline-section h3 .badge { background:var(--primary); color:#fff; border-radius:10px; padding:1px 8px; font-size:0.7rem; }
    .crm-kanban { display:flex; gap:12px; overflow-x:auto; padding-bottom:8px; }
    .crm-kanban-col { min-width:180px; max-width:220px; flex:0 0 auto; background:var(--bg-color); border:1px solid var(--border-color); border-radius:8px; overflow:hidden; }
    .crm-kanban-col-header { background:var(--card-bg); padding:8px 12px; font-size:0.75rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.04em; border-bottom:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center; }
    .crm-kanban-col-header .col-count { background:var(--border-color); color:var(--text-color); border-radius:8px; padding:1px 7px; font-size:0.68rem; }
    .crm-kanban-cards { padding:8px; display:flex; flex-direction:column; gap:6px; }
    .crm-kanban-card { background:var(--card-bg); border:1px solid var(--border-color); border-radius:6px; padding:10px 12px; font-size:0.8rem; cursor:pointer; transition:box-shadow 0.12s; }
    .crm-kanban-card:hover { box-shadow:0 2px 8px rgba(0,0,0,0.10); }
    .crm-kanban-card .card-name { font-weight:600; color:var(--text-color); margin-bottom:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .crm-kanban-card .card-meta { color:var(--text-muted); font-size:0.72rem; }
    .crm-kanban-card .card-amount { color:var(--primary); font-weight:600; font-size:0.78rem; margin-top:4px; }
    .crm-kanban-empty { padding:12px; text-align:center; color:var(--text-muted); font-size:0.75rem; }
    .crm-leads-table-wrap { overflow-x:auto; }
    .crm-leads-table { width:100%; border-collapse:collapse; font-size:0.82rem; }
    .crm-leads-table th { background:var(--card-bg); color:var(--text-muted); padding:8px 12px; text-align:left; font-weight:600; font-size:0.73rem; text-transform:uppercase; letter-spacing:0.04em; border-bottom:2px solid var(--border-color); white-space:nowrap; }
    .crm-leads-table td { padding:9px 12px; border-bottom:1px solid var(--border-color); color:var(--text-color); vertical-align:middle; }
    .crm-leads-table tr:hover td { background:var(--bg-color); }
    .crm-leads-table .badge-source { background:var(--border-color); color:var(--text-muted); border-radius:8px; padding:2px 8px; font-size:0.7rem; }
    .badge-type { border-radius:8px; padding:2px 8px; font-size:0.68rem; font-weight:600; }
    .badge-type-erpnext { background:#e8f4fd; color:#1a73e8; }
    .badge-type-crm { background:#fce8fd; color:#8e24aa; }
    .crm-activity-list { display:flex; flex-direction:column; gap:0; }
    .crm-activity-item { display:flex; gap:14px; align-items:flex-start; padding:13px 0; border-bottom:1px solid var(--border-color); }
    .crm-activity-item:last-child { border-bottom:none; }
    .crm-activity-icon { width:34px; height:34px; border-radius:50%; background:var(--card-bg); border:1px solid var(--border-color); display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:0.85rem; color:var(--primary); }
    .crm-activity-body { flex:1; min-width:0; }
    .crm-activity-title { font-weight:600; font-size:0.85rem; color:var(--text-color); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .crm-activity-sub { font-size:0.75rem; color:var(--text-muted); margin-top:2px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .crm-activity-time { font-size:0.7rem; color:var(--text-muted); white-space:nowrap; flex-shrink:0; padding-top:4px; }
    .crm-loading { display:flex; align-items:center; justify-content:center; padding:60px 0; color:var(--text-muted); font-size:0.9rem; gap:10px; }
    .crm-spinner { width:22px; height:22px; border:3px solid var(--border-color); border-top-color:var(--primary); border-radius:50%; animation:crm-spin 0.7s linear infinite; }
    @keyframes crm-spin { to { transform:rotate(360deg); } }
    .crm-empty { text-align:center; color:var(--text-muted); padding:40px 0; font-size:0.85rem; }
  </style>

  <div class="crm-db-header">
    <h2>${__("CRM Dashboard")}</h2>
    <div class="crm-db-actions">
      <button class="btn btn-sm btn-primary crm-action-btn" data-action="new-lead">+ ${__("New Lead")}</button>
      <button class="btn btn-sm btn-default crm-action-btn" data-action="new-crm-lead">+ ${__("New CRM Lead")}</button>
      <button class="btn btn-sm btn-default crm-action-btn" data-action="new-opportunity">+ ${__("New Opportunity")}</button>
    </div>
  </div>

  <div class="crm-kpi-strip">
    <div class="crm-kpi-card">
      <div class="crm-kpi-label">${__("Open Leads")}</div>
      <div class="crm-kpi-value" id="kpi-open-leads">—</div>
      <div class="crm-kpi-sub">${__("ERPNext + Frappe CRM")}</div>
    </div>
    <div class="crm-kpi-card">
      <div class="crm-kpi-label">${__("Open Deals")}</div>
      <div class="crm-kpi-value" id="kpi-open-deals">—</div>
      <div class="crm-kpi-sub">${__("Opportunities + CRM Deals")}</div>
    </div>
    <div class="crm-kpi-card">
      <div class="crm-kpi-label">${__("Pipeline Value")}</div>
      <div class="crm-kpi-value" id="kpi-pipeline">—</div>
      <div class="crm-kpi-sub">${__("Open pipeline (₹)")}</div>
    </div>
    <div class="crm-kpi-card">
      <div class="crm-kpi-label">${__("Won This Month")}</div>
      <div class="crm-kpi-value" id="kpi-won">—</div>
      <div class="crm-kpi-sub">${__("Closed won deals")}</div>
    </div>
  </div>

  <div class="crm-tabs">
    <div class="crm-tab-pill active" data-tab="pipeline">${__("Pipeline")}</div>
    <div class="crm-tab-pill" data-tab="leads">${__("Leads")}</div>
    <div class="crm-tab-pill" data-tab="activity">${__("Activity")}</div>
  </div>

  <div id="crm-tab-pipeline" class="crm-tab-content active">
    <div class="crm-loading"><div class="crm-spinner"></div> ${__("Loading pipeline…")}</div>
  </div>
  <div id="crm-tab-leads" class="crm-tab-content">
    <div class="crm-loading"><div class="crm-spinner"></div> ${__("Loading leads…")}</div>
  </div>
  <div id="crm-tab-activity" class="crm-tab-content">
    <div class="crm-loading"><div class="crm-spinner"></div> ${__("Loading activity…")}</div>
  </div>
</div>`;
        this.$main.html(html);
    }

    _bind() {
        const me = this;
        this.$main.on("click", ".crm-tab-pill", function () {
            me._go($(this).data("tab"));
        });
        this.$main.on("click", "[data-route]", function () {
            const route = $(this).data("route");
            if (route) frappe.set_route(route.split("/"));
        });
        this.$main.on("click", "[data-crm-route]", function () {
            const route = $(this).data("crm-route");
            if (route) frappe.set_route(route);
        });
        this.$main.on("click", ".crm-action-btn", function () {
            const action = $(this).data("action");
            if (action === "new-lead") {
                frappe.new_doc("Lead");
            } else if (action === "new-crm-lead") {
                try {
                    frappe.new_doc("CRM Lead");
                } catch (e) {
                    frappe.msgprint(__("Frappe CRM is not installed."));
                }
            } else if (action === "new-opportunity") {
                frappe.new_doc("Opportunity");
            }
        });
    }

    load_data() {
        const me = this;
        frappe.call({
            method: "erpnext.crm.page.crm_dashboard.crm_dashboard.get_dashboard_data",
            callback: function (r) {
                if (r.message) {
                    me._render_kpis(r.message.kpis);
                    me._render_pipeline(r.message);
                    me._render_leads(r.message);
                    me._render_activity(r.message.activities);
                }
            },
            error: function (err) {
                frappe.msgprint(__("Failed to load dashboard data."));
                console.warn("CRM Dashboard: data load failed");
            }
        });
    }

    _render_kpis(kpis) {
        this.$main.find("#kpi-open-leads").text(kpis.open_leads || 0);
        this.$main.find("#kpi-open-deals").text(kpis.open_deals || 0);
        this.$main.find("#kpi-pipeline").text(this._fmt_currency(kpis.pipeline_value || 0));
        this.$main.find("#kpi-won").text(kpis.won_this_month || 0);
    }

    _render_pipeline(data) {
        const opps = data.erpnext_opportunities || [];
        const deals = data.crm_deals || [];
        const dealStatuses = data.crm_deal_statuses || ["Qualification", "Proposal", "Negotiation"];

        // ERPNext Opportunities kanban
        const oppStages = [...new Set(opps.map(o => o.sales_stage || o.status || "Open"))];
        let oppKanban = oppStages.map(stage => {
            const cards = opps.filter(o => (o.sales_stage || o.status || "Open") === stage);
            return `<div class="crm-kanban-col">
              <div class="crm-kanban-col-header">${frappe.utils.escape_html(stage)} <span class="col-count">${cards.length}</span></div>
              <div class="crm-kanban-cards">
                ${cards.length ? cards.map(o => `<div class="crm-kanban-card" data-route="Form/Opportunity/${frappe.utils.escape_html(o.name)}">
                  <div class="card-name">${frappe.utils.escape_html(o.party_name || o.name)}</div>
                  <div class="card-meta">${frappe.utils.escape_html(o.owner || "")}</div>
                  ${o.opportunity_amount ? `<div class="card-amount">${this._fmt_currency(o.opportunity_amount)}</div>` : ""}
                </div>`).join("") : `<div class="crm-kanban-empty">${__("No items")}</div>`}
              </div>
            </div>`;
        }).join("");

        if (!oppStages.length) {
            oppKanban = `<div class="crm-empty">${__("No open opportunities")}</div>`;
        }

        // CRM Deals kanban
        let dealKanban = dealStatuses.map(status => {
            const cards = deals.filter(d => d.status === status);
            return `<div class="crm-kanban-col">
              <div class="crm-kanban-col-header">${frappe.utils.escape_html(status)} <span class="col-count">${cards.length}</span></div>
              <div class="crm-kanban-cards">
                ${cards.length ? cards.map(d => `<div class="crm-kanban-card">
                  <div class="card-name">${frappe.utils.escape_html(d.lead_name || d.organization || d.name)}</div>
                  <div class="card-meta">${frappe.utils.escape_html(d.deal_owner || "")}</div>
                  ${d.deal_value ? `<div class="card-amount">${this._fmt_currency(d.deal_value)}</div>` : ""}
                </div>`).join("") : `<div class="crm-kanban-empty">${__("No items")}</div>`}
              </div>
            </div>`;
        }).join("");

        const html = `
          <div class="crm-pipeline-section">
            <h3>${__("ERPNext Opportunities")} <span class="badge">${opps.length}</span></h3>
            <div class="crm-kanban">${oppKanban}</div>
          </div>
          <div class="crm-pipeline-section">
            <h3>${__("Frappe CRM Deals")} <span class="badge">${deals.length}</span></h3>
            <div class="crm-kanban">${dealKanban || `<div class="crm-empty">${__("Frappe CRM not installed or no deals")}</div>`}</div>
          </div>`;

        this.$main.find("#crm-tab-pipeline").html(html);
    }

    _render_leads(data) {
        const erpLeads = (data.erpnext_leads || []).map(l => ({ ...l, _type: "erpnext" }));
        const crmLeads = (data.crm_leads || []).map(l => ({ ...l, _type: "crm" }));
        const all = [...erpLeads, ...crmLeads].sort((a, b) =>
            (b.creation || "").localeCompare(a.creation || "")
        );

        if (!all.length) {
            this.$main.find("#crm-tab-leads").html(`<div class="crm-empty">${__("No open leads")}</div>`);
            return;
        }

        const rows = all.map(l => {
            const name = frappe.utils.escape_html(l.lead_name || l.name);
            const company = frappe.utils.escape_html(l.company_name || l.organization || "—");
            const status = frappe.utils.escape_html(l.status || "—");
            const owner = frappe.utils.escape_html(l.lead_owner || "—");
            const source = frappe.utils.escape_html(l.source || "");
            const typeBadge = l._type === "crm"
                ? `<span class="badge-type badge-type-crm">Frappe CRM</span>`
                : `<span class="badge-type badge-type-erpnext">ERPNext</span>`;
            const age = this._time_ago(l.creation);
            const routeAttr = l._type === "erpnext"
                ? `data-route="Form/Lead/${frappe.utils.escape_html(l.name)}"`
                : `data-crm-route="crm/leads/${frappe.utils.escape_html(l.name)}"`;
            return `<tr style="cursor:pointer;" ${routeAttr}>
              <td>${name}</td>
              <td>${company}</td>
              <td>${typeBadge}</td>
              <td>${status}</td>
              <td>${owner}</td>
              <td>${source ? `<span class="badge-source">${source}</span>` : "—"}</td>
              <td>${age}</td>
            </tr>`;
        }).join("");

        const html = `<div class="crm-leads-table-wrap">
          <table class="crm-leads-table">
            <thead>
              <tr>
                <th>${__("Name")}</th>
                <th>${__("Company")}</th>
                <th>${__("Source App")}</th>
                <th>${__("Status")}</th>
                <th>${__("Owner")}</th>
                <th>${__("Source")}</th>
                <th>${__("Age")}</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;

        this.$main.find("#crm-tab-leads").html(html);
    }

    _render_activity(activities) {
        if (!activities || !activities.length) {
            this.$main.find("#crm-tab-activity").html(`<div class="crm-empty">${__("No recent activity")}</div>`);
            return;
        }

        const iconMap = {
            mail: "✉",
            phone: "☎",
            "file-text": "📄"
        };

        const items = activities.map(a => {
            const icon = iconMap[a.icon] || "●";
            return `<div class="crm-activity-item">
              <div class="crm-activity-icon">${icon}</div>
              <div class="crm-activity-body">
                <div class="crm-activity-title">${frappe.utils.escape_html(a.title || "")}</div>
                <div class="crm-activity-sub">${frappe.utils.escape_html(a.subtitle || "")}</div>
              </div>
              <div class="crm-activity-time">${this._time_ago(a.creation)}</div>
            </div>`;
        }).join("");

        this.$main.find("#crm-tab-activity").html(`<div class="crm-activity-list">${items}</div>`);
    }

    _go(tab) {
        this.$main.find(".crm-tab-pill").removeClass("active");
        this.$main.find(`.crm-tab-pill[data-tab="${tab}"]`).addClass("active");
        this.$main.find(".crm-tab-content").removeClass("active");
        this.$main.find(`#crm-tab-${tab}`).addClass("active");
    }

    _fmt_currency(val) {
        const n = parseFloat(val) || 0;
        if (n >= 10000000) return "₹" + (n / 10000000).toFixed(1) + "Cr";
        if (n >= 100000) return "₹" + (n / 100000).toFixed(1) + "L";
        if (n >= 1000) return "₹" + (n / 1000).toFixed(1) + "K";
        return "₹" + n.toFixed(0);
    }

    _time_ago(dt) {
        if (!dt) return "—";
        try {
            const d = new Date(dt);
            const diff = Math.floor((Date.now() - d.getTime()) / 1000);
            if (diff < 60) return "just now";
            if (diff < 3600) return Math.floor(diff / 60) + "m ago";
            if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
            if (diff < 2592000) return Math.floor(diff / 86400) + "d ago";
            return d.toLocaleDateString();
        } catch (e) {
            return dt;
        }
    }
}
