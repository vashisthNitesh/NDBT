import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from register.models import Trip, Customer, Transporter, Vehicle

User = get_user_model()


class RegisterAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testadmin', password='password123', is_staff=True)

        self.customer = Customer.objects.create(name='Acme Corp', code='ACME', city='Vapi')
        self.transporter = Transporter.objects.create(name='Balaji Roadlines', pan='ABCDE1234F')
        self.vehicle = Vehicle.objects.create(reg_no='HR38W-8905', default_owner=self.transporter)

        self.trip1 = Trip.objects.create(
            booking_date=date(2026, 9, 20),
            lr_no=9001,
            vehicle=self.vehicle,
            consignor=self.customer,
            lorry_owner=self.transporter,
            origin='Silvassa',
            destination='Noida',
            freight=Decimal('60000.00'),
            advance=Decimal('40000.00'),
            commission=Decimal('1500.00'),
            lorry_advance=Decimal('35000.00'),
            tds=Decimal('600.00'),
            memo_no=501,
            balance_status=Trip.BalanceStatus.PENDING,
        )

        self.trip2 = Trip.objects.create(
            booking_date=date(2026, 9, 21),
            lr_no=9002,
            vehicle=self.vehicle,
            consignor=self.customer,
            lorry_owner=self.transporter,
            origin='Vapi',
            destination='Ghaziabad',
            freight=Decimal('50000.00'),
            advance=Decimal('30000.00'),
            commission=Decimal('1500.00'),
            lorry_advance=Decimal('25000.00'),
            tds=Decimal('500.00'),
            memo_no=None,
            balance_status=Trip.BalanceStatus.RECEIVED,
        )

    def test_current_user_api(self):
        res = self.client.get(reverse('api_current_user'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data['isAuthenticated'])

        self.client.force_login(self.user)
        res = self.client.get(reverse('api_current_user'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['isAuthenticated'])
        self.assertEqual(data['username'], 'testadmin')

    def test_dashboard_analytics_api(self):
        res = self.client.get(reverse('api_dashboard_analytics'))
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data['kpis']['total_trips'], 2)
        self.assertEqual(data['kpis']['total_freight'], 110000.0)
        self.assertEqual(data['settlement']['total'], 2)
        self.assertEqual(data['attention']['pending_memos'], 1)
        self.assertEqual(len(data['recent_trips']), 2)

    def test_trips_collection_api_get(self):
        res = self.client.get(reverse('api_trips_collection'))
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data['count'], 2)
        self.assertEqual(data['summary_totals']['total_freight'], 110000.0)
        self.assertEqual(len(data['results']), 2)

        # Search filter
        res_search = self.client.get(reverse('api_trips_collection') + '?q=9001')
        data_search = res_search.json()
        self.assertEqual(data_search['count'], 1)
        self.assertEqual(data_search['results'][0]['lr_no'], 9001)

    def test_trips_collection_api_post(self):
        payload = {
            'lr_no': 9003,
            'booking_date': '2026-09-22',
            'vehicle': 'HR55BE-9483',
            'consignor': 'Laxmi Express',
            'transporter': 'JCM Logistics',
            'origin': 'Silvassa',
            'destination': 'Dadri',
            'freight': 58000,
            'advance': 35000,
            'commission': 1500,
            'lorry_advance': 30000,
            'tds': 580,
            'memo_no': 502,
        }
        res = self.client.post(
            reverse('api_trips_collection'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data['lr_no'], 9003)

        created_trip = Trip.objects.get(lr_no=9003)
        self.assertEqual(created_trip.freight, Decimal('58000.00'))
        self.assertEqual(created_trip.consignor.name, 'Laxmi Express')
        self.assertEqual(created_trip.balance, Decimal('23000.00'))

    def test_trip_detail_api(self):
        res = self.client.get(reverse('api_trip_detail', kwargs={'pk': self.trip1.id}))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['lr_no'], 9001)
        self.assertEqual(data['freight'], 60000.0)

        # Update
        patch_payload = {'freight': 65000, 'balance_status': 'RECEIVED'}
        res_patch = self.client.patch(
            reverse('api_trip_detail', kwargs={'pk': self.trip1.id}),
            data=json.dumps(patch_payload),
            content_type='application/json'
        )
        self.assertEqual(res_patch.status_code, 200)
        self.trip1.refresh_from_db()
        self.assertEqual(self.trip1.freight, Decimal('65000.00'))
        self.assertEqual(self.trip1.balance_status, 'RECEIVED')

    def test_masters_and_reports_api(self):
        res_cust = self.client.get(reverse('api_master_customers'))
        self.assertEqual(res_cust.status_code, 200)
        self.assertGreaterEqual(len(res_cust.json()), 1)

        res_rep_party = self.client.get(reverse('api_report_party_outstanding'))
        self.assertEqual(res_rep_party.status_code, 200)
        self.assertEqual(res_rep_party.json()['totals']['trip_count'], 2)
