import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default {
  // Auth
  getCurrentUser() {
    return client.get('/auth/me/')
  },

  // Dashboard
  getDashboard(fy = 'ALL') {
    return client.get(`/dashboard/?fy=${encodeURIComponent(fy)}`)
  },

  // Trips
  getTrips(params = {}) {
    return client.get('/trips/', { params })
  },

  getTrip(id) {
    return client.get(`/trips/${id}/`)
  },

  createTrip(payload) {
    return client.post('/trips/', payload)
  },

  updateTrip(id, payload) {
    return client.patch(`/trips/${id}/`, payload)
  },

  deleteTrip(id) {
    return client.delete(`/trips/${id}/`)
  },

  getTripSlipPdfUrl(id, params = {}) {
    const query = new URLSearchParams(params).toString()
    return `/api/trips/${id}/slip-pdf/${query ? '?' + query : ''}`
  },

  generateCustomSlipPdf(payload) {
    return client.post('/trips/custom-slip-pdf/', payload, { responseType: 'blob' })
  },

  async downloadCustomSlipPdf(payload) {
    const res = await client.post('/trips/custom-slip-pdf/?download=1', payload, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const slipNo = payload.slip_no || payload.lr_no || 'Document'
    link.download = `NDBT_Slip_${slipNo}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    return true
  },

  // Masters
  getCustomers(q = '') {
    return client.get('/masters/customers/', { params: { q } })
  },

  createCustomer(payload) {
    return client.post('/masters/customers/', payload)
  },

  getTransporters(q = '') {
    return client.get('/masters/transporters/', { params: { q } })
  },

  createTransporter(payload) {
    return client.post('/masters/transporters/', payload)
  },

  getVendors(q = '') {
    return client.get('/masters/vendors/', { params: { q } })
  },

  createVendor(payload) {
    return client.post('/masters/vendors/', payload)
  },

  getVehicleTypes(q = '') {
    return client.get('/masters/vehicle-types/', { params: { q } })
  },

  createVehicleType(payload) {
    return client.post('/masters/vehicle-types/', payload)
  },

  getVehicles(q = '') {
    return client.get('/masters/vehicles/', { params: { q } })
  },

  createVehicle(payload) {
    return client.post('/masters/vehicles/', payload)
  },

  getLocations(q = '') {
    return client.get('/masters/locations/', { params: { q } })
  },

  createLocation(payload) {
    return client.post('/masters/locations/', payload)
  },

  getLanes(q = '') {
    return client.get('/masters/lanes/', { params: { q } })
  },

  createLane(payload) {
    return client.post('/masters/lanes/', payload)
  },

  // Reports
  getPartyOutstanding(fy = '', q = '') {
    return client.get('/reports/party-outstanding/', { params: { fy, q } })
  },

  getTransporterPayable(fy = '', q = '') {
    return client.get('/reports/transporter-payable/', { params: { fy, q } })
  },

  getTdsRegister(fy = '', q = '') {
    return client.get('/reports/tds-register/', { params: { fy, q } })
  },

  getMonthlySummary(fy = '') {
    return client.get('/reports/monthly-summary/', { params: { fy } })
  },

  getPendingOperations(fy = '') {
    return client.get('/reports/pending-operations/', { params: { fy } })
  },
}
