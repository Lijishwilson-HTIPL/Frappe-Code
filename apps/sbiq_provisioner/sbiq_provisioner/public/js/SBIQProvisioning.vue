<template>
  <div class="sbiqc-app">
    <!-- Sidebar -->
    <div class="sbiqc-sidebar">
      <div class="sbiqc-sidebar-logo">
        <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
          <rect x="2" y="3" width="24" height="9" rx="3" fill="currentColor" opacity=".9"/>
          <rect x="2" y="16" width="24" height="9" rx="3" fill="currentColor" opacity=".5"/>
          <circle cx="7" cy="7.5" r="1.5" fill="#040C18"/>
          <circle cx="7" cy="20.5" r="1.5" fill="#040C18"/>
        </svg>
        <div>
          <div class="sbiqc-logo-text">Provisioner</div>
          <div class="sbiqc-logo-sub">mysite.local</div>
        </div>
      </div>

      <div
        v-for="nav in navItems"
        :key="nav.section"
        class="sbiqc-nav-item"
        :class="{ active: section === nav.section }"
        @click="goSection(nav.section)"
      >
        <span class="sbiqc-nav-icon">{{ nav.icon }}</span>
        {{ nav.label }}
        <span
          v-if="nav.section === 'queue' && queueBadge > 0"
          class="sbiqc-nav-badge blue sbiqc-badge-queue"
        >{{ queueBadge }}</span>
        <span
          v-if="nav.section === 'errors' && errorBadge > 0"
          class="sbiqc-nav-badge sbiqc-badge-errors"
        >{{ errorBadge }}</span>
      </div>

      <div class="sbiqc-sidebar-bottom">
        <span class="sbiqc-env-chip sbiqc-env-label">{{ envLabel }}</span>
      </div>
    </div>

    <!-- Main Area -->
    <div class="sbiqc-main">
      <!-- Topbar -->
      <div class="sbiqc-topbar">
        <span class="sbiqc-topbar-title sbiqc-section-title">{{ sectionTitle }}</span>
        <div class="sbiqc-topbar-actions">
          <button
            class="sbiqc-btn-icon sbiqc-btn-refresh"
            :class="{ 'sbiqc-spin': refreshSpinning }"
            title="Refresh"
            @click="onRefreshClick"
          >refresh</button>
          <button
            v-if="section === 'tenants' && !wizardActive"
            class="sbiqc-btn-primary sbiqc-btn-new-tenant"
            @click="wizardShow"
          ><span style="font-family:'Material Icons';font-size:15px;line-height:1;">add</span> New Tenant</button>
        </div>
      </div>

      <!-- KPI Strip -->
      <div v-if="section === 'tenants' && !wizardActive" class="sbiqc-kpi-row sbiqc-kpi-strip">
        <div
          v-for="k in kpis"
          :key="k.key"
          class="sbiqc-kpi"
          :style="{ '--kpi-c': k.color }"
        >
          <div class="sbiqc-kpi-val">{{ k.val }}</div>
          <div class="sbiqc-kpi-label">{{ k.label }}</div>
        </div>
      </div>

      <!-- Toolbar -->
      <div v-if="section === 'tenants' && !wizardActive" class="sbiqc-toolbar sbiqc-toolbar-area">
        <div class="sbiqc-search-wrap">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            class="sbiqc-search-input"
            placeholder="Search tenants…"
            v-model="search"
          />
        </div>
        <div class="sbiqc-chips">
          <button
            v-for="chip in filterChips"
            :key="chip.status"
            class="sbiqc-chip"
            :class="{ active: filter === chip.status }"
            @click="setFilter(chip.status)"
          >{{ chip.label }}</button>
        </div>
      </div>

      <!-- Tenants Panel -->
      <div v-show="section === 'tenants'" class="sbiqc-panel sbiqc-panel-tenants" id="sbiqc-panel-tenants">
        <!-- Wizard -->
        <div v-if="wizardActive" class="sbiqc-wizard">
          <div class="sbiqc-wizard-steps">
            <div
              v-for="i in 3"
              :key="i"
              class="sbiqc-wstep"
              :class="{ done: i < wizardStep, active: i === wizardStep }"
            ></div>
          </div>
          <div class="sbiqc-wizard-step-labels">
            <span :class="{ active: wizardStep === 1 }">1. Identity</span>
            <span :class="{ active: wizardStep === 2 }">2. Apps</span>
            <span :class="{ active: wizardStep === 3 }">3. Confirm</span>
          </div>
          <div class="sbiqc-wizard-title">{{ ['', 'Identity', 'Choose Apps', 'Confirm & Provision'][wizardStep] }}</div>

          <!-- Step 1 -->
          <template v-if="wizardStep === 1">
            <div class="sbiqc-field">
              <label>Subdomain *</label>
              <input id="wiz-subdomain" v-model="wizardData.subdomain" placeholder="e.g. acme-corp" @input="sanitizeSubdomain" />
              <div class="sbiqc-hint">Site will be at: <span class="sbiqc-preview">{{ wizardData.subdomain ? wizardData.subdomain + '.localhost' : '' }}</span></div>
            </div>
            <div class="sbiqc-field">
              <label>Client Name *</label>
              <input v-model="wizardData.client_name" placeholder="Acme Corporation" />
            </div>
            <div class="sbiqc-field">
              <label>Admin Email</label>
              <input type="email" v-model="wizardData.admin_email" placeholder="admin@client.com" />
            </div>
            <div class="sbiqc-field">
              <label>Plan</label>
              <select v-model="wizardData.plan">
                <option>Starter</option>
                <option>Standard</option>
                <option>Enterprise</option>
              </select>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div class="sbiqc-field">
                <label>Currency</label>
                <select v-model="wizardData.currency">
                  <option>INR</option><option>USD</option><option>EUR</option><option>GBP</option>
                </select>
              </div>
              <div class="sbiqc-field">
                <label>Timezone</label>
                <select v-model="wizardData.timezone">
                  <option>Asia/Kolkata</option><option>UTC</option>
                  <option>America/New_York</option><option>Europe/London</option><option>Asia/Dubai</option>
                </select>
              </div>
            </div>
          </template>

          <!-- Step 2 -->
          <template v-if="wizardStep === 2">
            <div v-if="!allApps.length" style="color:var(--text-muted)">No apps available</div>
            <div v-else class="sbiqc-app-grid">
              <div
                v-for="app in allApps"
                :key="app"
                class="sbiqc-app-card"
                :class="{ selected: wizardData.apps.includes(app), locked: app === 'erpnext' }"
                @click="toggleWizardApp(app)"
              >
                <span class="check">{{ wizardData.apps.includes(app) ? '✓' : '○' }}</span>
                {{ app }}
              </div>
            </div>
          </template>

          <!-- Step 3 -->
          <template v-if="wizardStep === 3">
            <div style="background:var(--bg-color);border:1px solid var(--border-color);border-radius:8px;padding:16px;">
              <div v-for="row in wizardConfirmRows" :key="row[0]" style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border-color);font-size:12px;">
                <span style="color:var(--text-muted);">{{ row[0] }}</span>
                <span style="color:var(--text-color);font-weight:600;">{{ row[1] }}</span>
              </div>
            </div>
          </template>

          <div class="sbiqc-wizard-foot">
            <button class="sbiqc-btn-secondary" @click="wizardCancel">Cancel</button>
            <button v-if="wizardStep > 1" class="sbiqc-btn-secondary" @click="wizardStep--">← Back</button>
            <button v-if="wizardStep < 3" class="sbiqc-btn-primary" @click="wizardNext">Next →</button>
            <button v-if="wizardStep === 3" class="sbiqc-btn-primary" @click="wizardSubmit">
              <span style="font-family:'Material Icons';font-size:15px;line-height:1;">rocket_launch</span> Provision
            </button>
          </div>
        </div>

        <!-- Tenants Table -->
        <template v-else>
          <div v-if="!filteredTenants.length" v-html="emptyHtml('No tenants found', 'Create your first tenant to begin provisioning.')"></div>
          <template v-else>
            <table class="sbiqc-table">
              <thead>
                <tr>
                  <th>Tenant</th><th>Site / DB</th><th>Plan</th><th>Status</th><th></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="t in pagedTenants"
                  :key="t.name"
                  class="sbiqc-trow"
                  @click="onRowClick($event, t)"
                >
                  <td>
                    <div class="sbiqc-tenant-name">{{ t.client_name || t.subdomain }}</div>
                    <div class="sbiqc-tenant-sub">{{ t.subdomain }}{{ t.provisioned_at ? ' · ' + prettyDate(t.provisioned_at) : '' }}</div>
                  </td>
                  <td>
                    <template v-if="t.status === 'Active' && t.site_name">
                      <a class="sbiqc-site-link" :href="'http://' + t.site_name + ':8000'" target="_blank">{{ t.site_name }} ↗</a>
                    </template>
                    <template v-else>
                      <span class="sbiqc-muted">{{ t.site_name || '—' }}</span>
                    </template>
                    <div v-if="t.db_name" class="sbiqc-db-name"><code>{{ t.db_name }}</code></div>
                  </td>
                  <td><span class="sbiqc-pill" :style="{ '--pc': planColor(t.plan) }">{{ t.plan || '—' }}</span></td>
                  <td><span class="sbiqc-badge" :style="{ '--bc': badgeColor(t.status) }">{{ t.status || '—' }}</span></td>
                  <td>
                    <div class="sbiqc-actions">
                      <template v-if="t.status === 'Active'">
                        <button class="sbiqc-act act-success" :title="'Open site'" @click.stop="openSite(t.site_name)">open_in_new</button>
                        <button class="sbiqc-act" :title="'Suspend'" @click.stop="suspendTenant(t.name)">pause</button>
                        <button class="sbiqc-act act-blue" :title="'Add Apps'" @click.stop="addappsOpen(t.name)">add_circle_outline</button>
                        <button class="sbiqc-act danger" :title="'Delete'" @click.stop="deleteTenant(t.name)">delete_outline</button>
                      </template>
                      <template v-else-if="t.status === 'Provisioning'">
                        <button class="sbiqc-act act-blue" :title="'View log'" @click.stop="viewLog(t.name)">list_alt</button>
                      </template>
                      <template v-else-if="t.status === 'Error'">
                        <button class="sbiqc-act act-blue" :title="'Retry'" @click.stop="retryTenant(t.name)">refresh</button>
                        <button class="sbiqc-act danger" :title="'Delete'" @click.stop="deleteTenant(t.name)">delete_outline</button>
                      </template>
                      <template v-else-if="t.status === 'Suspended'">
                        <button class="sbiqc-act act-success" :title="'Resume'" @click.stop="resumeTenant(t.name)">play_arrow</button>
                        <button class="sbiqc-act danger" :title="'Delete'" @click.stop="deleteTenant(t.name)">delete_outline</button>
                      </template>
                      <template v-else-if="t.status === 'Pending'">
                        <button class="sbiqc-act danger" :title="'Delete'" @click.stop="deleteTenant(t.name)">delete_outline</button>
                      </template>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div
              v-if="filteredTenants.length > pagedTenants.length || canLoadMore"
              class="sbiqc-load-more"
              @click="loadMore"
            >Load more ↓</div>
          </template>
        </template>
      </div>

      <!-- Queue Panel -->
      <div v-show="section === 'queue'" class="sbiqc-panel" id="sbiqc-panel-queue">
        <div v-if="!queueLogs.length" v-html="emptyHtml('Queue is clear', 'Jobs appear here during tenant provisioning.')"></div>
        <template v-else>
          <div v-for="l in queueLogs" :key="l.name" class="sbiqc-job">
            <div class="sbiqc-job-top">
              <a class="sbiqc-job-id" :href="'/app/provisioning-log/' + l.name">{{ l.name }}</a>
              <span class="sbiqc-job-site">{{ l.site_name || l.tenant }}</span>
              <span class="sbiqc-badge" :style="{ '--bc': logBadgeColor(l.status) }">{{ l.status }}</span>
              <button
                v-if="l.status === 'Queued'"
                class="sbiqc-btn-secondary"
                style="font-size:10px;padding:2px 8px;"
                @click="cancelJob(l.name)"
              >Cancel</button>
            </div>
            <div v-if="l.current_step" class="sbiqc-job-step">{{ l.current_step }}</div>
            <div v-if="l.status === 'Running' || l.status === 'Queued'" class="sbiqc-bar">
              <div class="sbiqc-bar-fill" :data-site="l.site_name || ''" :style="{ width: (l.progress || 0) + '%' }"></div>
            </div>
            <div v-else-if="l.status === 'Completed'" class="sbiqc-bar">
              <div class="sbiqc-bar-fill" style="width:100%;background:var(--green-avatar-bg,#10b981);"></div>
            </div>
            <div v-if="l.completed_at || l.started_at" class="sbiqc-job-ts">{{ prettyDate(l.completed_at || l.started_at) }}</div>
          </div>
        </template>
      </div>

      <!-- Health Panel -->
      <div v-show="section === 'health'" class="sbiqc-panel" id="sbiqc-panel-health">
        <div v-if="healthLoading" class="sbiqc-empty"><p>Loading health checks...</p></div>
        <template v-else-if="healthData">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
            <span :style="{ fontFamily: '\'Syne\',sans-serif', fontSize: '11px', fontWeight: 800, color: overallHealthColor, textTransform: 'uppercase', letterSpacing: '1.2px', display: 'inline-flex', alignItems: 'center', gap: '7px' }">
              <span :style="{ width: '7px', height: '7px', borderRadius: '50%', background: overallHealthColor, boxShadow: '0 0 8px ' + overallHealthColor, display: 'inline-block', flexShrink: 0 }"></span>
              {{ overallHealthLabel }}
            </span>
          </div>
          <div class="sbiqc-health-grid">
            <div v-for="c in healthData.checks" :key="c.name" class="sbiqc-health-card" :style="{ '--hc': healthCheckColor(c.status) }">
              <div class="sbiqc-health-name">{{ c.name }}</div>
              <div class="sbiqc-health-status">{{ (c.status || '').toUpperCase() }}</div>
              <div v-if="c.detail" class="sbiqc-health-detail">{{ c.detail }}</div>
            </div>
          </div>
        </template>
      </div>

      <!-- Reports Panel -->
      <div v-show="section === 'reports'" class="sbiqc-panel" id="sbiqc-panel-reports">
        <div v-if="reportsLoading" class="sbiqc-empty"><p>Loading reports...</p></div>
        <template v-else-if="reportsData">
          <div style="display:flex;gap:12px;margin-bottom:24px;">
            <div class="sbiqc-kpi" style="--kpi-c:var(--primary);">
              <div class="sbiqc-kpi-val">{{ reportsData.avg_provision_minutes || 0 }}m</div>
              <div class="sbiqc-kpi-label">Avg Provision Time</div>
            </div>
            <div class="sbiqc-kpi" style="--kpi-c:#10b981;">
              <div class="sbiqc-kpi-val">{{ reportsData.total_tenants || 0 }}</div>
              <div class="sbiqc-kpi-label">Total Tenants</div>
            </div>
          </div>

          <div class="sbiqc-report-section">
            <div class="sbiqc-report-title">Provisioning by Month</div>
            <div class="sbiqc-bar-chart">
              <div v-for="m in reportsData.monthly || []" :key="m.month" class="sbiqc-bar-row">
                <span class="sbiqc-bar-label">{{ m.month }}</span>
                <div class="sbiqc-bar-track">
                  <div class="sbiqc-bar-seg" :style="{ width: monthlyPct(m) + '%' }">
                    <span class="sbiqc-bar-seg-val">{{ m.count }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="sbiqc-report-section">
            <div class="sbiqc-report-title">Tenants by Plan</div>
            <div class="sbiqc-bar-chart">
              <div v-for="p in reportsData.plans || []" :key="p.plan" class="sbiqc-bar-row">
                <span class="sbiqc-bar-label">{{ p.plan || '—' }}</span>
                <div class="sbiqc-bar-track">
                  <div class="sbiqc-bar-seg" :style="{ width: planReportPct(p) + '%', background: planReportColor(p.plan) }">
                    <span class="sbiqc-bar-seg-val">{{ p.count }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="sbiqc-report-section">
            <div class="sbiqc-report-title">Top Apps Installed</div>
            <div v-for="a in reportsData.top_apps || []" :key="a.app_name" style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border-color);font-size:12px;color:var(--text-color);">
              <span>{{ a.app_name }}</span>
              <span style="color:var(--primary);font-weight:700;">{{ a.count }}</span>
            </div>
          </div>
        </template>
      </div>

      <!-- Errors Panel -->
      <div v-show="section === 'errors'" class="sbiqc-panel" id="sbiqc-panel-errors">
        <div v-if="errorsLoading" class="sbiqc-empty"><p style="color:var(--text-muted);font-size:12px;">Loading...</p></div>
        <div v-else-if="!errorTenants.length" v-html="emptyHtml('No errors', 'All tenants are healthy.')"></div>
        <template v-else>
          <div v-for="t in errorTenants" :key="t.name" class="sbiqc-error-row">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
              <span style="font-weight:700;font-size:13px;color:var(--text-color);">{{ t.client_name || t.subdomain }}</span>
              <span class="sbiqc-muted">{{ t.site_name || '' }}</span>
              <span style="margin-left:auto;display:flex;gap:6px;">
                <button
                  class="sbiqc-act act-blue"
                  style="width:auto;padding:0 8px;gap:4px;font-family:inherit;font-size:11px;"
                  @click="retryTenant(t.name)"
                ><span style="font-family:'Material Icons';font-size:14px;line-height:1;vertical-align:middle;">refresh</span> Retry</button>
                <button
                  class="sbiqc-act"
                  style="width:auto;padding:0 8px;gap:4px;font-family:inherit;font-size:11px;"
                  @click="toggleTraceback(t.name)"
                ><span style="font-family:'Material Icons';font-size:14px;line-height:1;vertical-align:middle;">terminal</span> Traceback</button>
              </span>
            </div>
            <div v-if="t.error_log" class="sbiqc-error-traceback" :class="{ open: openTracebacks.has(t.name) }">{{ (t.error_log || '').substring(0, 5000) }}</div>
          </div>
        </template>
      </div>
    </div>

    <!-- Add Apps Slideout -->
    <div
      class="sbiqc-slideout-backdrop"
      id="sbiqc-backdrop"
      :style="{ display: slideoutOpen ? 'block' : 'none' }"
      @click="slideoutClose"
    ></div>
    <div class="sbiqc-slideout-panel" id="sbiqc-slideout" :class="{ open: slideoutOpen }">
      <div class="sbiqc-slideout-head">
        <span class="sbiqc-slideout-title" id="sbiqc-slideout-title">{{ slideoutTitle }}</span>
        <button class="sbiqc-btn-icon sbiqc-slideout-close" @click="slideoutClose">close</button>
      </div>
      <div class="sbiqc-slideout-body" id="sbiqc-slideout-body">
        <template v-if="slideoutApps !== null">
          <template v-if="installedApps.size > 0">
            <p style="font-size:11px;color:var(--text-muted);margin-bottom:8px;font-weight:600;">Already installed</p>
            <div v-for="a in [...installedApps]" :key="'ins-'+a" class="sbiqc-app-card locked selected" style="margin-bottom:6px;">
              <span class="check">✓</span>{{ a }}
            </div>
          </template>
          <template v-if="availableApps.length > 0">
            <p style="font-size:11px;color:var(--text-muted);margin:12px 0 8px;font-weight:600;">Available to install</p>
            <div
              v-for="a in availableApps"
              :key="'avail-'+a"
              class="sbiqc-app-card sbiqc-addapp-toggle"
              :class="{ selected: selectedAddApps.includes(a) }"
              style="margin-bottom:6px;"
              @click="toggleAddApp(a)"
            >
              <span class="check">{{ selectedAddApps.includes(a) ? '✓' : '○' }}</span>{{ a }}
            </div>
          </template>
          <p v-if="availableApps.length === 0" style="color:var(--text-muted);font-size:12px;margin-top:8px;">All available apps are already installed.</p>
        </template>
      </div>
      <div class="sbiqc-slideout-foot" id="sbiqc-slideout-foot">
        <button
          v-if="availableApps.length > 0"
          class="sbiqc-btn-primary sbiqc-install-selected"
          style="width:100%;"
          @click="addappsSubmit"
        >Install Selected</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";

/* ── globals injected by Frappe ── */
/* globals frappe, __ */

// ── State ──────────────────────────────────────────────────────────────────
const section      = ref("tenants");
const data         = ref(null);
const loading      = ref(false);
const search       = ref("");
const filter       = ref("");
const offset       = ref(0);
const limit        = 20;
const canLoadMore  = ref(false);
const envLabel     = ref("● Local Dev");
const refreshSpinning = ref(false);

// Wizard
const wizardActive  = ref(false);
const wizardStep    = ref(1);
const allApps       = ref([]);
const wizardData    = ref({ subdomain: "", client_name: "", admin_email: "", plan: "Standard", currency: "INR", timezone: "Asia/Kolkata", apps: ["erpnext"] });

// Panels
const healthLoading  = ref(false);
const healthData     = ref(null);
const reportsLoading = ref(false);
const reportsData    = ref(null);
const errorsLoading  = ref(false);
const errorTenants   = ref([]);
const openTracebacks = ref(new Set());

// Slideout
const slideoutOpen    = ref(false);
const slideoutTitle   = ref("Add Apps");
const slideTenant     = ref(null);
const slideoutApps    = ref(null);
const installedApps   = ref(new Set());
const selectedAddApps = ref([]);

// Timers
let _timer = null;
let _health_timer = null;

// ── Static data ────────────────────────────────────────────────────────────
const navItems = [
  { section: "tenants", icon: "dns",              label: "Tenants" },
  { section: "queue",   icon: "pending_actions",  label: "Queue" },
  { section: "health",  icon: "health_and_safety", label: "Health" },
  { section: "reports", icon: "bar_chart",        label: "Reports" },
  { section: "errors",  icon: "error_outline",    label: "Errors" },
];

const filterChips = [
  { status: "",             label: "All" },
  { status: "Active",       label: "Active" },
  { status: "Provisioning", label: "Running" },
  { status: "Pending",      label: "Pending" },
  { status: "Suspended",    label: "Suspended" },
  { status: "Error",        label: "Errors" },
];

// ── Computed ───────────────────────────────────────────────────────────────
const sectionTitle = computed(() => {
  const map = { tenants: "Tenants", queue: "Queue", health: "Health", reports: "Reports", errors: "Errors" };
  return map[section.value] || section.value;
});

const kpis = computed(() => {
  const d = data.value || {};
  return [
    { key: "total",        label: "Total",   val: d.total || 0,        color: "#00D9BE" },
    { key: "Active",       label: "Active",  val: d.Active || 0,       color: "#00CC88" },
    { key: "Provisioning", label: "Running", val: d.Provisioning || 0, color: "#4D9EFF" },
    { key: "Error",        label: "Errors",  val: d.Error || 0,        color: "#FF3F60" },
  ];
});

const queueBadge = computed(() => {
  const d = data.value || {};
  return (d.Provisioning || 0) + (d.Pending || 0);
});

const errorBadge = computed(() => (data.value || {}).Error || 0);

const filteredTenants = computed(() => {
  let tenants = (data.value && data.value.recent_tenants) || [];
  if (filter.value && filter.value !== "total") {
    tenants = tenants.filter(t => t.status === filter.value);
  }
  if (search.value) {
    const s = search.value.toLowerCase();
    tenants = tenants.filter(t =>
      ((t.client_name || "") + " " + (t.subdomain || "") + " " + (t.site_name || "")).toLowerCase().includes(s)
    );
  }
  return tenants;
});

const pagedTenants = computed(() => filteredTenants.value.slice(0, offset.value + limit));

const queueLogs = computed(() => (data.value && data.value.recent_logs) || []);

const overallHealthColor = computed(() => {
  const map = { ok: "#10b981", warn: "#f59e0b", error: "#ef4444" };
  return map[(healthData.value || {}).overall] || map.ok;
});

const overallHealthLabel = computed(() => {
  const o = (healthData.value || {}).overall;
  if (o === "warn") return "Degraded";
  if (o === "error") return "Service error";
  return "All systems operational";
});

const wizardConfirmRows = computed(() => {
  const d = wizardData.value;
  return [
    ["Subdomain", d.subdomain + ".localhost"],
    ["Client Name", d.client_name],
    ["Admin Email", d.admin_email || "—"],
    ["Plan", d.plan],
    ["Currency", d.currency],
    ["Timezone", d.timezone],
    ["Apps", d.apps.join(", ")],
  ];
});

const availableApps = computed(() => {
  if (!slideoutApps.value) return [];
  return slideoutApps.value.filter(a => !installedApps.value.has(a));
});

// ── Reports helpers ────────────────────────────────────────────────────────
function monthlyPct(m) {
  const monthly = (reportsData.value && reportsData.value.monthly) || [];
  const max = Math.max(...monthly.map(x => x.count), 1);
  return Math.round((m.count / max) * 100);
}
function planReportPct(p) {
  const plans = (reportsData.value && reportsData.value.plans) || [];
  const max = Math.max(...plans.map(x => x.count), 1);
  return Math.round((p.count / max) * 100);
}
function planReportColor(plan) {
  const colors = { Starter: "#3D5A7A", Standard: "#4D9EFF", Enterprise: "#9B72FF" };
  return colors[plan] || "var(--primary)";
}

// ── Helper fns ─────────────────────────────────────────────────────────────
function badgeColor(status) {
  const colors = { Active: "#00CC88", Provisioning: "#4D9EFF", Pending: "#FFB300", Error: "#FF3F60", Suspended: "#3D5A7A", Terminated: "#3D5A7A" };
  return colors[status] || "#6b7280";
}
function logBadgeColor(status) {
  const colors = { Completed: "#00CC88", Running: "#4D9EFF", Queued: "#FFB300", Failed: "#FF3F60" };
  return colors[status] || "#6b7280";
}
function planColor(plan) {
  const colors = { Starter: "#3D5A7A", Standard: "#4D9EFF", Enterprise: "#9B72FF" };
  return colors[plan] || "#6b7280";
}
function healthCheckColor(status) {
  const map = { ok: "#10b981", warn: "#f59e0b", error: "#ef4444" };
  return map[status] || map.ok;
}
function prettyDate(dt) {
  return (frappe.datetime && frappe.datetime.prettyDate) ? frappe.datetime.prettyDate(dt) : dt;
}
function emptyHtml(h, p) {
  return `<div class="sbiqc-empty"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="6" cy="6" r="1"/><circle cx="6" cy="18" r="1"/></svg><p class="sbiqc-empty-h">${h}</p><p>${p}</p></div>`;
}

// ── Navigation ─────────────────────────────────────────────────────────────
function goSection(sec) {
  section.value = sec;
  wizardActive.value = false;
  if (sec === "health")  loadHealth();
  if (sec === "reports") loadReports();
  if (sec === "errors")  loadErrors();
}

function setFilter(status) {
  filter.value = status;
  offset.value = 0;
}

// ── Data loading ───────────────────────────────────────────────────────────
function loadStats(cb) {
  if (loading.value) { if (cb) cb(); return; }
  loading.value = true;
  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.get_provisioning_stats",
    args: { offset: 0, limit: limit },
    callback(r) {
      loading.value = false;
      if (r.message) {
        data.value = r.message;
        offset.value = limit;
        canLoadMore.value = (r.message.recent_tenants || []).length === limit;
      }
      if (cb) cb();
    },
    error() { loading.value = false; if (cb) cb(); },
  });
}

