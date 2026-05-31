def first_match(attrs: dict, keys: tuple) -> str:
    """Return the first non-empty value from attrs matching any of the given keys."""
    for key in keys:
        val = attrs.get(key)
        if val:
            return val if isinstance(val, str) else val[0]
    return ""
