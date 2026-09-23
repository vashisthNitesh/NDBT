from decimal import Decimal
from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse

from register.models import Customer, Transporter, Vehicle, Trip
from register.views import (
    dashboard_callback,
    customer_outstanding_report,
    transporter_payable_report,
    tds_register_report,
    monthly_summary_report,
    pending_work_report,
)


class ViewsAndReportsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser('admin_test', 'admin@example.com', 'pass1234')

        self.customer = Customer.objects.create(code='C1', name='Consignor Alpha', city='Vapi')
        self.transporter = Transporter.objects.create(code='T1', name='Transporter Bravo', pan='ABCDE1234F')
        self.vehicle = Vehicle.objects.create(reg_no='GJ15XX-1234', default_owner=self.transporter)

        self.trip1 = Trip.objects.create(
            lr_no=9001,
            booking_date=date(2025, 5, 10),
            consignor=self.customer,
            lorry_owner=self.transporter,
            vehicle=self.vehicle,
            freight=Decimal('50000.00'),
            advance=Decimal('30000.00'),
            commission=Decimal('1500.00'),
            lorry_advance=Decimal('25000.00'),
            tds=Decimal('500.00'),
            memo_pending=True,
            has_pod=False,
        )

        self.trip2 = Trip.objects.create(
            lr_no=9002,
            booking_date=date(2025, 6, 15),
            consignor=self.customer,
            lorry_owner=self.transporter,
            vehicle=self.vehicle,
            freight=Decimal('80000.00'),
            advance=Decimal('50000.00'),
            commission=Decimal('1500.00'),
            lorry_advance=Decimal('40000.00'),
            tds=Decimal('800.00'),
            memo_no=123,
            memo_pending=False,
            has_pod=True,
        )

    def test_dashboard_callback(self):
        request = self.factory.get('/admin/')
        request.user = self.admin_user
        context = {}
        result = dashboard_callback(request, context)

        self.assertIn('kpi_total_trips', result)
        self.assertEqual(result['kpi_total_trips'], 2)
        self.assertEqual(result['kpi_total_freight'], Decimal('130000.00'))
        self.assertEqual(result['kpi_pending_memos'], 1)
        self.assertEqual(result['kpi_missing_pods'], 1)
        self.assertIn('top_customers', result)
        self.assertIn('recent_trips', result)

    def test_customer_outstanding_report_html_and_csv(self):
        # HTML
        request = self.factory.get('/admin/reports/customer-outstanding/')
        request.user = self.admin_user
        response = customer_outstanding_report(request)
        self.assertEqual(response.status_code, 200)

        # CSV Export
        request_csv = self.factory.get('/admin/reports/customer-outstanding/?format=csv')
        request_csv.user = self.admin_user
        response_csv = customer_outstanding_report(request_csv)
        self.assertEqual(response_csv.status_code, 200)
        self.assertEqual(response_csv['Content-Type'], 'text/csv')
        self.assertIn(b'Consignor Alpha', response_csv.content)

    def test_transporter_payable_report_html_and_csv(self):
        # HTML
        request = self.factory.get('/admin/reports/transporter-payable/')
        request.user = self.admin_user
        response = transporter_payable_report(request)
        self.assertEqual(response.status_code, 200)

        # CSV Export
        request_csv = self.factory.get('/admin/reports/transporter-payable/?format=csv')
        request_csv.user = self.admin_user
        response_csv = transporter_payable_report(request_csv)
        self.assertEqual(response_csv.status_code, 200)
        self.assertEqual(response_csv['Content-Type'], 'text/csv')
        self.assertIn(b'Transporter Bravo', response_csv.content)

    def test_tds_register_report_html_and_csv(self):
        # HTML
        request = self.factory.get('/admin/reports/tds-register/?fy=2025-26')
        request.user = self.admin_user
        response = tds_register_report(request)
        self.assertEqual(response.status_code, 200)

        # CSV Export
        request_csv = self.factory.get('/admin/reports/tds-register/?fy=2025-26&format=csv')
        request_csv.user = self.admin_user
        response_csv = tds_register_report(request_csv)
        self.assertEqual(response_csv.status_code, 200)
        self.assertEqual(response_csv['Content-Type'], 'text/csv')
        self.assertIn(b'ABCDE1234F', response_csv.content)

    def test_monthly_summary_report_html_and_csv(self):
        # HTML
        request = self.factory.get('/admin/reports/monthly-summary/')
        request.user = self.admin_user
        response = monthly_summary_report(request)
        self.assertEqual(response.status_code, 200)

        # CSV
        request_csv = self.factory.get('/admin/reports/monthly-summary/?format=csv')
        request_csv.user = self.admin_user
        response_csv = monthly_summary_report(request_csv)
        self.assertEqual(response_csv.status_code, 200)
        self.assertEqual(response_csv['Content-Type'], 'text/csv')

    def test_pending_work_report(self):
        for tab in ['memo', 'pod', 'settlement']:
            request = self.factory.get(f'/admin/reports/pending-work/?tab={tab}')
            request.user = self.admin_user
            response = pending_work_report(request)
            self.assertEqual(response.status_code, 200)

    def test_trip_admin_changelist(self):
        self.client.force_login(self.admin_user)
        url = reverse('admin:register_trip_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary_totals', response.context)
        self.assertEqual(response.context['summary_totals']['trip_count'], 2)
