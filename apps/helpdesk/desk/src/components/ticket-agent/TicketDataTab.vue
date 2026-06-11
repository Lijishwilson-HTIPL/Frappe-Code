<template>
  <div class="td-root">

    <!-- ── Submitter ─────────────────────────────────────── -->
    <section class="td-sec">
      <p class="td-sec-title"><span class="td-sec-dot" style="--c:#818CF8"></span>Submitter</p>
      <div class="contact-card">
        <div class="contact-av" :style="{ background: avatarGradient }">{{ avatarInitial }}</div>
        <div class="contact-info">
          <p class="contact-name">{{ ticket.doc.custom_submitter_name || ticket.doc.contact || "—" }}</p>
          <p class="contact-meta">{{ ticket.doc.raised_by || "—" }}</p>
          <p v-if="contactPhone" class="contact-meta">{{ contactPhone }}</p>
          <span v-if="ticket.doc.customer" class="contact-customer">{{ ticket.doc.customer }}</span>
        </div>
      </div>
    </section>

    <!-- ── Ticket Details ─────────────────────────────────── -->
    <section class="td-sec">
      <p class="td-sec-title"><span class="td-sec-dot" style="--c:#38BDF8"></span>Ticket Details</p>
      <div class="detail-grid">
        <div class="detail-cell">
          <span class="dc-l">Ticket ID</span>
          <span class="dc-v mono">{{ ticket.doc.name || "—" }}</span>
        </div>
        <div class="detail-cell">
          <span class="dc-l">Product / License</span>
          <span class="dc-v" :title="licenseProduct ? 'License found for this email' : ''">
            <span v-if="licenseLoading" style="color:#94A3B8;font-size:11px">Loading…</span>
            <span v-else-if="licenseProduct" style="display:flex;align-items:center;gap:5px">
              <span style="width:6px;height:6px;border-radius:50%;background:#10B981;flex-shrink:0;display:inline-block"></span>
              {{ licenseProduct }}
            </span>
            <span v-else>{{ ticket.doc.custom_product || "—" }}</span>
          </span>
        </div>
        <div class="detail-cell">
          <span class="dc-l">Issue Type</span>
          <span class="dc-v">{{ ticket.doc.ticket_type || "—" }}</span>
        </div>
        <div class="detail-cell">
          <span class="dc-l">Team</span>
          <span class="dc-v">{{ ticket.doc.agent_group || "—" }}</span>
        </div>
        <div class="detail-cell">
          <span class="dc-l">Created</span>
          <span class="dc-v">{{ formatDate(ticket.doc.creation) }}</span>
        </div>
        <div class="detail-cell">
          <span class="dc-l">Priority</span>
          <span :class="['priority-chip', 'pc-' + (ticket.doc.priority || 'medium').toLowerCase()]">
            <span class="pc-dot"></span>{{ ticket.doc.priority || "—" }}
          </span>
        </div>
      </div>
    </section>

    <!-- ── Status & Escalation ────────────────────────────── -->
    <section class="td-sec">
      <p class="td-sec-title"><span class="td-sec-dot" style="--c:#34D399"></span>Status &amp; Escalation</p>
      <div class="pipeline-card">
        <!-- Pipeline steps -->
        <div class="pipeline">
          <div
            v-for="(stage, i) in pipelineStages"
            :key="stage"
            :class="['pipe-item', i < currentStageIndex && 'done', i === currentStageIndex && 'active']"
          >
            <div class="pipe-track">
              <div v-if="i > 0" :class="['pipe-line', i <= currentStageIndex && 'filled']"></div>
              <div class="pipe-node">
                <svg v-if="i < currentStageIndex" width="9" height="9" viewBox="0 0 9 9" fill="none">
                  <path d="M1.5 4.5l2 2L7.5 2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span v-else style="font-size:9px;font-weight:700;line-height:1">{{ i + 1 }}</span>
              </div>
            </div>
            <p class="pipe-label">{{ stage }}</p>
          </div>
        </div>

        <!-- Escalation pills -->
        <div class="esc-row">
          <span class="esc-label">Escalation</span>
          <div style="display:flex;gap:6px">
            <span
              v-for="lvl in ['L1','L2']"
              :key="lvl"
              :class="['esc-pill', currentLevel === lvl && 'active']"
            >{{ lvl }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── SLA ────────────────────────────────────────────── -->
    <section class="td-sec">
      <p class="td-sec-title"><span class="td-sec-dot" style="--c:#FBBF24"></span>SLA</p>
      <div class="sla-card">

        <div class="sla-top">
          <span class="sla-name">{{ ticket.doc.sla || "No SLA" }}</span>
          <span :class="['agreement-badge', 'ab-' + (ticket.doc.agreement_status || '').toLowerCase().replace(/\s+/g,'-')]">
            {{ ticket.doc.agreement_status || "—" }}
          </span>
        </div>

        <div class="sla-items">
          <!-- Response -->
          <div class="sla-item">
            <div class="sla-item-hdr">
              <FeatherIcon name="clock" class="sla-icon" />
              <span class="sla-item-label">Response By</span>
              <span class="sla-item-val">{{ formatDate(ticket.doc.response_by) }}</span>
            </div>
            <div v-if="ticket.doc.response_by" class="sla-bar-track">
              <div
                class="sla-bar-fill"
                :class="progressBarClass(responsePercent)"
                :style="{ width: responsePercent + '%' }"
              ></div>
            </div>
          </div>

          <!-- Resolution -->
          <div class="sla-item">
            <div class="sla-item-hdr">
              <FeatherIcon name="check-circle" class="sla-icon" />
              <span class="sla-item-label">Resolve By</span>
              <span class="sla-item-val">{{ formatDate(ticket.doc.resolution_by) }}</span>
            </div>
          </div>
        </div>

      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { FeatherIcon } from "frappe-ui";
import { computed, inject, ref, watch } from "vue";
import { TicketContactSymbol, TicketSymbol } from "@/types";

const ticket = inject(TicketSymbol);
const ticketContact = inject(TicketContactSymbol);
const contact = computed(() => ticketContact?.value?.data);

const avatarInitial = computed(() => {
  const name =
    ticket.value?.doc?.custom_submitter_name ||
    ticket.value?.doc?.contact ||
    "";
  return name.charAt(0).toUpperCase() || "?";
});

/* Deterministic gradient from name */
const avatarGradient = computed(() => {
  const name = ticket.value?.doc?.custom_submitter_name || ticket.value?.doc?.contact || "X";
  const palettes = [
    "linear-gradient(135deg,#6366F1,#818CF8)",
    "linear-gradient(135deg,#0EA5E9,#38BDF8)",
    "linear-gradient(135deg,#10B981,#34D399)",
    "linear-gradient(135deg,#F59E0B,#FCD34D)",
    "linear-gradient(135deg,#EC4899,#F9A8D4)",
    "linear-gradient(135deg,#8B5CF6,#C4B5FD)",
  ];
  const idx = name.charCodeAt(0) % palettes.length;
  return palettes[idx];
});

const contactPhone = computed(
  () =>
    ticket.value?.doc?.custom_phone ||
    contact.value?.phone ||
    contact.value?.mobile_no ||
    ""
);

// Any assigned team → L2; no team → L1
const currentLevel = computed(() =>
  (ticket.value?.doc?.agent_group || "").trim() ? "L2" : "L1"
);

// License product lookup by submitter email
const licenseProduct = ref("");
const licenseLoading = ref(false);
const submitterEmail = computed(() => ticket.value?.doc?.raised_by || "");

async function fetchLicense(email: string) {
  if (!email) { licenseProduct.value = ""; return; }
  licenseLoading.value = true;
  try {
    const res = await fetch(
      "/api/method/helpdesk.helpdesk.portal_api.get_license_by_email",
      {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": (window as any).frappe?.csrf_token || "",
        },
        body: JSON.stringify({ email }),
      }
    );
    const data = await res.json();
    licenseProduct.value = data?.message?.product || "";
  } catch {
    licenseProduct.value = "";
  } finally {
    licenseLoading.value = false;
  }
}

