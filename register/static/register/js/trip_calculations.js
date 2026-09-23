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

    const previewAdvBal = document.getElementById('preview-adv-bal');
    const previewBalance = document.getElementById('preview-balance');
    const previewTotalBal = document.getElementById('preview-total-bal');

    if (!freightInput || !advanceInput || !previewAdvBal) return;

    // Connect Quick TDS buttons
    const btnTds1 = document.getElementById('btn-tds-1');
    const btnTds2 = document.getElementById('btn-tds-2');

    if (btnTds1 && tdsInput) {
        btnTds1.addEventListener('click', function () {
            const f = parseFloat(freightInput.value) || 0;
            tdsInput.value = (f * 0.01).toFixed(2);
            updateCalculations();
        });
    }

    if (btnTds2 && tdsInput) {
        btnTds2.addEventListener('click', function () {
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
        const lorryAdvance = parseFloat(lorryAdvanceInput ? lorryAdvanceInput.value : 0) || 0;
        const tds = parseFloat(tdsInput ? tdsInput.value : 0) || 0;
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

        if (previewAdvBal) previewAdvBal.textContent = formatCurrency(advBal);
        if (previewBalance) previewBalance.textContent = formatCurrency(balance);
        if (previewTotalBal) previewTotalBal.textContent = formatCurrency(totalBal);
    }

    const inputs = [freightInput, advanceInput, commissionInput, lorryAdvanceInput, tdsInput, labourInput, holdingDaysInput, holdingRateInput, holdingInput];
    inputs.forEach(input => {
        if (input) {
            input.addEventListener('input', updateCalculations);
        }
    });

    updateCalculations();
});
