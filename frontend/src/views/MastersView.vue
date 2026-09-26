<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <!-- Header with Action Button -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
          <component :is="currentIcon" class="w-6 h-6 text-blue-600" />
          <span>{{ title }}</span>
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Manage system master directory, registrations, codes, and operational attributes.
        </p>
      </div>

      <button
        type="button"
        @click="openAddModal"
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-sm shadow-blue-500/20 shrink-0 cursor-pointer"
      >
        <Plus class="w-4 h-4" />
        <span>Add {{ singularName }}</span>
      </button>
    </div>

    <!-- Master Navigation Tabs Bar -->
    <div class="bg-white rounded-2xl p-1.5 border border-slate-200/90 shadow-xs flex items-center gap-1 overflow-x-auto">
      <router-link
        v-for="tab in masterTabs"
        :key="tab.type"
        :to="tab.path"
        class="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap"
        :class="masterType === tab.type ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
      >
        <component :is="tab.icon" class="w-4 h-4" />
        <span>{{ tab.label }}</span>
        <span
          class="text-[10px] px-1.5 py-0.2 rounded-full font-mono"
          :class="masterType === tab.type ? 'bg-blue-700 text-white' : 'bg-slate-200 text-slate-700'"
        >
          {{ tab.count !== null ? tab.count : '' }}
        </span>
      </router-link>
    </div>

    <!-- Search & Quick Filters -->
    <div class="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
      <div class="relative w-full sm:w-96">
        <input
          type="text"
          v-model="searchQuery"
          @input="debounceSearch"
          :placeholder="`Search ${title.toLowerCase()}...`"
          class="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
        />
        <Search class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
      </div>

      <div class="text-xs text-slate-500 font-medium">
        Showing <span class="font-bold text-slate-900">{{ items.length }}</span> records
      </div>
    </div>

    <!-- Data Table -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50 text-[11px] font-black uppercase text-slate-500 border-b border-slate-200">
            <!-- 1. Customers -->
            <tr v-if="masterType === 'customers'">
              <th class="py-3 px-4">Customer Name</th>
              <th class="py-3 px-4">Short Code</th>
              <th class="py-3 px-4">City</th>
              <th class="py-3 px-4">Phone</th>
              <th class="py-3 px-4">PAN Number</th>
              <th class="py-3 px-4">GSTIN</th>
            </tr>

            <!-- 2. Vendors (Transporters) -->
            <tr v-else-if="masterType === 'vendors'">
              <th class="py-3 px-4">Vendor / Transporter Name</th>
              <th class="py-3 px-4">Short Code</th>
              <th class="py-3 px-4">PAN Number</th>
              <th class="py-3 px-4">Phone</th>
            </tr>

            <!-- 3. Vehicle Types -->
            <tr v-else-if="masterType === 'vehicle-types'">
              <th class="py-3 px-4">Vehicle Type / Category</th>
              <th class="py-3 px-4">Standard Capacity</th>
            </tr>

            <!-- 4. Vehicles -->
            <tr v-else-if="masterType === 'vehicles'">
              <th class="py-3 px-4">Vehicle Registration No.</th>
              <th class="py-3 px-4">Vehicle Type</th>
              <th class="py-3 px-4">Capacity</th>
              <th class="py-3 px-4">Default Transporter / Owner</th>
            </tr>

            <!-- 5. Locations -->
            <tr v-else-if="masterType === 'locations'">
              <th class="py-3 px-4">Location / Station Name</th>
              <th class="py-3 px-4">Code</th>
              <th class="py-3 px-4">City</th>
              <th class="py-3 px-4">State</th>
              <th class="py-3 px-4">Category</th>
            </tr>

            <!-- 6. Lanes -->
            <tr v-else-if="masterType === 'lanes'">
              <th class="py-3 px-4">Corridor / Route Name</th>
              <th class="py-3 px-4">Origin Station</th>
              <th class="py-3 px-4">Destination Station</th>
              <th class="py-3 px-4">Distance</th>
              <th class="py-3 px-4">Transit Time</th>
            </tr>
          </thead>

          <tbody class="divide-y divide-slate-100">
            <tr v-if="loading" class="text-center">
              <td colspan="6" class="py-12 text-slate-400 italic">
                Loading {{ title.toLowerCase() }}...
              </td>
            </tr>

            <tr v-else-if="items.length === 0" class="text-center">
              <td colspan="6" class="py-12 text-slate-400 italic">
                No matching records found in {{ title.toLowerCase() }}.
              </td>
            </tr>

            <tr
              v-else
              v-for="item in items"
              :key="item.id"
              class="hover:bg-slate-50 transition-colors"
            >
              <!-- 1. Customers -->
              <template v-if="masterType === 'customers'">
                <td class="py-3 px-4 font-bold text-slate-900">{{ item.name }}</td>
                <td class="py-3 px-4 text-slate-600 font-mono font-semibold">{{ item.code || '-' }}</td>
                <td class="py-3 px-4 text-slate-700">{{ item.city || '-' }}</td>
                <td class="py-3 px-4 text-slate-600 font-mono">{{ item.phone || '-' }}</td>
                <td class="py-3 px-4 font-mono font-bold text-slate-700">{{ item.pan || '-' }}</td>
                <td class="py-3 px-4 font-mono text-slate-600">{{ item.gstin || '-' }}</td>
              </template>

              <!-- 2. Vendors -->
              <template v-else-if="masterType === 'vendors'">
                <td class="py-3 px-4 font-bold text-slate-900">{{ item.name }}</td>
                <td class="py-3 px-4 text-slate-600 font-mono font-semibold">{{ item.code || '-' }}</td>
                <td class="py-3 px-4 font-mono font-bold text-slate-700">
                  <span :class="item.pan ? 'text-slate-800' : 'text-amber-600 font-normal italic'">
                    {{ item.pan || 'NO PAN' }}
                  </span>
                </td>
                <td class="py-3 px-4 text-slate-600 font-mono">{{ item.phone || '-' }}</td>
              </template>

              <!-- 3. Vehicle Types -->
              <template v-else-if="masterType === 'vehicle-types'">
                <td class="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span>{{ item.name }}</span>
                </td>
                <td class="py-3 px-4 font-mono font-bold text-slate-700">
                  {{ item.capacity_tons ? `${item.capacity_tons} MT` : '-' }}
                </td>
              </template>

              <!-- 4. Vehicles -->
              <template v-else-if="masterType === 'vehicles'">
                <td class="py-3 px-4 font-mono font-bold text-slate-900">
                  <span class="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 shadow-2xs">
                    {{ item.reg_no }}
                  </span>
                </td>
                <td class="py-3 px-4 text-slate-700 font-medium">
                  <span v-if="item.vehicle_type" class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-bold text-[11px]">
                    {{ item.vehicle_type }}
                  </span>
                  <span v-else class="text-slate-400">-</span>
                </td>
                <td class="py-3 px-4 font-mono text-slate-600">
                  {{ item.capacity_tons ? `${item.capacity_tons} MT` : '-' }}
                </td>
                <td class="py-3 px-4 text-slate-800 font-semibold">{{ item.owner || 'Independent' }}</td>
              </template>

              <!-- 5. Locations -->
              <template v-else-if="masterType === 'locations'">
                <td class="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                  <MapPin class="w-3.5 h-3.5 text-rose-500" />
                  <span>{{ item.name }}</span>
                </td>
                <td class="py-3 px-4 font-mono font-semibold text-slate-600">{{ item.code || '-' }}</td>
                <td class="py-3 px-4 text-slate-700">{{ item.city || '-' }}</td>
                <td class="py-3 px-4 text-slate-700 font-medium">{{ item.state || '-' }}</td>
                <td class="py-3 px-4">
                  <span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[10px]">
                    {{ item.location_type || 'Station' }}
                  </span>
                </td>
              </template>

              <!-- 6. Lanes -->
              <template v-else-if="masterType === 'lanes'">
                <td class="py-3 px-4 font-bold text-slate-900 flex items-center gap-1.5">
                  <Route class="w-3.5 h-3.5 text-emerald-600" />
                  <span>{{ item.name }}</span>
                </td>
                <td class="py-3 px-4 text-slate-700 font-medium">{{ item.origin }}</td>
                <td class="py-3 px-4 text-slate-700 font-medium">{{ item.destination }}</td>
                <td class="py-3 px-4 font-mono text-slate-700 font-semibold">
                  {{ item.distance_km ? `${item.distance_km} KM` : '-' }}
                </td>
                <td class="py-3 px-4 text-slate-600">
                  {{ item.transit_days ? `${item.transit_days} Days` : '-' }}
                </td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Quick Add Modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div class="bg-white rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4 border border-slate-200">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-sm font-black uppercase text-slate-900 flex items-center gap-2">
            <component :is="currentIcon" class="w-4 h-4 text-blue-600" />
            <span>Add New {{ singularName }}</span>
          </h3>
          <button
            type="button"
            @click="showModal = false"
            class="text-slate-400 hover:text-slate-600 text-lg leading-none cursor-pointer"
          >
            &times;
          </button>
        </div>

        <form @submit.prevent="createMaster" class="space-y-3.5">
          <!-- 1. Customers Form -->
          <template v-if="masterType === 'customers'">
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Customer / Consignor Name *</label>
              <input
                type="text"
                v-model="modalForm.name"
                required
                placeholder="e.g. Acme Corporation Pvt Ltd"
                class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Short Code</label>
                <input
                  type="text"
                  v-model="modalForm.code"
                  placeholder="e.g. ACME"
                  class="w-full px-3 py-2 text-xs uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 font-mono"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">City</label>
                <input
                  type="text"
                  v-model="modalForm.city"
                  placeholder="e.g. Vapi"
                  class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Phone</label>
                <input
                  type="text"
                  v-model="modalForm.phone"
                  placeholder="e.g. 9825012345"
                  class="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">PAN Number</label>
                <input
                  type="text"
                  v-model="modalForm.pan"
                  placeholder="e.g. ABCDE1234F"
                  class="w-full px-3 py-2 text-xs font-mono uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
            </div>
          </template>

          <!-- 2. Vendors (Transporters) Form -->
          <template v-else-if="masterType === 'vendors'">
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Transporter / Vendor Name *</label>
              <input
                type="text"
                v-model="modalForm.name"
                required
                placeholder="e.g. Sharma Roadways"
                class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Short Code</label>
                <input
                  type="text"
                  v-model="modalForm.code"
                  placeholder="e.g. SRR"
                  class="w-full px-3 py-2 text-xs uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 font-mono"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">PAN Number</label>
                <input
                  type="text"
                  v-model="modalForm.pan"
                  placeholder="e.g. ABCDE1234F"
                  class="w-full px-3 py-2 text-xs font-mono uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Contact Phone</label>
              <input
                type="text"
                v-model="modalForm.phone"
                placeholder="e.g. 9812345678"
                class="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </template>

          <!-- 3. Vehicle Types Form -->
          <template v-else-if="masterType === 'vehicle-types'">
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Vehicle Type / Category Name *</label>
              <input
                type="text"
                v-model="modalForm.name"
                required
                placeholder="e.g. 32 FT Multi-Axle, 20 FT Container"
                class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Default Capacity (Metric Tons)</label>
              <input
                type="number"
                step="0.1"
                v-model.number="modalForm.capacity_tons"
                placeholder="e.g. 15.0"
                class="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </template>

          <!-- 4. Vehicles Form -->
          <template v-else-if="masterType === 'vehicles'">
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Vehicle Registration No. *</label>
              <input
                type="text"
                v-model="modalForm.reg_no"
                required
                placeholder="e.g. HR 38 W 8905"
                class="w-full px-3 py-2 text-xs font-mono uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 font-bold"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Vehicle Type</label>
                <input
                  type="text"
                  v-model="modalForm.vehicle_type"
                  placeholder="e.g. 32 FT MXL"
                  class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Capacity (MT)</label>
                <input
                  type="number"
                  step="0.1"
                  v-model.number="modalForm.capacity_tons"
                  placeholder="e.g. 15.0"
                  class="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Default Vendor / Owner</label>
              <input
                type="text"
                v-model="modalForm.owner"
                placeholder="e.g. Sharma Roadways"
                class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </template>

          <!-- 5. Locations Form -->
          <template v-else-if="masterType === 'locations'">
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Location / Hub Name *</label>
              <input
                type="text"
                v-model="modalForm.name"
                required
                placeholder="e.g. Vapi Hub, Silvassa Depot"
                class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Code</label>
                <input
                  type="text"
                  v-model="modalForm.code"
                  placeholder="e.g. VAP"
                  class="w-full px-3 py-2 text-xs uppercase font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Type</label>
                <select
                  v-model="modalForm.location_type"
                  class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                >
                  <option value="City">City</option>
                  <option value="Hub">Hub</option>
                  <option value="Warehouse">Warehouse</option>
                  <option value="Branch">Branch</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">City</label>
                <input
                  type="text"
                  v-model="modalForm.city"
                  placeholder="e.g. Vapi"
                  class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">State</label>
                <input
                  type="text"
                  v-model="modalForm.state"
                  placeholder="e.g. Gujarat"
                  class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
            </div>
          </template>

          <!-- 6. Lanes Form -->
          <template v-else-if="masterType === 'lanes'">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Origin *</label>
                <input
                  type="text"
                  v-model="modalForm.origin"
                  required
                  placeholder="e.g. Silvassa"
                  class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Destination *</label>
                <input
                  type="text"
                  v-model="modalForm.destination"
                  required
                  placeholder="e.g. Ghaziabad"
                  class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 mb-1">Lane Name (optional, defaults to Origin → Destination)</label>
              <input
                type="text"
                v-model="modalForm.name"
                placeholder="e.g. Silvassa - Ghaziabad Express"
                class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Distance (KM)</label>
                <input
                  type="number"
                  v-model.number="modalForm.distance_km"
                  placeholder="e.g. 1320"
                  class="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 mb-1">Standard Transit (Days)</label>
                <input
                  type="number"
                  v-model.number="modalForm.transit_days"
                  placeholder="e.g. 4"
                  class="w-full px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
                />
              </div>
            </div>
          </template>

          <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              @click="showModal = false"
              class="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-700 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-bold text-white transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ saving ? 'Saving...' : `Save ${singularName}` }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Plus,
  Search,
  Users,
  Building2,
  Layers,
  Truck,
  MapPin,
  Route,
} from '@lucide/vue'
import api from '../services/api'

