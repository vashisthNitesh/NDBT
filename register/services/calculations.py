from decimal import Decimal
from datetime import date
from typing import Dict, Any, Optional


def to_decimal(val: Any) -> Decimal:
    """Helper to safely convert any numeric or string value to Decimal with 2 decimal places."""
    if val is None or val == '':
        return Decimal('0.00')
    if isinstance(val, Decimal):
        return val.quantize(Decimal('0.01'))
    try:
        return Decimal(str(val)).quantize(Decimal('0.01'))
    except Exception:
        return Decimal('0.00')


def calculate_trip_totals(
    freight: Any,
    advance: Any,
    commission: Any,
    lorry_advance: Any,
    tds: Any,
    labour: Any,
    holding_days: int = 0,
    holding_rate: Any = None,
    holding_manual: Any = None,
    is_cancelled: bool = False,
) -> Dict[str, Decimal]:
    """
    Pure calculation function for Trip financial fields.
    Computes holding, advance_balance, balance, and total_balance.
    """
    if is_cancelled:
        return {
            'freight': Decimal('0.00'),
            'advance': Decimal('0.00'),
            'commission': Decimal('0.00'),
            'lorry_advance': Decimal('0.00'),
            'tds': Decimal('0.00'),
            'advance_balance': Decimal('0.00'),
            'balance': Decimal('0.00'),
            'labour': Decimal('0.00'),
            'holding': Decimal('0.00'),
            'total_balance': Decimal('0.00'),
        }

    f = to_decimal(freight)
    adv = to_decimal(advance)
    com = to_decimal(commission)
    l_adv = to_decimal(lorry_advance)
    t = to_decimal(tds)
    lab = to_decimal(labour)
    h_rate = to_decimal(holding_rate)
    h_man = to_decimal(holding_manual)

    days = int(holding_days) if holding_days else 0

    if days > 0 and h_rate > Decimal('0.00'):
        holding = (Decimal(days) * h_rate).quantize(Decimal('0.01'))
    else:
        holding = h_man

    advance_balance = (adv - com - l_adv - t).quantize(Decimal('0.01'))
    balance = (f - adv).quantize(Decimal('0.01'))
    total_balance = (balance + lab + holding).quantize(Decimal('0.01'))

    return {
        'freight': f,
        'advance': adv,
        'commission': com,
        'lorry_advance': l_adv,
        'tds': t,
        'advance_balance': advance_balance,
        'balance': balance,
        'labour': lab,
        'holding': holding,
        'total_balance': total_balance,
    }


def get_financial_year(dt: Optional[date]) -> str:
    """
    Derives Indian Financial Year string (e.g. '2022-23', '2025-26') from a given date.
    Financial Year runs from April 1 to March 31.
    """
    if not dt:
        return ''
    year = dt.year
    if dt.month >= 4:
        start_year = year
        end_year = year + 1
    else:
        start_year = year - 1
        end_year = year
    return f"{start_year}-{str(end_year)[-2:]}"
