import re


def slugify(text: str) -> str:
    """Convert text into a lowercase, dash-separated slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