const route = useRoute()

const masterType = computed(() => {
  const p = route.path
  if (p.includes('customers')) return 'customers'
  if (p.includes('vendors') || p.includes('transporters')) return 'vendors'
  if (p.includes('vehicle-types')) return 'vehicle-types'
  if (p.includes('vehicles')) return 'vehicles'
  if (p.includes('locations')) return 'locations'
  if (p.includes('lanes')) return 'lanes'
  return 'customers'
})

const masterTabs = [
  { type: 'customers', label: 'Customers', path: '/masters/customers', icon: Users, count: null },
  { type: 'vendors', label: 'Vendors (Owners)', path: '/masters/vendors', icon: Building2, count: null },
  { type: 'vehicle-types', label: 'Vehicle Types', path: '/masters/vehicle-types', icon: Layers, count: null },
  { type: 'vehicles', label: 'Vehicles (Lorries)', path: '/masters/vehicles', icon: Truck, count: null },
  { type: 'locations', label: 'Locations', path: '/masters/locations', icon: MapPin, count: null },
  { type: 'lanes', label: 'Lanes (Routes)', path: '/masters/lanes', icon: Route, count: null },
]

const title = computed(() => {
  switch (masterType.value) {
    case 'customers': return 'Customers (Consignors)'
    case 'vendors': return 'Vendors (Lorry Owners & Transporters)'
    case 'vehicle-types': return 'Vehicle Types & Configurations'
    case 'vehicles': return 'Vehicles (Lorries)'
    case 'locations': return 'Locations (Hubs & Stations)'
    case 'lanes': return 'Transit Lanes (Routes)'
    default: return 'Master Directory'
  }
})

