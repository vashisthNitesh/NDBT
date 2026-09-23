from datetime import date
from decimal import Decimal
from django.test import TestCase

from register.services.calculations import calculate_trip_totals, get_financial_year, to_decimal
from register.services.vehicle import normalize_vehicle_reg
from register.templatetags.indian_numbers import indian_currency


class CalculationsTestCase(TestCase):
    def test_calculate_trip_totals_standard(self):
        # Test standard math matching Excel LR 5762
        totals = calculate_trip_totals(
            freight=108000,
            advance=0,
            commission=1500,
            lorry_advance=26000,
            tds=0,
            labour=0,
            holding_manual=0,
            is_cancelled=False,
        )
        self.assertEqual(totals['freight'], Decimal('108000.00'))
        self.assertEqual(totals['advance'], Decimal('0.00'))
        self.assertEqual(totals['commission'], Decimal('1500.00'))
        self.assertEqual(totals['lorry_advance'], Decimal('26000.00'))
        self.assertEqual(totals['tds'], Decimal('0.00'))
        # advance - commission - lorry_advance - tds = 0 - 1500 - 26000 - 0 = -27500
        self.assertEqual(totals['advance_balance'], Decimal('-27500.00'))
        # balance = freight - advance = 108000
        self.assertEqual(totals['balance'], Decimal('108000.00'))
        # total_balance = balance + labour + holding = 108000 + 0 + 0 = 108000
        self.assertEqual(totals['total_balance'], Decimal('108000.00'))

    def test_calculate_trip_totals_with_advance_and_holding_days(self):
        # Trip with holding days * rate
        totals = calculate_trip_totals(
            freight=75000,
            advance=50000,
            commission=1500,
            lorry_advance=40000,
            tds=750,
            labour=500,
            holding_days=3,
            holding_rate=1500,
            holding_manual=1000,  # should be overridden by days * rate = 4500
        )
        self.assertEqual(totals['holding'], Decimal('4500.00'))
        # advance_balance = 50000 - 1500 - 40000 - 750 = 7750
        self.assertEqual(totals['advance_balance'], Decimal('7750.00'))
        # balance = 75000 - 50000 = 25000
        self.assertEqual(totals['balance'], Decimal('25000.00'))
        # total_balance = 25000 + 500 + 4500 = 30000
        self.assertEqual(totals['total_balance'], Decimal('30000.00'))

    def test_calculate_trip_totals_manual_holding(self):
        # Holding days is 0, manual holding specified
        totals = calculate_trip_totals(
            freight=50000,
            advance=30000,
            commission=1500,
            lorry_advance=25000,
            tds=500,
            labour=200,
            holding_days=0,
            holding_rate=0,
            holding_manual=2000,
        )
        self.assertEqual(totals['holding'], Decimal('2000.00'))
        # balance = 50000 - 30000 = 20000
        # total_balance = 20000 + 200 + 2000 = 22200
        self.assertEqual(totals['total_balance'], Decimal('22200.00'))

    def test_calculate_trip_totals_cancelled(self):
        totals = calculate_trip_totals(
            freight=100000,
            advance=50000,
            commission=1500,
            lorry_advance=40000,
            tds=1000,
            labour=1000,
            holding_manual=2000,
            is_cancelled=True,
        )
        for key, val in totals.items():
            self.assertEqual(val, Decimal('0.00'), f"Field {key} must be 0 for cancelled trip")

    def test_get_financial_year(self):
        # March 31, 2022 -> 2021-22
        self.assertEqual(get_financial_year(date(2022, 3, 31)), '2021-22')
        # April 1, 2022 -> 2022-23
        self.assertEqual(get_financial_year(date(2022, 4, 1)), '2022-23')
        # September 21, 2026 -> 2026-27
        self.assertEqual(get_financial_year(date(2026, 9, 21)), '2026-27')
        # January 15, 2026 -> 2025-26
        self.assertEqual(get_financial_year(date(2026, 1, 15)), '2025-26')
        # None
        self.assertEqual(get_financial_year(None), '')

    def test_normalize_vehicle_reg(self):
        # Missing hyphen inserted
        norm, valid = normalize_vehicle_reg('HR38AE5461')
        self.assertEqual(norm, 'HR38AE-5461')
        self.assertTrue(valid)

        # Standard with hyphen and spaces
        norm, valid = normalize_vehicle_reg('  gj15at - 3912  ')
        self.assertEqual(norm, 'GJ15AT-3912')
        self.assertTrue(valid)

        # Invalid format flagged without changing
        norm, valid = normalize_vehicle_reg('HR338AF-5842')
        self.assertEqual(norm, 'HR338AF-5842')
        self.assertFalse(valid)

        norm, valid = normalize_vehicle_reg('HR63-2243')
        self.assertEqual(norm, 'HR63-2243')
        self.assertFalse(valid)

    def test_indian_currency_formatting(self):
        self.assertEqual(indian_currency(108000), '₹ 1,08,000')
        self.assertEqual(indian_currency(-27500), '-₹ 27,500')
        self.assertEqual(indian_currency(1234567.89), '₹ 12,34,567.89')
        self.assertEqual(indian_currency(1500), '₹ 1,500')
        self.assertEqual(indian_currency(0), '₹ 0')
        self.assertEqual(indian_currency(None), '')
