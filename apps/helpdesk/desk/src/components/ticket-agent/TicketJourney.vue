<template>
  <div class="px-5 pt-3 pb-4">
    <div
      class="flex items-center justify-between cursor-pointer select-none"
      @click="isOpen = !isOpen"
    >
      <span class="text-xs font-semibold text-ink-gray-5 uppercase tracking-wide">
        Ticket Journey
      </span>
      <FeatherIcon
        :name="isOpen ? 'chevron-up' : 'chevron-down'"
        class="h-3.5 w-3.5 text-ink-gray-4"
      />
    </div>

    <div v-if="isOpen" class="mt-2">
      <div v-if="journeySteps.length === 0" class="text-xs text-ink-gray-4 py-1">
        No journey recorded yet.
      </div>
      <ol v-else class="relative border-l border-outline-gray-2 ml-1.5">
        <li
          v-for="(step, idx) in journeySteps"
          :key="step.key"
          class="mb-3 ml-3.5 last:mb-0"
        >
          <!-- dot -->
          <span
            class="absolute -left-[5px] flex h-2.5 w-2.5 items-center justify-center rounded-full ring-2 ring-surface-white"
            :class="idx === journeySteps.length - 1 ? 'bg-blue-500' : 'bg-outline-gray-3'"
          />
          <p class="text-xs font-medium text-ink-gray-7 leading-snug">
            {{ step.content }}
          </p>
          <p class="text-[11px] text-ink-gray-4 mt-0.5">
            {{ step.user }}· {{ formatDate(step.creation) }}
          </p>
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ActivitiesSymbol } from "@/types";
import { FeatherIcon } from "frappe-ui";
import { computed, inject, ref } from "vue";

const activities = inject(ActivitiesSymbol);
const isOpen = ref(true);

const journeySteps = computed(() => {
  if (!activities?.value?.data?.history) return [];

  return activities.value.data.history
    .filter((h) => h.action && h.action !== "viewed this")
    .map((h) => ({
      key: h.creation,
      content: h.action,
      creation: h.creation,
      user: (h.user?.name || "") + " ",
    }))
    .sort((a, b) => new Date(a.creation).getTime() - new Date(b.creation).getTime());
});

function formatDate(dateStr: string) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>