const singularName = computed(() => {
  switch (masterType.value) {
    case 'customers': return 'Customer'
    case 'vendors': return 'Vendor'
    case 'vehicle-types': return 'Vehicle Type'
    case 'vehicles': return 'Vehicle'
    case 'locations': return 'Location'
    case 'lanes': return 'Lane'
    default: return 'Item'
  }
})

const currentIcon = computed(() => {
  switch (masterType.value) {
    case 'customers': return Users
    case 'vendors': return Building2
    case 'vehicle-types': return Layers
    case 'vehicles': return Truck
    case 'locations': return MapPin
    case 'lanes': return Route
    default: return Users
  }
})

const items = ref([])
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const showModal = ref(false)

const modalForm = ref({
  name: '',
  code: '',
  city: '',
  state: '',
  phone: '',
  pan: '',
  gstin: '',
  reg_no: '',
  owner: '',
  vehicle_type: '',
  capacity_tons: null,
  location_type: 'City',
  origin: '',
  destination: '',
  distance_km: null,
  transit_days: null,
})

let searchTimer = null

function openAddModal() {
  modalForm.value = {
    name: '',
    code: '',
    city: '',
    state: '',
    phone: '',
    pan: '',
    gstin: '',
    reg_no: '',
    owner: '',
    vehicle_type: '',
    capacity_tons: null,
    location_type: 'City',
    origin: '',
    destination: '',
    distance_km: null,
    transit_days: null,
  }
  showModal.value = true
}

