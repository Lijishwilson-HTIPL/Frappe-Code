<template>
  <div class="overflow-y-auto h-full px-4 py-4 space-y-6">

    <!-- Submitter Info -->
    <section>
      <p class="text-[11px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        Submitter
      </p>
      <div class="space-y-3">
        <DataRow label="Name" :value="ticket.doc.custom_submitter_name || ticket.doc.contact || '—'" icon="user" />
        <DataRow label="Email" :value="ticket.doc.raised_by || '—'" icon="mail" />
        <DataRow label="Phone" :value="ticket.doc.custom_phone || contact?.phone || contact?.mobile_no || '—'" icon="phone" />
        <DataRow label="Customer" :value="ticket.doc.customer || '—'" icon="briefcase" />
      </div>
    </section>

    <Divider />

    <!-- Ticket Details -->
    <section>
      <p class="text-[11px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        Ticket Details
      </p>
      <div class="space-y-3">
        <DataRow label="Ticket ID" :value="String(ticket.doc.name || '—')" icon="hash" />
        <DataRow label="Product" :value="ticket.doc.custom_product || '—'" icon="box" />
        <DataRow label="Issue Type" :value="ticket.doc.ticket_type || '—'" icon="tag" />
        <div class="flex items-center justify-between py-1.5">
          <span class="flex items-center gap-1.5 text-sm text-ink-gray-6">
            <FeatherIcon name="alert-circle" class="w-3.5 h-3.5 text-ink-gray-4" />
            Priority
          </span>
          <PriorityBadge :priority="ticket.doc.priority" />
        </div>
        <DataRow label="Team" :value="ticket.doc.agent_group || '—'" icon="users" />
        <DataRow label="Created" :value="formatDate(ticket.doc.creation)" icon="calendar" />
      </div>
    </section>

    <Divider />

    <!-- Status & Escalation -->
    <section>
      <p class="text-[11px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        Status & Escalation
      </p>
      <div class="space-y-3">

        <!-- Current Status -->
        <div class="flex items-center justify-between py-1.5">
          <span class="flex items-center gap-1.5 text-sm text-ink-gray-6">
            <FeatherIcon name="activity" class="w-3.5 h-3.5 text-ink-gray-4" />
            Status
          </span>
          <StatusBadge :status="ticket.doc.status" />
        </div>

        <!-- Escalation Level -->
        <div class="flex items-center justify-between py-1.5">
          <span class="flex items-center gap-1.5 text-sm text-ink-gray-6">
            <FeatherIcon name="layers" class="w-3.5 h-3.5 text-ink-gray-4" />
            Level
          </span>
          <div class="flex gap-1.5">
            <LevelBadge v-for="lvl in ['L1', 'L2', 'L3']" :key="lvl" :level="lvl" :active="currentLevel === lvl" />
          </div>
        </div>

        <!-- Stage pills -->
        <div class="pt-1">
          <p class="text-xs text-ink-gray-4 mb-2">Stage</p>
          <div class="flex flex-wrap gap-1.5">
            <StagePill
              v-for="stage in stages"
              :key="stage.key"
              :label="stage.label"
              :active="currentStage === stage.key"
              :color="stage.color"
            />
          </div>
        </div>

      </div>
    </section>

    <Divider />

    <!-- SLA -->
    <section>
      <p class="text-[11px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        SLA
      </p>
      <div class="space-y-3">
        <DataRow label="SLA" :value="ticket.doc.sla || '—'" icon="shield" />
        <DataRow label="Response By" :value="formatDate(ticket.doc.response_by)" icon="clock" />
        <DataRow label="Resolve By" :value="formatDate(ticket.doc.resolution_by)" icon="check-circle" />
        <div class="flex items-center justify-between py-1.5">
          <span class="flex items-center gap-1.5 text-sm text-ink-gray-6">
            <FeatherIcon name="bar-chart-2" class="w-3.5 h-3.5 text-ink-gray-4" />
            Agreement
          </span>
          <SLABadge :status="ticket.doc.agreement_status" />
        </div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { FeatherIcon } from "frappe-ui";
import { computed, inject } from "vue";
import { TicketContactSymbol, TicketSymbol } from "@/types";

const ticket = inject(TicketSymbol);
const ticketContact = inject(TicketContactSymbol);
const contact = computed(() => ticketContact?.value?.data);

// Derive escalation level from agent_group name (L1 / L2 / L3)
const currentLevel = computed(() => {
  const group = (ticket.value?.doc?.agent_group || "").toUpperCase();
  if (group.includes("L3")) return "L3";
  if (group.includes("L2")) return "L2";
  return "L1";
});

