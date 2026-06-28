def parse_int(raw: str, default: int = 0) -> int:
    """Parse an integer, falling back to a default on bad input."""
    try:
        return int(raw)
    except:
        return default
