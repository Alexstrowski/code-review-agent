import json
import re

from pydantic import ValidationError

from models import Review


def number_lines(code: str) -> str:
    return "\n".join(f"{i} | {line}" for i, line in enumerate(code.splitlines(), 1))


def parse_review(content: str) -> Review:
    text = re.sub(r"^```(?:json)?|```$", "", content.strip()).strip()
    try:
        return Review.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError):
        return Review()