function loadMore() {
  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.get_provisioning_stats",
    args: { offset: offset.value, limit: limit },
    callback(r) {
      if (!r.message) return;
      const more = r.message.recent_tenants || [];
      if (data.value) {
        data.value.recent_tenants = (data.value.recent_tenants || []).concat(more);
      }
      offset.value += limit;
      canLoadMore.value = more.length === limit;
    },
  });
}

function loadHealth() {
  healthLoading.value = true;
  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.get_bench_health",
    callback(r) {
      healthLoading.value = false;
      if (r.message) healthData.value = r.message;
    },
  });
  clearInterval(_health_timer);
  _health_timer = setInterval(() => {
    if (section.value === "health") loadHealth();
  }, 30000);
}

function loadReports() {
  reportsLoading.value = true;
  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.get_provisioning_report",
    callback(r) {
      reportsLoading.value = false;
      if (r.message) reportsData.value = r.message;
    },
  });
}

function loadErrors() {
  errorsLoading.value = true;
  frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Tenant",
      filters: [["status", "=", "Error"]],
      fields: ["name", "client_name", "subdomain", "site_name", "error_log"],
      limit: 50,
      order_by: "modified desc",
    },
    callback(r) {
      errorsLoading.value = false;
      errorTenants.value = r.message || [];
    },
  });
}

