<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 mb-1">
          <router-link to="/trips" class="text-xs font-bold text-slate-500 hover:text-blue-600 flex items-center gap-1">
            <ArrowLeft class="w-3.5 h-3.5" />
            <span>Back to Trip Register</span>
          </router-link>
        </div>
        <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight break-words">
          {{ isEditMode ? `LR #${form.lr_no} - ${form.vehicle || 'Trip Details'}` : 'Book New Trip (LR Entry)' }}
        </h1>
        <p class="text-xs text-slate-500 mt-0.5">
          {{ isEditMode ? 'Edit freight details, ledger balances, and payment milestones.' : 'Create a new transport order and calculate margins in real time.' }}
        </p>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <button
          v-if="isEditMode"
          type="button"
          @click="activeTab = 'slip'"
          class="px-3.5 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold border border-indigo-200 transition-colors flex items-center gap-1.5"
        >
          <Printer class="w-3.5 h-3.5" />
          <span>Lorry Slip (PDF)</span>
        </button>

        <button
          v-if="isEditMode"
          type="button"
          @click="deleteTrip"
          class="px-3.5 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold border border-rose-200 transition-colors"
        >
          Delete Trip
        </button>

        <button
          type="button"
          @click="saveTrip"
          :disabled="saving"
          class="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-sm shadow-blue-500/20 disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : (isEditMode ? 'Save Changes' : 'Create Trip (LR)') }}
        </button>
      </div>
    </div>

    <!-- Alert / Notice message -->
    <div v-if="alertMessage" class="p-4 rounded-xl text-xs font-semibold" :class="alertSuccess ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'">
      {{ alertMessage }}
    </div>

    <!-- Live 3-Deck Margin Engine -->
    <LiveMarginCalculator
      :freight="Number(form.freight) || 0"
      :advance="Number(form.advance) || 0"
      :commission="Number(form.commission) || 0"
      :lorry-advance="Number(form.lorry_advance) || 0"
      :tds="Number(form.tds) || 0"
      :labour="Number(form.labour) || 0"
      :holding-days="Number(form.holding_days) || 0"
      :holding-rate="Number(form.holding_rate) || 0"
      :holding-manual="Number(form.holding) || 0"
      @update:tds="form.tds = $event"
    />

    <!-- Tabbed Navigation -->
    <div class="border-b border-slate-200 flex items-center gap-2 overflow-x-auto">
      <button
        type="button"
        @click="activeTab = 'booking'"
        class="pb-3 px-4 text-xs font-bold transition-all border-b-2 whitespace-nowrap"
        :class="activeTab === 'booking' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
      >
        📋 Booking & Logistics
      </button>

      <button
        type="button"
        @click="activeTab = 'financials'"
        class="pb-3 px-4 text-xs font-bold transition-all border-b-2 whitespace-nowrap"
        :class="activeTab === 'financials' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
      >
        💰 Financial Ledger & Margins
      </button>

      <button
        type="button"
        @click="activeTab = 'milestones'"
        class="pb-3 px-4 text-xs font-bold transition-all border-b-2 whitespace-nowrap"
        :class="activeTab === 'milestones' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
      >
        🚚 Settlement & Milestones
      </button>

      <button
        v-if="isEditMode"
        type="button"
        @click="activeTab = 'receipts'"
        class="pb-3 px-4 text-xs font-bold transition-all border-b-2 whitespace-nowrap"
        :class="activeTab === 'receipts' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
      >
        💵 Customer Receipts ({{ tripData.receipts?.length || 0 }})
      </button>

      <button
        v-if="isEditMode"
        type="button"
        @click="activeTab = 'payments'"
        class="pb-3 px-4 text-xs font-bold transition-all border-b-2 whitespace-nowrap"
        :class="activeTab === 'payments' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
      >
        💳 Owner Payments ({{ tripData.owner_payments?.length || 0 }})
      </button>

      <button
        v-if="isEditMode"
        type="button"
        @click="activeTab = 'documents'"
        class="pb-3 px-4 text-xs font-bold transition-all border-b-2 whitespace-nowrap"
        :class="activeTab === 'documents' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'"
      >
        📄 POD & Documents ({{ tripData.documents?.length || 0 }})
      </button>

      <button
        v-if="isEditMode"
        type="button"
        @click="activeTab = 'slip'"
        class="pb-3 px-4 text-xs font-bold transition-all border-b-2 whitespace-nowrap flex items-center gap-1.5"
        :class="activeTab === 'slip' ? 'border-blue-600 text-blue-600 font-black' : 'border-transparent text-slate-500 hover:text-slate-800'"
      >
        <span>🎫 Lorry Slip (PDF)</span>
      </button>
    </div>

    <!-- Tab 1: Booking & Logistics -->
    <div v-show="activeTab === 'booking'" class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-5">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <!-- Date -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Booking Date <span class="text-rose-500">*</span>
          </label>
          <input
            type="date"
            v-model="form.booking_date"
            required
            class="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- LR No -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Lorry Receipt (LR) No. <span class="text-rose-500">*</span>
          </label>
          <input
            type="number"
            v-model.number="form.lr_no"
            required
            placeholder="e.g. 8909"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Consignor -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Customer / Consignor <span class="text-rose-500">*</span>
          </label>
          <input
            type="text"
            v-model="form.consignor"
            required
            placeholder="e.g. MRS or Laxmi Express"
            class="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Vehicle -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Vehicle Registration No. <span class="text-rose-500">*</span>
          </label>
          <input
            type="text"
            v-model="form.vehicle"
            required
            placeholder="e.g. HR38W-8905"
            class="w-full px-3.5 py-2 text-xs font-mono uppercase bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Transporter -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Transporter / Lorry Owner <span class="text-rose-500">*</span>
          </label>
          <input
            type="text"
            v-model="form.transporter"
            required
            placeholder="e.g. JCM or TLS"
            class="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Lane / Transit -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Transit Lane / Corridor
          </label>
          <div class="grid grid-cols-2 gap-2">
            <input
              type="text"
              v-model="form.origin"
              placeholder="Origin (e.g. Silvassa)"
              class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
            />
            <input
              type="text"
              v-model="form.destination"
              placeholder="Destination (e.g. Ghaziabad)"
              class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: Financial Ledger & Margins -->
    <div v-show="activeTab === 'financials'" class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-5">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <!-- Freight -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Contracted Freight (₹)
          </label>
          <input
            type="number"
            v-model.number="form.freight"
            placeholder="60000"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Advance Due -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Advance Due from Customer (₹)
          </label>
          <input
            type="number"
            v-model.number="form.advance"
            placeholder="40000"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Commission -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Brokerage Commission (₹)
          </label>
          <input
            type="number"
            v-model.number="form.commission"
            placeholder="1500"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Lorry Advance -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Advance Paid to Lorry Owner (₹)
          </label>
          <input
            type="number"
            v-model.number="form.lorry_advance"
            placeholder="35000"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- TDS -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            TDS Withheld (Sec 194C) (₹)
          </label>
          <input
            type="number"
            v-model.number="form.tds"
            placeholder="600"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Labour -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Hamali / Labour Charges (₹)
          </label>
          <input
            type="number"
            v-model.number="form.labour"
            placeholder="0"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Detention Days & Rate -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Detention Days
          </label>
          <input
            type="number"
            v-model.number="form.holding_days"
            placeholder="0"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Daily Detention Rate (₹)
          </label>
          <input
            type="number"
            v-model.number="form.holding_rate"
            placeholder="0"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>
      </div>
    </div>

    <!-- Tab 3: Milestones & Settlement -->
    <div v-show="activeTab === 'milestones'" class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-5">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <!-- Memo No -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Memo Number
          </label>
          <input
            type="number"
            v-model.number="form.memo_no"
            placeholder="Leave empty if pending memo"
            class="w-full px-3.5 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Unloading Date -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Unloading Date
          </label>
          <input
            type="date"
            v-model="form.unloading_date"
            class="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- Settlement Status -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Balance Settlement Status
          </label>
          <select
            v-model="form.balance_status"
            class="w-full px-3.5 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 text-slate-800"
          >
            <option value="PENDING">Pending</option>
            <option value="RECEIVED">Received</option>
            <option value="NIL">Nil / Cleared</option>
            <option value="NOT_RECEIVED">Not Received</option>
            <option value="TO_PAY">To Pay</option>
          </select>
        </div>

        <!-- Balance Received Date -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Balance Receipt Date
          </label>
          <input
            type="date"
            v-model="form.balance_received_date"
            class="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          />
        </div>

        <!-- POD Checkbox -->
        <div class="flex items-center gap-3 md:col-span-2 pt-2">
          <input
            type="checkbox"
            id="hasPod"
            v-model="form.has_pod"
            class="w-4 h-4 text-blue-600 rounded-md border-slate-300 focus:ring-blue-500"
          />
          <label for="hasPod" class="text-xs font-bold text-slate-700 cursor-pointer">
            Physical Proof of Delivery (POD) received and verified
          </label>
        </div>

        <!-- Remarks -->
        <div class="md:col-span-2">
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
            Ledger Remarks / Driver Notes
          </label>
          <textarea
            v-model="form.remarks"
            rows="3"
            placeholder="Add payment notes, driver contact, or transit remarks..."
            class="w-full px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 focus:bg-white text-slate-800"
          ></textarea>
        </div>
      </div>
    </div>

    <!-- Tab 4: Customer Receipts History -->
    <div v-show="activeTab === 'receipts'" class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-black uppercase tracking-wider text-slate-900">
            Customer Receipts History
          </h3>
          <p class="text-xs text-slate-500">Payments received against LR #{{ form.lr_no }}</p>
        </div>
        <div class="text-right">
          <span class="text-xs text-slate-500">Total Collected:</span>
          <span class="text-sm font-black text-emerald-600 font-mono-numbers block">
            {{ formatINR(tripData.advance_received_total) }}
          </span>
        </div>
      </div>

      <div v-if="!tripData.receipts || tripData.receipts.length === 0" class="py-8 text-center text-xs text-slate-400">
        No customer receipts allocated to this trip yet.
      </div>

      <div v-else class="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
        <div
          v-for="r in tripData.receipts"
          :key="r.id"
          class="p-3.5 flex items-center justify-between text-xs hover:bg-slate-50"
        >
          <div>
            <div class="font-bold text-slate-800">Payment Reference: {{ r.reference || 'N/A' }}</div>
            <div class="text-slate-500 font-medium">Mode: {{ r.mode }} • Date: {{ formatDate(r.date) }}</div>
          </div>
          <div class="text-right">
            <span class="font-black text-slate-900 font-mono-numbers text-sm">{{ formatINR(r.amount) }}</span>
            <span class="text-[10px] text-emerald-600 font-bold block uppercase">{{ r.kind }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 5: Owner Payments History -->
    <div v-show="activeTab === 'payments'" class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-black uppercase tracking-wider text-slate-900">
            Transporter Payments History
          </h3>
          <p class="text-xs text-slate-500">Payments made to lorry owner for LR #{{ form.lr_no }}</p>
        </div>
        <div class="text-right">
          <span class="text-xs text-slate-500">Total Paid:</span>
          <span class="text-sm font-black text-blue-600 font-mono-numbers block">
            {{ formatINR(tripData.owner_paid_total) }}
          </span>
        </div>
      </div>

      <div v-if="!tripData.owner_payments || tripData.owner_payments.length === 0" class="py-8 text-center text-xs text-slate-400">
        No owner payments allocated to this trip yet.
      </div>

      <div v-else class="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
        <div
          v-for="p in tripData.owner_payments"
          :key="p.id"
          class="p-3.5 flex items-center justify-between text-xs hover:bg-slate-50"
        >
          <div>
            <div class="font-bold text-slate-800">Payment Ref: {{ p.reference || 'N/A' }}</div>
            <div class="text-slate-500 font-medium">Mode: {{ p.mode }} • Date: {{ formatDate(p.date) }}</div>
          </div>
          <div class="text-right">
            <span class="font-black text-slate-900 font-mono-numbers text-sm">{{ formatINR(p.amount) }}</span>
            <span class="text-[10px] text-blue-600 font-bold block uppercase">{{ p.kind }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 6: POD Documents -->
    <div v-show="activeTab === 'documents'" class="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm space-y-4">
      <div>
        <h3 class="text-sm font-black uppercase tracking-wider text-slate-900">
          Attached Proof of Delivery & Documents
        </h3>
        <p class="text-xs text-slate-500">Verified documents for audit and settlement</p>
      </div>

      <div v-if="!tripData.documents || tripData.documents.length === 0" class="py-8 text-center text-xs text-slate-400">
        No documents attached to this trip yet. Use the Django admin or API to attach physical scanned copies.
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div
          v-for="d in tripData.documents"
          :key="d.id"
          class="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between"
        >
          <div>
            <div class="font-bold text-xs text-slate-800">{{ d.title || d.doc_type }}</div>
            <div class="text-[11px] text-slate-500">{{ formatDate(d.uploaded_at) }}</div>
          </div>
          <a
            v-if="d.file_url"
            :href="d.file_url"
            target="_blank"
            class="px-2.5 py-1 text-xs font-bold rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            View File
          </a>
        </div>
      </div>
    </div>

    <!-- Tab 7: Lorry Loading Slip PDF Generator -->
    <div v-show="activeTab === 'slip'" class="space-y-6">
      <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 class="text-sm font-black uppercase tracking-wider text-slate-900 flex items-center gap-2">
            <span>Official Lorry Loading Slip (Challan)</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">Authentic NDBT Format</span>
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">
            Auto-populated from LR #{{ form.lr_no }}. You can customize goods, weight, or driver info before printing.
          </p>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <router-link
            :to="`/lorry-slip?trip=${route.params.id}`"
            class="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors"
          >
            Open Standalone Slip Page
          </router-link>

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
            @click="downloadSlipPdf"
            :disabled="isGeneratingPdf"
            class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-sm shadow-blue-500/20 disabled:opacity-50"
          >
            <Download class="w-4 h-4" />
            <span>{{ isGeneratingPdf ? 'Generating...' : 'Download PDF' }}</span>
          </button>
        </div>
      </div>

      <!-- Quick Slip Fields Customization -->
      <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
        <h4 class="text-xs font-black uppercase tracking-wider text-slate-700 mb-3">
          Customize Slip Details (Driver, Goods, Weight)
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
              Goods Particulars
            </label>
            <input
              type="text"
              v-model="slipFields.goods_particulars"
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
              v-model="slipFields.weight"
              placeholder="7 mt."
              class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 font-mono"
            />
          </div>

          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
              Driver's Name
            </label>
            <input
              type="text"
              v-model="slipFields.driver_name"
              placeholder="Driver Name"
              class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500"
            />
          </div>

          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
              Driver License No.
            </label>
            <input
              type="text"
              v-model="slipFields.lic_no"
              placeholder="DL-XXXXX"
              class="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 font-mono"
            />
          </div>

          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
              Authorised Signatory
            </label>
            <select
              v-model="slipFields.signatory"
              class="w-full px-3 py-1.5 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-blue-500 cursor-pointer"
            >
              <option value="Dharambir Vashisth">Dharambir Vashisth</option>
              <option value="Satbir Vashisth">Satbir Vashisth</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Live Slip Preview -->
      <div class="flex justify-center p-2 bg-slate-100/70 border border-slate-200 rounded-2xl overflow-x-auto">
        <LorrySlipDocument :slip-data="computedSlipData" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Printer, Download } from '@lucide/vue'
import html2pdf from 'html2pdf.js'
import api from '../services/api'
import { formatINR, formatDate } from '../utils/formatters'
import LiveMarginCalculator from '../components/common/LiveMarginCalculator.vue'
import LorrySlipDocument from '../components/common/LorrySlipDocument.vue'

const route = useRoute()
const router = useRouter()

const isEditMode = computed(() => Boolean(route.params.id))
const activeTab = ref('booking')
const saving = ref(false)
const alertMessage = ref('')
const alertSuccess = ref(true)

const tripData = ref({})
const form = ref({
  booking_date: new Date().toISOString().split('T')[0],
  lr_no: null,
  consignor: '',
  transporter: '',
  vehicle: '',
  origin: 'Silvassa',
  destination: 'North Hub',
  freight: 0,
  advance: 0,
  commission: 1500,
  lorry_advance: 0,
  tds: 0,
  labour: 0,
  holding_days: 0,
  holding_rate: 0,
  holding: 0,
  memo_no: null,
  unloading_date: null,
  balance_status: 'PENDING',
  balance_received_date: null,
  remarks: '',
  has_pod: false,
})

async function loadTrip(id) {
  try {
    const res = await api.getTrip(id)
    tripData.value = res.data
    form.value = {
      booking_date: res.data.booking_date,
      lr_no: res.data.lr_no,
      consignor: res.data.consignor,
      transporter: res.data.transporter,
      vehicle: res.data.vehicle,
      origin: res.data.origin,
      destination: res.data.destination,
      freight: res.data.freight,
      advance: res.data.advance,
      commission: res.data.commission,
      lorry_advance: res.data.lorry_advance,
      tds: res.data.tds,
      labour: res.data.labour,
      holding_days: res.data.holding_days,
      holding_rate: res.data.holding_rate,
      holding: res.data.holding,
      memo_no: res.data.memo_no,
      unloading_date: res.data.unloading_date,
      balance_status: res.data.balance_status,
      balance_received_date: res.data.balance_received_date,
      remarks: res.data.remarks,
      has_pod: res.data.has_pod,
    }
  } catch (err) {
    alertMessage.value = 'Failed to load trip details'
    alertSuccess.value = false
  }
}

async function saveTrip() {
  saving.value = true
  alertMessage.value = ''
  try {
    if (isEditMode.value) {
      await api.updateTrip(route.params.id, form.value)
      alertMessage.value = 'Trip updated successfully.'
      alertSuccess.value = true
      loadTrip(route.params.id)
    } else {
      const res = await api.createTrip(form.value)
      alertMessage.value = 'Trip created successfully.'
      alertSuccess.value = true
      setTimeout(() => {
        router.push(`/trips/${res.data.id}`)
      }, 800)
    }
  } catch (err) {
    alertMessage.value = err.response?.data?.error || 'Failed to save trip'
    alertSuccess.value = false
  } finally {
    saving.value = false
  }
}

async function deleteTrip() {
  if (!confirm(`Are you sure you want to delete Trip LR #${form.value.lr_no}?`)) return
  try {
    await api.deleteTrip(route.params.id)
    router.push('/trips')
  } catch (err) {
    alertMessage.value = 'Failed to delete trip'
    alertSuccess.value = false
  }
}

// Lorry Slip state & helpers
const isGeneratingPdf = ref(false)
const slipFields = reactive({
  driver_name: '',
  lic_no: '',
  goods_particulars: 'P. Goods',
  weight: '7 mt.',
  address: '',
  signatory: 'Dharambir Vashisth',
})

const computedSlipData = computed(() => ({
  slip_no: form.value.lr_no,
  date: form.value.booking_date,
  customer_name: form.value.consignor,
  customer_city: '',
  truck_no: form.value.vehicle,
  owner_name: form.value.transporter,
  address: slipFields.address,
  driver_name: slipFields.driver_name,
  lic_no: slipFields.lic_no,
  goods_particulars: slipFields.goods_particulars,
  weight: slipFields.weight,
  destination: form.value.destination,
  origin: form.value.origin,
  to_place: form.value.destination,
  rate: form.value.freight,
  advance: form.value.advance,
  balance: (Number(form.value.freight) || 0) - (Number(form.value.advance) || 0),
  signatory: slipFields.signatory,
}))

function printSlip() {
  window.print()
}

async function downloadSlipPdf() {
  const element = document.getElementById('lorry-slip-print-area')
  if (!element) return

  isGeneratingPdf.value = true
  const opt = {
    margin: [10, 10, 10, 10],
    filename: `NDBT_Slip_${form.value.lr_no || 'Trip'}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2.5, useCORS: true, logging: false },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }

  try {
    await html2pdf().set(opt).from(element).save()
  } catch (err) {
    console.error('PDF generation error:', err)
    window.open(api.getTripSlipPdfUrl(route.params.id, { download: '1' }), '_blank')
  } finally {
    isGeneratingPdf.value = false
  }
}

onMounted(() => {
  if (isEditMode.value) {
    loadTrip(route.params.id)
  }
})
</script>
