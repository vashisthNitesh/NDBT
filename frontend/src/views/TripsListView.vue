<template>
  <div class="space-y-6">
    <!-- Header & Action Row -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">Trip Register (LR Ledger)</h1>
        <p class="text-xs text-slate-500 mt-1">
          Full transactional lorry receipt register, revenue volumes, and settlement audit.
        </p>
      </div>

      <router-link
        to="/trips/new"
        class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-sm shadow-blue-500/20"
      >
        <Plus class="w-4 h-4" />
        <span>Book New Trip (LR)</span>
      </router-link>
    </div>

    <!-- Filter Bar -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-sm flex flex-col md:flex-row items-stretch md:items-center gap-3">
      <!-- Search -->
      <div class="relative flex-1">
        <Search class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          v-model="filters.q"
          @input="debounceSearch"
          placeholder="Filter by LR No, vehicle, consignor, transporter, route..."
          class="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800 transition-colors"
        />
      </div>

      <!-- FY Dropdown -->
      <select
        v-model="filters.fy"
        @change="applyFilters"
        class="px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 text-slate-700"
      >
        <option value="">All Financial Years</option>
        <option value="2026-27">FY 2026-27</option>
        <option value="2025-26">FY 2025-26</option>
        <option value="2024-25">FY 2024-25</option>
        <option value="2023-24">FY 2023-24</option>
        <option value="2022-23">FY 2022-23</option>
        <option value="2021-22">FY 2021-22</option>
      </select>

      <!-- Status Dropdown -->
      <select
        v-model="filters.status"
        @change="applyFilters"
        class="px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 text-slate-700"
      >
        <option value="">All Statuses</option>
        <option value="RECEIVED">Received</option>
        <option value="PENDING">Pending</option>
        <option value="NIL">Nil / Cleared</option>
        <option value="NOT_RECEIVED">Not Received</option>
        <option value="TO_PAY">To Pay</option>
      </select>

      <!-- Memo Filter -->
      <button
        type="button"
        @click="toggleMemoFilter"
        class="px-3 py-2 rounded-xl text-xs font-bold transition-colors border"
        :class="filters.memo_pending === 'true' ? 'bg-amber-500 text-white border-amber-600' : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'"
      >
        Pending Memos
      </button>

      <!-- Reset Filter Button -->
      <button
        v-if="hasActiveFilters"
        type="button"
        @click="resetFilters"
        class="px-3 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 transition-colors"
      >
        Reset
      </button>
    </div>

    <!-- 5-Column Balanced Totals Bar -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-sm">
      <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 flex-wrap gap-2">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="text-xs font-black uppercase tracking-wider text-slate-900">
            Filtered Ledger Summary
          </span>
          <span class="text-xs text-slate-400">
            • {{ pagination.pageSize }} trips / page
          </span>
        </div>
        <span class="text-xs font-bold px-3 py-1 rounded-full bg-slate-100 text-slate-800 border border-slate-200 font-mono-numbers">
          {{ formatNumber(summaryTotals.trip_count) }} Trips Filtered
        </span>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <!-- 1. Freight -->
        <div class="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
            Contracted Freight
          </span>
          <span class="text-base font-black text-slate-900 font-mono-numbers block">
            {{ formatINR(summaryTotals.total_freight) }}
          </span>
        </div>

        <!-- 2. Advance -->
        <div class="p-3 rounded-xl bg-amber-50/70 border border-amber-200">
          <span class="text-[11px] font-bold text-amber-700 uppercase tracking-wider block mb-1">
            Advance Liability
          </span>
          <span class="text-base font-black text-amber-900 font-mono-numbers block">
            {{ formatINR(summaryTotals.total_advance) }}
          </span>
        </div>

        <!-- 3. Adv. Collected -->
        <div class="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200">
          <span class="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block mb-1">
            Adv. Collected
          </span>
          <span class="text-base font-black text-emerald-900 font-mono-numbers block">
            {{ formatINR(summaryTotals.total_adv_recd) }}
          </span>
        </div>

        <!-- 4. Brokerage Commission -->
        <div class="p-3 rounded-xl bg-indigo-50/70 border border-indigo-200">
          <span class="text-[11px] font-bold text-indigo-700 uppercase tracking-wider block mb-1">
            Brokerage Margin
          </span>
          <span class="text-base font-black text-indigo-900 font-mono-numbers block">
            {{ formatINR(summaryTotals.total_commission) }}
          </span>
        </div>

        <!-- 5. Party Balance Due -->
        <div class="p-3 rounded-xl bg-rose-50/70 border border-rose-200">
          <span class="text-[11px] font-bold text-rose-700 uppercase tracking-wider block mb-1">
            Party Balance Due
          </span>
          <span class="text-base font-black text-rose-900 font-mono-numbers block">
            {{ formatINR(summaryTotals.total_balance) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <!-- Mobile Table Swipe Hint -->
      <div class="sm:hidden px-3.5 py-1.5 text-[11px] font-semibold text-slate-500 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
        <span>👉 Swipe horizontally for full trip ledger</span>
        <span class="text-[10px] text-slate-400">Scroll &rarr;</span>
      </div>

      <div class="overflow-x-auto table-containment-region">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50/90 text-[11px] font-black uppercase tracking-wider text-slate-500 border-b border-slate-200">
            <tr>
              <th class="py-3.5 px-4 cursor-pointer hover:text-blue-600" @click="sortBy('lr_no')">
                LR No.
              </th>
              <th class="py-3.5 px-4 cursor-pointer hover:text-blue-600" @click="sortBy('booking_date')">
                Date
              </th>
              <th class="py-3.5 px-4">Vehicle</th>
              <th class="py-3.5 px-4">Customer (Consignor)</th>
              <th class="py-3.5 px-4">Transporter (Owner)</th>
              <th class="py-3.5 px-4">Route</th>
              <th class="py-3.5 px-4 text-right cursor-pointer hover:text-blue-600" @click="sortBy('freight')">
                Freight
              </th>
              <th class="py-3.5 px-4 text-right">Advance</th>
              <th class="py-3.5 px-4 text-right cursor-pointer hover:text-blue-600" @click="sortBy('total_balance')">
                Balance Due
              </th>
              <th class="py-3.5 px-4 text-center">Status</th>
              <th class="py-3.5 px-4 text-center">Memo</th>
              <th class="py-3.5 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="loading">
              <td colspan="12" class="py-12 text-center text-slate-400">
                Loading trip ledger data...
              </td>
            </tr>
            <tr v-else-if="trips.length === 0">
              <td colspan="12" class="py-12 text-center text-slate-400">
                No trips matching your filter criteria.
              </td>
            </tr>
            <tr
              v-else
              v-for="t in trips"
              :key="t.id"
              class="hover:bg-blue-50/40 transition-colors"
            >
              <td class="py-3 px-4 font-black text-blue-600 font-mono-numbers">
                <router-link :to="`/trips/${t.id}`" class="hover:underline">
                  #{{ t.lr_no }}
                </router-link>
              </td>
              <td class="py-3 px-4 text-slate-600 font-mono-numbers">
                {{ formatDate(t.booking_date) }}
              </td>
              <td class="py-3 px-4">
                <span class="px-2 py-0.5 rounded-md font-mono text-[11px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                  {{ t.vehicle }}
                </span>
              </td>
              <td class="py-3 px-4 font-bold text-slate-800 max-w-[160px] truncate" :title="t.consignor">
                {{ t.consignor }}
              </td>
              <td class="py-3 px-4 text-slate-600 max-w-[150px] truncate" :title="t.transporter">
                {{ t.transporter }}
              </td>
              <td class="py-3 px-4 text-slate-600">
                {{ t.origin }} &rarr; {{ t.destination }}
              </td>
              <td class="py-3 px-4 text-right font-black text-slate-900 font-mono-numbers">
                {{ formatINR(t.freight) }}
              </td>
              <td class="py-3 px-4 text-right text-slate-700 font-mono-numbers">
                {{ formatINR(t.advance) }}
              </td>
              <td class="py-3 px-4 text-right font-black text-slate-900 font-mono-numbers">
                {{ formatINR(t.total_balance) }}
              </td>
              <td class="py-3 px-4 text-center">
                <StatusPill :status="t.balance_status" />
              </td>
              <td class="py-3 px-4 text-center">
                <span
                  v-if="t.memo_pending"
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800"
                >
                  Pending
                </span>
                <span v-else class="font-mono-numbers text-slate-600 text-xs">
                  #{{ t.memo_no }}
                </span>
              </td>
              <td class="py-3 px-4 text-center">
                <div class="flex items-center justify-center gap-1.5">
                  <router-link
                    :to="`/trips/${t.id}`"
                    class="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-blue-600 hover:text-white text-slate-700 text-xs font-bold transition-colors"
                  >
                    View / Edit
                  </router-link>
                  <button
                    type="button"
                    @click="openSlipModal(t)"
                    class="p-1 rounded-lg bg-indigo-50 hover:bg-indigo-600 hover:text-white text-indigo-700 text-xs font-bold transition-colors border border-indigo-200"
                    title="Print / Generate Lorry Slip (PDF)"
                  >
                    <Printer class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div class="p-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div class="text-slate-500 font-medium">
          Showing page <span class="font-black text-slate-900">{{ pagination.currentPage }}</span> of
          <span class="font-black text-slate-900">{{ pagination.totalPages }}</span>
          (<span class="font-mono-numbers font-bold">{{ formatNumber(pagination.count) }}</span> total trips)
        </div>

        <div class="flex items-center gap-2">
          <button
            type="button"
            :disabled="pagination.currentPage <= 1"
            @click="changePage(pagination.currentPage - 1)"
            class="px-3 py-1.5 rounded-xl border border-slate-200 bg-white font-bold text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 transition-colors"
          >
            Previous
          </button>
          <button
            type="button"
            :disabled="pagination.currentPage >= pagination.totalPages"
            @click="changePage(pagination.currentPage + 1)"
            class="px-3 py-1.5 rounded-xl border border-slate-200 bg-white font-bold text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Lorry Slip Modal Preview -->
    <div
      v-if="activeSlipTrip"
      class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/60 backdrop-blur-xs overflow-y-auto"
    >
      <div class="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-3xl my-auto overflow-hidden flex flex-col max-h-[92vh]">
        <!-- Modal Top Bar -->
        <div class="p-4 sm:px-6 bg-slate-900 text-white flex items-center justify-between shrink-0">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-blue-400 animate-pulse"></span>
            <h3 class="text-xs sm:text-sm font-black uppercase tracking-wider text-white">
              Lorry Loading Slip — LR #{{ activeSlipTrip.lr_no }}
            </h3>
          </div>

          <div class="flex items-center gap-2">
            <router-link
              :to="`/lorry-slip?trip=${activeSlipTrip.id}`"
              class="hidden sm:inline-flex px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700"
            >
              Open in Editor
            </router-link>

            <div class="hidden xs:flex items-center gap-1.5 text-xs">
              <span class="text-[10px] text-slate-400 font-bold uppercase">Sign:</span>
              <select
                v-model="modalSignatory"
                class="bg-slate-800 text-white text-xs font-bold border border-slate-700 rounded-xl px-2 py-1 outline-hidden cursor-pointer"
              >
                <option value="Dharambir Vashisth">Dharambir Vashisth</option>
                <option value="Satbir Vashisth">Satbir Vashisth</option>
              </select>
            </div>

            <button
              type="button"
              @click="printModalSlip"
              class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold border border-slate-700 flex items-center gap-1.5"
            >
              <Printer class="w-3.5 h-3.5" />
              <span>Print</span>
            </button>

            <button
              type="button"
              @click="downloadModalSlip"
              :disabled="modalGeneratingPdf"
              class="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-blue-500/20 disabled:opacity-50"
            >
              <Download class="w-3.5 h-3.5" />
              <span>{{ modalGeneratingPdf ? 'Generating...' : 'PDF' }}</span>
            </button>

            <button
              type="button"
              @click="closeSlipModal"
              class="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 ml-1"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Modal Slip Body (Scrollable) -->
        <div class="p-2 sm:p-6 overflow-y-auto flex-1 bg-slate-100/60 flex justify-center">
          <LorrySlipDocument :slip-data="modalSlipData" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, Search, Printer, Download, X } from '@lucide/vue'
import html2pdf from 'html2pdf.js'
import api from '../services/api'
import { formatINR, formatNumber, formatDate } from '../utils/formatters'
import StatusPill from '../components/common/StatusPill.vue'
import LorrySlipDocument from '../components/common/LorrySlipDocument.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const trips = ref([])
const summaryTotals = ref({})
const pagination = ref({
  count: 0,
  totalPages: 1,
  currentPage: 1,
  pageSize: 50,
})

const filters = ref({
  q: route.query.q || '',
  fy: route.query.fy || '',
  status: route.query.status || '',
  memo_pending: route.query.memo_pending || '',
  sort: '-lr_no',
})

const hasActiveFilters = computed(() => {
  return Boolean(filters.value.q || filters.value.fy || filters.value.status || filters.value.memo_pending)
})

let searchTimeout = null
function debounceSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pagination.value.currentPage = 1
    fetchTrips()
  }, 300)
}

