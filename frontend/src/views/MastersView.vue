<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">{{ title }}</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Manage system master directory, codes, contact details, and registrations.
        </p>
      </div>

      <button
        type="button"
        @click="showModal = true"
        class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-sm shadow-blue-500/20"
      >
        <Plus class="w-4 h-4" />
        <span>Add {{ singularName }}</span>
      </button>
    </div>

    <!-- Search Input -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-sm">
      <input
        type="text"
        v-model="searchQuery"
        @input="debounceSearch"
        :placeholder="`Search ${title.toLowerCase()}...`"
        class="w-full sm:w-80 px-3.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
      />
    </div>

    <!-- Data Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <div class="overflow-x-auto table-containment-region">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50 text-[11px] font-black uppercase text-slate-500 border-b border-slate-200">
            <!-- Headers based on master type -->
            <tr v-if="masterType === 'customers'">
              <th class="py-3 px-4">Customer Name</th>
              <th class="py-3 px-4">Short Code</th>
              <th class="py-3 px-4">City</th>
              <th class="py-3 px-4">Phone</th>
              <th class="py-3 px-4">PAN</th>
            </tr>
            <tr v-else-if="masterType === 'transporters'">
              <th class="py-3 px-4">Transporter Name</th>
              <th class="py-3 px-4">Short Code</th>
              <th class="py-3 px-4">PAN Number</th>
              <th class="py-3 px-4">Phone</th>
            </tr>
            <tr v-else-if="masterType === 'vehicles'">
              <th class="py-3 px-4">Vehicle Registration No.</th>
              <th class="py-3 px-4">Default Transporter / Owner</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="item in items" :key="item.id" class="hover:bg-slate-50">
              <template v-if="masterType === 'customers'">
                <td class="py-3 px-4 font-bold text-slate-900">{{ item.name }}</td>
                <td class="py-3 px-4 text-slate-600 font-mono">{{ item.code || '-' }}</td>
                <td class="py-3 px-4 text-slate-600">{{ item.city || '-' }}</td>
                <td class="py-3 px-4 text-slate-600 font-mono">{{ item.phone || '-' }}</td>
                <td class="py-3 px-4 font-mono font-bold text-slate-700">{{ item.pan || '-' }}</td>
              </template>
              <template v-else-if="masterType === 'transporters'">
                <td class="py-3 px-4 font-bold text-slate-900">{{ item.name }}</td>
                <td class="py-3 px-4 text-slate-600 font-mono">{{ item.code || '-' }}</td>
                <td class="py-3 px-4 font-mono font-bold text-slate-700">{{ item.pan || 'NO PAN' }}</td>
                <td class="py-3 px-4 text-slate-600 font-mono">{{ item.phone || '-' }}</td>
              </template>
              <template v-else-if="masterType === 'vehicles'">
                <td class="py-3 px-4 font-mono font-bold text-slate-900">
                  <span class="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200">{{ item.reg_no }}</span>
                </td>
                <td class="py-3 px-4 text-slate-700 font-medium">{{ item.owner || 'Independent' }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Quick Add Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div class="bg-white rounded-2xl p-6 max-w-md w-full shadow-xl space-y-4">
        <h3 class="text-sm font-black uppercase text-slate-900">Add New {{ singularName }}</h3>
        
        <div class="space-y-3">
          <div v-if="masterType !== 'vehicles'">
            <label class="block text-xs font-bold text-slate-600 mb-1">Name *</label>
            <input
              type="text"
              v-model="modalForm.name"
              placeholder="e.g. Acme Logistics"
              class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
            />
          </div>
          <div v-else>
            <label class="block text-xs font-bold text-slate-600 mb-1">Vehicle Registration No. *</label>
            <input
              type="text"
              v-model="modalForm.reg_no"
              placeholder="e.g. HR38W-8905"
              class="w-full px-3 py-2 text-xs font-mono uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
            />
          </div>

          <div v-if="masterType === 'customers'">
            <label class="block text-xs font-bold text-slate-600 mb-1">City</label>
            <input
              type="text"
              v-model="modalForm.city"
              placeholder="e.g. Vapi"
              class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
            />
          </div>

          <div v-if="masterType === 'transporters' || masterType === 'customers'">
            <label class="block text-xs font-bold text-slate-600 mb-1">PAN Number</label>
            <input
              type="text"
              v-model="modalForm.pan"
              placeholder="e.g. ABCDE1234F"
              class="w-full px-3 py-2 text-xs font-mono uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
            />
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            @click="showModal = false"
            class="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-700"
          >
            Cancel
          </button>
          <button
            type="button"
            @click="createMaster"
            class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-bold text-white"
          >
            Save {{ singularName }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Plus } from '@lucide/vue'
import api from '../services/api'

const route = useRoute()
const masterType = computed(() => {
  if (route.path.includes('customers')) return 'customers'
  if (route.path.includes('transporters')) return 'transporters'
  return 'vehicles'
})

const title = computed(() => {
  if (masterType.value === 'customers') return 'Customers (Consignors)'
  if (masterType.value === 'transporters') return 'Transporters (Lorry Owners)'
  return 'Vehicles (Lorries)'
})

const singularName = computed(() => {
  if (masterType.value === 'customers') return 'Customer'
  if (masterType.value === 'transporters') return 'Transporter'
  return 'Vehicle'
})

const items = ref([])
const searchQuery = ref('')
const showModal = ref(false)
const modalForm = ref({ name: '', reg_no: '', city: '', pan: '', code: '' })
let searchTimer = null

async function loadData() {
  try {
    let res
    if (masterType.value === 'customers') {
      res = await api.getCustomers(searchQuery.value)
    } else if (masterType.value === 'transporters') {
      res = await api.getTransporters(searchQuery.value)
    } else {
      res = await api.getVehicles(searchQuery.value)
    }
    items.value = res.data || []
  } catch (err) {
    console.error(err)
  }
}

function debounceSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadData()
  }, 300)
}

async function createMaster() {
  try {
    if (masterType.value === 'customers') {
      await api.createCustomer(modalForm.value)
    } else if (masterType.value === 'transporters') {
      await api.createTransporter(modalForm.value)
    } else {
      await api.createVehicle(modalForm.value)
    }
    showModal.value = false
    modalForm.value = { name: '', reg_no: '', city: '', pan: '', code: '' }
    loadData()
  } catch (err) {
    alert(err.response?.data?.error || 'Failed to create')
  }
}

watch(masterType, () => {
  searchQuery.value = ''
  loadData()
})

onMounted(() => {
  loadData()
})
</script>
