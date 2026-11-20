from decimal import Decimal, ROUND_HALF_UP

FOUR = Decimal("0.0001")
ZERO = Decimal("0")


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(FOUR, rounding=ROUND_HALF_UP)
