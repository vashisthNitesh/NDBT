<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">Transporter Payable Report</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Settlement liabilities, TDS deductions, and agreed balances for vehicle owners.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <select
          v-model="selectedFy"
          @change="loadReport"
          class="px-3 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 text-slate-700"
        >
          <option value="">All Financial Years</option>
          <option value="2026-27">FY 2026-27</option>
          <option value="2025-26">FY 2025-26</option>
          <option value="2024-25">FY 2024-25</option>
          <option value="2023-24">FY 2023-24</option>
          <option value="2022-23">FY 2022-23</option>
        </select>
      </div>
    </div>

    <!-- Summary KPI cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="p-4 rounded-xl bg-white border border-slate-200">
        <span class="text-[11px] font-bold text-slate-500 uppercase">Transporters</span>
        <div class="text-xl font-black text-slate-900 font-mono-numbers mt-1">{{ formatNumber(reportData.results?.length || 0) }}</div>
      </div>
      <div class="p-4 rounded-xl bg-white border border-slate-200">
        <span class="text-[11px] font-bold text-slate-500 uppercase">Total Trips</span>
        <div class="text-xl font-black text-slate-900 font-mono-numbers mt-1">{{ formatNumber(reportData.totals?.trip_count || 0) }}</div>
      </div>
      <div class="p-4 rounded-xl bg-white border border-slate-200">
        <span class="text-[11px] font-bold text-slate-500 uppercase">Total TDS Withheld</span>
        <div class="text-xl font-black text-blue-600 font-mono-numbers mt-1">{{ formatINR(reportData.totals?.tds || 0) }}</div>
      </div>
      <div class="p-4 rounded-xl bg-amber-50/70 border border-amber-200">
        <span class="text-[11px] font-bold text-amber-700 uppercase">Balance Due to Owners</span>
        <div class="text-xl font-black text-amber-900 font-mono-numbers mt-1">{{ formatINR(reportData.totals?.balance_due || 0) }}</div>
      </div>
    </div>

    <!-- Search & Data Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <div class="p-4 border-b border-slate-100">
        <input
          type="text"
          v-model="searchQuery"
          @input="debounceSearch"
          placeholder="Search transporter name or PAN..."
          class="w-full sm:w-80 px-3.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
        />
      </div>

      <div class="overflow-x-auto table-containment-region">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50 text-[11px] font-black uppercase text-slate-500 border-b border-slate-200">
            <tr>
              <th class="py-3 px-4">Transporter (Lorry Owner)</th>
              <th class="py-3 px-4">PAN Number</th>
              <th class="py-3 px-4 text-center">Trips</th>
              <th class="py-3 px-4 text-right">Total Freight</th>
              <th class="py-3 px-4 text-right">TDS Withheld (194C)</th>
              <th class="py-3 px-4 text-right">Balance Due</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="t in reportData.results || []" :key="t.transporter_id" class="hover:bg-slate-50">
              <td class="py-3 px-4 font-bold text-slate-800">
                <router-link :to="{ path: '/trips', query: { transporter: t.transporter_id } }" class="text-blue-600 hover:underline">
                  {{ t.transporter_name }}
                </router-link>
              </td>
              <td class="py-3 px-4 font-mono text-slate-700">
                <span class="px-2 py-0.5 rounded-md bg-slate-100 text-[11px] font-bold">
                  {{ t.pan }}
                </span>
              </td>
              <td class="py-3 px-4 text-center font-bold font-mono-numbers">{{ formatNumber(t.trip_count) }}</td>
              <td class="py-3 px-4 text-right font-black font-mono-numbers">{{ formatINR(t.freight) }}</td>
              <td class="py-3 px-4 text-right font-bold text-blue-600 font-mono-numbers">{{ formatINR(t.tds) }}</td>
              <td class="py-3 px-4 text-right font-black text-amber-700 font-mono-numbers">{{ formatINR(t.balance_due) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { formatINR, formatNumber } from '../utils/formatters'

const selectedFy = ref('')
const searchQuery = ref('')
const reportData = ref({})
let searchTimer = null

async function loadReport() {
  try {
    const res = await api.getTransporterPayable(selectedFy.value, searchQuery.value)
    reportData.value = res.data
  } catch (err) {
    console.error(err)
  }
}

function debounceSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadReport()
  }, 300)
}

onMounted(() => {
  loadReport()
})
</script>
