def remember(key: str, value: int, store: dict = {}) -> dict:
    """Store a key/value pair and return the updated store."""
    store[key] = value
    return store
