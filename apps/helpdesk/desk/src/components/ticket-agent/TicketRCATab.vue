<template>
  <div class="overflow-y-auto h-full px-4 py-5 space-y-5">

    <!-- RCA Status Banner -->
    <div v-if="ticket.doc.rca_required" :class="bannerClass" class="rounded-xl px-4 py-3 flex items-center gap-3">
      <FeatherIcon :name="bannerIcon" class="w-4 h-4 shrink-0" />
      <div class="flex-1 min-w-0">
        <p class="text-sm font-semibold">RCA Required</p>
        <p v-if="ticket.doc.rca_trigger_reason" class="text-xs mt-0.5 opacity-80">{{ ticket.doc.rca_trigger_reason }}</p>
      </div>
      <StatusPill :status="ticket.doc.rca_status || 'Pending'" />
    </div>
    <div v-else class="bg-surface-gray-1 rounded-xl px-4 py-3 flex items-center gap-3">
      <FeatherIcon name="info" class="w-4 h-4 text-ink-gray-4 shrink-0" />
      <p class="text-sm text-ink-gray-5">RCA not required for this ticket. You can still document one below.</p>
    </div>

    <!-- Root Cause -->
    <RcaSection title="Root Cause" icon="alert-circle" color="red">
      <RcaEditor
        fieldname="rca_root_cause"
        placeholder="Describe what caused this issue..."
        :value="ticket.doc.rca_root_cause"
        @save="saveField"
      />
    </RcaSection>

    <!-- Fix / Workaround -->
    <RcaSection title="Fix / Workaround" icon="tool" color="blue">
      <RcaEditor
        fieldname="rca_fix_workaround"
        placeholder="Describe the fix or workaround applied..."
        :value="ticket.doc.rca_fix_workaround"
        @save="saveField"
      />
    </RcaSection>

    <!-- Preventive Measures -->
    <RcaSection title="Preventive Measures" icon="shield" color="green">
      <RcaEditor
        fieldname="rca_prevention"
        placeholder="How can this be prevented in future?"
        :value="ticket.doc.rca_prevention"
        @save="saveField"
      />
    </RcaSection>

    <!-- References -->
    <div class="bg-surface-gray-1 rounded-xl p-4 space-y-3">
      <p class="text-[10px] font-bold uppercase tracking-widest text-ink-gray-4">References</p>

      <div class="flex flex-col gap-1">
        <label class="text-xs text-ink-gray-5">KB Article</label>
        <input
          class="w-full text-sm px-3 py-2 rounded-lg border border-outline-gray-2 bg-surface-white focus:outline-none focus:border-blue-400 text-ink-gray-8"
          placeholder="HD-ARTICLE-..."
          :value="ticket.doc.rca_kb_article || ''"
          @blur="e => saveField('rca_kb_article', e.target.value)"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs text-ink-gray-5">Problem Ticket</label>
        <input
          class="w-full text-sm px-3 py-2 rounded-lg border border-outline-gray-2 bg-surface-white focus:outline-none focus:border-blue-400 text-ink-gray-8"
          placeholder="HD-TICKET-..."
          :value="ticket.doc.rca_problem_ticket || ''"
          @blur="e => saveField('rca_problem_ticket', e.target.value)"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs text-ink-gray-5">Escalation Reason</label>
        <textarea
          class="w-full text-sm px-3 py-2 rounded-lg border border-outline-gray-2 bg-surface-white focus:outline-none focus:border-blue-400 text-ink-gray-8 resize-none"
          rows="2"
          placeholder="Why was this escalated?"
          :value="ticket.doc.rca_escalation_reason || ''"
          @blur="e => saveField('rca_escalation_reason', e.target.value)"
        />
      </div>
    </div>

    <!-- Mark Complete -->
    <div class="pt-1">
      <button
        v-if="ticket.doc.rca_status !== 'Completed'"
        @click="markComplete"
        class="w-full py-2.5 rounded-xl bg-green-600 hover:bg-green-700 text-white text-sm font-semibold flex items-center justify-center gap-2 transition-colors"
      >
        <FeatherIcon name="check-circle" class="w-4 h-4" />
        Mark RCA Complete
      </button>
      <div v-else class="w-full py-2.5 rounded-xl bg-green-50 border border-green-200 text-green-700 text-sm font-semibold flex items-center justify-center gap-2">
        <FeatherIcon name="check-circle" class="w-4 h-4" />
        RCA Completed{{ ticket.doc.rca_completed_on ? ' · ' + formatDate(ticket.doc.rca_completed_on) : '' }}
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { FeatherIcon } from "frappe-ui";
import { computed, inject } from "vue";
import { TicketSymbol } from "@/types";

