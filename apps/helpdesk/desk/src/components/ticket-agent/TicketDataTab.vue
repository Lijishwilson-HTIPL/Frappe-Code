<template>
  <div class="overflow-y-auto h-full px-4 py-5 space-y-5">

    <!-- Section 1: Submitter card -->
    <section>
      <p class="text-[10px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        Submitter
      </p>
      <div class="bg-surface-gray-1 rounded-xl p-4">
        <div class="flex items-start gap-3">
          <!-- Avatar -->
          <div
            class="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-base font-bold shrink-0"
          >
            {{ avatarInitial }}
          </div>
          <!-- Info -->
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-ink-gray-9 truncate">
              {{ ticket.doc.custom_submitter_name || ticket.doc.contact || "—" }}
            </p>
            <p class="text-xs text-ink-gray-5 truncate mt-0.5">
              {{ ticket.doc.raised_by || "—" }}
            </p>
            <p
              v-if="contactPhone"
              class="text-xs text-ink-gray-5 truncate mt-0.5"
            >
              {{ contactPhone }}
            </p>
            <span
              v-if="ticket.doc.customer"
              class="inline-block mt-2 bg-surface-gray-2 text-ink-gray-6 text-xs rounded-full px-2 py-0.5"
            >
              {{ ticket.doc.customer }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 2: Ticket snapshot (2-col grid) -->
    <section>
      <p class="text-[10px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        Ticket Details
      </p>
      <div class="bg-surface-gray-1 rounded-xl p-4">
        <div class="grid grid-cols-2 gap-x-4 gap-y-4">
          <DataCell label="Ticket ID" :value="String(ticket.doc.name || '—')" />
          <DataCell label="Product" :value="ticket.doc.custom_product || '—'" />
          <DataCell label="Issue Type" :value="ticket.doc.ticket_type || '—'" />
          <DataCell label="Team" :value="ticket.doc.agent_group || '—'" />
          <DataCell label="Created" :value="formatDate(ticket.doc.creation)" />
          <!-- Priority cell -->
          <div>
            <p class="text-[10px] text-ink-gray-4 uppercase tracking-wide mb-1">Priority</p>
            <PriorityDot :priority="ticket.doc.priority" />
          </div>
        </div>
      </div>
    </section>

    <!-- Section 3: Status pipeline -->
    <section>
      <p class="text-[10px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        Status & Escalation
      </p>
      <div class="bg-surface-gray-1 rounded-xl p-4 space-y-4">
        <StatusPipeline :current="currentStageIndex" :stages="pipelineStages" />
        <EscalationBar :level="currentLevel" />
      </div>
    </section>

    <!-- Section 4: SLA card -->
    <section>
      <p class="text-[10px] font-bold uppercase tracking-widest text-ink-gray-4 mb-3">
        SLA
      </p>
      <div class="bg-surface-gray-1 rounded-xl p-4 space-y-3">
        <p class="text-sm font-semibold text-ink-gray-8">
          {{ ticket.doc.sla || "—" }}
        </p>

        <div class="space-y-2">
          <!-- Response By -->
          <div class="flex items-center justify-between">
            <span class="flex items-center gap-1.5 text-sm text-ink-gray-6">
              <FeatherIcon name="clock" class="w-3.5 h-3.5 text-ink-gray-4" />
              Response By
            </span>
            <span class="text-sm font-medium text-ink-gray-8">
              {{ formatDate(ticket.doc.response_by) }}
            </span>
          </div>
          <!-- Response progress bar -->
          <div
            v-if="ticket.doc.response_by"
            class="h-1.5 rounded-full bg-surface-gray-2 overflow-hidden"
          >
            <div
              class="h-full rounded-full transition-all"
              :class="progressBarColor(responsePercent)"
              :style="{ width: responsePercent + '%' }"
            />
          </div>

          <!-- Resolve By -->
          <div class="flex items-center justify-between mt-1">
            <span class="flex items-center gap-1.5 text-sm text-ink-gray-6">
              <FeatherIcon name="check-circle" class="w-3.5 h-3.5 text-ink-gray-4" />
              Resolve By
            </span>
            <span class="text-sm font-medium text-ink-gray-8">
              {{ formatDate(ticket.doc.resolution_by) }}
            </span>
          </div>
        </div>

        <div class="flex items-center justify-between pt-1">
          <span class="text-sm text-ink-gray-5">Agreement</span>
          <AgreementBadge :status="ticket.doc.agreement_status" />
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

// Avatar initial
const avatarInitial = computed(() => {
  const name =
    ticket.value?.doc?.custom_submitter_name ||
    ticket.value?.doc?.contact ||
    "";
  return name.charAt(0).toUpperCase() || "?";
});

// Phone from ticket or contact
const contactPhone = computed(
  () =>
    ticket.value?.doc?.custom_phone ||
    contact.value?.phone ||
    contact.value?.mobile_no ||
    ""
);

// Escalation level from agent_group
const currentLevel = computed(() => {
  const group = (ticket.value?.doc?.agent_group || "").toUpperCase();
  if (group.includes("L3")) return "L3";
  if (group.includes("L2")) return "L2";
  return "L1";
});

// Pipeline stages
const pipelineStages = ["Open", "In Progress", "Awaiting", "Resolved", "Closed"];

const currentStageIndex = computed(() => {
  const s = (ticket.value?.doc?.status || "").toLowerCase();
  if (s.includes("clos")) return 4;
  if (s.includes("resolv")) return 3;
  if (s.includes("wait") || s.includes("hold") || s.includes("awai")) return 2;
  if (s.includes("progress") || s.includes("reply")) return 1;
  return 0;
});

// SLA response percent elapsed
const responsePercent = computed(() => {
  const creation = ticket.value?.doc?.creation;
  const responsBy = ticket.value?.doc?.response_by;
  if (!creation || !responsBy) return 0;
  const start = new Date(creation).getTime();
  const end = new Date(responsBy).getTime();
  const now = Date.now();
  if (end <= start) return 100;
  return Math.min(100, Math.round(((now - start) / (end - start)) * 100));
});

function progressBarColor(pct: number) {
  if (pct >= 90) return "bg-red-500";
  if (pct >= 70) return "bg-amber-400";
  return "bg-green-500";
}

function formatDate(val?: string) {
  if (!val) return "—";
  return new Date(val).toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<!-- ── Inline sub-components ──────────────────────────────────────────────── -->

<script lang="ts">
import { defineComponent, h } from "vue";

/* DataCell — label on top, value below */
export const DataCell = defineComponent({
  props: { label: String, value: String },
  setup(p) {
    return () =>
      h("div", {}, [
        h(
          "p",
          { class: "text-[10px] text-ink-gray-4 uppercase tracking-wide mb-1" },
          p.label
        ),
        h(
          "p",
          { class: "text-sm font-medium text-ink-gray-8 break-words" },
          p.value || "—"
        ),
      ]);
  },
});

/* PriorityDot — colored dot + text */
const priorityDotMap: Record<string, { dot: string; text: string }> = {
  High:   { dot: "bg-red-500",   text: "text-red-700"   },
  Medium: { dot: "bg-amber-400", text: "text-amber-700" },
  Low:    { dot: "bg-green-500", text: "text-green-700" },
};
export const PriorityDot = defineComponent({
  props: { priority: String },
  setup(p) {
    return () => {
      const cfg = priorityDotMap[p.priority || ""] || {
        dot: "bg-surface-gray-3",
        text: "text-ink-gray-5",
      };
      return h("span", { class: "inline-flex items-center gap-1.5" }, [
        h("span", { class: `w-2 h-2 rounded-full shrink-0 ${cfg.dot}` }),
        h(
          "span",
          { class: `text-sm font-medium ${cfg.text}` },
          p.priority || "—"
        ),
      ]);
    };
  },
});

/* AgreementBadge */
const agreementMap: Record<string, string> = {
  Fulfilled:            "bg-green-50  text-green-700  border-green-200",
  "First Response Due": "bg-amber-50  text-amber-700  border-amber-200",
  "Resolution Due":     "bg-orange-50 text-orange-700 border-orange-200",
  Failed:               "bg-red-50    text-red-700    border-red-200",
  Paused:               "bg-slate-50  text-slate-600  border-slate-200",
};
export const AgreementBadge = defineComponent({
  props: { status: String },
  setup(p) {
    return () =>
      h(
        "span",
        {
          class: `inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
            agreementMap[p.status || ""] ||
            "bg-surface-gray-1 text-ink-gray-4 border-outline-gray-2"
          }`,
        },
        p.status || "—"
      );
  },
});

/* EscalationBar — L1 / L2 / L3 pills */
export const EscalationBar = defineComponent({
  props: { level: String },
  setup(p) {
    return () =>
      h("div", { class: "flex items-center gap-2" }, [
        h(
          "span",
          { class: "text-xs text-ink-gray-4 shrink-0" },
          "Escalation:"
        ),
        h(
          "div",
          { class: "flex gap-1.5" },
          ["L1", "L2", "L3"].map((lvl) =>
            h(
              "span",
              {
                key: lvl,
                class: `inline-flex items-center justify-center w-8 h-6 rounded text-[11px] font-bold border transition-colors ${
                  p.level === lvl
                    ? "bg-blue-500 text-white border-blue-500"
                    : "bg-surface-gray-1 text-ink-gray-4 border-outline-gray-2"
                }`,
              },
              lvl
            )
          )
        ),
      ]);
  },
});

/* StatusPipeline — horizontal 5-step pipeline */
export const StatusPipeline = defineComponent({
  props: {
    stages: { type: Array as () => string[], default: () => [] },
    current: { type: Number, default: 0 },
  },
  setup(p) {
    return () => {
      const nodes = p.stages.map((label, i) => {
        let circleClass = "";
        let labelClass = "text-ink-gray-3";

        if (i < p.current) {
          // completed
          circleClass =
            "bg-green-500 text-white";
          labelClass = "text-green-700";
        } else if (i === p.current) {
          // active
          circleClass =
            "bg-blue-500 text-white ring-2 ring-blue-200";
          labelClass = "text-blue-700 font-semibold";
        } else {
          // upcoming
          circleClass = "bg-surface-gray-2 text-ink-gray-3";
        }

        const isLast = i === p.stages.length - 1;

        return h("div", { key: label, class: "flex flex-col items-center flex-1" }, [
          // row: circle + connector
          h("div", { class: "flex items-center w-full" }, [
            h(
              "div",
              {
                class: `w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${circleClass}`,
              },
              String(i + 1)
            ),
            !isLast
              ? h("div", {
                  class: `flex-1 h-0.5 ${i < p.current ? "bg-green-400" : "bg-surface-gray-2"}`,
                })
              : null,
          ]),
          // label
          h(
            "p",
            {
              class: `mt-1.5 text-[9px] text-center leading-tight ${labelClass}`,
              style: "max-width:40px",
            },
            label
          ),
        ]);
      });

      return h("div", { class: "flex items-start w-full" }, nodes);
    };
  },
});
</script>
