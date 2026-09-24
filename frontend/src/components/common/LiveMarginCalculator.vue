<template>
  <div class="bg-slate-900 text-white rounded-2xl p-5 shadow-lg border border-slate-800 mb-6">
    <div class="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <h4 class="text-xs font-black uppercase tracking-wider text-slate-200">
          Live Financial Margin Engine
        </h4>
        <span class="text-[11px] text-slate-400 hidden sm:inline">• Real-time server validated</span>
      </div>

      <!-- Quick TDS Buttons -->
      <div class="flex items-center gap-2">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Quick TDS:</span>
        <button
          type="button"
          @click="applyTds(1)"
          class="px-2.5 py-1 text-xs font-bold rounded-lg bg-slate-800 hover:bg-blue-600 text-slate-200 hover:text-white transition-colors border border-slate-700 hover:border-blue-500"
        >
          1% (Individual)
        </button>
        <button
          type="button"
          @click="applyTds(2)"
          class="px-2.5 py-1 text-xs font-bold rounded-lg bg-slate-800 hover:bg-blue-600 text-slate-200 hover:text-white transition-colors border border-slate-700 hover:border-blue-500"
        >
          2% (Company)
        </button>
      </div>
    </div>

    <!-- 3-Deck Live Margin Indicators -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- 1. Advance Balance -->
      <div class="p-4 rounded-xl bg-slate-800/80 border border-slate-700/80">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
          Advance Balance
        </span>
        <div class="text-2xl font-black text-white font-mono-numbers">
          {{ formatINR(calculatedAdvanceBalance) }}
        </div>
        <span class="text-[11px] text-slate-400 block mt-1">
          Advance ({{ formatINR(advance) }}) - Comm - Lorry Adv - TDS
        </span>
      </div>

      <!-- 2. Freight Balance -->
      <div class="p-4 rounded-xl bg-slate-800/80 border border-slate-700/80">
        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
          Freight Balance
        </span>
        <div class="text-2xl font-black text-amber-400 font-mono-numbers">
          {{ formatINR(calculatedBalance) }}
        </div>
        <span class="text-[11px] text-slate-400 block mt-1">
          Contracted Freight ({{ formatINR(freight) }}) - Advance
        </span>
      </div>

      <!-- 3. Total Due -->
      <div class="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40">
        <span class="text-[11px] font-bold text-emerald-400 uppercase tracking-wider block mb-1">
          Total Net Due
        </span>
        <div class="text-2xl font-black text-emerald-300 font-mono-numbers">
          {{ formatINR(calculatedTotalBalance) }}
        </div>
        <span class="text-[11px] text-emerald-400/90 block mt-1">
          Balance + Hamali Labour ({{ formatINR(labour) }}) + Detention ({{ formatINR(calculatedHolding) }})
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatINR } from '../../utils/formatters'

const props = defineProps({
  freight: { type: Number, default: 0 },
  advance: { type: Number, default: 0 },
  commission: { type: Number, default: 1500 },
  lorryAdvance: { type: Number, default: 0 },
  tds: { type: Number, default: 0 },
  labour: { type: Number, default: 0 },
  holdingDays: { type: Number, default: 0 },
  holdingRate: { type: Number, default: 0 },
  holdingManual: { type: Number, default: 0 },
})

const emit = defineEmits(['update:tds', 'update:holding'])

const calculatedHolding = computed(() => {
  if (props.holdingDays > 0 && props.holdingRate > 0) {
    return props.holdingDays * props.holdingRate
  }
  return props.holdingManual || 0
})

const calculatedAdvanceBalance = computed(() => {
  return (props.advance || 0) - (props.commission || 0) - (props.lorryAdvance || 0) - (props.tds || 0)
})

const calculatedBalance = computed(() => {
  return (props.freight || 0) - (props.advance || 0)
})

const calculatedTotalBalance = computed(() => {
  return calculatedBalance.value + (props.labour || 0) + calculatedHolding.value
})

function applyTds(percent) {
  const calculated = Math.round(((props.freight || 0) * percent) / 100)
  emit('update:tds', calculated)
}
</script>
