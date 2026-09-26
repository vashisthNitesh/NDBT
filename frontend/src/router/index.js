import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '../views/DashboardView.vue'
import TripsListView from '../views/TripsListView.vue'
import TripFormView from '../views/TripFormView.vue'
import PartyOutstandingView from '../views/PartyOutstandingView.vue'
import TransporterPayableView from '../views/TransporterPayableView.vue'
import TdsRegisterView from '../views/TdsRegisterView.vue'
import MonthlySummaryView from '../views/MonthlySummaryView.vue'
import PendingOperationsView from '../views/PendingOperationsView.vue'
import MastersView from '../views/MastersView.vue'
import LorrySlipView from '../views/LorrySlipView.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView,
  },
  {
    path: '/trips',
    name: 'trips',
    component: TripsListView,
  },
  {
    path: '/trips/new',
    name: 'trip-new',
    component: TripFormView,
  },
  {
    path: '/trips/:id',
    name: 'trip-detail',
    component: TripFormView,
  },
  {
    path: '/lorry-slip',
    name: 'lorry-slip',
    component: LorrySlipView,
  },
  {
    path: '/reports/party-outstanding',
    name: 'party-outstanding',
    component: PartyOutstandingView,
  },
  {
    path: '/reports/transporter-payable',
    name: 'transporter-payable',
    component: TransporterPayableView,
  },
  {
    path: '/reports/tds-register',
    name: 'tds-register',
    component: TdsRegisterView,
  },
  {
    path: '/reports/monthly-summary',
    name: 'monthly-summary',
    component: MonthlySummaryView,
  },
  {
    path: '/reports/pending-operations',
    name: 'pending-operations',
    component: PendingOperationsView,
  },
  {
    path: '/masters/customers',
    name: 'master-customers',
    component: MastersView,
  },
  {
    path: '/masters/vendors',
    name: 'master-vendors',
    component: MastersView,
  },
  {
    path: '/masters/transporters',
    name: 'master-transporters',
    component: MastersView,
  },
  {
    path: '/masters/vehicle-types',
    name: 'master-vehicle-types',
    component: MastersView,
  },
  {
    path: '/masters/vehicles',
    name: 'master-vehicles',
    component: MastersView,
  },
  {
    path: '/masters/locations',
    name: 'master-locations',
    component: MastersView,
  },
  {
    path: '/masters/lanes',
    name: 'master-lanes',
    component: MastersView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