// Map ticket status → stage key
const stages = [
  { key: "open",                  label: "Open",                  color: "blue"   },
  { key: "in_progress",           label: "In Progress",           color: "amber"  },
  { key: "awaiting_confirmation", label: "Awaiting Confirmation", color: "violet" },
  { key: "resolved",              label: "Resolved",              color: "green"  },
  { key: "closed",                label: "Closed",                color: "gray"   },
];

const currentStage = computed(() => {
  const s = (ticket.value?.doc?.status || "").toLowerCase().replace(/\s+/g, "_");
  if (s.includes("progress") || s.includes("reply") || s.includes("open")) return "open";
  if (s.includes("waiting") || s.includes("hold") || s.includes("paused")) return "awaiting_confirmation";
  if (s.includes("resolv")) return "resolved";
  if (s.includes("clos")) return "closed";
  return "open";
});

function formatDate(val?: string) {
  if (!val) return "—";
  return new Date(val).toLocaleString(undefined, {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}
</script>

<!-- ── Sub-components defined inline ────────────────────────────────────────── -->

<script lang="ts">
import { defineComponent, h } from "vue";
import { FeatherIcon } from "frappe-ui";

/* DataRow */
export const DataRow = defineComponent({
  props: { label: String, value: String, icon: String },
  setup(p) {
    return () =>
      h("div", { class: "flex items-start justify-between py-1.5 gap-2" }, [
        h("span", { class: "flex items-center gap-1.5 text-sm text-ink-gray-6 shrink-0" }, [
          h(FeatherIcon, { name: p.icon || "info", class: "w-3.5 h-3.5 text-ink-gray-4" }),
          p.label,
        ]),
        h("span", { class: "text-sm font-medium text-ink-gray-8 text-right max-w-[55%] break-words" }, p.value || "—"),
      ]);
  },
});

/* Divider */
export const Divider = defineComponent({
  setup: () => () => h("div", { class: "border-t border-outline-gray-1" }),
});

/* PriorityBadge */
const priorityMap: Record<string, string> = {
  High:   "bg-red-50   text-red-700   border-red-200",
  Medium: "bg-amber-50 text-amber-700 border-amber-200",
  Low:    "bg-green-50 text-green-700 border-green-200",
};
export const PriorityBadge = defineComponent({
  props: { priority: String },
  setup(p) {
    return () =>
      h("span", {
        class: `inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${priorityMap[p.priority || ""] || "bg-surface-gray-2 text-ink-gray-5 border-outline-gray-2"}`,
      }, p.priority || "—");
  },
});

/* StatusBadge */
export const StatusBadge = defineComponent({
  props: { status: String },
  setup(p) {
    return () =>
      h("span", {
        class: "inline-flex items-center rounded-full bg-sky-50 border border-sky-200 text-sky-700 px-2.5 py-0.5 text-xs font-semibold",
      }, p.status || "—");
  },
});

/* LevelBadge */
export const LevelBadge = defineComponent({
  props: { level: String, active: Boolean },
  setup(p) {
    return () =>
      h("span", {
        class: `inline-flex items-center justify-center w-8 h-6 rounded text-[11px] font-bold border transition-colors ${
          p.active
            ? "bg-sky-500 text-white border-sky-500"
            : "bg-surface-gray-1 text-ink-gray-4 border-outline-gray-2"
        }`,
      }, p.level);
  },
});

/* StagePill */
const colorMap: Record<string, string> = {
  blue:   "bg-blue-50   text-blue-700   border-blue-200",
  amber:  "bg-amber-50  text-amber-700  border-amber-200",
  violet: "bg-violet-50 text-violet-700 border-violet-200",
  green:  "bg-green-50  text-green-700  border-green-200",
  gray:   "bg-surface-gray-1 text-ink-gray-5 border-outline-gray-2",
};
export const StagePill = defineComponent({
  props: { label: String, active: Boolean, color: String },
  setup(p) {
    return () =>
      h("span", {
        class: `inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-all ${
          p.active
            ? (colorMap[p.color || "gray"] || colorMap.gray) + " ring-1 ring-offset-1 ring-current"
            : "bg-surface-gray-1 text-ink-gray-3 border-outline-gray-1 opacity-50"
        }`,
      }, p.label);
  },
});

/* SLABadge */
const slaMap: Record<string, string> = {
  "Fulfilled":           "bg-green-50  text-green-700  border-green-200",
  "First Response Due":  "bg-amber-50  text-amber-700  border-amber-200",
  "Resolution Due":      "bg-orange-50 text-orange-700 border-orange-200",
  "Failed":              "bg-red-50    text-red-700    border-red-200",
  "Paused":              "bg-slate-50  text-slate-600  border-slate-200",
};
export const SLABadge = defineComponent({
  props: { status: String },
  setup(p) {
    return () =>
      h("span", {
        class: `inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${slaMap[p.status || ""] || "bg-surface-gray-1 text-ink-gray-4 border-outline-gray-2"}`,
      }, p.status || "—");
  },
});
</script>
