from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='indian_currency')
def indian_currency(value, with_symbol=True):
    """
    Formats a number or Decimal according to the Indian numbering system.
    e.g. 108000 -> ₹ 1,08,000 or -27500 -> -₹ 27,500
    """
    if value is None or value == '':
        return ''

    try:
        val = Decimal(str(value))
    except Exception:
        return value

    is_negative = val < 0
    val = abs(val)

    # Format to two decimal places
    val_str = f"{val:.2f}"
    parts = val_str.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ','.join(groups) + ',' + last_three
    else:
        formatted_int = integer_part

    if decimal_part == '00':
        result = formatted_int
    else:
        result = f"{formatted_int}.{decimal_part}"

    prefix = '₹ ' if with_symbol else ''
    if is_negative:
        return f"-{prefix}{result}"
    return f"{prefix}{result}"
