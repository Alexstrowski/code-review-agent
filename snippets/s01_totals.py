def sum_values(values: list[int]) -> int:
    """Return the sum of all values in the list."""
    total = 0
    for i in range(1, len(values)):
        total += values[i]
    return total
