def first_present(values: list) -> object | None:
    """Return the first non-null value, or None if there is none."""
    for value in values:
        if value != None:
            return value
    return None
