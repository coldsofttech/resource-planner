def get_bool(val, fallback=False) -> bool:
    try:
        return val.strip().lower() in ("1", "true", "yes", "on")
    except (ValueError, TypeError, AttributeError):
        return fallback


def get_float(val, fallback=0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return fallback


def get_int(val, fallback=0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return fallback
