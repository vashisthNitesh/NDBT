from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from register.models import (
    LorryOwner,
    Consignor,
    Vehicle,
    Trip,
    Receipt,
    ReceiptAllocation,
    OwnerPayment,
    OwnerPaymentAllocation,
    TripDocument,
)


class ModelsTestCase(TestCase):
    def setUp(self):
        self.owner = LorryOwner.objects.create(name='NDBT Logistics', short_code='NDBT')
        self.consignor = Consignor.objects.create(name='Laxmi Express', short_code='LE')
        self.vehicle = Vehicle.objects.create(reg_no='GJ15AT-3912', default_owner=self.owner)

    def test_trip_save_computes_fields(self):
        trip = Trip.objects.create(
            booking_date=date(2022, 3, 1),
            vehicle=self.vehicle,
            lr_no=5762,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Kalsar+Vapi',
            destination='Etah + Kamah',
            freight=Decimal('108000.00'),
            advance=Decimal('0.00'),
            commission=Decimal('1500.00'),
            lorry_advance=Decimal('26000.00'),
            tds=Decimal('0.00'),
            labour=Decimal('0.00'),
            holding=Decimal('0.00'),
            memo_no=None,
        )

        self.assertEqual(trip.financial_year, '2021-22')
        self.assertTrue(trip.memo_pending)
        self.assertEqual(trip.advance_balance, Decimal('-27500.00'))
        self.assertEqual(trip.balance, Decimal('108000.00'))
        self.assertEqual(trip.total_balance, Decimal('108000.00'))

    def test_trip_memo_not_pending_when_memo_no_present(self):
        trip = Trip.objects.create(
            booking_date=date(2023, 5, 10),
            vehicle=self.vehicle,
            lr_no=6000,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Silvassa',
            destination='Delhi',
            freight=Decimal('50000.00'),
            memo_no=1234,
        )
        self.assertFalse(trip.memo_pending)
        self.assertEqual(trip.financial_year, '2023-24')

    def test_trip_lr_no_unique_constraint(self):
        Trip.objects.create(
            booking_date=date(2023, 1, 1),
            vehicle=self.vehicle,
            lr_no=7000,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Silvassa',
            destination='Kanpur',
            freight=Decimal('40000.00'),
        )
        with self.assertRaises(IntegrityError):
            Trip.objects.create(
                booking_date=date(2023, 1, 2),
                vehicle=self.vehicle,
                lr_no=7000,  # Duplicate LR
                lorry_owner=self.owner,
                consignor=self.consignor,
                origin='Silvassa',
                destination='Kanpur',
                freight=Decimal('42000.00'),
            )

    def test_historical_records_tracking(self):
        trip = Trip.objects.create(
            booking_date=date(2024, 6, 1),
            vehicle=self.vehicle,
            lr_no=8000,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Vapi',
            destination='Jaipur',
            freight=Decimal('60000.00'),
        )
        self.assertEqual(trip.history.count(), 1)

        trip.freight = Decimal('65000.00')
        trip.save()
        self.assertEqual(trip.history.count(), 2)
        self.assertEqual(trip.balance, Decimal('65000.00'))

    def test_receipt_and_allocations(self):
        trip1 = Trip.objects.create(
            booking_date=date(2024, 7, 1),
            vehicle=self.vehicle,
            lr_no=8101,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Vapi',
            destination='Delhi',
            freight=Decimal('70000.00'),
            advance=Decimal('50000.00'),
        )
        trip2 = Trip.objects.create(
            booking_date=date(2024, 7, 2),
            vehicle=self.vehicle,
            lr_no=8102,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Vapi',
            destination='Delhi',
            freight=Decimal('70000.00'),
            advance=Decimal('50000.00'),
        )

        receipt = Receipt.objects.create(
            consignor=self.consignor,
            date=date(2024, 7, 3),
            amount=Decimal('100000.00'),
            reference='UPI/1234567890',
        )

        # Allocate to trip1 and trip2
        ReceiptAllocation.objects.create(receipt=receipt, trip=trip1, amount=Decimal('50000.00'))
        ReceiptAllocation.objects.create(receipt=receipt, trip=trip2, amount=Decimal('50000.00'))

        self.assertEqual(receipt.allocated_total, Decimal('100000.00'))
        self.assertEqual(receipt.unallocated_amount, Decimal('0.00'))
        self.assertEqual(trip1.advance_received_total, Decimal('50000.00'))
        self.assertEqual(trip1.advance_short, Decimal('0.00'))

        # Allocation exceeding receipt total amount must fail
        with self.assertRaises(ValidationError):
            ReceiptAllocation.objects.create(receipt=receipt, trip=trip1, amount=Decimal('1000.00'))

    def test_owner_payment_and_outstanding(self):
        trip = Trip.objects.create(
            booking_date=date(2024, 8, 1),
            vehicle=self.vehicle,
            lr_no=8200,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Daman',
            destination='Ludhiana',
            freight=Decimal('80000.00'),
            advance=Decimal('60000.00'),
            commission=Decimal('1500.00'),
            lorry_advance=Decimal('45000.00'),
            tds=Decimal('800.00'),
            lorry_balance_amount=Decimal('5000.00'),
        )
        # advance_balance = 60000 - 1500 - 45000 - 800 = 12700
        self.assertEqual(trip.advance_balance, Decimal('12700.00'))
        # owner_due = 12700 + 5000 = 17700
        self.assertEqual(trip.owner_outstanding, Decimal('17700.00'))

        # Pay part of owner balance
        payment = OwnerPayment.objects.create(
            lorry_owner=self.owner,
            date=date(2024, 8, 10),
            amount=Decimal('17700.00'),
        )
        OwnerPaymentAllocation.objects.create(
            payment=payment,
            trip=trip,
            amount=Decimal('17700.00'),
        )

        self.assertEqual(trip.owner_paid_total, Decimal('17700.00'))
        self.assertEqual(trip.owner_outstanding, Decimal('0.00'))

    def test_trip_document_pod_flag_sync(self):
        trip = Trip.objects.create(
            booking_date=date(2024, 9, 1),
            vehicle=self.vehicle,
            lr_no=8300,
            lorry_owner=self.owner,
            consignor=self.consignor,
            origin='Silvassa',
            destination='Amritsar',
            freight=Decimal('90000.00'),
        )
        self.assertFalse(trip.has_pod)

        dummy_file = SimpleUploadedFile("pod.jpg", b"file_content", content_type="image/jpeg")
        doc = TripDocument.objects.create(
            trip=trip,
            kind=TripDocument.Kind.POD,
            file=dummy_file,
        )

        trip.refresh_from_db()
        self.assertTrue(trip.has_pod)

        # Deleting the POD updates has_pod back to False
        doc.delete()
        trip.refresh_from_db()
        self.assertFalse(trip.has_pod)
