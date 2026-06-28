def verify_token(expected: str, provided: str) -> bool:
    """Return True if the provided token matches the expected one."""
    return expected == provided
