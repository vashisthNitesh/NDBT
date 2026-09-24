<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">Monthly Volume & Revenue Summary</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Month-by-month freight volume, margin trends, and financial movements.
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

    <!-- Data Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <div class="overflow-x-auto table-containment-region">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50 text-[11px] font-black uppercase text-slate-500 border-b border-slate-200">
            <tr>
              <th class="py-3 px-4">Billing Month</th>
              <th class="py-3 px-4 text-center">Trips Dispatched</th>
              <th class="py-3 px-4 text-right">Contracted Freight</th>
              <th class="py-3 px-4 text-right">Advances</th>
              <th class="py-3 px-4 text-right">Brokerage Margin</th>
              <th class="py-3 px-4 text-right">TDS Withheld</th>
              <th class="py-3 px-4 text-right">Pending Balance</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="m in reportData.results || []" :key="m.month_iso" class="hover:bg-slate-50">
              <td class="py-3 px-4 font-black text-slate-900">{{ m.month }}</td>
              <td class="py-3 px-4 text-center font-bold font-mono-numbers">{{ formatNumber(m.trips) }}</td>
              <td class="py-3 px-4 text-right font-black font-mono-numbers">{{ formatINR(m.freight) }}</td>
              <td class="py-3 px-4 text-right text-slate-600 font-mono-numbers">{{ formatINR(m.advance) }}</td>
              <td class="py-3 px-4 text-right font-bold text-indigo-600 font-mono-numbers">{{ formatINR(m.commission) }}</td>
              <td class="py-3 px-4 text-right text-slate-600 font-mono-numbers">{{ formatINR(m.tds) }}</td>
              <td class="py-3 px-4 text-right font-black text-rose-600 font-mono-numbers">{{ formatINR(m.balance) }}</td>
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
const reportData = ref({})

async function loadReport() {
  try {
    const res = await api.getMonthlySummary(selectedFy.value)
    reportData.value = res.data
  } catch (err) {
    console.error(err)
  }
}

onMounted(() => {
  loadReport()
})
</script>
