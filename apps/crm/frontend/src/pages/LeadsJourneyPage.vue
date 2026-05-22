<template>
  <div class="flex h-full flex-col overflow-hidden">
    <div class="flex items-center justify-between border-b px-5 py-3">
      <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Leads Journey') }}</h1>
    </div>
    <div class="flex-1 overflow-auto p-5">
      <LeadsJourney />
    </div>
  </div>
</template>

<script setup>
import LeadsJourney from '@/components/Dashboard/LeadsJourney.vue'
</script>
