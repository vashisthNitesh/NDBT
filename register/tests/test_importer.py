import os
import tempfile
import datetime
from decimal import Decimal
import openpyxl

from django.test import TestCase
from django.core.management import call_command

from register.models import (
    Customer,
    Transporter,
    Vehicle,
    Trip,
    Receipt,
    ReceiptAllocation,
    OwnerPayment,
    OwnerPaymentAllocation,
)


class ImporterRulesTestCase(TestCase):
    def setUp(self):
        # Create a temporary Excel workbook with test fixtures
        self.tmp_dir = tempfile.mkdtemp()
        self.wb_path = os.path.join(self.tmp_dir, "test_office.xlsx")
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = "2022-2023"

        # Headers A to Z
        headers = [
            'Date', 'Lorry no. ', 'L. R. No. ', 'Lorry Owner ', 'Consignor ', 'From', 'To',
            'Freight ', 'Advance ', 'Advance Received ', 'Date', 'Remarks ', 'Comis. ',
            'Lorry Advance ', 'TDS', 'Adv. Bal.', 'Balance', 'Memo', 'Date ', 'Un. date',
            'Labour', 'Holding ', 'Total Balance ', 'Payment ', 'Lorry balance dt.', 'Remark '
        ]
        self.ws.append(headers)

    def tearDown(self):
        if os.path.exists(self.wb_path):
            os.remove(self.wb_path)

    def test_importer_rules(self):
        # 1. Normal row
        row_normal = [
            datetime.date(2022, 3, 1), 'GJ15AT3912', 5762, 'NDBT ', 'MRC ', 'Silvassa', 'Delhi',
            108000, 50000, 50000, datetime.date(2022, 3, 2), 'UPI123', 1500,
            26000, 1080, 21420, 58000, 1234, datetime.date(2022, 3, 3), datetime.date(2022, 3, 4),
            500, 0, 58500, 'Paid ', None, None
        ]

        # 2. Cancelled row (CANCIL)
        row_cancil = [
            'CANCIL', 'CANCIL', 5795, 'CANCIL', 'CANCIL', 'CANCIL', 'CANCIL',
            'CANCIL', 'CANCIL', None, None, None, 'CANCIL',
            'CANCIL', 'CANCIL', '#VALUE!', '#VALUE!', 99, 'CANCIL', 'CANCIL',
            'CANCIL', 'CANCIL', '#VALUE!', 'Paid ', None, None
        ]

        # 3. Invalid vehicle number (HR338AF-5842), memo 99, dirty money 'OTC00', dirty date 'OTC'
        row_dirty = [
            datetime.date(2023, 1, 10), 'HR338AF-5842', 7121, 'TLS', 'MRS', 'Vapi', 'Noida',
            60000, 40000, 'OTC00', 'OTC', '96', 1500,
            30000, 600, 7900, 20000, 99, None, '31-11',
            0, 0, 20000, 'no payment', datetime.date(2023, 1, 15), 'lorry bal. 5000/- | 1500*2 days'
        ]

        # 4 & 5. Consecutive combined receipt rows (LR 8001 & 8002)
        row_comb_1 = [
            datetime.date(2024, 2, 1), 'GJ15AT-3912', 8001, 'TLS', 'MRS', 'Vapi', 'Delhi',
            70000, 50000, 100000, datetime.date(2024, 2, 2), 'REFCOMB', 1500,
            40000, 700, 7800, 20000, '#', None, None,
            0, 0, 20000, 'nil', None, None
        ]
        row_comb_2 = [
            datetime.date(2024, 2, 1), 'GJ15AT-3912', 8002, 'TLS', 'MRS', 'Vapi', 'Delhi',
            70000, 50000, 100000, datetime.date(2024, 2, 2), 'REFCOMB', 1500,
            40000, 700, 7800, 20000, None, None, None,
            0, 0, 20000, 'To pay', None, None
        ]

        self.ws.append(row_normal)
        self.ws.append(row_cancil)
        self.ws.append(row_dirty)
        self.ws.append(row_comb_1)
        self.ws.append(row_comb_2)
        self.wb.save(self.wb_path)

        # Run importer in commit mode
        call_command('import_register', self.wb_path, sheet='2022-2023', commit=True)

        # Assertions
        # 1. Normal trip
        t1 = Trip.objects.get(lr_no=5762)
        self.assertEqual(t1.vehicle.reg_no, 'GJ15AT-3912')  # hyphen inserted
        self.assertEqual(t1.consignor.name, 'MRC')           # trimmed
        self.assertEqual(t1.lorry_owner.name, 'NDBT')        # trimmed
        self.assertEqual(t1.balance_status, Trip.BalanceStatus.RECEIVED)
        self.assertFalse(t1.memo_pending)
        self.assertEqual(t1.memo_no, 1234)

        # 2. Cancelled trip (5795)
        t_cancil = Trip.objects.get(lr_no=5795)
        self.assertTrue(t_cancil.is_cancelled)
        self.assertEqual(t_cancil.freight, Decimal('0.00'))
        self.assertEqual(t_cancil.total_balance, Decimal('0.00'))

        # 3. Dirty trip (7121)
        t_dirty = Trip.objects.get(lr_no=7121)
        self.assertEqual(t_dirty.vehicle.reg_no, 'HR338AF-5842')  # preserved despite invalid format
        self.assertTrue(t_dirty.memo_pending)
        self.assertIsNone(t_dirty.memo_no)
        self.assertEqual(t_dirty.balance_status, Trip.BalanceStatus.NOT_RECEIVED)
        self.assertEqual(t_dirty.holding_days, 2)
        self.assertEqual(t_dirty.holding_rate, Decimal('1500.00'))
        self.assertEqual(t_dirty.holding, Decimal('3000.00'))
        self.assertEqual(t_dirty.lorry_balance_amount, Decimal('5000.00'))

        # Check OwnerPayment created for 7121
        pmt = OwnerPayment.objects.filter(allocations__trip=t_dirty).first()
        self.assertIsNotNone(pmt)
        self.assertEqual(pmt.amount, Decimal('5000.00'))
        self.assertEqual(pmt.date, datetime.date(2023, 1, 15))

        # 4 & 5. Combined receipts (8001 & 8002)
        # Should be ONE Receipt with amount 100,000 allocated across both LRs
        t_c1 = Trip.objects.get(lr_no=8001)
        t_c2 = Trip.objects.get(lr_no=8002)
        alloc1 = ReceiptAllocation.objects.get(trip=t_c1)
        alloc2 = ReceiptAllocation.objects.get(trip=t_c2)
        self.assertEqual(alloc1.receipt_id, alloc2.receipt_id)
        self.assertEqual(alloc1.receipt.amount, Decimal('100000.00'))
        self.assertEqual(alloc1.amount, Decimal('50000.00'))
        self.assertEqual(alloc2.amount, Decimal('50000.00'))
        self.assertEqual(t_c1.balance_status, Trip.BalanceStatus.NIL)
        self.assertEqual(t_c2.balance_status, Trip.BalanceStatus.TO_PAY)

        # Idempotence: re-running importer updates without duplicating
        call_command('import_register', self.wb_path, sheet='2022-2023', commit=True)
        self.assertEqual(Trip.objects.count(), 5)
        self.assertEqual(Receipt.objects.count(), 2)  # 1 individual for 5762 + 1 combined for 8001/8002
