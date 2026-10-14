from decimal import Decimal, InvalidOperation


def paise(amount, unit):
    if isinstance(amount, bool):
        raise ValueError("Invalid price")
    try:
        value = Decimal(str(amount))
        if unit == "rupees":
            value *= 100
        elif unit != "paise":
            raise ValueError("Price unit must be documented as rupees or paise")
        if not value.is_finite() or value <= 0 or value != value.to_integral_value():
            raise ValueError("Price has an unsupported precision")
        return int(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary value") from exc
