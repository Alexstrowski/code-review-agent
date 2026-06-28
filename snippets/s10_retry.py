import time


def retry(action, attempts: int = 3, delay: float = 0.5):
    """Call action(), retrying on failure up to `attempts` times."""
    for attempt in range(attempts):
        try:
            return action()
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)
