/* globals frappe, __ */
var SBIQC_APP_LABELS = { erpnext: "SBIQC", quality_dms: "DMS" };
function sbiqc_app_label(app) {
    return SBIQC_APP_LABELS[app] || app;
}

frappe.pages["sbiqc-provisioning"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "SBIQC Provisioning",
        single_column: true,
    });
    $(wrapper).find(".page-head").addClass("hide");
    page.main.html(frappe.render_template("sbiqc_provisioning"));
    wrapper.__sbiqc = new SBIQCProvisioning(wrapper);
};

frappe.pages["sbiqc-provisioning"].on_page_show = function (wrapper) {
    if (wrapper.__sbiqc) wrapper.__sbiqc.on_show();
};

frappe.pages["sbiqc-provisioning"].on_page_unload = function (wrapper) {
    if (wrapper.__sbiqc) {
        clearInterval(wrapper.__sbiqc._timer);
        clearInterval(wrapper.__sbiqc._health_timer);
    }
};

class SBIQCProvisioning {
    constructor(wrapper) {
        this.$w        = $(wrapper);
        this.data      = null;
        this.section   = "tenants";
        this.filter    = "";
        this.search    = "";
        this.offset    = 0;
        this.limit     = 20;
        this.loading   = false;
        this._timer    = null;
        this._health_timer = null;
        this._slide_tenant = null;
        this._all_apps = [];
        this._installed_apps = {};

        this._is_production = false;
        frappe.call({
            method: "frappe.client.get_single_value",
            args: { doctype: "System Settings", field: "app_name" },
            callback: () => {
                var is_prod = frappe.boot && frappe.boot.conf && frappe.boot.conf.is_production;
                this._is_production = !!is_prod;
                this.$w.find(".sbiqc-env-label").text(
                    (is_prod ? "● Production" : "● Local Dev")
                );
            }
        });

        this._bind();
        this.load_stats();
        this._auto_refresh();
        this._wire_realtime();
    }

    on_show() { this.load_stats(); }

    _bind() {
        var self = this;
        this.$w.on("click", ".sbiqc-nav-item", function () {
            self._go($(this).data("section"));
        });
        this.$w.on("click", ".sbiqc-btn-refresh", function () {
            var $b = $(this);
            $b.addClass("sbiqc-spin");
            self.load_stats(function () {
                setTimeout(function () { $b.removeClass("sbiqc-spin"); }, 500);
            });
        });
        this.$w.on("click", ".sbiqc-btn-new-tenant", function () { self._wizard_show(); });
        this.$w.on("click", ".sbiqc-chip", function () {
            var s = $(this).data("status") || "";
            self.filter = s;
            self.$w.find(".sbiqc-chip").removeClass("active");
            $(this).addClass("active");
            self.offset = 0;
            self._render_tenants();
        });
        this.$w.on("input", ".sbiqc-search-input", function () {
            self.search = $(this).val().toLowerCase().trim();
            self._render_tenants();
        });
        this.$w.on("click", ".sbiqc-trow", function (e) {
            if ($(e.target).closest("button,a").length) return;
            frappe.set_route("Form", "Tenant", $(this).data("name"));
        });
        this.$w.on("click", ".sbiqc-act-open",    function (e) { e.stopPropagation(); window.open("http://" + $(this).data("site") + ":8000", "_blank"); });
        this.$w.on("click", ".sbiqc-act-suspend",  function (e) { e.stopPropagation(); self._suspend($(this).data("name")); });
        this.$w.on("click", ".sbiqc-act-resume",   function (e) { e.stopPropagation(); self._resume($(this).data("name")); });
        this.$w.on("click", ".sbiqc-act-retry",    function (e) { e.stopPropagation(); self._retry($(this).data("name")); });
        this.$w.on("click", ".sbiqc-act-addapps",  function (e) { e.stopPropagation(); self._addapps_open($(this).data("name")); });
        this.$w.on("click", ".sbiqc-act-delete",   function (e) { e.stopPropagation(); self._delete($(this).data("name")); });
        this.$w.on("click", ".sbiqc-act-viewlog",  function (e) { e.stopPropagation(); frappe.set_route("List", "Provisioning Log", { tenant: $(this).data("name") }); });
        this.$w.on("click", ".sbiqc-act-cancel",   function (e) { e.stopPropagation(); self._cancel_job($(this).data("log")); });
        this.$w.on("click", ".sbiqc-load-more", function () { self._load_more(); });
        this.$w.on("click", ".sbiqc-err-expand", function () {
            $(this).closest(".sbiqc-error-row").find(".sbiqc-error-traceback").toggleClass("open");
        });
        this.$w.on("click", ".sbiqc-err-retry", function () { self._retry($(this).data("name")); });
        this.$w.on("click", "#sbiqc-backdrop, .sbiqc-slideout-close", function () { self._slideout_close(); });
        this.$w.on("click", ".sbiqc-install-selected", function () { self._addapps_submit(); });
    }

