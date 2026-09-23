document.addEventListener('DOMContentLoaded', function () {
    const freightInput = document.getElementById('id_freight');
    const advanceInput = document.getElementById('id_advance');
    const commissionInput = document.getElementById('id_commission');
    const lorryAdvanceInput = document.getElementById('id_lorry_advance');
    const tdsInput = document.getElementById('id_tds');
    const labourInput = document.getElementById('id_labour');
    const holdingDaysInput = document.getElementById('id_holding_days');
    const holdingRateInput = document.getElementById('id_holding_rate');
    const holdingInput = document.getElementById('id_holding');

    if (!freightInput || !advanceInput) return;

    // Create live preview ticker banner
    const banner = document.createElement('div');
    banner.id = 'live-calculation-banner';
    banner.className = 'sticky top-4 z-20 mb-6 p-4 rounded-lg border bg-white/95 dark:bg-gray-800/95 backdrop-blur shadow-md flex flex-wrap gap-6 items-center justify-between';
    banner.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">Live Calculation</span>
            <span class="text-xs text-gray-500 dark:text-gray-400">Auto-computed as you type</span>
        </div>
        <div class="flex flex-wrap items-center gap-6 text-sm">
            <div>
                <span class="text-gray-500 dark:text-gray-400 text-xs block">Adv. Balance:</span>
                <span id="preview-adv-bal" class="font-bold text-gray-800 dark:text-gray-100">₹ 0.00</span>
            </div>
            <div>
                <span class="text-gray-500 dark:text-gray-400 text-xs block">Freight Balance:</span>
                <span id="preview-balance" class="font-bold text-blue-600 dark:text-blue-400">₹ 0.00</span>
            </div>
            <div>
                <span class="text-gray-500 dark:text-gray-400 text-xs block">Total Balance Due:</span>
                <span id="preview-total-bal" class="font-bold text-emerald-600 dark:text-emerald-400 text-base">₹ 0.00</span>
            </div>
        </div>
    `;

    const form = document.querySelector('form');
    if (form) {
        form.parentNode.insertBefore(banner, form);
    }

    // Add TDS 1% and 2% quick buttons next to TDS field
    if (tdsInput && tdsInput.parentNode) {
        const btnGroup = document.createElement('div');
        btnGroup.className = 'flex gap-2 mt-1.5';
        btnGroup.innerHTML = `
            <button type="button" id="btn-tds-1" class="text-xs px-2.5 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded text-gray-700 dark:text-gray-300 font-medium transition">1% TDS</button>
            <button type="button" id="btn-tds-2" class="text-xs px-2.5 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded text-gray-700 dark:text-gray-300 font-medium transition">2% TDS</button>
        `;
        tdsInput.parentNode.appendChild(btnGroup);

        document.getElementById('btn-tds-1').addEventListener('click', function () {
            const f = parseFloat(freightInput.value) || 0;
            tdsInput.value = (f * 0.01).toFixed(2);
            updateCalculations();
        });

        document.getElementById('btn-tds-2').addEventListener('click', function () {
            const f = parseFloat(freightInput.value) || 0;
            tdsInput.value = (f * 0.02).toFixed(2);
            updateCalculations();
        });
    }

    function formatCurrency(val) {
        const isNeg = val < 0;
        const absVal = Math.abs(val).toFixed(2);
        return (isNeg ? '-' : '') + '₹ ' + Number(absVal).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function updateCalculations() {
        const freight = parseFloat(freightInput.value) || 0;
        const advance = parseFloat(advanceInput.value) || 0;
        const commission = parseFloat(commissionInput.value) || 0;
        const lorryAdvance = parseFloat(lorryAdvanceInput.value) || 0;
        const tds = parseFloat(tdsInput.value) || 0;
        const labour = parseFloat(labourInput ? labourInput.value : 0) || 0;

        let holding = 0;
        const hDays = parseInt(holdingDaysInput ? holdingDaysInput.value : 0) || 0;
        const hRate = parseFloat(holdingRateInput ? holdingRateInput.value : 0) || 0;
        if (hDays > 0 && hRate > 0) {
            holding = hDays * hRate;
            if (holdingInput) holdingInput.value = holding.toFixed(2);
        } else if (holdingInput) {
            holding = parseFloat(holdingInput.value) || 0;
        }

        const advBal = advance - commission - lorryAdvance - tds;
        const balance = freight - advance;
        const totalBal = balance + labour + holding;

        document.getElementById('preview-adv-bal').textContent = formatCurrency(advBal);
        document.getElementById('preview-balance').textContent = formatCurrency(balance);
        document.getElementById('preview-total-bal').textContent = formatCurrency(totalBal);
    }

    const inputs = [freightInput, advanceInput, commissionInput, lorryAdvanceInput, tdsInput, labourInput, holdingDaysInput, holdingRateInput, holdingInput];
    inputs.forEach(input => {
        if (input) {
            input.addEventListener('input', updateCalculations);
        }
    });

    updateCalculations();
});
