<template>
  <div class="min-h-screen bg-slate-50 flex">
    <!-- Sidebar Navigation -->
    <aside
      class="fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-slate-200 flex flex-col justify-between transition-transform duration-300 lg:translate-x-0"
      :class="isMobileOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div>
        <!-- Brand Header -->
        <div class="h-16 px-6 border-b border-slate-100 flex items-center justify-between">
          <router-link to="/" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <Truck class="w-5 h-5" />
            </div>
            <div>
              <div class="font-black text-sm tracking-tight text-slate-900 group-hover:text-blue-600 transition-colors">
                NDBT Transport
              </div>
              <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                TMS Cloud Portal
              </div>
            </div>
          </router-link>

          <button
            @click="isMobileOpen = false"
            class="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Navigation Links -->
        <div class="px-4 py-4 space-y-6 overflow-y-auto max-h-[calc(100vh-140px)]">
          <!-- Command Center -->
          <div>
            <div class="px-3 text-[10px] font-black uppercase tracking-wider text-slate-400 mb-2">
              Command Center
            </div>
            <router-link
              to="/"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
              :class="isCurrentRoute('/') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
            >
              <LayoutDashboard class="w-4 h-4" />
              <span>Executive Dashboard</span>
            </router-link>
          </div>

          <!-- Operations -->
          <div>
            <div class="px-3 text-[10px] font-black uppercase tracking-wider text-slate-400 mb-2">
              Operations
            </div>
            <div class="space-y-1">
              <router-link
                to="/trips"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/trips') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <Truck class="w-4 h-4" />
                <span>Trip Register (LR)</span>
              </router-link>

              <router-link
                to="/trips/new"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors text-emerald-700 bg-emerald-50/60 hover:bg-emerald-100/70 border border-emerald-200/50"
              >
                <Plus class="w-4 h-4 text-emerald-600" />
                <span>Book New Trip (LR)</span>
              </router-link>
            </div>
          </div>

          <!-- Reports & Analytics -->
          <div>
            <div class="px-3 text-[10px] font-black uppercase tracking-wider text-slate-400 mb-2">
              Reports & Ledgers
            </div>
            <div class="space-y-1">
              <router-link
                to="/reports/party-outstanding"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/reports/party-outstanding') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <Receipt class="w-4 h-4" />
                <span>Party Outstanding</span>
              </router-link>

              <router-link
                to="/reports/transporter-payable"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/reports/transporter-payable') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <Wallet class="w-4 h-4" />
                <span>Transporter Payable</span>
              </router-link>

              <router-link
                to="/reports/tds-register"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/reports/tds-register') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <FileText class="w-4 h-4" />
                <span>TDS 194C Register</span>
              </router-link>

              <router-link
                to="/reports/monthly-summary"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/reports/monthly-summary') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <BarChart3 class="w-4 h-4" />
                <span>Monthly Summary</span>
              </router-link>

              <router-link
                to="/reports/pending-operations"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/reports/pending-operations') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <AlertTriangle class="w-4 h-4 text-amber-500" />
                <span>Operational Attention</span>
              </router-link>
            </div>
          </div>

          <!-- Master Data -->
          <div>
            <div class="px-3 text-[10px] font-black uppercase tracking-wider text-slate-400 mb-2">
              Master Registers
            </div>
            <div class="space-y-1">
              <router-link
                to="/masters/customers"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/masters/customers') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <Users class="w-4 h-4" />
                <span>Customers (Consignors)</span>
              </router-link>

              <router-link
                to="/masters/transporters"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/masters/transporters') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <Building2 class="w-4 h-4" />
                <span>Transporters / Owners</span>
              </router-link>

              <router-link
                to="/masters/vehicles"
                class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-bold transition-colors"
                :class="isCurrentRoute('/masters/vehicles') ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              >
                <Truck class="w-4 h-4" />
                <span>Vehicles (Lorries)</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Profile & Admin Link -->
      <div class="p-4 border-t border-slate-100 bg-slate-50/50">
        <a
          href="/admin/"
          target="_blank"
          class="flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-blue-600 hover:bg-white border border-slate-200/80 mb-3 transition-colors shadow-2xs"
        >
          <span class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            Django Admin Portal
          </span>
          <ExternalLink class="w-3.5 h-3.5 text-slate-400" />
        </a>

        <div class="flex items-center gap-3 px-2">
          <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-black text-xs flex items-center justify-center">
            NV
          </div>
          <div class="overflow-hidden">
            <div class="text-xs font-bold text-slate-900 truncate">Satbir & Nitesh</div>
            <div class="text-[10px] text-slate-400 truncate">NDBT Transport Admin</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Mobile Overlay -->
    <div
      v-if="isMobileOpen"
      @click="isMobileOpen = false"
      class="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
    ></div>

    <!-- Main Content Area -->
    <div class="flex-1 lg:pl-72 flex flex-col min-w-0">
      <!-- Top Navbar -->
      <header class="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-30">
        <div class="flex items-center gap-4">
          <button
            @click="isMobileOpen = true"
            class="lg:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100"
          >
            <Menu class="w-5 h-5" />
          </button>

          <!-- Search Bar -->
          <div class="relative w-64 md:w-80">
            <Search class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              v-model="globalSearch"
              @keyup.enter="handleSearch"
              placeholder="Search LR, vehicle, party..."
              class="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-100 hover:bg-slate-100/80 focus:bg-white border border-transparent focus:border-blue-500 rounded-xl outline-hidden transition-all text-slate-800 placeholder-slate-400"
            />
          </div>
        </div>

        <div class="flex items-center gap-3">
          <div class="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200/60 text-blue-700 text-xs font-bold">
            <span class="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
            FY 2026-27 Active
          </div>

          <router-link
            to="/trips/new"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-sm shadow-blue-500/20"
          >
            <Plus class="w-4 h-4" />
            <span class="hidden sm:inline">New Trip</span>
          </router-link>
        </div>
      </header>

      <!-- Page Outlet -->
      <main class="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Truck,
  LayoutDashboard,
  Receipt,
  Wallet,
  FileText,
  BarChart3,
  AlertTriangle,
  Users,
  Building2,
  ExternalLink,
  Search,
  Plus,
  Menu,
  X,
} from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const isMobileOpen = ref(false)
const globalSearch = ref('')

function isCurrentRoute(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function handleSearch() {
  if (globalSearch.value.trim()) {
    router.push({ path: '/trips', query: { q: globalSearch.value.trim() } })
  }
}
</script>
