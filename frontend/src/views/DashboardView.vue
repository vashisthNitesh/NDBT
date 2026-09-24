<template>
  <div class="space-y-6">
    <!-- Header Banner with Financial Year Selector -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
            Live Cloud TMS
          </span>
          <span class="text-xs font-bold text-slate-400">Current FY: {{ dashboardData.current_fy || '2026-27' }}</span>
        </div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">Transport Command Center</h1>
        <p class="text-xs text-slate-500 mt-1">
          Executive analytics, freight volumes, settlement health, and transit corridors.
        </p>
      </div>

      <!-- Financial Year Switcher Pills -->
      <div class="flex items-center gap-1.5 flex-wrap">
        <button
          v-for="fy in dashboardData.available_fys || ['ALL', '2026-27', '2025-26', '2024-25']"
          :key="fy"
          type="button"
          @click="selectFy(fy)"
          class="px-3 py-1.5 rounded-full text-xs font-bold transition-all"
          :class="selectedFy === fy ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'"
        >
          {{ fy === 'ALL' ? 'All Time' : fy }}
        </button>
      </div>
    </div>

    <!-- 8 High-Level KPI Metric Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 1. Total Trips -->
      <MetricCard
        title="Total Trips"
        :value="formatNumber(kpis.total_trips)"
        :subtitle="`${formatNumber(kpis.active_vehicles)} Active Vehicles • ${formatNumber(kpis.active_customers)} Customers`"
        :icon="Truck"
      />

      <!-- 2. Contracted Freight -->
      <MetricCard
        title="Contracted Freight"
        :value="formatINR(kpis.total_freight)"
        subtitle="Gross transport revenue"
        :icon="IndianRupee"
      />

      <!-- 3. Party Receivables -->
      <MetricCard
        title="Party Receivables"
        :value="formatINR(kpis.party_balance)"
        subtitle="Total party balance due"
        :icon="Receipt"
      >
        <template #footer>
          <router-link
            to="/reports/party-outstanding"
            class="text-[11px] font-bold text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1 mt-2"
          >
            <span>View party outstanding</span>
            <ArrowRight class="w-3 h-3" />
          </router-link>
        </template>
      </MetricCard>

      <!-- 4. Transporter Advance -->
      <MetricCard
        title="Transporter Advances"
        :value="formatINR(kpis.total_advance)"
        subtitle="Party advance liability"
        :icon="Wallet"
      />

      <!-- 5. Commission Margin -->
      <MetricCard
        title="Brokerage Margin"
        :value="formatINR(kpis.total_commission)"
        subtitle="Net brokerage earned"
        :icon="Percent"
      />

      <!-- 6. TDS Section 194C -->
      <MetricCard
        title="TDS (Sec 194C)"
        :value="formatINR(kpis.total_tds)"
        subtitle="Audit-ready tax ledger"
        :icon="FileText"
      >
        <template #footer>
          <router-link
            to="/reports/tds-register"
            class="text-[11px] font-bold text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1 mt-2"
          >
            <span>Audit-ready TDS ledger</span>
            <ArrowRight class="w-3 h-3" />
          </router-link>
        </template>
      </MetricCard>

      <!-- 7. Detention & Extra -->
      <MetricCard
        title="Detention & Labour"
        :value="formatINR(kpis.total_extra_charges)"
        subtitle="Holding & hamali charges"
        :icon="Clock"
      />

      <!-- 8. Average Ticket Size -->
      <MetricCard
        title="Avg Freight / Trip"
        :value="formatINR(kpis.avg_freight)"
        subtitle="Average contracted freight per LR"
        :icon="TrendingUp"
      />
    </div>

    <!-- Settlement Health & Operational Attention Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Settlement Health Progress Bar (2 Columns) -->
      <div class="lg:col-span-2">
        <SettlementBar :settlement="dashboardData.settlement || {}" />
      </div>

      <!-- Operational Attention (1 Column) -->
      <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col justify-between">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <AlertTriangle class="w-4 h-4 text-amber-500" />
            <h3 class="text-sm font-black uppercase tracking-wider text-slate-900">
              Operational Attention
            </h3>
          </div>
          <p class="text-xs text-slate-500 mb-4">
            Items requiring immediate operational review
          </p>

          <div class="space-y-3">
            <router-link
              to="/reports/pending-operations"
              class="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 transition-all group"
            >
              <div class="flex items-center gap-2.5">
                <FileQuestion class="w-4 h-4 text-amber-600" />
                <span class="text-xs font-bold text-slate-700 group-hover:text-blue-700">Pending Memos</span>
              </div>
              <span class="px-2 py-0.5 rounded-full text-xs font-black bg-amber-100 text-amber-800 font-mono-numbers">
                {{ formatNumber(attention.pending_memos) }}
              </span>
            </router-link>

            <router-link
              to="/reports/pending-operations"
              class="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 transition-all group"
            >
              <div class="flex items-center gap-2.5">
                <FileX class="w-4 h-4 text-rose-500" />
                <span class="text-xs font-bold text-slate-700 group-hover:text-blue-700">Missing Physical PODs</span>
              </div>
              <span class="px-2 py-0.5 rounded-full text-xs font-black bg-rose-100 text-rose-800 font-mono-numbers">
                {{ formatNumber(attention.missing_pods) }}
              </span>
            </router-link>

            <router-link
              to="/reports/pending-operations"
              class="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 transition-all group"
            >
              <div class="flex items-center gap-2.5">
                <AlertCircle class="w-4 h-4 text-rose-600" />
                <span class="text-xs font-bold text-slate-700 group-hover:text-blue-700">Overdue Uncollected</span>
              </div>
              <span class="px-2 py-0.5 rounded-full text-xs font-black bg-rose-100 text-rose-800 font-mono-numbers">
                {{ formatNumber(attention.overdue_balances) }}
              </span>
            </router-link>
          </div>
        </div>

        <router-link
          to="/reports/pending-operations"
          class="text-xs font-bold text-blue-600 hover:text-blue-700 hover:underline flex items-center justify-center gap-1.5 mt-4 pt-3 border-t border-slate-100"
        >
          <span>Open Complete Operations Backlog</span>
          <ArrowRight class="w-3.5 h-3.5" />
        </router-link>
      </div>
    </div>

    <!-- Top Transit Corridors -->
    <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <div>
          <div class="flex items-center gap-2">
            <MapPin class="w-4 h-4 text-blue-600" />
            <h3 class="text-sm font-black uppercase tracking-wider text-slate-900">
              Top High-Volume Transit Corridors
            </h3>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">
            Highest density freight lanes ranked by completed trips
          </p>
        </div>

        <router-link to="/trips" class="text-xs font-bold text-blue-600 hover:underline flex items-center gap-1">
          <span>View all trips</span>
          <ArrowRight class="w-3 h-3" />
        </router-link>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <div
          v-for="(lane, idx) in dashboardData.top_lanes || []"
          :key="idx"
          class="p-4 rounded-xl bg-slate-50 border border-slate-200/80 hover:border-blue-300 hover:shadow-xs transition-all"
        >
          <div class="flex items-center justify-between mb-1.5">
            <span class="px-2 py-0.5 rounded-md text-[10px] font-black bg-blue-100 text-blue-800">
              #{{ idx + 1 }}
            </span>
            <span class="text-xs font-black text-slate-800 font-mono-numbers">
              {{ formatNumber(lane.trips) }} Trips
            </span>
          </div>
          <div class="text-xs font-bold text-slate-900 truncate" :title="lane.name">
            {{ lane.name }}
          </div>
          <div class="text-xs text-slate-500 font-medium font-mono-numbers mt-1">
            {{ formatINR(lane.freight) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Trips Ledger Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <div class="p-6 border-b border-slate-100 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2">
            <Clock class="w-4 h-4 text-blue-600" />
            <h3 class="text-sm font-black uppercase tracking-wider text-slate-900">
              Recent Trips Ledger
            </h3>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">Latest trip entries and freight settlements</p>
        </div>

        <router-link
          to="/trips"
          class="px-3.5 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold flex items-center gap-1.5 transition-colors"
        >
          <span>Open Full Register</span>
          <ArrowRight class="w-3.5 h-3.5" />
        </router-link>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto table-containment-region">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50/80 text-[11px] font-black uppercase tracking-wider text-slate-500 border-b border-slate-200">
            <tr>
              <th class="py-3 px-4">LR No.</th>
              <th class="py-3 px-4">Date</th>
              <th class="py-3 px-4">Vehicle</th>
              <th class="py-3 px-4">Customer (Consignor)</th>
              <th class="py-3 px-4">Route</th>
              <th class="py-3 px-4 text-right">Freight</th>
              <th class="py-3 px-4 text-right">Balance Due</th>
              <th class="py-3 px-4 text-center">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="trip in dashboardData.recent_trips || []"
              :key="trip.id"
              @click="$router.push(`/trips/${trip.id}`)"
              class="hover:bg-blue-50/40 cursor-pointer transition-colors"
            >
              <td class="py-3 px-4 font-black text-blue-600 font-mono-numbers">
                #{{ trip.lr_no }}
              </td>
              <td class="py-3 px-4 text-slate-600 font-mono-numbers">
                {{ formatDate(trip.booking_date) }}
              </td>
              <td class="py-3 px-4">
                <span class="px-2 py-0.5 rounded-md font-mono text-[11px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                  {{ trip.vehicle }}
                </span>
              </td>
              <td class="py-3 px-4 font-bold text-slate-800 max-w-[180px] truncate" :title="trip.consignor">
                {{ trip.consignor }}
              </td>
              <td class="py-3 px-4 text-slate-600">
                {{ trip.origin }} &rarr; {{ trip.destination }}
              </td>
              <td class="py-3 px-4 text-right font-black text-slate-900 font-mono-numbers">
                {{ formatINR(trip.freight) }}
              </td>
              <td class="py-3 px-4 text-right font-black text-slate-700 font-mono-numbers">
                {{ formatINR(trip.total_balance) }}
              </td>
              <td class="py-3 px-4 text-center">
                <StatusPill :status="trip.balance_status" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  Truck,
  IndianRupee,
  Receipt,
  Wallet,
  Percent,
  FileText,
  Clock,
  TrendingUp,
  AlertTriangle,
  FileQuestion,
  FileX,
  AlertCircle,
  MapPin,
  ArrowRight,
} from '@lucide/vue'
import api from '../services/api'
import { formatINR, formatNumber, formatDate } from '../utils/formatters'
import MetricCard from '../components/common/MetricCard.vue'
import SettlementBar from '../components/common/SettlementBar.vue'
import StatusPill from '../components/common/StatusPill.vue'

const selectedFy = ref('ALL')
const dashboardData = ref({})
const loading = ref(true)

const kpis = computed(() => dashboardData.value.kpis || {})
const attention = computed(() => dashboardData.value.attention || {})

async function loadDashboard(fy = 'ALL') {
  try {
    loading.value = true
    const res = await api.getDashboard(fy)
    dashboardData.value = res.data
  } catch (err) {
    console.error('Failed to load dashboard:', err)
  } finally {
    loading.value = false
  }
}

function selectFy(fy) {
  selectedFy.value = fy
  loadDashboard(fy)
}

onMounted(() => {
  loadDashboard(selectedFy.value)
})
</script>