// ── Row / actions ─────────────────────────────────────────────────────────
function onRowClick(e, t) {
  if (e.target.closest("button,a")) return;
  frappe.set_route("Form", "Tenant", t.name);
}
function openSite(site_name) { window.open("http://" + site_name + ":8000", "_blank"); }
function viewLog(name) { frappe.set_route("List", "Provisioning Log", { tenant: name }); }
function toggleTraceback(name) {
  const s = new Set(openTracebacks.value);
  s.has(name) ? s.delete(name) : s.add(name);
  openTracebacks.value = s;
}

function suspendTenant(name) {
  frappe.confirm(`Suspend tenant ${name}? Their site will become inaccessible.`, () => {
    frappe.db.set_value("Tenant", name, "status", "Suspended").then(() => {
      frappe.show_alert({ message: "Tenant suspended", indicator: "orange" });
      loadStats();
    });
  });
}

function resumeTenant(name) {
  frappe.db.set_value("Tenant", name, "status", "Active").then(() => {
    frappe.show_alert({ message: "Tenant resumed", indicator: "green" });
    loadStats();
  });
}

function retryTenant(name) {
  frappe.confirm(`Re-queue provisioning for ${name}?`, () => {
    frappe.call({
      method: "frappe.client.get",
      args: { doctype: "Tenant", name },
      callback(r) {
        if (!r.message) return;
        if (r.message.docstatus !== 1) {
          frappe.show_alert({ message: "Cannot retry: tenant document is not submitted", indicator: "orange" });
          return;
        }
        frappe.call({
          method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.retry_provisioning",
          args: { tenant_name: name },
          callback() {
            frappe.show_alert({ message: "Provisioning re-queued", indicator: "blue" });
            loadStats();
          },
          error() { frappe.show_alert({ message: "Retry failed — check system logs", indicator: "red" }); },
        });
      },
    });
  });
}

