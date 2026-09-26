<template>
  <div class="relative w-full select-none" ref="containerRef">
    <!-- Selector Input Box with Explicit Chevron Arrow -->
    <div
      class="relative flex items-center w-full bg-slate-50 border border-slate-200 rounded-xl transition-all focus-within:border-blue-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-500/10"
      :class="{ 'border-blue-500 bg-white ring-2 ring-blue-500/10': isOpen, 'opacity-60 cursor-not-allowed': disabled }"
    >
      <input
        ref="inputRef"
        type="text"
        :value="searchQuery"
        @input="handleInput"
        @focus="openDropdown"
        @keydown.down.prevent="highlightNext"
        @keydown.up.prevent="highlightPrev"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.esc="closeDropdown"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        class="w-full px-3 py-1.5 text-xs bg-transparent outline-hidden text-slate-800 placeholder:text-slate-400 font-medium pr-14 select-text"
        :class="inputClass"
      />

      <div class="absolute right-1.5 top-0 bottom-0 flex items-center gap-0.5">
        <!-- Clear Button -->
        <button
          v-if="clearable && searchQuery && !disabled"
          type="button"
          tabindex="-1"
          @click.stop="clearSelection"
          class="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          title="Clear"
        >
          <X class="w-3 h-3" />
        </button>

        <!-- Dropdown Chevron Arrow Indicator -->
        <button
          type="button"
          tabindex="-1"
          @click.stop="toggleDropdown"
          :disabled="disabled"
          class="p-1 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-200/60 transition-colors cursor-pointer"
          title="Toggle dropdown"
        >
          <ChevronDown
            class="w-4 h-4 transition-transform duration-200 text-slate-500"
            :class="{ 'rotate-180 text-blue-600': isOpen }"
          />
        </button>
      </div>
    </div>

    <!-- Dropdown Menu: STRICTLY Positioned Directly Below Selector (top-full mt-1.5) -->
    <div
      v-if="isOpen"
      class="absolute z-50 left-0 right-0 top-full mt-1.5 bg-white border border-slate-200 rounded-xl shadow-xl max-h-60 overflow-y-auto divide-y divide-slate-100 animate-in fade-in slide-in-from-top-1 duration-150"
      style="box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);"
    >
      <!-- Option items -->
      <div
        v-for="(opt, idx) in filteredOptions"
        :key="opt.id || opt.value || idx"
        @click="selectOption(opt)"
        @mouseenter="highlightedIndex = idx"
        class="px-3.5 py-2 text-xs cursor-pointer flex items-center justify-between transition-colors"
        :class="{
          'bg-blue-50/80 text-blue-900 font-semibold': isSelected(opt) || highlightedIndex === idx,
          'hover:bg-slate-50 text-slate-800': !isSelected(opt) && highlightedIndex !== idx
        }"
      >
        <div class="flex flex-col min-w-0 pr-2">
          <span class="truncate font-medium" :class="opt.labelClass || ''">
            {{ getOptLabel(opt) }}
          </span>
          <span v-if="getOptSublabel(opt)" class="text-[10px] text-slate-400 truncate">
            {{ getOptSublabel(opt) }}
          </span>
        </div>

        <Check v-if="isSelected(opt)" class="w-3.5 h-3.5 text-blue-600 shrink-0" />
      </div>

      <!-- Free-text / Custom Option if query not matching exactly -->
      <div
        v-if="allowCustom && searchQuery.trim() && !hasExactMatch"
        @click="selectCustom(searchQuery.trim())"
        class="px-3.5 py-2 text-xs text-blue-600 hover:bg-blue-50 cursor-pointer flex items-center gap-1.5 font-bold border-t border-slate-100"
      >
        <Plus class="w-3.5 h-3.5" />
        <span>Use "{{ searchQuery.trim() }}"</span>
      </div>

      <!-- Empty state -->
      <div
        v-if="filteredOptions.length === 0 && (!allowCustom || !searchQuery.trim())"
        class="px-3.5 py-3 text-xs text-slate-400 text-center italic"
      >
        No matching options
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ChevronDown, X, Check, Plus } from '@lucide/vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Select...',
  },
  labelKey: {
    type: String,
    default: 'name',
  },
  valueKey: {
    type: String,
    default: 'name',
  },
  sublabelKey: {
    type: String,
    default: '',
  },
  allowCustom: {
    type: Boolean,
    default: true,
  },
  clearable: {
    type: Boolean,
    default: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  required: {
    type: Boolean,
    default: false,
  },
  inputClass: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change', 'select', 'clear'])

const containerRef = ref(null)
const inputRef = ref(null)
const isOpen = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(-1)

// Synchronize external modelValue with internal searchQuery
watch(
  () => props.modelValue,
  (val) => {
    searchQuery.value = val !== undefined && val !== null ? String(val) : ''
  },
  { immediate: true }
)

function getOptLabel(opt) {
  if (typeof opt === 'string' || typeof opt === 'number') return String(opt)
  return opt[props.labelKey] || opt.label || opt.name || opt.reg_no || ''
}

function getOptValue(opt) {
  if (typeof opt === 'string' || typeof opt === 'number') return opt
  return opt[props.valueKey] !== undefined ? opt[props.valueKey] : getOptLabel(opt)
}

function getOptSublabel(opt) {
  if (typeof opt !== 'object' || !opt) return ''
  if (props.sublabelKey && opt[props.sublabelKey]) return opt[props.sublabelKey]
  if (opt.code) return `Code: ${opt.code}`
  if (opt.owner) return `Owner: ${opt.owner}`
  if (opt.city) return opt.city
  if (opt.capacity_tons) return `${opt.capacity_tons} tons`
  return ''
}

const filteredOptions = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return props.options

  return props.options.filter((opt) => {
    const lbl = getOptLabel(opt).toLowerCase()
    const sub = getOptSublabel(opt).toLowerCase()
    return lbl.includes(q) || sub.includes(q)
  })
})

