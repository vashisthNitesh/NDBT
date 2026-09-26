<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <!-- Header Row -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <router-link to="/trips" class="text-xs font-bold text-slate-500 hover:text-blue-600 flex items-center gap-1">
            <ArrowLeft class="w-3.5 h-3.5" />
            <span>Trip Register</span>
          </router-link>
          <span class="text-slate-300">/</span>
          <span class="text-xs font-bold text-blue-600">Lorry Loading Slip</span>
        </div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          <span>Lorry Loading Slip Generator</span>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-100 text-blue-800">
            PDF & Print
          </span>
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Generate, edit, and print official NDBT lorry loading slips and transport challans in authentic format.
        </p>
      </div>

      <!-- Action Buttons Row -->
      <div class="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          @click="loadSampleReceipt"
          class="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors"
        >
          Load Photo Sample
        </button>

        <button
          type="button"
          @click="printSlip"
          class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold transition-colors shadow-sm"
        >
          <Printer class="w-4 h-4" />
          <span>Print Slip</span>
        </button>

        <button
          type="button"
          @click="downloadPdf"
          :disabled="isGeneratingPdf"
          class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-sm shadow-blue-500/20 disabled:opacity-50"
        >
          <Download class="w-4 h-4" />
          <span>{{ isGeneratingPdf ? 'Generating PDF...' : 'Download PDF' }}</span>
        </button>
      </div>
    </div>

    <!-- Alert / Status -->
    <div
      v-if="statusMsg"
      class="p-3.5 rounded-xl text-xs font-bold"
      :class="statusSuccess ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'"
    >
      {{ statusMsg }}
    </div>

    <!-- Mobile View Mode Toggle (Edit vs Preview) -->
    <div class="lg:hidden flex items-center p-1 bg-slate-200/80 rounded-xl">
      <button
        type="button"
        @click="mobileView = 'edit'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="mobileView === 'edit' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'"
      >
        ✏️ Edit Slip Data
      </button>
      <button
        type="button"
        @click="mobileView = 'preview'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="mobileView === 'preview' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'"
      >
        📄 Slip Preview
      </button>
    </div>

    <!-- Main Content: Editor & Live Preview Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Left Column: Form Editor (5 cols on lg) -->
      <div
        class="lg:col-span-5 space-y-4"
        :class="mobileView === 'preview' ? 'hidden lg:block' : 'block'"
      >
        <!-- 1. Quick Trip Selector -->
        <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-black uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <Search class="w-3.5 h-3.5 text-blue-600" />
              <span>Auto-Fill From Existing Trip (LR)</span>
            </label>
            <span v-if="selectedTripId" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              Trip #{{ slip.slip_no }} Loaded
            </span>
          </div>

          <div class="relative">
            <input
              type="text"
              v-model="tripSearchQuery"
              @input="searchTrips"
              @focus="showTripDropdown = true"
              placeholder="Type LR No, vehicle (e.g. 6907, HR61)..."
              class="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
            />

            <!-- Dropdown Results -->
            <div
              v-if="showTripDropdown && searchResults.length > 0"
              class="absolute z-20 left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg max-h-56 overflow-y-auto divide-y divide-slate-100"
            >
              <div
                v-for="t in searchResults"
                :key="t.id"
                @click="selectTrip(t)"
                class="p-2.5 hover:bg-blue-50 cursor-pointer text-xs transition-colors"
              >
                <div class="flex items-center justify-between">
                  <span class="font-black text-blue-600 font-mono">LR #{{ t.lr_no }}</span>
                  <span class="font-mono text-[11px] font-bold bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">{{ t.vehicle }}</span>
                </div>
                <div class="text-[11px] text-slate-600 mt-0.5 truncate">
                  {{ t.consignor }} • {{ t.origin }} &rarr; {{ t.destination }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Slip Field Controls -->
        <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 class="text-xs font-black uppercase tracking-wider text-slate-900">
              Slip Information Details
            </h3>
            <button
              type="button"
              @click="resetSlip"
              class="text-[11px] font-bold text-slate-400 hover:text-rose-600"
            >
              Clear Fields
            </button>
          </div>

          <!-- Slip No & Date -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Slip / LR No. <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                v-model="slip.slip_no"
                placeholder="6907"
                class="w-full px-3 py-1.5 text-xs font-mono font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Date <span class="text-rose-500">*</span>
              </label>
              <input
                type="date"
                v-model="slip.date"
                class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Customer (To, M/s.) -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                To, M/s. (Customer) <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                v-model="slip.customer_name"
                placeholder="R. J. Logistics"
                class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Customer City / Branch
              </label>
              <input
                type="text"
                v-model="slip.customer_city"
                placeholder="Vapi"
                class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Vehicle / Truck No & Owner -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Motor Truck No. <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                v-model="slip.truck_no"
                placeholder="HR 61 F 8822"
                class="w-full px-3 py-1.5 text-xs font-mono uppercase font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Owner's Name <span class="text-rose-500">*</span>
              </label>
              <input
                type="text"
                v-model="slip.owner_name"
                placeholder="Jamnagiri"
                class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Owner Address -->
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
              Owner Address
            </label>
            <input
              type="text"
              v-model="slip.address"
              placeholder="e.g. Vapi / Valsad"
              class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
            />
          </div>

          <!-- Driver Name & License No -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Driver's Name
              </label>
              <input
                type="text"
                v-model="slip.driver_name"
                placeholder="Driver Name"
                class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Lic No.
              </label>
              <input
                type="text"
                v-model="slip.lic_no"
                placeholder="DL-XXXX"
                class="w-full px-3 py-1.5 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Goods Particulars & Weight -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Goods Particulars
              </label>
              <input
                type="text"
                v-model="slip.goods_particulars"
                placeholder="P. Goods"
                class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Weight
              </label>
              <input
                type="text"
                v-model="slip.weight"
                placeholder="7 mt."
                class="w-full px-3 py-1.5 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Destination & Route -->
          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                From
              </label>
              <input
                type="text"
                v-model="slip.origin"
                placeholder="Umbergaon"
                class="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                To
              </label>
              <input
                type="text"
                v-model="slip.to_place"
                placeholder="Ghaziabad"
                class="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Destination
              </label>
              <input
                type="text"
                v-model="slip.destination"
                placeholder="Ghaziabad"
                class="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Financials: Rate, Advance, Balance -->
          <div class="grid grid-cols-3 gap-2 pt-1 border-t border-slate-100">
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Rate / Freight (₹)
              </label>
              <input
                type="number"
                v-model.number="slip.rate"
                @input="autoCalculateBalance"
                placeholder="61000"
                class="w-full px-2.5 py-1.5 text-xs font-mono font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Advance (₹)
              </label>
              <input
                type="number"
                v-model.number="slip.advance"
                @input="autoCalculateBalance"
                placeholder="59000"
                class="w-full px-2.5 py-1.5 text-xs font-mono font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                Balance (₹)
              </label>
              <input
                type="number"
                v-model.number="slip.balance"
                placeholder="2000"
                class="w-full px-2.5 py-1.5 text-xs font-mono font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <!-- 5. Signatory Authority -->
        <div class="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm">
          <label class="block text-xs font-black uppercase tracking-wider text-slate-700 mb-2">
            Authorised Signatory Authority
          </label>
          <select
            v-model="slip.signatory"
            class="w-full px-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 text-slate-800 cursor-pointer"
          >
            <option value="Dharambir Vashisth">Dharambir Vashisth</option>
            <option value="Satbir Vashisth">Satbir Vashisth</option>
          </select>
        </div>
      </div>

      <!-- Right Column: Live Visual Slip Preview (7 cols on lg) -->
      <div
        class="lg:col-span-7 flex flex-col items-center"
        :class="mobileView === 'edit' ? 'hidden lg:flex' : 'flex'"
      >
        <!-- Preview Header Bar (Single, non-duplicated) -->
        <div class="w-full max-w-[760px] mb-3 flex items-center justify-between text-xs text-slate-500">
          <div class="flex items-center gap-1.5 font-bold">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Live Authentic Print Preview</span>
          </div>
          <span class="text-[11px] text-slate-400 font-medium">Updates live with your changes</span>
        </div>

        <!-- The Slip Document Component -->
        <div class="w-full flex justify-center overflow-x-auto p-1">
          <LorrySlipDocument :slip-data="slip" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Printer, Download, Search } from '@lucide/vue'