function deleteTenant(name) {
  frappe.confirm(`Permanently delete tenant ${name} and drop its database? This cannot be undone.`, () => {
    frappe.call({
      method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.delete_tenant",
      args: { tenant_name: name },
      callback(r) {
        if (r.message && r.message.status === "ok") {
          frappe.show_alert({ message: "Tenant deleted", indicator: "green" });
          loadStats();
        }
      },
    });
  });
}

function cancelJob(log_name) {
  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.cancel_queued_job",
    args: { log_name },
    callback() { frappe.show_alert({ message: "Job cancelled", indicator: "orange" }); loadStats(); },
  });
}

// ── Wizard ─────────────────────────────────────────────────────────────────
function wizardShow() {
  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.get_installable_apps",
    callback(r) {
      allApps.value = r.message || [];
      wizardData.value = { subdomain: "", client_name: "", admin_email: "", plan: "Standard", currency: "INR", timezone: "Asia/Kolkata", apps: ["erpnext"] };
      wizardStep.value = 1;
      wizardActive.value = true;
    },
  });
}

function sanitizeSubdomain(e) {
  const val = (e.target.value || "").toLowerCase().replace(/[^a-z0-9-]/g, "");
  wizardData.value.subdomain = val;
  e.target.value = val;
}

function toggleWizardApp(app) {
  if (app === "erpnext") return;
  const apps = [...wizardData.value.apps];
  const idx = apps.indexOf(app);
  if (idx !== -1) apps.splice(idx, 1);
  else apps.push(app);
  wizardData.value.apps = apps;
}