function applyFilters() {
  pagination.value.currentPage = 1
  fetchTrips()
}

function toggleMemoFilter() {
  filters.value.memo_pending = filters.value.memo_pending === 'true' ? '' : 'true'
  applyFilters()
}

function resetFilters() {
  filters.value.q = ''
  filters.value.fy = ''
  filters.value.status = ''
  filters.value.memo_pending = ''
  pagination.value.currentPage = 1
  fetchTrips()
}

function sortBy(field) {
  if (filters.value.sort === field) {
    filters.value.sort = `-${field}`
  } else {
    filters.value.sort = field
  }
  fetchTrips()
}

function changePage(newPage) {
  if (newPage >= 1 && newPage <= pagination.value.totalPages) {
    pagination.value.currentPage = newPage
    fetchTrips()
  }
}

async function fetchTrips() {
  try {
    loading.value = true
    const params = {
      q: filters.value.q,
      fy: filters.value.fy,
      status: filters.value.status,
      memo_pending: filters.value.memo_pending,
      sort: filters.value.sort,
      page: pagination.value.currentPage,
      page_size: pagination.value.pageSize,
    }
    const res = await api.getTrips(params)
    trips.value = res.data.results || []
    summaryTotals.value = res.data.summary_totals || {}
    pagination.value.count = res.data.count || 0
    pagination.value.totalPages = res.data.total_pages || 1
    pagination.value.currentPage = res.data.current_page || 1
  } catch (err) {
    console.error('Failed to load trips:', err)
  } finally {
    loading.value = false
  }
}

