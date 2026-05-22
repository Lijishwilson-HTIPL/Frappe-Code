<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Stats cards -->
    <div class="grid grid-cols-4 gap-3 px-5 pt-4 pb-3 shrink-0">
      <div
        v-for="card in statsCards"
        :key="card.label"
        class="bg-white border border-outline-gray-2 rounded-xl p-4 shadow-sm"
      >
        <div class="text-xs text-ink-gray-5 mb-1">{{ __(card.label) }}</div>
        <div class="text-2xl font-bold text-ink-gray-9">{{ card.value }}</div>
      </div>
    </div>

    <!-- Phase filter bar -->
    <div class="flex items-center gap-2 px-5 pb-3 flex-wrap shrink-0">
      <button
        class="px-3 py-1 rounded-full text-sm font-medium border transition-colors"
        :class="
          selectedStatus === null
            ? 'bg-purple-600 text-white border-purple-600'
            : 'text-ink-gray-6 border-outline-gray-2 hover:bg-surface-gray-2'
        "
        @click="setStatus(null)"
      >
        {{ __('All') }}
      </button>
      <button
        v-for="stage in allStatuses"
        :key="stage.name"
        class="px-3 py-1 rounded-full text-sm font-medium border transition-colors"
        :class="
          selectedStatus === stage.name
            ? 'bg-purple-600 text-white border-purple-600'
            : 'text-ink-gray-6 border-outline-gray-2 hover:bg-surface-gray-2'
        "
        @click="setStatus(stage.name)"
      >
        {{ stage.name }}
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-5 pb-5">
      <div v-if="leadsData.loading" class="flex items-center justify-center h-40">
        <LoadingIndicator class="size-6 text-ink-gray-4" />
      </div>

      <div
        v-else-if="!leads.length"
        class="flex items-center justify-center h-40 text-ink-gray-4 text-base"
      >
        {{ __('No leads found') }}
      </div>

      <div v-else class="flex flex-col gap-3">
        <div
          v-for="lead in leads"
          :key="lead.name"
          class="bg-white border border-outline-gray-2 rounded-xl p-4 hover:shadow-sm transition-shadow"
        >
          <!-- Lead info + pipeline -->
          <div class="flex items-center gap-6">
            <!-- Left: avatar + name + org + status badge -->
            <div class="flex items-start gap-3 w-52 shrink-0">
              <div
                class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold text-sm shrink-0 select-none"
                style="background: #7c3aed"
              >
                {{ initials(lead.lead_name) }}
              </div>
              <div class="min-w-0">
                <div class="text-sm font-semibold text-ink-gray-9 leading-tight truncate">
                  {{ lead.lead_name || lead.name }}
                </div>
                <div class="text-xs text-ink-gray-5 mt-0.5 truncate">
                  {{ lead.organization || '—' }}
                </div>
                <div
                  class="inline-block mt-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
                  :style="statusStyle(lead.status)"
                >
                  {{ lead.status }}
                </div>
              </div>
            </div>

            <!-- Right: pipeline stages -->
            <div class="flex-1">
              <div class="flex items-center">
                <template v-for="(stage, idx) in journeyStages" :key="stage.name">
                  <div class="flex flex-col items-center">
                    <div
                      class="rounded-full border-2 transition-all"
                      :class="stepClass(stage, lead.status, idx)"
                    />
                    <span
                      class="text-[10px] mt-1.5 text-center leading-tight whitespace-nowrap"
                      :class="stepLabelClass(stage, lead.status)"
                    >
                      {{ stage.name }}
                    </span>
                  </div>
                  <div
                    v-if="idx < journeyStages.length - 1"
                    class="h-0.5 flex-1 mb-5 transition-all"
                    :class="connectorClass(idx, lead.status)"
                  />
                </template>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div
            class="flex items-center justify-between mt-3 pt-3 border-t border-outline-gray-1"
          >
            <div class="text-xs text-ink-gray-5 flex items-center gap-1">
              <span>{{ __('Last Activity') }}: {{ timeAgo(lead.modified) }}</span>
              <span class="mx-1 text-ink-gray-3">·</span>
              <span>{{ __('Owner') }}: {{ ownerName(lead.lead_owner) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                :label="__('View')"
                @click="openLead(lead.name)"
              />
              <Button
                size="sm"
                :label="__('Update Status')"
                class="!bg-purple-600 !border-purple-600 hover:!bg-purple-700 !text-white"
                @click="openLead(lead.name)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div
      v-if="totalPages > 1"
      class="flex items-center justify-between px-5 py-3 border-t border-outline-gray-2 bg-white shrink-0"
    >
      <span class="text-sm text-ink-gray-5">
        {{ __('Showing') }} {{ startItem }}–{{ endItem }} {{ __('of') }} {{ total }}
      </span>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon="chevron-left"
          :disabled="currentPage === 1"
          @click="goToPage(currentPage - 1)"
        />
        <button
          v-for="p in visiblePages"
          :key="p"
          class="min-w-[2rem] h-8 px-2 rounded text-sm font-medium transition-colors"
          :class="
            p === currentPage
              ? 'bg-purple-600 text-white'
              : 'text-ink-gray-6 hover:bg-surface-gray-2'
          "
          @click="goToPage(p)"
        >
          {{ p }}
        </button>
        <Button
          variant="ghost"
          icon="chevron-right"
          :disabled="currentPage === totalPages"
          @click="goToPage(currentPage + 1)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource, LoadingIndicator, Button } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { usersStore } from '@/stores/users'

const props = defineProps({
  user: { type: String, default: null },
})

const router = useRouter()
const currentPage = ref(1)
const selectedStatus = ref(null)
const { getUser } = usersStore()

const leadsData = createResource({
  url: 'crm.api.dashboard.get_leads_journey',
  makeParams() {
    return { user: props.user, page: currentPage.value, status: selectedStatus.value }
  },
  auto: true,
})

watch(
  () => props.user,
  () => {
    currentPage.value = 1
    leadsData.reload()
  },
)

const allStatuses = computed(() => leadsData.data?.statuses || [])

const statsCards = computed(() => {
  const s = leadsData.data?.stats || {}
  return [
    { label: 'Total Leads', value: s.total ?? '—' },
    { label: 'Qualified', value: s.qualified ?? '—' },
    { label: 'Converted', value: s.converted ?? '—' },
    { label: 'Conversion Rate', value: s.total ? `${s.conversion_rate}%` : '—' },
  ]
})

function setStatus(status) {
  selectedStatus.value = status
  currentPage.value = 1
  leadsData.reload()
}

const JOURNEY_ORDER = ['New', 'Contacted', 'Nurture', 'Qualified', 'Converted']
const TERMINAL = ['Junk', 'Unqualified']

const journeyStages = computed(() => {
  if (!leadsData.data?.statuses) return JOURNEY_ORDER.map((n) => ({ name: n, color: null }))
  return JOURNEY_ORDER.map(
    (name) => leadsData.data.statuses.find((s) => s.name === name) || { name, color: null },
  )
})

const leads = computed(() => leadsData.data?.leads || [])
const total = computed(() => leadsData.data?.total || 0)
const pageSize = computed(() => leadsData.data?.page_size || 20)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
const startItem = computed(() => (currentPage.value - 1) * pageSize.value + 1)
const endItem = computed(() => Math.min(currentPage.value * pageSize.value, total.value))

const visiblePages = computed(() => {
  const pages = []
  const range = 2
  for (
    let p = Math.max(1, currentPage.value - range);
    p <= Math.min(totalPages.value, currentPage.value + range);
    p++
  ) {
    pages.push(p)
  }
  return pages
})

const statusMap = computed(() => {
  const map = {}
  ;(leadsData.data?.statuses || []).forEach((s) => (map[s.name] = s))
  return map
})

function goToPage(p) {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  leadsData.reload()
}

function currentStepIndex(status) {
  return journeyStages.value.findIndex((s) => s.name === status)
}

function stepClass(stage, currentStatus, idx) {
  const current = currentStepIndex(currentStatus)
  const isTerminal = TERMINAL.includes(currentStatus)
  if (isTerminal) return 'w-3 h-3 border-ink-gray-3 bg-surface-gray-2'
  if (idx < current) return 'w-3 h-3 border-purple-600 bg-purple-600'
  if (idx === current) return 'w-4 h-4 border-purple-600 bg-white'
  return 'w-3 h-3 border-ink-gray-3 bg-white'
}

function stepLabelClass(stage, currentStatus) {
  return stage.name === currentStatus
    ? 'text-purple-600 font-semibold'
    : 'text-ink-gray-4'
}

function connectorClass(idx, currentStatus) {
  const current = currentStepIndex(currentStatus)
  if (TERMINAL.includes(currentStatus)) return 'bg-ink-gray-2'
  return idx < current ? 'bg-purple-600' : 'bg-ink-gray-2'
}

function statusStyle(status) {
  const s = statusMap.value[status]
  if (!s?.color) return { background: '#f3f4f6', color: '#6b7280' }
  const colorMap = {
    blue: { background: '#dbeafe', color: '#1d4ed8' },
    green: { background: '#dcfce7', color: '#15803d' },
    yellow: { background: '#fef9c3', color: '#a16207' },
    orange: { background: '#ffedd5', color: '#c2410c' },
    red: { background: '#fee2e2', color: '#b91c1c' },
    gray: { background: '#f3f4f6', color: '#6b7280' },
    purple: { background: '#f3e8ff', color: '#7e22ce' },
    teal: { background: '#ccfbf1', color: '#0f766e' },
  }
  return colorMap[s.color] || { background: '#f3f4f6', color: '#6b7280' }
}

function initials(name) {
  if (!name) return '?'
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || '')
    .join('')
}

function ownerName(userId) {
  if (!userId) return '—'
  return getUser(userId)?.full_name || userId
}

function timeAgo(dateStr) {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return __('just now')
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return `${Math.floor(days / 30)}mo ago`
}

function openLead(name) {
  router.push({ name: 'Lead', params: { leadId: name } })
}
</script>
