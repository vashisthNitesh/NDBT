import re
from typing import Tuple

# Pattern matching normalized XX00XX-0000 or XX00X-0000 or XX00XXX-0000
NORM_RE = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{1,3}-\d{4}$")
# Pattern matching unhyphenated standard vehicle reg: XX00XX0000
UNHYPHENATED_RE = re.compile(r"^([A-Z]{2}\d{1,2}[A-Z]{1,3})(\d{4})$")


def normalize_vehicle_reg(reg_no: str) -> Tuple[str, bool]:
    """
    Normalizes a vehicle registration number:
    - Upper-case
    - Strips whitespace
    - Inserts missing hyphen before the 4-digit number: HR38AE5461 -> HR38AE-5461
    Returns (normalized_reg, is_valid_format)
    """
    if not reg_no:
        return ('', False)

    cleaned = str(reg_no).strip().upper().replace(' ', '')

    # Already has hyphen and matches standard
    if NORM_RE.match(cleaned):
        return (cleaned, True)

    # Missing hyphen
    m = UNHYPHENATED_RE.match(cleaned)
    if m:
        normalized = f"{m.group(1)}-{m.group(2)}"
        return (normalized, True)

    # Does not match standard pattern (e.g. HR338AF-5842, HR63-2243)
    return (cleaned, False)