watch(() => route.query, (newQuery) => {
  if (newQuery.status !== undefined) filters.value.status = newQuery.status
  if (newQuery.q !== undefined) filters.value.q = newQuery.q
  if (newQuery.fy !== undefined) filters.value.fy = newQuery.fy
  fetchTrips()
})

// Quick Slip Modal state & handlers
const activeSlipTrip = ref(null)
const modalGeneratingPdf = ref(false)
const modalSignatory = ref('Dharambir Vashisth')

const modalSlipData = computed(() => {
  if (!activeSlipTrip.value) return {}
  const t = activeSlipTrip.value
  return {
    slip_no: t.lr_no,
    date: t.booking_date,
    customer_name: t.consignor,
    customer_city: '',
    truck_no: t.vehicle,
    owner_name: t.transporter,
    address: '',
    driver_name: '',
    lic_no: '',
    goods_particulars: 'P. Goods',
    weight: '7 mt.',
    destination: t.destination,
    origin: t.origin,
    to_place: t.destination,
    rate: t.freight,
    advance: t.advance,
    balance: t.balance || (Number(t.freight || 0) - Number(t.advance || 0)),
    signatory: modalSignatory.value,
  }
})

function openSlipModal(trip) {
  activeSlipTrip.value = trip
}

function closeSlipModal() {
  activeSlipTrip.value = null
}

function printModalSlip() {
  window.print()
}

async function downloadModalSlip() {
  const element = document.getElementById('lorry-slip-print-area')
  if (!element) return

  modalGeneratingPdf.value = true
  const lr = activeSlipTrip.value?.lr_no || 'Trip'
  const opt = {
    margin: [10, 10, 10, 10],
    filename: `NDBT_Slip_${lr}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2.5, useCORS: true, logging: false },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }

  try {
    await html2pdf().set(opt).from(element).save()
  } catch (err) {
    console.error('PDF generation error:', err)
    if (activeSlipTrip.value?.id) {
      window.open(api.getTripSlipPdfUrl(activeSlipTrip.value.id, { download: '1' }), '_blank')
    }
  } finally {
    modalGeneratingPdf.value = false
  }
}

onMounted(() => {
  fetchTrips()
})
</script>