function wizardNext() {
  if (wizardStep.value === 1) {
    const d = wizardData.value;
    if (!d.subdomain || !d.client_name) {
      frappe.show_alert({ message: "Subdomain and Client Name are required", indicator: "red" });
      return;
    }
    if (!/^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$/.test(d.subdomain)) {
      frappe.show_alert({ message: "Invalid subdomain format", indicator: "red" });
      return;
    }
  }
  wizardStep.value++;
}

function wizardCancel() {
  wizardActive.value = false;
  wizardStep.value = 1;
}

function wizardSubmit() {
  const d = wizardData.value;
  const apps_rows = d.apps.map(a => ({ app_name: a }));
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
      },
    },
    callback(r) {
      if (!r.exc && r.message) {
        frappe.call({
          method: "frappe.client.submit",
          args: { doc: r.message },
          callback(sr) {
            if (sr.exc) {
              frappe.show_alert({ message: sr.exc || "Submission failed", indicator: "red" });
              return;
            }
            frappe.show_alert({ message: `Provisioning queued for ${d.subdomain}.localhost`, indicator: "blue" });
            wizardCancel();
            loadStats();
          },
          error() { frappe.show_alert({ message: "Failed to submit tenant — please try again", indicator: "red" }); },
        });
      }
    },
  });
}