watch(submitterEmail, (e) => fetchLicense(e), { immediate: true });

const pipelineStages = ["Open", "In Progress", "Awaiting", "Resolved", "Closed"];

const currentStageIndex = computed(() => {
  const s = (ticket.value?.doc?.status || "").toLowerCase();
  if (s.includes("clos"))                              return 4;
  if (s.includes("resolv"))                            return 3;
  if (s.includes("wait") || s.includes("hold") || s.includes("awai")) return 2;
  if (s.includes("progress") || s.includes("reply"))  return 1;
  return 0;
});

const responsePercent = computed(() => {
  const creation  = ticket.value?.doc?.creation;
  const responsBy = ticket.value?.doc?.response_by;
  if (!creation || !responsBy) return 0;
  const start = new Date(creation).getTime();
  const end   = new Date(responsBy).getTime();
  const now   = Date.now();
  if (end <= start) return 100;
  return Math.min(100, Math.round(((now - start) / (end - start)) * 100));
});

function progressBarClass(pct: number) {
  if (pct >= 90) return "fill-danger";
  if (pct >= 70) return "fill-warn";
  return "fill-ok";
}

function formatDate(val?: string) {
  if (!val) return "—";
  return new Date(val).toLocaleString(undefined, {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Root ── */
.td-root {
  overflow-y: auto;
  height: 100%;
  padding: 14px 14px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: 'DM Sans', system-ui, sans-serif;
}

/* ── Section wrapper ── */
.td-sec { display: flex; flex-direction: column; gap: 8px; }

.td-sec-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .09em;
  color: #94A3B8;
}

.td-sec-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c, #94A3B8);
  flex-shrink: 0;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--c, #94A3B8) 20%, transparent);
}

/* ── Contact Card ── */
.contact-card {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  padding: 12px 13px;
}

.contact-av {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'DM Mono', monospace;
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,.14);
}

