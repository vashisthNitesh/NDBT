<template>
  <div class="lorry-slip-wrapper flex justify-center w-full">
    <!-- Physical Document Container: Clean White Paper Format Without Outer Border -->
    <div
      id="lorry-slip-print-area"
      class="lorry-slip-card bg-white text-slate-800 p-6 sm:p-8 w-full max-w-[760px] font-sans relative select-text"
      style="box-sizing: border-box;"
    >
      <!-- Top Sacred Header: Centered Lord Ganesha Image with Hindi Salutation -->
      <div class="flex flex-col items-center justify-center pb-2">
        <img
          :src="ganeshaHeaderImg"
          alt="Lord Ganesha - श्री गणेशाय नमः"
          class="w-16 sm:w-20 h-auto object-contain"
        />
      </div>

      <!-- Top Contact & Address Bar: Subtle Hairlines, No Grey Fill -->
      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pt-2 pb-3 border-b border-slate-200 text-xs">
        <!-- Left: Office Address (No 'Booking Station' label) -->
        <div class="text-left text-[10.5px] sm:text-[11px] text-slate-600 leading-snug">
          <div class="font-bold text-slate-900">Shop No. 212, 2nd Floor, Sai Leela Arcade No. 2,</div>
          <div>Opp. Hyundai Showroom, Near Big Bazar, N.H. No. 8,</div>
          <div>Morai Fatak, Vapi - 396 191. Dist. Valsad (Gujarat)</div>
        </div>

        <!-- Right: Mobile Numbers Row-Wise -->
        <div class="text-left sm:text-right text-[11px] text-slate-800 space-y-0.5 shrink-0">
          <div class="flex items-center sm:justify-end gap-1.5 font-mono">
            <span class="text-[10px] text-slate-500 font-sans font-medium">Mob:</span>
            <span class="font-semibold text-slate-900">+91 98795 86221</span>
          </div>
          <div class="flex items-center sm:justify-end gap-1.5 font-mono">
            <span class="text-[10px] text-slate-500 font-sans font-medium">Mob:</span>
            <span class="font-semibold text-slate-900">+91 93769 07046</span>
          </div>
        </div>
      </div>

      <!-- Main Business Title & Branding -->
      <div class="text-center pt-3 pb-2">
        <h2 class="text-xl sm:text-2xl md:text-[25px] font-black tracking-tight text-slate-900 uppercase font-sans leading-tight">
          NEW DELHI BOMBAY TRANSPORT
        </h2>
        <div class="text-[10.5px] sm:text-xs font-semibold tracking-wider text-slate-600 uppercase mt-0.5">
          FLEET OWNERS, TRANSPORT CONTRACTORS & COMMISSION AGENTS
        </div>
      </div>

      <!-- Route Coverage Strip: Clean Hairlines, Pure White -->
      <div class="border-y border-slate-200 py-1.5 px-2 text-center my-2 text-[9.5px] sm:text-[10.5px] font-medium text-slate-700 uppercase tracking-tight">
        Daily Fleet Service : DELHI • HARYANA • PUNJAB • RAJASTHAN • HIMACHAL • U.P. • PAN-INDIA FULL & PART LOAD
      </div>

      <!-- Document Metadata Bar: Minimalist Clean Header, No Dark/Grey Box -->
      <div class="border border-slate-200 bg-white px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 my-3 text-xs">
        <div class="font-bold uppercase tracking-wider text-slate-900 text-xs sm:text-sm">
          LORRY LOADING SLIP <span class="text-slate-500 font-normal text-xs">(CHALLAN)</span>
        </div>
        <div class="flex items-center gap-6 flex-wrap">
          <div class="flex items-baseline gap-1.5">
            <span class="text-[10.5px] font-medium uppercase text-slate-500">Challan No:</span>
            <span class="font-bold font-mono text-sm sm:text-base text-blue-900">
              #{{ slipData.slip_no || slipData.lr_no || '______' }}
            </span>
          </div>
          <div class="flex items-baseline gap-1.5">
            <span class="text-[10.5px] font-medium uppercase text-slate-500">Date:</span>
            <span class="font-semibold font-mono text-xs sm:text-sm text-slate-900">
              {{ formattedDate || '___/___/____' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Customer / Consignor Dispatch Agreement Box -->
      <div class="border border-slate-200 bg-white p-3.5 mb-3 text-xs">
        <div class="flex items-baseline gap-2 mb-1.5">
          <span class="font-bold text-slate-500 uppercase tracking-wider text-[11px] shrink-0">To, M/s. (Consignor):</span>
          <span class="font-bold text-sm text-slate-900 uppercase tracking-wide">
            {{ formattedCustomer }}
          </span>
        </div>
        <div class="text-[11px] text-slate-600 leading-relaxed border-t border-slate-100 pt-2">
          We are sending herewith Motor Truck No.
          <strong class="font-bold text-slate-900 uppercase font-mono px-1.5 py-0.5 border border-slate-200 text-xs">
            {{ slipData.truck_no || slipData.vehicle || '_________________' }}
          </strong>
          as per your booking instruction subject to standard terms and conditions. Please inspect vehicle registration, fitness and permit papers before loading.
        </div>
      </div>

      <!-- Structured 2-Column Specification Matrix: Clean White Backgrounds, Subtle Hairlines -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3 text-xs">
        <!-- Column 1: Fleet & Transit Particulars -->
        <div class="border border-slate-200 bg-white overflow-hidden">
          <div class="border-b border-slate-200 text-slate-900 font-bold text-[11px] uppercase tracking-wider px-3.5 py-2">
            1. Fleet & Transit Details
          </div>
          <div class="divide-y divide-slate-100">
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Truck No:</span>
              <span class="col-span-7 font-bold font-mono text-blue-900 uppercase text-xs">
                {{ slipData.truck_no || slipData.vehicle || '-' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Fleet Owner:</span>
              <span class="col-span-7 font-semibold text-slate-900 uppercase">
                {{ slipData.owner_name || slipData.transporter || '-' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Address / Hub:</span>
              <span class="col-span-7 text-slate-700">
                {{ slipData.address || 'Vapi / Valsad' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Driver Name:</span>
              <span class="col-span-7 font-medium text-slate-800">
                {{ slipData.driver_name || '-' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Driver Lic No:</span>
              <span class="col-span-7 font-mono text-slate-800">
                {{ slipData.lic_no || '-' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Route:</span>
              <span class="col-span-7 font-semibold text-slate-900">
                {{ slipData.origin || '-' }} → {{ slipData.to_place || slipData.destination || '-' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Destination:</span>
              <span class="col-span-7 font-bold text-slate-900 uppercase">
                {{ slipData.destination || '-' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Column 2: Consignment & Commercial Terms -->
        <div class="border border-slate-200 bg-white overflow-hidden">
          <div class="border-b border-slate-200 text-slate-900 font-bold text-[11px] uppercase tracking-wider px-3.5 py-2">
            2. Commercial & Cargo Terms
          </div>
          <div class="divide-y divide-slate-100">
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Goods:</span>
              <span class="col-span-7 font-semibold text-slate-900">
                {{ slipData.goods_particulars || 'P. Goods' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Weight:</span>
              <span class="col-span-7 font-mono font-semibold text-slate-900">
                {{ slipData.weight || '-' }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Freight Rate:</span>
              <span class="col-span-7 font-mono font-semibold text-slate-900">
                {{ formatRupee(slipData.rate || slipData.freight) }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Total Freight:</span>
              <span class="col-span-7 font-mono font-semibold text-slate-900">
                {{ formatRupee(slipData.freight || slipData.rate) }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Advance Paid:</span>
              <span class="col-span-7 font-mono font-semibold text-slate-900">
                {{ formatRupee(slipData.advance) }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 font-bold text-slate-900">Balance Payable:</span>
              <span class="col-span-7 font-mono font-bold text-slate-950 text-xs sm:text-sm">
                {{ formatRupee(slipData.balance) }}
              </span>
            </div>
            <div class="grid grid-cols-12 px-3.5 py-2 items-center">
              <span class="col-span-5 text-slate-500 font-medium">Payment Terms:</span>
              <span class="col-span-7 font-medium text-slate-700">
                Subject to safe delivery
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Regulatory Terms & Signature Block: Pure White, Clean Signatures, No Dropdown on PDF -->
      <div class="border border-slate-200 bg-white p-3.5">
        <div class="grid grid-cols-1 sm:grid-cols-12 gap-4 items-end">
          <!-- Terms Left -->
          <div class="sm:col-span-7 space-y-1 text-[10px] text-slate-600 leading-tight">
            <div class="font-bold text-slate-800 uppercase tracking-wider text-[10px] mb-1">
              Terms & Operational Conditions:
            </div>
            <div class="flex items-start gap-1">
              <span class="font-semibold text-slate-700">1.</span>
              <span>We are not responsible for excess weight other than specified above.</span>
            </div>
            <div class="flex items-start gap-1">
              <span class="font-semibold text-slate-700">2.</span>
              <span>Please check truck papers (Permit, R.C. Book, Insurance, Driver Licence) before loading. Return vehicle empty if papers are not presented.</span>
            </div>
            <div class="flex items-start gap-1">
              <span class="font-semibold text-slate-700">3.</span>
              <span>All disputes are subject to Vapi (Valsad, Gujarat) jurisdiction only.</span>
            </div>
          </div>

          <!-- Signatures Right: Display Selected Signatory Name (No Dropdown on PDF) -->
          <div class="sm:col-span-5 flex flex-col justify-between text-right pt-2 sm:pt-0">
            <div>
              <div class="text-[11px] font-bold text-slate-900 uppercase tracking-wide">
                For NEW DELHI BOMBAY TRANSPORT
              </div>
              <div class="text-[9.5px] text-slate-500">
                Fleet Owners & Commission Agents
              </div>
            </div>

            <!-- Signature Line & Dynamic Signatory Name -->
            <div class="mt-8 flex flex-col items-end">
              <div class="w-44 border-b border-slate-400"></div>
              <div class="text-xs font-bold text-slate-900 uppercase tracking-wider mt-1.5 font-sans">
                ({{ signatoryName }})
              </div>
              <div class="text-[10px] font-medium text-slate-500 uppercase tracking-wider mt-0.5">
                Authorised Signatory
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ganeshaHeaderImg from '../../assets/ganesha_header.png'

const props = defineProps({
  slipData: {
    type: Object,
    default: () => ({}),
  },
})

const signatoryName = computed(() => {
  return props.slipData?.signatory || 'Dharambir Vashisth'
})

const formattedDate = computed(() => {
  const d = props.slipData?.date || props.slipData?.booking_date
  if (!d) return ''
  if (d.includes('/')) return d
  try {
    const parts = d.split('-')
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`
    }
  } catch (e) {}
  return d
})

const formattedCustomer = computed(() => {
  const name = props.slipData?.customer_name || props.slipData?.consignor || ''
  const city = props.slipData?.customer_city || ''
  if (city && !name.toLowerCase().includes(city.toLowerCase())) {
    return `${name}, ${city}`
  }
  return name || 'M/s. _________________________________'
})

function formatRupee(val) {
  if (val === undefined || val === null || val === '') return '-'
  const num = Number(val)
  if (isNaN(num)) return `₹ ${val}/-`
  return `₹ ${num.toLocaleString('en-IN')}/-`
}
</script>

<style scoped>
@media print {
  /* Hide all surrounding page chrome when printing */
  body * {
    visibility: hidden;
  }
  
  #lorry-slip-print-area,
  #lorry-slip-print-area * {
    visibility: visible;
  }

  #lorry-slip-print-area {
    position: absolute;
    left: 0;
    top: 0;
    width: 100% !important;
    max-width: 100% !important;
    box-shadow: none !important;
    border: none !important;
    padding: 16px !important;
    background: #fff !important;
    color: #0f172a !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  @page {
    size: A4 portrait;
    margin: 8mm;
  }
}
</style>
