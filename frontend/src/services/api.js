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

  getVehicles(q = '') {
    return client.get('/masters/vehicles/', { params: { q } })
  },

  createVehicle(payload) {
    return client.post('/masters/vehicles/', payload)
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
