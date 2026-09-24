/**
 * NDBT Financial & Logistics Formatters
 */

export function formatINR(val, decimals = 0) {
  if (val === null || val === undefined || isNaN(val)) return '₹ 0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)
}

export function formatNumber(val) {
  if (val === null || val === undefined || isNaN(val)) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('en-IN').format(num)
}

export function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return dateStr
  }
}
