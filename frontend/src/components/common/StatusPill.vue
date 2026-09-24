<template>
  <span
    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold whitespace-nowrap tracking-wide border transition-colors"
    :class="styleClasses"
  >
    <span class="w-2 h-2 rounded-full shrink-0" :class="dotClass"></span>
    {{ labelText }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
})

const styleMap = {
  RECEIVED: {
    pill: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500 shadow-sm shadow-emerald-400',
    label: 'Received',
  },
  PENDING: {
    pill: 'bg-amber-50 text-amber-700 border-amber-200',
    dot: 'bg-amber-500 shadow-sm shadow-amber-400',
    label: 'Pending',
  },
  NIL: {
    pill: 'bg-slate-100 text-slate-700 border-slate-200',
    dot: 'bg-slate-400',
    label: 'Nil / Cleared',
  },
  NOT_RECEIVED: {
    pill: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500 animate-pulse shadow-sm shadow-rose-400',
    label: 'Not Received',
  },
  TO_PAY: {
    pill: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    dot: 'bg-indigo-500 shadow-sm shadow-indigo-400',
    label: 'To Pay',
  },
}

const currentConfig = computed(() => {
  return styleMap[props.status] || {
    pill: 'bg-slate-100 text-slate-700 border-slate-200',
    dot: 'bg-slate-400',
    label: props.status || 'Unknown',
  }
})

const styleClasses = computed(() => currentConfig.value.pill)
const dotClass = computed(() => currentConfig.value.dot)
const labelText = computed(() => currentConfig.value.label)
</script>