import html2pdf from 'html2pdf.js'
import api from '../services/api'
import LorrySlipDocument from '../components/common/LorrySlipDocument.vue'

const route = useRoute()

const mobileView = ref('edit')
const isGeneratingPdf = ref(false)
const statusMsg = ref('')
const statusSuccess = ref(true)

const tripSearchQuery = ref('')
const searchResults = ref([])
const showTripDropdown = ref(false)
const selectedTripId = ref(null)

const slip = reactive({
  slip_no: '6907',
  date: new Date().toISOString().split('T')[0],
  customer_name: 'R. J. Logistics',
  customer_city: 'Vapi',
  truck_no: 'HR 61 F 8822',
  owner_name: 'Jamnagiri',
  address: '',
  driver_name: '',
  lic_no: '',
  goods_particulars: 'P. Goods',
  weight: '7 mt.',
  destination: 'Ghaziabad',
  origin: 'Umbergaon',
  to_place: 'Ghaziabad',
  rate: 61000,
  advance: 59000,
  balance: 2000,
  signatory: 'Dharambir Vashisth',
})

function autoCalculateBalance() {
  if (slip.rate !== null && slip.rate !== undefined && slip.advance !== null && slip.advance !== undefined) {
    slip.balance = Number(slip.rate) - Number(slip.advance)
  }
}

