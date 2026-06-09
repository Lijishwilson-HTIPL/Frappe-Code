const DashboardView = {
  name: 'DashboardView',

  props: {
    email: { type: String, required: true },
    token: { type: String, required: true },
  },

  emits: ['open-ticket', 'raise-ticket', 'logout'],

  data() {
    return {
      API_BASE: '/api/method/helpdesk.helpdesk.portal_api.',
      loading: true,
      error: '',
      tickets: [],
      stats: {
        total: 0,
        awaiting_reply: 0,
        in_progress: 0,
        resolved: 0,
      },
      searchQuery: '',
      statusFilter: 'all',
      activeCard: 'all',
      currentPage: 1,
      pageSize: 10,
    };
  },

  computed: {
    statusOptions() {
      return [
        { value: 'all', label: 'All Statuses' },
        { value: 'awaiting_reply', label: 'Awaiting Reply' },
        { value: 'in_progress', label: 'In Progress' },
        { value: 'resolved', label: 'Resolved' },
      ];
    },

    filteredTickets() {
      let rows = this.tickets.slice();

      // Card / dropdown status filter
      if (this.statusFilter && this.statusFilter !== 'all') {
        rows = rows.filter((t) => this.normalizeStatus(t.status) === this.statusFilter);
      }

      // Search filter (ID or subject)
      const q = this.searchQuery.trim().toLowerCase();
      if (q) {
        rows = rows.filter((t) => {
          const id = (t.name || '').toLowerCase();
          const subject = (t.subject || '').toLowerCase();
          return id.indexOf(q) !== -1 || subject.indexOf(q) !== -1;
        });
      }

      return rows;
    },

    totalPages() {
      return Math.max(1, Math.ceil(this.filteredTickets.length / this.pageSize));
    },

    pagedTickets() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.filteredTickets.slice(start, start + this.pageSize);
    },

    pageStartIndex() {
      if (this.filteredTickets.length === 0) return 0;
      return (this.currentPage - 1) * this.pageSize + 1;
    },

    pageEndIndex() {
      return Math.min(this.currentPage * this.pageSize, this.filteredTickets.length);
    },

    skeletonRows() {
      return [1, 2, 3, 4, 5];
    },
  },

  watch: {
    searchQuery() {
      this.currentPage = 1;
    },
    statusFilter() {
      this.currentPage = 1;
    },
  },

  created() {
    this.fetchTickets();
  },

  methods: {
    async fetchTickets() {
      this.loading = true;
      this.error = '';
      try {
        const res = await fetch(this.API_BASE + 'get_my_tickets', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Frappe-CSRF-Token': window.CSRF_TOKEN || '',
          },
          body: JSON.stringify({
            email: this.email,
            token: this.token,
          }),
        });

        if (!res.ok) {
          throw new Error('Request failed with status ' + res.status);
        }

        const payload = await res.json();
        const data = payload && payload.message ? payload.message : payload;

        this.tickets = (data && data.tickets) ? data.tickets : [];
        const s = (data && data.stats) ? data.stats : {};
        this.stats = {
          total: s.total || 0,
          awaiting_reply: s.awaiting_reply || 0,
          in_progress: s.in_progress || 0,
          resolved: s.resolved || 0,
        };
      } catch (e) {
        this.error = (e && e.message) ? e.message : 'Unable to load tickets.';
        this.tickets = [];
      } finally {
        this.loading = false;
      }
    },

    normalizeStatus(status) {
      const s = (status || '').toString().toLowerCase().replace(/\s+/g, '_');
      if (s.indexOf('await') !== -1 || s.indexOf('open') !== -1 || s.indexOf('reply') !== -1) {
        return 'awaiting_reply';
      }
      if (s.indexOf('progress') !== -1 || s.indexOf('replied') !== -1) {
        return 'in_progress';
      }
      if (s.indexOf('resolved') !== -1 || s.indexOf('closed') !== -1) {
        return 'resolved';
      }
      return s;
    },

    selectCard(key) {
      this.activeCard = key;
      this.statusFilter = key;
    },

    cardClasses(key) {
      const base =
        'cursor-pointer bg-white border rounded-xl p-5 transition-all duration-150 hover:shadow-md focus:outline-none';
      if (this.activeCard === key) {
        return base + ' border-[#1B3A6B] ring-1 ring-[#1B3A6B]';
      }
      return base + ' border-gray-200';
    },

    statusBadge(ticket) {
      const key = this.normalizeStatus(ticket.status);
      const label = ticket.status_label || ticket.status || 'Unknown';
      const map = {
        awaiting_reply: { dot: 'bg-orange-500', text: 'text-orange-700', bg: 'bg-orange-50' },
        in_progress: { dot: 'bg-teal-500', text: 'text-teal-700', bg: 'bg-teal-50' },
        resolved: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
      };
      const style = map[key] || { dot: 'bg-gray-400', text: 'text-gray-700', bg: 'bg-gray-100' };
      return { label: label, dot: style.dot, text: style.text, bg: style.bg };
    },

    priorityBadge(priority) {
      const p = (priority || '').toString().toLowerCase();
      const label = priority || 'Medium';
      if (p === 'urgent') return { label: label, cls: 'bg-red-100 text-red-700' };
      if (p === 'high') return { label: label, cls: 'bg-orange-100 text-orange-700' };
      if (p === 'low') return { label: label, cls: 'bg-gray-100 text-gray-600' };
      return { label: label, cls: 'bg-blue-100 text-blue-700' };
    },

    formatDate(value) {
      if (!value) return '—';
      const d = new Date(value.toString().replace(' ', 'T'));
      if (isNaN(d.getTime())) return value;
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return months[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
    },

    relativeUpdated(value) {
      if (!value) return '—';
      const d = new Date(value.toString().replace(' ', 'T'));
      if (isNaN(d.getTime())) return value;
      const diffMs = Date.now() - d.getTime();
      const mins = Math.floor(diffMs / 60000);
      if (mins < 1) return 'just now';
      if (mins < 60) return mins + 'm ago';
      const hrs = Math.floor(mins / 60);
      if (hrs < 24) return hrs + 'h ago';
      const days = Math.floor(hrs / 24);
      if (days < 30) return days + 'd ago';
      return this.formatDate(value);
    },

    goToPage(page) {
      if (page < 1 || page > this.totalPages) return;
      this.currentPage = page;
    },

    prevPage() {
      this.goToPage(this.currentPage - 1);
    },

    nextPage() {
      this.goToPage(this.currentPage + 1);
    },
  },

  template: `
    <div class="min-h-screen bg-[#F9FAFB]">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <!-- Page header -->
        <div class="flex items-start justify-between gap-4 mb-8">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 tracking-tight">
              Welcome back, Hephzibah QC!
            </h1>
            <p class="mt-1 text-sm text-gray-500">Here's an overview of your support tickets.</p>
          </div>
          <button
            @click="$emit('raise-ticket')"
            class="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white font-semibold px-4 py-2.5 rounded-lg shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-offset-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Raise New Ticket
          </button>
        </div>

        <!-- KPI cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">

          <!-- Total -->
          <div :class="cardClasses('all')" @click="selectCard('all')" role="button" tabindex="0">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Total</p>
                <p class="mt-2 text-3xl font-bold text-gray-900">{{ stats.total }}</p>
              </div>
              <div class="p-2 rounded-lg bg-gray-100">
                <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Awaiting Reply -->
          <div :class="cardClasses('awaiting_reply')" @click="selectCard('awaiting_reply')" role="button" tabindex="0">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Awaiting Reply</p>
            <div class="mt-2 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
              <span class="text-3xl font-bold text-orange-500">{{ stats.awaiting_reply }}</span>
            </div>
          </div>

          <!-- In Progress -->
          <div :class="cardClasses('in_progress')" @click="selectCard('in_progress')" role="button" tabindex="0">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">In Progress</p>
            <div class="mt-2 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
              <span class="text-3xl font-bold text-teal-500">{{ stats.in_progress }}</span>
            </div>
          </div>

          <!-- Resolved -->
          <div :class="cardClasses('resolved')" @click="selectCard('resolved')" role="button" tabindex="0">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Resolved</p>
            <div class="mt-2 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-green-500"></span>
              <span class="text-3xl font-bold text-green-600">{{ stats.resolved }}</span>
            </div>
          </div>
        </div>

        <!-- Ticket table card -->
        <div class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">

          <!-- Toolbar -->
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border-b border-gray-100">
            <div class="relative w-full sm:max-w-xs">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11a6 6 0 11-12 0 6 6 0 0112 0z" />
                </svg>
              </span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search by ID or subject..."
                class="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1B3A6B] focus:border-transparent"
              />
            </div>

            <div class="relative">
              <select
                v-model="statusFilter"
                class="appearance-none w-full sm:w-48 pl-3 pr-9 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#1B3A6B] focus:border-transparent"
              >
                <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
              <span class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </span>
            </div>
          </div>

          <!-- Error -->
          <div v-if="error" class="p-4">
            <div class="flex items-center justify-between gap-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
              <span>{{ error }}</span>
              <button @click="fetchTickets" class="font-semibold underline hover:no-underline">Retry</button>
            </div>
          </div>

          <!-- Table -->
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-100">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Ticket ID</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Subject</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Priority</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Submitted</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Updated</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Action</th>
                </tr>
              </thead>

              <!-- Loading skeleton -->
              <tbody v-if="loading" class="divide-y divide-gray-100">
                <tr v-for="n in skeletonRows" :key="'sk-' + n">
                  <td class="px-4 py-4"><div class="h-3 w-16 bg-gray-200 rounded animate-pulse"></div></td>
                  <td class="px-4 py-4"><div class="h-3 w-48 bg-gray-200 rounded animate-pulse"></div></td>
                  <td class="px-4 py-4"><div class="h-5 w-24 bg-gray-200 rounded-full animate-pulse"></div></td>
                  <td class="px-4 py-4"><div class="h-5 w-16 bg-gray-200 rounded-full animate-pulse"></div></td>
                  <td class="px-4 py-4"><div class="h-3 w-20 bg-gray-200 rounded animate-pulse"></div></td>
                  <td class="px-4 py-4"><div class="h-3 w-20 bg-gray-200 rounded animate-pulse"></div></td>
                  <td class="px-4 py-4"><div class="h-8 w-32 bg-gray-200 rounded-lg animate-pulse ml-auto"></div></td>
                </tr>
              </tbody>

              <!-- Data rows -->
              <tbody v-else-if="pagedTickets.length" class="divide-y divide-gray-100">
                <tr v-for="ticket in pagedTickets" :key="ticket.name" class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-4 whitespace-nowrap text-sm font-mono font-medium text-[#1B3A6B]">{{ ticket.name }}</td>
                  <td class="px-4 py-4 text-sm text-gray-900 max-w-xs">
                    <div class="truncate font-medium">{{ ticket.subject }}</div>
                    <div v-if="ticket.agent" class="text-xs text-gray-400 truncate">Assigned: {{ ticket.agent }}</div>
                  </td>
                  <td class="px-4 py-4 whitespace-nowrap">
                    <span :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', statusBadge(ticket).bg, statusBadge(ticket).text]">
                      <span :class="['w-1.5 h-1.5 rounded-full', statusBadge(ticket).dot]"></span>
                      {{ statusBadge(ticket).label }}
                    </span>
                  </td>
                  <td class="px-4 py-4 whitespace-nowrap">
                    <span :class="['inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium', priorityBadge(ticket.priority).cls]">
                      {{ priorityBadge(ticket.priority).label }}
                    </span>
                  </td>
                  <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{{ formatDate(ticket.creation) }}</td>
                  <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{{ relativeUpdated(ticket.modified) }}</td>
                  <td class="px-4 py-4 whitespace-nowrap text-right">
                    <button
                      @click="$emit('open-ticket', ticket.name)"
                      class="inline-flex items-center gap-1.5 bg-[#1B3A6B] hover:bg-[#15305a] text-white text-xs font-semibold px-3 py-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-[#1B3A6B] focus:ring-offset-1"
                    >
                      View Discussion
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </button>
                  </td>
                </tr>
              </tbody>

              <!-- Empty state -->
              <tbody v-else>
                <tr>
                  <td colspan="7" class="px-4 py-16">
                    <div class="flex flex-col items-center justify-center text-center">
                      <svg class="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p class="text-base font-semibold text-gray-700">No tickets yet</p>
                      <p class="mt-1 text-sm text-gray-400">
                        {{ searchQuery || statusFilter !== 'all' ? 'No tickets match your filters.' : 'Raise a new ticket to get started.' }}
                      </p>
                      <button
                        v-if="!searchQuery && statusFilter === 'all'"
                        @click="$emit('raise-ticket')"
                        class="mt-4 inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
                      >
                        Raise New Ticket
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="!loading && filteredTickets.length" class="flex items-center justify-between gap-3 px-4 py-3 border-t border-gray-100">
            <p class="text-xs text-gray-500">
              Showing <span class="font-medium text-gray-700">{{ pageStartIndex }}</span>
              to <span class="font-medium text-gray-700">{{ pageEndIndex }}</span>
              of <span class="font-medium text-gray-700">{{ filteredTickets.length }}</span> tickets
            </p>
            <div class="flex items-center gap-1">
              <button
                @click="prevPage"
                :disabled="currentPage === 1"
                class="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                v-for="page in totalPages"
                :key="'pg-' + page"
                @click="goToPage(page)"
                :class="[
                  'px-3 py-1.5 text-xs font-medium rounded-lg border',
                  page === currentPage
                    ? 'bg-[#1B3A6B] border-[#1B3A6B] text-white'
                    : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                ]"
              >
                {{ page }}
              </button>
              <button
                @click="nextPage"
                :disabled="currentPage === totalPages"
                class="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        <!-- Footer / logout -->
        <div class="flex items-center justify-between mt-6">
          <p class="text-xs text-gray-400">Signed in as {{ email }}</p>
          <button
            @click="$emit('logout')"
            class="text-xs font-medium text-gray-500 hover:text-[#1B3A6B] transition-colors"
          >
            Log out
          </button>
        </div>

      </div>
    </div>
  `,
};
