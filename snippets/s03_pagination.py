def page_items(items: list, page: int, size: int) -> list:
    """Return the items belonging to a zero-indexed page."""
    start = page * size
    end = start + size - 1
    return items[start:end]
