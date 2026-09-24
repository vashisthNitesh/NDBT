<template>
  <div class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse"></span>
          <h3 class="text-sm font-black uppercase tracking-wider text-slate-900">
            Settlement Health & Payment Pipeline
          </h3>
        </div>
        <p class="text-xs text-slate-500 mt-0.5">
          Breakdown of {{ formatNumber(settlement.total) }} trips across financial settlement stages
        </p>
      </div>

      <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold">
        <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
        {{ settlement.received?.pct || 0 }}% Settled
      </div>
    </div>

    <!-- Segmented Multi-Color Progress Bar -->
    <div class="w-full h-3.5 bg-slate-100 rounded-full flex overflow-hidden p-0.5 gap-0.5 mb-5 shadow-inner">
      <div
        v-if="settlement.received?.pct > 0"
        :style="{ width: `${settlement.received.pct}%` }"
        class="bg-emerald-500 rounded-l-full transition-all duration-500"
        :title="`Received: ${settlement.received.pct}% (${formatNumber(settlement.received.count)} trips)`"
      ></div>
      <div
        v-if="settlement.pending?.pct > 0"
        :style="{ width: `${settlement.pending.pct}%` }"
        class="bg-amber-400 transition-all duration-500"
        :title="`Pending: ${settlement.pending.pct}% (${formatNumber(settlement.pending.count)} trips)`"
      ></div>
      <div
        v-if="settlement.nil?.pct > 0"
        :style="{ width: `${settlement.nil.pct}%` }"
        class="bg-slate-400 transition-all duration-500"
        :title="`Nil / Cleared: ${settlement.nil.pct}% (${formatNumber(settlement.nil.count)} trips)`"
      ></div>
      <div
        v-if="settlement.not_received?.pct > 0"
        :style="{ width: `${settlement.not_received.pct}%` }"
        class="bg-rose-500 rounded-r-full transition-all duration-500"
        :title="`Overdue Uncollected: ${settlement.not_received.pct}% (${formatNumber(settlement.not_received.count)} trips)`"
      ></div>
    </div>

    <!-- Interactive Breakdown Badges Grid -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <!-- Received -->
      <router-link
        :to="{ path: '/trips', query: { status: 'RECEIVED' } }"
        class="p-3 rounded-xl bg-slate-50 hover:bg-emerald-50/70 border border-slate-200/80 hover:border-emerald-300 transition-all group"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-slate-600 group-hover:text-emerald-800">Received</span>
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
        </div>
        <div class="text-lg font-black text-slate-900 group-hover:text-emerald-900 font-mono-numbers">
          {{ formatNumber(settlement.received?.count || 0) }}
          <span class="text-xs font-semibold text-slate-400 group-hover:text-emerald-700">({{ settlement.received?.pct || 0 }}%)</span>
        </div>
      </router-link>

      <!-- Pending -->
      <router-link
        :to="{ path: '/trips', query: { status: 'PENDING' } }"
        class="p-3 rounded-xl bg-slate-50 hover:bg-amber-50/70 border border-slate-200/80 hover:border-amber-300 transition-all group"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-slate-600 group-hover:text-amber-800">Pending</span>
          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
        </div>
        <div class="text-lg font-black text-slate-900 group-hover:text-amber-900 font-mono-numbers">
          {{ formatNumber(settlement.pending?.count || 0) }}
          <span class="text-xs font-semibold text-slate-400 group-hover:text-amber-700">({{ settlement.pending?.pct || 0 }}%)</span>
        </div>
      </router-link>

      <!-- Nil / Cleared -->
      <router-link
        :to="{ path: '/trips', query: { status: 'NIL' } }"
        class="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200/80 hover:border-slate-300 transition-all group"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-slate-600 group-hover:text-slate-800">Nil / Cleared</span>
          <span class="w-2 h-2 rounded-full bg-slate-400"></span>
        </div>
        <div class="text-lg font-black text-slate-900 group-hover:text-slate-900 font-mono-numbers">
          {{ formatNumber(settlement.nil?.count || 0) }}
          <span class="text-xs font-semibold text-slate-400 group-hover:text-slate-600">({{ settlement.nil?.pct || 0 }}%)</span>
        </div>
      </router-link>

      <!-- Overdue Uncollected -->
      <router-link
        :to="{ path: '/trips', query: { status: 'NOT_RECEIVED' } }"
        class="p-3 rounded-xl bg-slate-50 hover:bg-rose-50/70 border border-slate-200/80 hover:border-rose-300 transition-all group"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-slate-600 group-hover:text-rose-800">Overdue</span>
          <span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
        </div>
        <div class="text-lg font-black text-slate-900 group-hover:text-rose-900 font-mono-numbers">
          {{ formatNumber(settlement.not_received?.count || 0) }}
          <span class="text-xs font-semibold text-slate-400 group-hover:text-rose-700">({{ settlement.not_received?.pct || 0 }}%)</span>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { formatNumber } from '../../utils/formatters'

defineProps({
  settlement: {
    type: Object,
    required: true,
  },
})
</script>