const ticket = inject(TicketSymbol);

const bannerClass = computed(() => {
  const s = ticket.value?.doc?.rca_status || "Pending";
  if (s === "Completed") return "bg-green-50 text-green-800 border border-green-200";
  if (s === "In Progress") return "bg-blue-50 text-blue-800 border border-blue-200";
  if (s === "Waived") return "bg-surface-gray-2 text-ink-gray-6 border border-outline-gray-2";
  return "bg-amber-50 text-amber-800 border border-amber-200";
});

const bannerIcon = computed(() => {
  const s = ticket.value?.doc?.rca_status || "Pending";
  if (s === "Completed") return "check-circle";
  if (s === "Waived") return "minus-circle";
  return "alert-triangle";
});

function saveField(fieldname: string, value: string) {
  if (ticket.value.doc[fieldname] === value) return;
  ticket.value.setValue.submit({ [fieldname]: value });
}

function markComplete() {
  ticket.value.setValue.submit({
    rca_status: "Completed",
    rca_completed_on: new Date().toISOString(),
  });
}

function formatDate(val: string) {
  return new Date(val).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}
</script>

<script lang="ts">
import { defineComponent, h, ref } from "vue";
import { FeatherIcon } from "frappe-ui";

/* StatusPill */
const statusColors: Record<string, string> = {
  "Pending":     "bg-amber-100 text-amber-700 border-amber-200",
  "In Progress": "bg-blue-100  text-blue-700  border-blue-200",
  "Completed":   "bg-green-100 text-green-700 border-green-200",
  "Waived":      "bg-surface-gray-2 text-ink-gray-5 border-outline-gray-2",
};
export const StatusPill = defineComponent({
  props: { status: String },
  setup(p) {
    return () => h("span", {
      class: `inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold shrink-0 ${statusColors[p.status || "Pending"] || statusColors["Pending"]}`,
    }, p.status || "Pending");
  },
});

/* RcaSection */
const sectionColors: Record<string, string> = {
  red:   "text-red-500",
  blue:  "text-blue-500",
  green: "text-green-600",
};
export const RcaSection = defineComponent({
  props: { title: String, icon: String, color: String },
  slots: ["default"],
  setup(p, { slots }) {
    return () => h("div", { class: "space-y-2" }, [
      h("p", {
        class: `flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-ink-gray-4`,
      }, [
        h(FeatherIcon, { name: p.icon || "info", class: `w-3.5 h-3.5 ${sectionColors[p.color || "blue"] || ""}` }),
        p.title,
      ]),
      slots.default?.(),
    ]);
  },
});

/* RcaEditor — textarea that saves on blur */
export const RcaEditor = defineComponent({
  props: { fieldname: String, placeholder: String, value: String },
  emits: ["save"],
  setup(p, { emit }) {
    const local = ref(p.value || "");
    return () => h("textarea", {
      class: "w-full text-sm px-3 py-2.5 rounded-xl border border-outline-gray-2 bg-surface-gray-1 focus:outline-none focus:border-blue-400 focus:bg-surface-white text-ink-gray-8 resize-none transition-colors",
      rows: 4,
      placeholder: p.placeholder,
      value: local.value,
      onInput: (e: Event) => { local.value = (e.target as HTMLTextAreaElement).value; },
      onBlur: () => emit("save", p.fieldname, local.value),
    });
  },
});
</script>
