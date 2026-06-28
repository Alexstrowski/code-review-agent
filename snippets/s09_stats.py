def mean(values: list[float]) -> float:
    """Return the arithmetic mean of a non-empty list of values."""
    if not values:
        raise ValueError("mean() requires at least one value")
    return sum(values) / len(values)