// ── Add Apps Slideout ──────────────────────────────────────────────────────
function addappsOpen(tenant_name) {
  slideTenant.value = tenant_name;
  const tenants = (data.value && data.value.recent_tenants) || [];
  const t = tenants.find(x => x.name === tenant_name);
  slideoutTitle.value = `Add Apps — ${t ? t.client_name : tenant_name}`;
  slideoutApps.value = null;
  selectedAddApps.value = [];

  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.get_installable_apps",
    callback(r) {
      const all_apps = r.message || [];
      frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Tenant", name: tenant_name },
        callback(tr) {
          const inst = new Set(((tr.message && tr.message.apps_to_install) || []).map(a => a.app_name));
          slideoutApps.value = all_apps;
          installedApps.value = inst;
          slideoutOpen.value = true;
        },
      });
    },
  });
}

function toggleAddApp(app) {
  const arr = [...selectedAddApps.value];
  const idx = arr.indexOf(app);
  if (idx !== -1) arr.splice(idx, 1);
  else arr.push(app);
  selectedAddApps.value = arr;
}

function addappsSubmit() {
  if (!selectedAddApps.value.length) {
    frappe.show_alert({ message: "Select at least one app", indicator: "orange" });
    return;
  }
  frappe.call({
    method: "sbiq_provisioner.sbiq_provisioner.doctype.tenant.tenant.update_tenant_apps",
    args: { tenant_name: slideTenant.value, new_apps: JSON.stringify(selectedAddApps.value) },
    callback(r) {
      if (r.message && r.message.status === "queued") {
        frappe.show_alert({ message: "App installation queued", indicator: "blue" });
        slideoutClose();
        loadStats();
      }
    },
  });
}