async function loadData() {
  loading.value = true
  try {
    let res
    const q = searchQuery.value.trim()
    switch (masterType.value) {
      case 'customers':
        res = await api.getCustomers(q)
        break
      case 'vendors':
        res = await api.getVendors(q)
        break
      case 'vehicle-types':
        res = await api.getVehicleTypes(q)
        break
      case 'vehicles':
        res = await api.getVehicles(q)
        break
      case 'locations':
        res = await api.getLocations(q)
        break
      case 'lanes':
        res = await api.getLanes(q)
        break
    }
    items.value = res?.data || []
  } catch (err) {
    console.error('Failed to load master data:', err)
  } finally {
    loading.value = false
  }
}

function debounceSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadData()
  }, 300)
}

async function createMaster() {
  saving.value = true
  try {
    switch (masterType.value) {
      case 'customers':
        await api.createCustomer(modalForm.value)
        break
      case 'vendors':
        await api.createVendor(modalForm.value)
        break
      case 'vehicle-types':
        await api.createVehicleType(modalForm.value)
        break
      case 'vehicles':
        await api.createVehicle(modalForm.value)
        break
      case 'locations':
        await api.createLocation(modalForm.value)
        break
      case 'lanes':
        await api.createLane(modalForm.value)
        break
    }
    showModal.value = false
    loadData()
  } catch (err) {
    alert(err.response?.data?.error || 'Failed to create record')
  } finally {
    saving.value = false
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
