<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">TDS Register (Section 194C)</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Audit-ready tax deductions on contractor/transporter freight payouts.
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

    <!-- Total TDS Card -->
    <div class="bg-blue-600 text-white rounded-2xl p-4 sm:p-6 shadow-md shadow-blue-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="min-w-0">
        <span class="text-xs font-bold uppercase tracking-wider text-blue-200">Total Section 194C TDS Deducted</span>
        <div class="text-2xl sm:text-3xl font-black font-mono-numbers mt-1 truncate">{{ formatINR(reportData.total_tds || 0) }}</div>
      </div>
      <div class="sm:text-right">
        <span class="text-xs text-blue-200 block">Deduction Entries</span>
        <span class="text-xl sm:text-2xl font-bold font-mono-numbers">{{ formatNumber(reportData.count || 0) }}</span>
      </div>
    </div>

    <!-- Data Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <div class="p-3.5 sm:p-4 border-b border-slate-100">
        <input
          type="text"
          v-model="searchQuery"
          @input="debounceSearch"
          placeholder="Filter by Transporter, PAN, Vehicle, LR No..."
          class="w-full sm:w-80 px-3.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
        />
      </div>

      <!-- Mobile Table Swipe Hint -->
      <div class="sm:hidden px-3.5 py-1.5 text-[11px] font-semibold text-slate-500 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
        <span>👉 Swipe horizontally for full TDS register</span>
        <span class="text-[10px] text-slate-400">Scroll &rarr;</span>
      </div>

      <div class="overflow-x-auto table-containment-region">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50 text-[11px] font-black uppercase text-slate-500 border-b border-slate-200">
            <tr>
              <th class="py-3 px-4">LR No.</th>
              <th class="py-3 px-4">Date</th>
              <th class="py-3 px-4">Transporter Name</th>
              <th class="py-3 px-4">PAN Number</th>
              <th class="py-3 px-4">Vehicle</th>
              <th class="py-3 px-4 text-right">Freight Amount</th>
              <th class="py-3 px-4 text-right">TDS (194C)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="r in reportData.results || []" :key="r.id" class="hover:bg-slate-50">
              <td class="py-3 px-4 font-black text-blue-600 font-mono-numbers">
                <router-link :to="`/trips/${r.id}`" class="hover:underline">#{{ r.lr_no }}</router-link>
              </td>
              <td class="py-3 px-4 text-slate-600 font-mono-numbers">{{ formatDate(r.date) }}</td>
              <td class="py-3 px-4 font-bold text-slate-800">{{ r.transporter }}</td>
              <td class="py-3 px-4 font-mono font-bold text-slate-700">
                <span class="px-2 py-0.5 rounded-md bg-slate-100 text-[11px]">{{ r.pan }}</span>
              </td>
              <td class="py-3 px-4 font-mono text-slate-600">{{ r.vehicle }}</td>
              <td class="py-3 px-4 text-right font-bold text-slate-900 font-mono-numbers">{{ formatINR(r.freight) }}</td>
              <td class="py-3 px-4 text-right font-black text-blue-600 font-mono-numbers">{{ formatINR(r.tds) }}</td>
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
import { formatINR, formatNumber, formatDate } from '../utils/formatters'

const selectedFy = ref('')
const searchQuery = ref('')
const reportData = ref({})
let searchTimer = null

async function loadReport() {
  try {
    const res = await api.getTdsRegister(selectedFy.value, searchQuery.value)
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