const hasExactMatch = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return props.options.some((opt) => getOptLabel(opt).toLowerCase() === q)
})

function isSelected(opt) {
  const val = getOptValue(opt)
  return String(val).toLowerCase() === String(props.modelValue).toLowerCase()
}

function openDropdown() {
  if (props.disabled) return
  isOpen.value = true
  highlightedIndex.value = -1
}

function closeDropdown() {
  isOpen.value = false
  highlightedIndex.value = -1
}

function toggleDropdown() {
  if (props.disabled) return
  if (isOpen.value) {
    closeDropdown()
  } else {
    openDropdown()
    inputRef.value?.focus()
  }
}

function handleInput(e) {
  const val = e.target.value
  searchQuery.value = val
  if (props.allowCustom) {
    emit('update:modelValue', val)
    emit('change', val)
  }
  openDropdown()
}

function selectOption(opt) {
  const val = getOptValue(opt)
  searchQuery.value = getOptLabel(opt)
  emit('update:modelValue', val)
  emit('change', val)
  emit('select', opt)
  closeDropdown()
}

function selectCustom(customVal) {
  searchQuery.value = customVal
  emit('update:modelValue', customVal)
  emit('change', customVal)
  emit('select', { name: customVal, label: customVal })
  closeDropdown()
}

function clearSelection() {
  searchQuery.value = ''
  emit('update:modelValue', '')
  emit('change', '')
  emit('clear')
  openDropdown()
}

function highlightNext() {
  if (!isOpen.value) {
    openDropdown()
    return
  }
  if (filteredOptions.value.length === 0) return
  highlightedIndex.value = (highlightedIndex.value + 1) % filteredOptions.value.length
}

function highlightPrev() {
  if (!isOpen.value) {
    openDropdown()
    return
  }
  if (filteredOptions.value.length === 0) return
  highlightedIndex.value =
    (highlightedIndex.value - 1 + filteredOptions.value.length) % filteredOptions.value.length
}

function selectHighlighted() {
  if (highlightedIndex.value >= 0 && highlightedIndex.value < filteredOptions.value.length) {
    selectOption(filteredOptions.value[highlightedIndex.value])
  } else if (props.allowCustom && searchQuery.value.trim()) {
    selectCustom(searchQuery.value.trim())
  }
}

function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
