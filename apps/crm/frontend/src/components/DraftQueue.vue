<template>
  <Popover placement="top-start">
    <template #target="{ open, isOpen }">
      <div class="relative">
        <Button
          variant="ghost"
          :label="__('Drafts')"
          :class="[isOpen ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '']"
          :iconLeft="DraftQueueIcon"
          @click="open"
        />
        <span
          v-if="drafts.length"
          class="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-ink-red-2 text-[10px] font-medium text-white"
        >
          {{ drafts.length }}
        </span>
      </div>
    </template>
    <template #body>
      <div class="w-72 rounded-lg border border-outline-gray-2 bg-surface-white shadow-xl">
        <div class="flex items-center justify-between border-b px-3 py-2">
          <span class="text-sm font-medium text-ink-gray-9">{{ __('Draft Queue') }}</span>
          <span class="text-xs text-ink-gray-5">{{ drafts.length }} {{ __('draft(s)') }}</span>
        </div>
        <div v-if="!drafts.length" class="px-4 py-6 text-center text-sm text-ink-gray-5">
          {{ __('No saved drafts') }}
        </div>
        <ul v-else class="max-h-64 divide-y overflow-y-auto">
          <li
            v-for="draft in drafts"
            :key="draft.id"
            class="flex items-start justify-between gap-2 px-3 py-2.5 hover:bg-surface-gray-2 cursor-pointer"
            @click="emit('load', draft)"
          >
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-ink-gray-9">
                {{ draft.subject || __('(No subject)') }}
              </p>
              <p class="truncate text-xs text-ink-gray-5">
                {{ draft.toEmails?.join(', ') || __('No recipients') }}
              </p>
              <p class="mt-0.5 text-xs text-ink-gray-4">
                {{ formatTime(draft.savedAt) }}
              </p>
            </div>
            <button
              class="mt-0.5 shrink-0 text-ink-gray-4 hover:text-ink-red-3"
              @click.stop="deleteDraft(draft.id)"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path
                  d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM5 2.5v-1A1.5 1.5 0 0 1 6.5 0h3A1.5 1.5 0 0 1 11 1.5v1h2.5a.5.5 0 0 1 0 1h-.441l-.605 9.08A2 2 0 0 1 10.459 14H5.54a2 2 0 0 1-1.995-1.92L2.941 3H2.5a.5.5 0 0 1 0-1H5Zm1.5 2a.5.5 0 0 0-.5.5v6a.5.5 0 0 0 1 0V5a.5.5 0 0 0-.5-.5Zm3 0a.5.5 0 0 0-.5.5v6a.5.5 0 0 0 1 0V5a.5.5 0 0 0-.5-.5Z"
                  fill="currentColor"
                />
              </svg>
            </button>
          </li>
        </ul>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import DraftQueueIcon from '@/components/Icons/DraftQueueIcon.vue'
import { Popover } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  drafts: { type: Array, default: () => [] },
})

const emit = defineEmits(['load', 'delete'])

function deleteDraft(id) {
  emit('delete', id)
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>