function slideoutClose() {
  slideoutOpen.value = false;
  slideTenant.value = null;
}

// ── Refresh button ─────────────────────────────────────────────────────────
function onRefreshClick() {
  refreshSpinning.value = true;
  loadStats(() => {
    setTimeout(() => { refreshSpinning.value = false; }, 500);
    if (section.value === "health") loadHealth();
    if (section.value === "reports") loadReports();
    if (section.value === "errors") loadErrors();
  });
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(() => {
  // Detect environment
  frappe.call({
    method: "frappe.client.get_single_value",
    args: { doctype: "System Settings", field: "app_name" },
    callback() {
      const is_prod = frappe.boot && frappe.boot.conf && frappe.boot.conf.is_production;
      envLabel.value = is_prod ? "● Production" : "● Local Dev";
    },
  });

  loadStats();

  // Auto-refresh every 15s when active provisioning jobs exist
  _timer = setInterval(() => {
    if (data.value && ((data.value.Provisioning || 0) > 0 || (data.value.Pending || 0) > 0)) {
      loadStats();
    }
  }, 15000);

  // Realtime progress updates for queue bar fills
  frappe.realtime.on("progress", (d) => {
    if (!d || !d.title || !d.percent) return;
    document.querySelectorAll(".sbiqc-bar-fill").forEach(el => {
      if (el.dataset.site === d.title) el.style.width = d.percent + "%";
    });
  });

  // Dashboard refresh on server-pushed update events
  frappe.realtime.on("sbiqc_update", loadStats);
});

onUnmounted(() => {
  clearInterval(_timer);
  clearInterval(_health_timer);
  frappe.realtime.off("progress");
  frappe.realtime.off("sbiqc_update", loadStats);
});
</script>

<style scoped>
/* All styles come from sbiq_provisioner.css (loaded globally) — no duplication needed */
</style>