    _go(section) {
        this.section = section;
        var titles = { tenants: __("Tenants"), queue: __("Queue"), health: __("Health"), reports: __("Reports"), errors: __("Errors") };
        this.$w.find(".sbiqc-section-title").text(titles[section] || section);
        this.$w.find(".sbiqc-nav-item").removeClass("active");
        this.$w.find('.sbiqc-nav-item[data-section="' + section + '"]').addClass("active");
        this.$w.find(".sbiqc-panel").addClass("sbiqc-panel-hidden");
        this.$w.find("#sbiqc-panel-" + section).removeClass("sbiqc-panel-hidden");
        var show_kpi     = (section === "tenants");
        var show_toolbar = (section === "tenants");
        this.$w.find(".sbiqc-kpi-strip").toggle(show_kpi);
        this.$w.find(".sbiqc-toolbar-area").toggle(show_toolbar);
        this.$w.find(".sbiqc-btn-new-tenant").toggle(section === "tenants");
        if (section === "tenants") { this._render_tenants(); }
        if (section === "queue")   { this._render_queue(); }
        if (section === "health")  { this._load_health(); }
        if (section === "reports") { this._load_reports(); }
        if (section === "errors")  { this._render_errors(); }
    }

    load_stats(cb) {
        var self = this;
        if (this.loading) return;
        this.loading = true;
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_provisioning_stats",
            args: { offset: 0, limit: this.limit },
            callback: function (r) {
                self.loading = false;
                if (r.message) {
                    self.data = r.message;
                    self.offset = self.limit;
                    self._render_kpis();
                    self._update_badges();
                    if (self.section === "tenants") self._render_tenants();
                    if (self.section === "queue")   self._render_queue();
                    if (self.section === "errors")  self._render_errors();
                }
                if (cb) cb();
            },
            error: function () { self.loading = false; if (cb) cb(); }
        });
    }

    _auto_refresh() {
        var self = this;
        this._timer = setInterval(function () {
            if (self.data && (self.data.Provisioning > 0 || self.data.Pending > 0)) {
                self.load_stats();
            }
        }, 15000);
    }

    _wire_realtime() {
        var self = this;
        frappe.realtime.on("progress", function (data) {
            if (!data || !data.title) return;
            var $bar = self.$w.find(".sbiqc-bar-fill").filter(function () {
                return $(this).data("site") === data.title;
            });
            if ($bar.length && data.percent) {
                $bar.css("width", data.percent + "%");
            }
        });
    }

    _render_kpis() {
        var d = this.data || {};
        var kpis = [
            { key: "total",        label: __("Total"),   val: d.total || 0,        color: "#00D9BE" },
            { key: "Active",       label: __("Active"),  val: d.Active || 0,       color: "#00CC88" },
            { key: "Provisioning", label: __("Running"), val: d.Provisioning || 0, color: "#4D9EFF" },
            { key: "Error",        label: __("Errors"),  val: d.Error || 0,        color: "#FF3F60" },
        ];
        var h = "";
        for (var i = 0; i < kpis.length; i++) {
            var k = kpis[i];
            h += '<div class="sbiqc-kpi" style="--kpi-c:' + k.color + ';" data-filter="' + k.key + '">';
            h += '<div class="sbiqc-kpi-val">' + k.val + '</div>';
            h += '<div class="sbiqc-kpi-label">' + k.label + '</div>';
            h += '</div>';
        }
        this.$w.find(".sbiqc-kpi-strip").html(h);
    }

    _update_badges() {
        var d = this.data || {};
        var q_count = (d.Provisioning || 0) + (d.Pending || 0);
        var e_count = d.Error || 0;
        var $qb = this.$w.find(".sbiqc-badge-queue");
        var $eb = this.$w.find(".sbiqc-badge-errors");
        if (q_count > 0) { $qb.text(q_count).addClass("show"); } else { $qb.text("").removeClass("show"); }
        if (e_count > 0) { $eb.text(e_count).addClass("show"); } else { $eb.text("").removeClass("show"); }
    }

    _render_tenants() {
        var self = this;
        var $panel = this.$w.find("#sbiqc-panel-tenants");
        var tenants = (this.data && this.data.recent_tenants) || [];
        if (this.filter && this.filter !== "total") {
            tenants = tenants.filter(function (t) { return t.status === self.filter; });
        }
        if (this.search) {
            var s = this.search;
            tenants = tenants.filter(function (t) {
                return ((t.client_name || "") + " " + (t.subdomain || "") + " " + (t.site_name || "")).toLowerCase().indexOf(s) !== -1;
            });
        }
        if (!tenants.length) {
            $panel.html(this._empty("No tenants found", "Create your first tenant to begin provisioning."));
            return;
        }
        var h = '<table class="sbiqc-table"><thead><tr>';
        h += '<th>' + __("Tenant") + '</th><th>' + __("Site / DB") + '</th><th>' + __("Plan") + '</th><th>' + __("Status") + '</th><th></th>';
        h += '</tr></thead><tbody>';
        for (var i = 0; i < tenants.length; i++) {
            var t = tenants[i];
            h += '<tr class="sbiqc-trow" data-name="' + frappe.utils.escape_html(t.name) + '">';
            h += '<td><div class="sbiqc-tenant-name">' + frappe.utils.escape_html(t.client_name || t.subdomain) + '</div>';
            h += '<div class="sbiqc-tenant-sub">' + frappe.utils.escape_html(t.subdomain) + (t.provisioned_at ? " · " + frappe.datetime.prettyDate(t.provisioned_at) : "") + '</div></td>';
            var site_h = "";
            if (t.status === "Active" && t.site_name) {
                site_h = '<a class="sbiqc-site-link" href="http://' + frappe.utils.escape_html(t.site_name) + ':8000" target="_blank">' + frappe.utils.escape_html(t.site_name) + ' &#8599;</a>';
            } else {
                site_h = '<span class="sbiqc-muted">' + (t.site_name || "—") + '</span>';
            }
            if (t.db_name) { site_h += '<div class="sbiqc-db-name"><code>' + t.db_name + '</code></div>'; }
            h += '<td>' + site_h + '</td>';
            h += '<td>' + this._plan_pill(t.plan) + '</td>';
            h += '<td>' + this._badge(t.status) + '</td>';
            h += '<td>' + this._row_actions(t) + '</td>';
            h += '</tr>';
        }
        h += '</tbody></table>';
        if (tenants.length === this.limit) {
            h += '<div class="sbiqc-load-more">' + __("Load more") + ' &#8595;</div>';
        }
        $panel.html(h);
    }

    _load_more() {
        if (this._loading_more) return;
        var self = this;
        this._loading_more = true;
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_provisioning_stats",
            args: { offset: this.offset, limit: this.limit },
            callback: function (r) {
                self._loading_more = false;
                if (!r.message) return;
                var more = r.message.recent_tenants || [];
                self.data.recent_tenants = (self.data.recent_tenants || []).concat(more);
                self.offset += self.limit;
                self._render_tenants();
            },
            error: function () { self._loading_more = false; }
        });
    }

    _row_actions(t) {
        var h = '<div class="sbiqc-actions">';
        var ename = frappe.utils.escape_html(t.name);
        var esite = frappe.utils.escape_html(t.site_name || "");
        if (t.status === "Active") {
            h += '<button class="sbiqc-act act-success sbiqc-act-open" data-site="' + esite + '" title="' + __("Open site") + '">open_in_new</button>';
            h += '<button class="sbiqc-act sbiqc-act-suspend" data-name="' + ename + '" title="' + __("Suspend") + '">pause_circle_outline</button>';
            h += '<button class="sbiqc-act act-blue sbiqc-act-addapps" data-name="' + ename + '" title="' + __("Add Apps") + '">add_circle_outline</button>';
            h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + ename + '" title="' + __("Delete") + '">delete_outline</button>';
        } else if (t.status === "Provisioning") {
            h += '<button class="sbiqc-act act-blue sbiqc-act-viewlog" data-name="' + ename + '" title="' + __("View log") + '">list_alt</button>';
        } else if (t.status === "Error") {
            h += '<button class="sbiqc-act act-blue sbiqc-act-retry" data-name="' + ename + '" title="' + __("Retry") + '">refresh</button>';
            h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + ename + '" title="' + __("Delete") + '">delete_outline</button>';
        } else if (t.status === "Suspended") {
            h += '<button class="sbiqc-act act-success sbiqc-act-resume" data-name="' + ename + '" title="' + __("Resume") + '">play_circle_outline</button>';
            h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + ename + '" title="' + __("Delete") + '">delete_outline</button>';
        } else if (t.status === "Pending") {
            h += '<button class="sbiqc-act danger sbiqc-act-delete" data-name="' + ename + '" title="' + __("Delete") + '">delete_outline</button>';
        }
        h += '</div>';
        return h;
    }

    _suspend(name) {
        frappe.confirm(__("Suspend tenant {0}? Their site will become inaccessible.", [name]), function () {
            frappe.db.set_value("Tenant", name, "status", "Suspended").then(function () {
                frappe.show_alert({ message: __("Tenant suspended"), indicator: "orange" });
            });
        });
    }

    _resume(name) {
        frappe.db.set_value("Tenant", name, "status", "Active").then(function () {
            frappe.show_alert({ message: __("Tenant resumed"), indicator: "green" });
        });
    }

    _retry(name) {
        var self = this;
        frappe.confirm(__("Re-queue provisioning for {0}?", [name]), function () {
            frappe.call({
                method: "frappe.client.get",
                args: { doctype: "Tenant", name: name },
                callback: function (r) {
                    if (!r.message) return;
                    if (r.message.docstatus !== 1) {
                        frappe.show_alert({ message: __("Cannot retry: tenant document is not submitted"), indicator: "orange" });
                        return;
                    }
                    frappe.call({
                        method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.retry_provisioning",
                        args: { tenant_name: name },
                        callback: function () {
                            frappe.show_alert({ message: __("Provisioning re-queued"), indicator: "blue" });
                            self.load_stats();
                        },
                        error: function () {
                            frappe.show_alert({ message: __("Retry failed — check system logs"), indicator: "red" });
                        }
                    });
                }
            });
        });
    }

    _delete(name) {
        var self = this;
        frappe.confirm(
            __("Permanently delete tenant {0} and drop its database? This cannot be undone.", [name]),
            function () {
                frappe.call({
                    method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.delete_tenant",
                    args: { tenant_name: name },
                    callback: function (r) {
                        if (r.message && r.message.status === "ok") {
                            frappe.show_alert({ message: __("Tenant deleted"), indicator: "green" });
                            self.load_stats();
                        }
                    }
                });
            }
        );
    }

    _cancel_job(log_name) {
        var self = this;
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.cancel_queued_job",
            args: { log_name: log_name },
            callback: function () {
                frappe.show_alert({ message: __("Job cancelled"), indicator: "orange" });
                self.load_stats();
            }
        });
    }

    _render_queue() {
        var $p = this.$w.find("#sbiqc-panel-queue");
        var logs = (this.data && this.data.recent_logs) || [];
        if (!logs.length) {
            $p.html(this._empty("Queue is clear", "Jobs appear here during tenant provisioning."));
            return;
        }
        var h = "";
        for (var i = 0; i < logs.length; i++) {
            var l = logs[i];
            var pct = l.progress || 0;
            var is_queued = l.status === "Queued";
            var is_running = l.status === "Running";
            h += '<div class="sbiqc-job">';
            h += '<div class="sbiqc-job-top">';
            h += '<a class="sbiqc-job-id" href="/app/provisioning-log/' + frappe.utils.escape_html(l.name) + '">' + frappe.utils.escape_html(l.name) + '</a>';
            h += '<span class="sbiqc-job-site">' + frappe.utils.escape_html(l.site_name || l.tenant) + '</span>';
            h += this._log_badge(l.status);
            if (is_queued) {
                h += '<button class="sbiqc-btn-secondary sbiqc-act-cancel" data-log="' + frappe.utils.escape_html(l.name) + '" style="font-size:10px;padding:2px 8px;">' + __("Cancel") + '</button>';
            }
            h += '</div>';
            if (l.current_step) { h += '<div class="sbiqc-job-step">' + frappe.utils.escape_html(l.current_step) + '</div>'; }
            if (is_running || is_queued) {
                h += '<div class="sbiqc-bar"><div class="sbiqc-bar-fill" data-site="' + frappe.utils.escape_html(l.site_name || "") + '" style="width:' + pct + '%;"></div></div>';
            } else if (l.status === "Completed") {
                h += '<div class="sbiqc-bar"><div class="sbiqc-bar-fill" style="width:100%;background:var(--green-avatar-bg,#10b981);"></div></div>';
            }
            var ts = l.completed_at || l.started_at;
            if (ts) h += '<div class="sbiqc-job-ts">' + frappe.datetime.prettyDate(ts) + '</div>';
            h += '</div>';
        }
        $p.html(h);
    }

    _load_health() {
        var self = this;
        var $p = this.$w.find("#sbiqc-panel-health");
        $p.html('<div class="sbiqc-empty"><p>Loading health checks...</p></div>');
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_bench_health",
            callback: function (r) { if (r.message) self._render_health(r.message); }
        });
        clearInterval(this._health_timer);
        this._health_timer = setInterval(function () {
            if (self.section === "health") self._load_health();
        }, 30000);
    }

    _render_health(data) {
        var $p = this.$w.find("#sbiqc-panel-health");
        var color_map = { ok: "#10b981", warn: "#f59e0b", error: "#ef4444" };
        var overall_color = color_map[data.overall] || color_map.ok;
        var overall_label = data.overall === "ok" ? __("All systems operational") : data.overall === "warn" ? __("Degraded") : __("Service error");
        var h = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">';
        h += '<span style="font-size:11px;font-weight:800;color:' + overall_color + ';text-transform:uppercase;letter-spacing:1.2px;">';
        h += overall_label + '</span></div>';
        h += '<div class="sbiqc-health-grid">';
        (data.checks || []).forEach(function (c) {
            var hc = color_map[c.status] || color_map.ok;
            h += '<div class="sbiqc-health-card" style="--hc:' + hc + ';">';
            h += '<div class="sbiqc-health-name">' + frappe.utils.escape_html(c.name) + '</div>';
            h += '<div class="sbiqc-health-status">' + frappe.utils.escape_html(c.status).toUpperCase() + '</div>';
            if (c.detail) h += '<div class="sbiqc-health-detail">' + frappe.utils.escape_html(c.detail) + '</div>';
            h += '</div>';
        });
        h += '</div>';
        $p.html(h);
    }

    _load_reports() {
        var self = this;
        var $p = this.$w.find("#sbiqc-panel-reports");
        $p.html('<div class="sbiqc-empty"><p>Loading reports...</p></div>');
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_provisioning_report",
            callback: function (r) { if (r.message) self._render_reports(r.message); }
        });
    }

    _render_reports(data) {
        var $p = this.$w.find("#sbiqc-panel-reports");
        var h = '<div style="display:flex;gap:12px;margin-bottom:24px;">';
        h += '<div class="sbiqc-kpi" style="--kpi-c:var(--primary);"><div class="sbiqc-kpi-val">' + (data.avg_provision_minutes || 0) + 'm</div><div class="sbiqc-kpi-label">' + __("Avg Provision Time") + '</div></div>';
        var total_active = 0;
        (data.plans || []).forEach(function (p) { total_active += (p.count || 0); });
        h += '<div class="sbiqc-kpi" style="--kpi-c:#10b981;"><div class="sbiqc-kpi-val">' + total_active + '</div><div class="sbiqc-kpi-label">' + __("Total Tenants") + '</div></div>';
        h += '</div>';
        h += '<div class="sbiqc-report-section"><div class="sbiqc-report-title">' + __("Provisioning by Month") + '</div>';
        var monthly = data.monthly || [];
        var max_monthly = Math.max.apply(null, monthly.map(function (m) { return m.count; }).concat([1]));
        h += '<div class="sbiqc-bar-chart">';
        monthly.forEach(function (m) {
            var pct = Math.round((m.count / max_monthly) * 100);
            h += '<div class="sbiqc-bar-row"><span class="sbiqc-bar-label">' + (m.month || "") + '</span>';
            h += '<div class="sbiqc-bar-track"><div class="sbiqc-bar-seg" style="width:' + pct + '%;">';
            h += '<span class="sbiqc-bar-seg-val">' + m.count + '</span></div></div></div>';
        });
        h += '</div></div>';
        h += '<div class="sbiqc-report-section"><div class="sbiqc-report-title">' + __("Tenants by Plan") + '</div>';
        var plan_colors = { Starter: "#6b7280", Standard: "#6366f1", Enterprise: "#7c3aed" };
        var max_plan = Math.max.apply(null, (data.plans || []).map(function (p) { return p.count; }).concat([1]));
        h += '<div class="sbiqc-bar-chart">';
        (data.plans || []).forEach(function (p) {
            var pct = Math.round((p.count / max_plan) * 100);
            var col = plan_colors[p.plan] || "var(--primary)";
            h += '<div class="sbiqc-bar-row"><span class="sbiqc-bar-label">' + (p.plan || "—") + '</span>';
            h += '<div class="sbiqc-bar-track"><div class="sbiqc-bar-seg" style="width:' + pct + '%;background:' + col + ';">';
            h += '<span class="sbiqc-bar-seg-val">' + p.count + '</span></div></div></div>';
        });
        h += '</div></div>';
        h += '<div class="sbiqc-report-section"><div class="sbiqc-report-title">' + __("Top Apps Installed") + '</div>';
        (data.top_apps || []).forEach(function (a) {
            h += '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border-color);font-size:12px;">';
            h += '<span>' + frappe.utils.escape_html(sbiqc_app_label(a.app_name)) + '</span><span style="color:var(--primary);font-weight:700;">' + a.count + '</span></div>';
        });
        h += '</div>';
        $p.html(h);
    }

    _render_errors() {
        var self = this;
        var $p = this.$w.find("#sbiqc-panel-errors");
        $p.html('<div class="sbiqc-empty"><p style="color:var(--text-muted);font-size:12px;">Loading...</p></div>');
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Tenant",
                filters: [["status", "=", "Error"]],
                fields: ["name", "client_name", "subdomain", "site_name", "error_log"],
                limit: 50,
                order_by: "modified desc",
            },
            callback: function (r) {
                var tenants = r.message || [];
                if (!tenants.length) {
                    $p.html(self._empty("No errors", "All tenants are healthy."));
                    return;
                }
                var h = "";
                tenants.forEach(function (t) {
                    h += '<div class="sbiqc-error-row">';
                    h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">';
                    h += '<span style="font-weight:700;font-size:13px;">' + frappe.utils.escape_html(t.client_name || t.subdomain) + '</span>';
                    h += '<span class="sbiqc-muted">' + frappe.utils.escape_html(t.site_name || "") + '</span>';
                    h += '<span style="margin-left:auto;display:flex;gap:6px;">';
                    h += '<button class="sbiqc-act act-blue sbiqc-err-retry" data-name="' + frappe.utils.escape_html(t.name) + '">' + __("Retry") + '</button>';
                    h += '<button class="sbiqc-act sbiqc-err-expand">' + __("Traceback") + '</button>';
                    h += '</span></div>';
                    if (t.error_log) {
                        h += '<div class="sbiqc-error-traceback">' + frappe.utils.escape_html((t.error_log || "").substring(0, 5000)) + '</div>';
                    }
                    h += '</div>';
                });
                $p.html(h);
            }
        });
    }

    _wizard_show() {
        var self = this;
        this._wizard_step = 1;
        this._wizard_data = { subdomain: "", client_name: "", admin_email: "", plan: "Standard", currency: "INR", timezone: "Asia/Kolkata", apps: [] };
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_installable_apps",
            callback: function (r) {
                self._all_apps = r.message || [];
                self._wizard_data.apps = ["erpnext"];
                self._wizard_render();
            }
        });
        this.$w.find(".sbiqc-kpi-strip").hide();
        this.$w.find(".sbiqc-toolbar-area").hide();
        this.$w.find(".sbiqc-btn-new-tenant").hide();
        this.$w.find(".sbiqc-btn-refresh").hide();
        this.$w.find("#sbiqc-panel-tenants").html('<div class="sbiqc-wizard"><p style="color:var(--text-muted);font-size:12px;">' + __("Loading apps list...") + '</p></div>');
    }

    _wizard_render() {
        var self = this;
        var step = this._wizard_step;
        var d    = this._wizard_data;
        var steps_h = '<div class="sbiqc-wizard-steps">';
        for (var i = 1; i <= 3; i++) {
            var cls = i < step ? "done" : (i === step ? "active" : "");
            steps_h += '<div class="sbiqc-wstep ' + cls + '"></div>';
        }
        steps_h += '</div><div class="sbiqc-wizard-step-labels">';
        steps_h += '<span class="' + (step === 1 ? "active" : "") + '">' + __("1. Identity") + '</span>';
        steps_h += '<span class="' + (step === 2 ? "active" : "") + '">' + __("2. Apps") + '</span>';
        steps_h += '<span class="' + (step === 3 ? "active" : "") + '">' + __("3. Confirm") + '</span>';
        steps_h += '</div>';
        var body_h = "";
        if (step === 1) { body_h = this._wizard_step1_html(d); }
        if (step === 2) { body_h = this._wizard_step2_html(d); }
        if (step === 3) { body_h = this._wizard_step3_html(d); }
        var foot_h = '<div class="sbiqc-wizard-foot">';
        foot_h += '<button class="sbiqc-btn-secondary sbiqc-wiz-cancel">' + __("Cancel") + '</button>';
        if (step > 1) foot_h += '<button class="sbiqc-btn-secondary sbiqc-wiz-back">' + __("Back") + '</button>';
        if (step < 3) foot_h += '<button class="sbiqc-btn-primary sbiqc-wiz-next">' + __("Next") + '</button>';
        if (step === 3) foot_h += '<button class="sbiqc-btn-primary sbiqc-wiz-submit">' + __("Provision") + '</button>';
        foot_h += '</div>';
        var html = '<div class="sbiqc-wizard">' + steps_h + '<div class="sbiqc-wizard-title">' + ["", __("Identity"), __("Choose Apps"), __("Confirm & Provision")][step] + '</div>' + body_h + foot_h + '</div>';
        this.$w.find("#sbiqc-panel-tenants").html(html);
        this.$w.find(".sbiqc-wiz-cancel").off("click").on("click", function () { self._wizard_cancel(); });
        this.$w.find(".sbiqc-wiz-back").off("click").on("click", function () { self._wizard_step--; self._wizard_render(); });
        this.$w.find(".sbiqc-wiz-next").off("click").on("click", function () { self._wizard_next(); });
        this.$w.find(".sbiqc-wiz-submit").off("click").on("click", function () { self._wizard_submit(); });
        this.$w.find("#wiz-subdomain").off("input").on("input", function () {
            var val = $(this).val().toLowerCase().replace(/[^a-z0-9-]/g, "");
            $(this).val(val);
            self.$w.find(".sbiqc-preview").text(val ? val + ".localhost" : "");
        });
        this.$w.off("click", ".sbiqc-app-card:not(.locked)").on("click", ".sbiqc-app-card:not(.locked)", function () {
            $(this).toggleClass("selected");
            var app = $(this).data("app");
            var idx = self._wizard_data.apps.indexOf(app);
            if ($(this).hasClass("selected")) { if (idx === -1) self._wizard_data.apps.push(app); }
            else { if (idx !== -1) self._wizard_data.apps.splice(idx, 1); }
            $(this).find(".check").text($(this).hasClass("selected") ? "✓" : "○");
        });
    }

    _wizard_step1_html(d) {
        return (
            '<div class="sbiqc-field"><label>' + __("Subdomain") + ' *</label>' +
            '<input id="wiz-subdomain" value="' + frappe.utils.escape_html(d.subdomain) + '" placeholder="e.g. acme-corp" />' +
            '<div class="sbiqc-hint">' + __("Site will be at:") + ' <span class="sbiqc-preview">' + (d.subdomain ? d.subdomain + ".localhost" : "") + '</span></div></div>' +
            '<div class="sbiqc-field"><label>' + __("Client Name") + ' *</label><input id="wiz-client" value="' + frappe.utils.escape_html(d.client_name) + '" placeholder="Acme Corporation" /></div>' +
            '<div class="sbiqc-field"><label>' + __("Admin Email") + '</label><input id="wiz-email" type="email" value="' + frappe.utils.escape_html(d.admin_email) + '" placeholder="admin@client.com" /></div>' +
            '<div class="sbiqc-field"><label>' + __("Plan") + '</label><select id="wiz-plan"><option ' + (d.plan==="Starter"?"selected":"") + '>Starter</option><option ' + (d.plan==="Standard"?"selected":"") + '>Standard</option><option ' + (d.plan==="Enterprise"?"selected":"") + '>Enterprise</option></select></div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
            '<div class="sbiqc-field"><label>' + __("Currency") + '</label><select id="wiz-currency"><option ' + (d.currency==="INR"?"selected":"") + '>INR</option><option ' + (d.currency==="USD"?"selected":"") + '>USD</option><option ' + (d.currency==="EUR"?"selected":"") + '>EUR</option><option ' + (d.currency==="GBP"?"selected":"") + '>GBP</option></select></div>' +
            '<div class="sbiqc-field"><label>' + __("Timezone") + '</label><select id="wiz-tz"><option ' + (d.timezone==="Asia/Kolkata"?"selected":"") + '>Asia/Kolkata</option><option ' + (d.timezone==="UTC"?"selected":"") + '>UTC</option><option ' + (d.timezone==="America/New_York"?"selected":"") + '>America/New_York</option><option ' + (d.timezone==="Europe/London"?"selected":"") + '>Europe/London</option><option ' + (d.timezone==="Asia/Dubai"?"selected":"") + '>Asia/Dubai</option></select></div>' +
            '</div>'
        );
    }

    _wizard_step2_html(d) {
        var h = '<div class="sbiqc-app-grid">';
        var apps = this._all_apps;
        if (!apps.length) return '<p style="color:var(--text-muted)">' + __("No apps available") + '</p>';
        for (var i = 0; i < apps.length; i++) {
            var app = apps[i];
            var is_locked   = (app === "erpnext");
            var is_selected = (d.apps.indexOf(app) !== -1);
            var cls = "sbiqc-app-card" + (is_selected ? " selected" : "") + (is_locked ? " locked" : "");
            h += '<div class="' + cls + '" data-app="' + app + '"><span class="check">' + (is_selected ? "✓" : "○") + '</span>' + frappe.utils.escape_html(sbiqc_app_label(app)) + '</div>';
        }
        h += '</div>';
        return h;
    }

    _wizard_step3_html(d) {
        var h = '<div style="background:var(--bg-color);border:1px solid var(--border-color);border-radius:8px;padding:16px;">';
        var rows = [
            [__("Subdomain"), d.subdomain + ".localhost"],
            [__("Client Name"), d.client_name],
            [__("Admin Email"), d.admin_email || "—"],
            [__("Plan"), d.plan],
            [__("Currency"), d.currency],
            [__("Timezone"), d.timezone],
            [__("Apps"), d.apps.map(sbiqc_app_label).join(", ")],
        ];
        rows.forEach(function (r) {
            h += '<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border-color);font-size:12px;">';
            h += '<span style="color:var(--text-muted);">' + r[0] + '</span>';
            h += '<span style="font-weight:600;">' + frappe.utils.escape_html(r[1]) + '</span>';
            h += '</div>';
        });
        h += '</div>';
        return h;
    }

    _wizard_next() {
        var d = this._wizard_data;
        if (this._wizard_step === 1) {
            d.subdomain    = (this.$w.find("#wiz-subdomain").val() || "").trim().toLowerCase();
            d.client_name  = (this.$w.find("#wiz-client").val() || "").trim();
            d.admin_email  = (this.$w.find("#wiz-email").val() || "").trim();
            d.plan         = this.$w.find("#wiz-plan").val();
            d.currency     = this.$w.find("#wiz-currency").val();
            d.timezone     = this.$w.find("#wiz-tz").val();
            if (!d.subdomain || !d.client_name) {
                frappe.show_alert({ message: __("Subdomain and Client Name are required"), indicator: "red" });
                return;
            }
            if (!/^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$/.test(d.subdomain)) {
                frappe.show_alert({ message: __("Invalid subdomain format"), indicator: "red" });
                return;
            }
        }
        this._wizard_step++;
        this._wizard_render();
    }

    _wizard_cancel() {
        this._wizard_step = 0;
        this.$w.find(".sbiqc-kpi-strip").show();
        this.$w.find(".sbiqc-toolbar-area").show();
        this.$w.find(".sbiqc-btn-new-tenant").show();
        this.$w.find(".sbiqc-btn-refresh").show();
        this._render_tenants();
    }

    _wizard_submit() {
        var self = this;
        var d    = this._wizard_data;
        var apps_rows = d.apps.map(function (a) { return { app_name: a }; });
        frappe.call({
            method: "frappe.client.insert",
            args: {
                doc: {
                    doctype: "Tenant",
                    subdomain: d.subdomain,
                    client_name: d.client_name,
                    admin_email: d.admin_email,
                    plan: d.plan,
                    currency: d.currency,
                    timezone: d.timezone,
                    apps_to_install: apps_rows,
                }
            },
            callback: function (r) {
                if (!r.exc && r.message) {
                    frappe.call({
                        method: "frappe.client.submit",
                        args: { doc: r.message },
                        callback: function (sr) {
                            if (sr.exc) {
                                frappe.show_alert({ message: sr.exc || __("Submission failed"), indicator: "red" });
                                return;
                            }
                            frappe.show_alert({ message: __("Provisioning queued for {0}", [d.subdomain + ".localhost"]), indicator: "blue" });
                            self._wizard_cancel();
                            self.load_stats();
                        },
                        error: function () {
                            frappe.show_alert({ message: __("Failed to submit tenant"), indicator: "red" });
                        }
                    });
                }
            }
        });
    }

    _addapps_open(tenant_name) {
        var self = this;
        this._slide_tenant = tenant_name;
        var t = (this.data && this.data.recent_tenants || []).find(function (x) { return x.name === tenant_name; });
        this.$w.find("#sbiqc-slideout-title").text(__("Add Apps — {0}", [t ? t.client_name : tenant_name]));
        this.$w.find("#sbiqc-slideout-body").html('<p style="color:var(--text-muted);font-size:12px;">' + __("Loading...") + '</p>');
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.get_installable_apps",
            callback: function (r) {
                var all_apps = r.message || [];
                frappe.call({
                    method: "frappe.client.get",
                    args: { doctype: "Tenant", name: tenant_name },
                    callback: function (tr) {
                        var installed = new Set((tr.message && tr.message.apps_to_install || []).map(function (a) { return a.app_name; }));
                        self._render_addapps_slideout(all_apps, installed);
                    }
                });
            }
        });
        this.$w.find("#sbiqc-backdrop").show();
        setTimeout(function () { self.$w.find("#sbiqc-slideout").addClass("open"); }, 10);
    }

    _render_addapps_slideout(all_apps, installed) {
        var h = "";
        if (installed.size) {
            h += '<p style="font-size:11px;color:var(--text-muted);margin-bottom:8px;font-weight:600;">' + __("Already installed") + '</p>';
            installed.forEach(function (a) {
                h += '<div class="sbiqc-app-card locked selected" style="margin-bottom:6px;"><span class="check">✓</span>' + frappe.utils.escape_html(sbiqc_app_label(a)) + '</div>';
            });
        }
        var available = all_apps.filter(function (a) { return !installed.has(a); });
        if (available.length) {
            h += '<p style="font-size:11px;color:var(--text-muted);margin:12px 0 8px;font-weight:600;">' + __("Available to install") + '</p>';
            available.forEach(function (a) {
                h += '<div class="sbiqc-app-card sbiqc-addapp-toggle" data-app="' + a + '" style="margin-bottom:6px;"><span class="check">○</span>' + frappe.utils.escape_html(sbiqc_app_label(a)) + '</div>';
            });
        }
        if (!available.length) {
            h += '<p style="color:var(--text-muted);font-size:12px;margin-top:8px;">' + __("All available apps are already installed.") + '</p>';
        }
        this.$w.find("#sbiqc-slideout-body").html(h);
        this.$w.find("#sbiqc-slideout-foot").html(
            available.length ? '<button class="sbiqc-btn-primary sbiqc-install-selected" style="width:100%;">' + __("Install Selected") + '</button>' : ''
        );
        this.$w.off("click", ".sbiqc-addapp-toggle").on("click", ".sbiqc-addapp-toggle", function () {
            $(this).toggleClass("selected");
            $(this).find(".check").text($(this).hasClass("selected") ? "✓" : "○");
        });
    }

    _addapps_submit() {
        var self = this;
        var selected = [];
        this.$w.find(".sbiqc-addapp-toggle.selected").each(function () { selected.push($(this).data("app")); });
        if (!selected.length) {
            frappe.show_alert({ message: __("Select at least one app"), indicator: "orange" });
            return;
        }
        frappe.call({
            method: "sbiqc_provisioning.sbiqc_provisioning.doctype.tenant.tenant.update_tenant_apps",
            args: { tenant_name: this._slide_tenant, new_apps: JSON.stringify(selected) },
            callback: function (r) {
                if (r.message && r.message.status === "queued") {
                    frappe.show_alert({ message: __("App installation queued"), indicator: "blue" });
                    self._slideout_close();
                    self.load_stats();
                }
            }
        });
    }

    _slideout_close() {
        this.$w.find("#sbiqc-slideout").removeClass("open");
        this.$w.find("#sbiqc-backdrop").hide();
        this._slide_tenant = null;
    }

    _badge(status) {
        var colors = { Active: "#00CC88", Provisioning: "#4D9EFF", Pending: "#FFB300", Error: "#FF3F60", Suspended: "#3D5A7A", Terminated: "#3D5A7A" };
        var c = colors[status] || "#6b7280";
        return '<span class="sbiqc-badge" style="--bc:' + c + ';">' + (status || "—") + '</span>';
    }
    _log_badge(status) {
        var colors = { Completed: "#00CC88", Running: "#4D9EFF", Queued: "#FFB300", Failed: "#FF3F60" };
        var c = colors[status] || "#6b7280";
        return '<span class="sbiqc-badge" style="--bc:' + c + ';">' + (status || "—") + '</span>';
    }
    _plan_pill(plan) {
        var colors = { Starter: "#3D5A7A", Standard: "#4D9EFF", Enterprise: "#9B72FF" };
        var c = colors[plan] || "#6b7280";
        return '<span class="sbiqc-pill" style="--pc:' + c + ';">' + (plan || "—") + '</span>';
    }
    _empty(h, p) {
        return '<div class="sbiqc-empty"><p class="sbiqc-empty-h">' + h + '</p><p>' + p + '</p></div>';
    }
}