function loadSampleReceipt() {
  slip.slip_no = '6907'
  slip.date = '2026-09-23'
  slip.customer_name = 'R. J. Logistics'
  slip.customer_city = 'Vapi'
  slip.truck_no = 'HR 61 F 8822'
  slip.owner_name = 'Jamnagiri'
  slip.address = ''
  slip.driver_name = ''
  slip.lic_no = ''
  slip.goods_particulars = 'P. Goods'
  slip.weight = '7 mt.'
  slip.destination = 'Ghaziabad'
  slip.origin = 'Umbergaon'
  slip.to_place = 'Ghaziabad'
  slip.rate = 61000
  slip.advance = 59000
  slip.balance = 2000
  slip.signatory = 'Dharambir Vashisth'
  statusMsg.value = 'Sample receipt data from the physical challan photo loaded!'
  statusSuccess.value = true
  setTimeout(() => { statusMsg.value = '' }, 4000)
}

function resetSlip() {
  slip.slip_no = ''
  slip.date = new Date().toISOString().split('T')[0]
  slip.customer_name = ''
  slip.customer_city = ''
  slip.truck_no = ''
  slip.owner_name = ''
  slip.address = ''
  slip.driver_name = ''
  slip.lic_no = ''
  slip.goods_particulars = 'P. Goods'
  slip.weight = ''
  slip.destination = ''
  slip.origin = ''
  slip.to_place = ''
  slip.rate = 0
  slip.advance = 0
  slip.balance = 0
  selectedTripId.value = null
  tripSearchQuery.value = ''
}

let searchTimer = null
function searchTrips() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!tripSearchQuery.value.trim()) {
      searchResults.value = []
      return
    }
    try {
      const res = await api.getTrips({ q: tripSearchQuery.value.trim(), page_size: 8 })
      searchResults.value = res.data.results || []
      showTripDropdown.value = true
    } catch (err) {
      console.error('Trip search failed', err)
    }
  }, 250)
}