.contact-info { flex: 1; min-width: 0; }

.contact-name {
  font-size: 13.5px;
  font-weight: 700;
  color: #0F172A;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.contact-meta {
  font-size: 11.5px;
  color: #64748B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 1px;
}

.contact-customer {
  display: inline-block;
  margin-top: 7px;
  background: #EFF6FF;
  color: #3B82F6;
  font-size: 10.5px;
  font-weight: 600;
  border-radius: 20px;
  padding: 2px 9px;
  border: 1px solid #BFDBFE;
}

/* ── Detail Grid ── */
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: #E2E8F0;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  overflow: hidden;
}

.detail-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: #FFFFFF;
}
.detail-cell:nth-child(1) { border-radius: 9px 0 0 0; }
.detail-cell:nth-child(2) { border-radius: 0 9px 0 0; }
.detail-cell:nth-last-child(2) { border-radius: 0 0 0 9px; }
.detail-cell:nth-last-child(1) { border-radius: 0 0 9px 0; }

.dc-l {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: #94A3B8;
}

.dc-v {
  font-size: 12.5px;
  font-weight: 600;
  color: #1E293B;
  word-break: break-word;
}

.mono { font-family: 'DM Mono', monospace; font-size: 12px; color: #6366F1; }

/* ── Priority chip ── */
.priority-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  white-space: nowrap;
  width: fit-content;
}
.pc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.pc-high   { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.pc-high   .pc-dot { background: #EF4444; }
.pc-medium { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.pc-medium .pc-dot { background: #F59E0B; }
.pc-low    { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.pc-low    .pc-dot { background: #22C55E; }
.pc-urgent { background: #FFF5F5; color: #C53030; border: 1px solid #FEB2B2; }
.pc-urgent .pc-dot { background: #FC8181; box-shadow: 0 0 0 2px rgba(252,129,129,.3); }

/* ── Pipeline ── */
.pipeline-card {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  padding: 14px 13px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pipeline {
  display: flex;
  align-items: flex-start;
}

.pipe-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.pipe-track {
  display: flex;
  align-items: center;
  width: 100%;
  position: relative;
}

.pipe-line {
  flex: 1;
  height: 2px;
  background: #E2E8F0;
  margin-right: 0;
  transition: background .3s;
}
.pipe-line.filled { background: #10B981; }

.pipe-node {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #E2E8F0;
  color: #94A3B8;
  border: 2px solid #E2E8F0;
  position: relative;
  z-index: 1;
  transition: all .25s cubic-bezier(.4,0,.2,1);
}

.pipe-item.done .pipe-node {
  background: #10B981;
  border-color: #10B981;
  color: #fff;
}

.pipe-item.active .pipe-node {
  background: #3B82F6;
  border-color: #3B82F6;
  color: #fff;
  box-shadow: 0 0 0 4px rgba(59,130,246,.2);
  animation: pulse-node 2s ease-in-out infinite;
}

@keyframes pulse-node {
  0%,100% { box-shadow: 0 0 0 4px rgba(59,130,246,.2); }
  50%      { box-shadow: 0 0 0 7px rgba(59,130,246,.08); }
}

.pipe-label {
  font-size: 9px;
  font-weight: 600;
  text-align: center;
  color: #94A3B8;
  margin-top: 5px;
  line-height: 1.3;
  max-width: 40px;
  text-transform: uppercase;
  letter-spacing: .04em;
}

.pipe-item.done  .pipe-label  { color: #059669; }
.pipe-item.active .pipe-label { color: #2563EB; font-weight: 700; }

/* ── Escalation ── */
.esc-row {
  display: flex;
  align-items: center;
  gap: 9px;
  padding-top: 8px;
  border-top: 1px solid #E2E8F0;
}

.esc-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #94A3B8;
  flex-shrink: 0;
}

.esc-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 24px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  font-family: 'DM Mono', monospace;
  border: 1.5px solid #E2E8F0;
  background: #fff;
  color: #94A3B8;
  transition: all .2s cubic-bezier(.4,0,.2,1);
}

.esc-pill.active {
  background: #3B82F6;
  border-color: #3B82F6;
  color: #fff;
  box-shadow: 0 2px 8px rgba(59,130,246,.35);
}

/* ── SLA Card ── */
.sla-card {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  padding: 12px 13px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sla-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.sla-name {
  font-size: 12.5px;
  font-weight: 700;
  color: #1E293B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agreement-badge {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
  border: 1px solid;
  white-space: nowrap;
  flex-shrink: 0;
}
.ab-fulfilled            { background: #F0FDF4; color: #16A34A; border-color: #BBF7D0; }
.ab-failed               { background: #FEF2F2; color: #DC2626; border-color: #FECACA; }
.ab-first-response-due   { background: #FFFBEB; color: #D97706; border-color: #FDE68A; }
.ab-resolution-due       { background: #FFF7ED; color: #C2410C; border-color: #FED7AA; }
.ab-paused               { background: #F8FAFC; color: #64748B; border-color: #CBD5E1; }

.sla-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sla-item { display: flex; flex-direction: column; gap: 5px; }

.sla-item-hdr {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sla-icon {
  width: 13px;
  height: 13px;
  color: #94A3B8;
  flex-shrink: 0;
}

.sla-item-label {
  font-size: 12px;
  color: #64748B;
  flex: 1;
}

.sla-item-val {
  font-size: 11.5px;
  font-weight: 600;
  color: #1E293B;
}

.sla-bar-track {
  height: 4px;
  border-radius: 9px;
  background: #E2E8F0;
  overflow: hidden;
  margin-left: 19px;
}

.sla-bar-fill {
  height: 100%;
  border-radius: 9px;
  transition: width .6s cubic-bezier(.4,0,.2,1);
}

.fill-ok     { background: #10B981; }
.fill-warn   { background: #F59E0B; }
.fill-danger { background: #EF4444; }
</style>
