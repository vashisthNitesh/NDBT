<template>
  <div
    class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex flex-col justify-between"
    :class="clickable ? 'cursor-pointer' : ''"
  >
    <div class="flex items-start justify-between gap-3 mb-2">
      <span class="text-xs font-bold uppercase tracking-wider text-slate-500">{{ title }}</span>
      <div v-if="icon" class="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
        <component :is="icon" class="w-4 h-4" />
      </div>
    </div>

    <div>
      <div class="text-2xl font-black text-slate-900 tracking-tight font-mono-numbers">
        {{ value }}
      </div>
      <div v-if="subtitle" class="text-xs text-slate-500 mt-1 flex items-center gap-1 font-medium">
        <span>{{ subtitle }}</span>
      </div>
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: Object,
    default: null,
  },
  clickable: {
    type: Boolean,
    default: false,
  },
})
</script>