function selectTrip(t) {
  selectedTripId.value = t.id
  slip.slip_no = t.lr_no
  slip.date = t.booking_date || new Date().toISOString().split('T')[0]
  slip.customer_name = t.consignor || ''
  slip.customer_city = ''
  slip.truck_no = t.vehicle || ''
  slip.owner_name = t.transporter || ''
  slip.address = ''
  slip.driver_name = ''
  slip.lic_no = ''
  slip.goods_particulars = 'P. Goods'
  slip.weight = ''
  slip.destination = t.destination || ''
  slip.origin = t.origin || ''
  slip.to_place = t.destination || ''
  slip.rate = t.freight ? Number(t.freight) : 0
  slip.advance = t.advance ? Number(t.advance) : 0
  slip.balance = t.balance ? Number(t.balance) : (slip.rate - slip.advance)
  
  showTripDropdown.value = false
  tripSearchQuery.value = `LR #${t.lr_no} - ${t.vehicle}`
  statusMsg.value = `Trip #${t.lr_no} data auto-filled into slip!`
  statusSuccess.value = true
  setTimeout(() => { statusMsg.value = '' }, 3500)
}

async function loadTripById(id) {
  try {
    const res = await api.getTrip(id)
    const t = res.data
    selectTrip({
      id: t.id,
      lr_no: t.lr_no,
      booking_date: t.booking_date,
      consignor: t.consignor,
      vehicle: t.vehicle,
      transporter: t.transporter,
      destination: t.destination,
      origin: t.origin,
      freight: t.freight,
      advance: t.advance,
      balance: t.balance,
    })
  } catch (err) {
    statusMsg.value = 'Failed to load specified trip'
    statusSuccess.value = false
  }
}

function printSlip() {
  const printArea = document.getElementById('lorry-slip-print-area')
  if (!printArea) {
    window.print()
    return
  }

  // Create or reuse hidden print iframe for isolated, clean printing of ONLY the slip with current data
  let iframe = document.getElementById('slip-print-frame')
  if (!iframe) {
    iframe = document.createElement('iframe')
    iframe.id = 'slip-print-frame'
    iframe.style.position = 'fixed'
    iframe.style.right = '0'
    iframe.style.bottom = '0'
    iframe.style.width = '0'
    iframe.style.height = '0'
    iframe.style.border = '0'
    document.body.appendChild(iframe)
  }

  const doc = iframe.contentWindow.document
  doc.open()
  doc.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>NDBT Slip #${slip.slip_no || ''}</title>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="/static/dist/assets/index.css" />
        <style>
          @page { size: A4 portrait; margin: 8mm; }
          body { margin: 0; padding: 0; background: #fff !important; font-family: system-ui, -apple-system, sans-serif; }
          .lorry-slip-wrapper { width: 100% !important; display: flex !important; justify-content: center !important; }
          .lorry-slip-card {
            width: 100% !important;
            max-width: 100% !important;
            border: none !important;
            box-shadow: none !important;
            margin: 0 auto;
            padding: 16px !important;
            background: #ffffff !important;
            color: #0f172a !important;
          }
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        </style>
      </head>
      <body>
        ${printArea.outerHTML}
      </body>
    </html>
  `)
  doc.close()

  setTimeout(() => {
    iframe.contentWindow.focus()
    iframe.contentWindow.print()
  }, 350)
}

async function downloadPdf() {
  isGeneratingPdf.value = true
  statusMsg.value = ''

  try {
    // 1. Primary: Download official crisp vector PDF generated directly from current form fields!
    await api.downloadCustomSlipPdf(slip)
    statusMsg.value = `PDF for Slip #${slip.slip_no} generated and downloaded with your latest data!`
    statusSuccess.value = true
  } catch (backendErr) {
    console.warn('Backend PDF download error, attempting client-side fallback:', backendErr)
    const element = document.getElementById('lorry-slip-print-area')
    if (element) {
      const opt = {
        margin: [8, 8, 8, 8],
        filename: `NDBT_Slip_${slip.slip_no || 'Document'}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      }
      await html2pdf().set(opt).from(element).save()
      statusMsg.value = `PDF for Slip #${slip.slip_no} downloaded successfully!`
      statusSuccess.value = true
    } else {
      statusMsg.value = 'Could not generate PDF. Please use the Print Slip option.'
      statusSuccess.value = false
    }
  } finally {
    isGeneratingPdf.value = false
    setTimeout(() => { statusMsg.value = '' }, 4000)
  }
}

onMounted(() => {
  if (route.query.trip) {
    loadTripById(route.query.trip)
  }
})

watch(() => route.query.trip, (newId) => {
  if (newId) loadTripById(newId)
})
</script>
