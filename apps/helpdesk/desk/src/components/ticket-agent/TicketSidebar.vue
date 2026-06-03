<template>
  <Resizer class="flex flex-col justify-between border-l" side="right">
    <TabButtons
      :buttons="tabs"
      v-model="currentTab"
      class="tab-buttons mb-1 px-5 mt-3.5"
    />
    <div class="flex-1 max-h-full">
      <TicketDetailsTab v-if="currentTab === 'details'" />
      <TicketContactTab v-else-if="currentTab === 'contact'" />
      <TicketDataTab v-else-if="currentTab === 'data'" />
      <TicketRCATab v-else-if="currentTab === 'rca'" />
    </div>
  </Resizer>
</template>

<script setup lang="ts">
import { TabButtons } from "frappe-ui";
import { ref } from "vue";
import Resizer from "../Resizer.vue";
import TicketContactTab from "./TicketContactTab.vue";
import TicketDataTab from "./TicketDataTab.vue";
import TicketDetailsTab from "./TicketDetailsTab.vue";
import TicketRCATab from "./TicketRCATab.vue";

const currentTab = ref("details");
const tabs = [
  {
    label: "Details",
    value: "details",
  },
  {
    label: "Contact",
    value: "contact",
  },
  {
    label: "Data",
    value: "data",
  },
  {
    label: "RCA",
    value: "rca",
  },
];
</script>

<style>
.tab-buttons div,
.tab-buttons button {
  width: 100%;
  flex: 1;
}
</style>
