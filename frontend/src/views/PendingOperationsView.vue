<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-black text-slate-900 tracking-tight">Operational Attention & Backlog</h1>
      <p class="text-xs text-slate-500 mt-0.5">
        Actionable audit queue for unissued memos, missing physical PODs, and overdue balances.
      </p>
    </div>

    <!-- 3 Action Queues -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 1. Pending Memos -->
      <div class="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <h3 class="text-xs font-black uppercase tracking-wider text-slate-900">Pending Memos</h3>
          </div>
          <span class="px-2 py-0.5 rounded-full text-xs font-black bg-amber-100 text-amber-800 font-mono-numbers">
            {{ formatNumber(reportData.counts?.pending_memos || 0) }}
          </span>
        </div>

        <div class="divide-y divide-slate-100 max-h-96 overflow-y-auto">
          <div
            v-for="t in reportData.pending_memos || []"
            :key="t.id"
            class="py-3 text-xs flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg"
          >
            <div>
              <router-link :to="`/trips/${t.id}`" class="font-black text-blue-600 hover:underline">
                LR #{{ t.lr_no }}
              </router-link>
              <div class="text-[11px] text-slate-500">{{ t.consignor }} • {{ t.vehicle }}</div>
            </div>
            <span class="text-[10px] text-amber-700 font-bold bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
              No Memo
            </span>
          </div>
        </div>
      </div>

      <!-- 2. Missing PODs -->
      <div class="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            <h3 class="text-xs font-black uppercase tracking-wider text-slate-900">Missing Physical PODs</h3>
          </div>
          <span class="px-2 py-0.5 rounded-full text-xs font-black bg-rose-100 text-rose-800 font-mono-numbers">
            {{ formatNumber(reportData.counts?.missing_pods || 0) }}
          </span>
        </div>

        <div class="divide-y divide-slate-100 max-h-96 overflow-y-auto">
          <div
            v-for="t in reportData.missing_pods || []"
            :key="t.id"
            class="py-3 text-xs flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg"
          >
            <div>
              <router-link :to="`/trips/${t.id}`" class="font-black text-blue-600 hover:underline">
                LR #{{ t.lr_no }}
              </router-link>
              <div class="text-[11px] text-slate-500">{{ t.consignor }} • {{ t.route }}</div>
            </div>
            <span class="text-[10px] text-rose-700 font-bold bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
              Unverified POD
            </span>
          </div>
        </div>
      </div>

      <!-- 3. Overdue Uncollected -->
      <div class="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-rose-600 animate-pulse"></span>
            <h3 class="text-xs font-black uppercase tracking-wider text-slate-900">Overdue Uncollected</h3>
          </div>
          <span class="px-2 py-0.5 rounded-full text-xs font-black bg-rose-100 text-rose-800 font-mono-numbers">
            {{ formatNumber(reportData.counts?.overdue_uncollected || 0) }}
          </span>
        </div>

        <div class="divide-y divide-slate-100 max-h-96 overflow-y-auto">
          <div
            v-for="t in reportData.overdue_uncollected || []"
            :key="t.id"
            class="py-3 text-xs flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg"
          >
            <div>
              <router-link :to="`/trips/${t.id}`" class="font-black text-blue-600 hover:underline">
                LR #{{ t.lr_no }}
              </router-link>
              <div class="text-[11px] text-slate-500">{{ t.consignor }}</div>
            </div>
            <span class="text-xs font-black text-rose-700 font-mono-numbers">
              {{ formatINR(t.total_balance) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { formatINR, formatNumber } from '../utils/formatters'

const reportData = ref({})

async function loadReport() {
  try {
    const res = await api.getPendingOperations()
    reportData.value = res.data
  } catch (err) {
    console.error(err)
  }
}

onMounted(() => {
  loadReport()
})
</script>
