from typing import Literal, TypedDict
from pydantic import BaseModel, Field, SecretStr, model_validator, ValidationError
import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from pathlib import Path
from langgraph.graph import START, END, StateGraph
from typing import Annotated
from operator import add


class Finding(BaseModel):
    category: Literal["bug", "security", "standards"]
    line_start: int = Field(description="first line of the issue (1-indexed)")
    line_end: int
    severity: Literal["low", "medium", "high"]
    message: str = Field(description="what is wrong and how to fix it")


class Review(BaseModel):
    findings: list[Finding] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_shape(cls, data):
        if isinstance(data, list):
            return {"findings": data}
        return data


class ReviewState(TypedDict):
    code: str
    findings: Annotated[list[Finding], add]
    verified: list[Finding]


load_dotenv()

# Cache LLM responses on disk: identical (prompt, model) calls skip the API.
# Makes eval re-runs free + reproducible. Delete the .db to force fresh calls.
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))


reviewer_llm = ChatOpenAI(
    model="google/gemma-4-26b-a4b-it:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
    max_retries=6,
)


REVIEWER_TEMPLATE = (
    "You are a meticulous code reviewer specialized in {focus}. "
    "The code is shown with line numbers as 'N | code'. "
    "Report ONLY {focus}. Do not invent issues.\n"
    "Respond with ONLY a raw JSON object, no prose and no markdown fences, "
    "of this exact shape:\n"
    '{{"findings": [{{"category": "{category}", "line_start": <int>, '
    '"line_end": <int>, "severity": "<low|medium|high>", "message": "<short text>"}}]}}\n'
    'If you find no issues, respond with {{"findings": []}}.'
)

REVIEWERS = {
    "bug": "logic bugs and correctness errors",
    "security": "security vulnerabilities",
    "standards": "code standards and style violations",
}

VERIFIER_SYSTEM = (
    "You are a strict senior engineer auditing a junior's code review. "
    "The code is shown as 'N | code'. You receive candidate findings as JSON. "
    "Keep ONLY findings that are genuinely real and correctly located. Drop "
    "false positives, duplicates, and anything you are not confident about. "
    "Be skeptical: when in doubt, drop it.\n"
    "Respond with ONLY a raw JSON object, no prose and no markdown fences, of "
    'this exact shape: {"findings": [ ...the findings you keep, unchanged... ]}'
)


def number_lines(code: str) -> str:
    return "\n".join(f"{i} | {line}" for i, line in enumerate(code.splitlines(), 1))


def parse_review(content: str) -> Review:
    text = re.sub(r"^```(?:json)?|```$", "", content.strip()).strip()
    try:
        return Review.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError):
        return Review()


def make_reviewer(category: str, focus: str):
    system = REVIEWER_TEMPLATE.format(focus=focus, category=category)

    def review(state: ReviewState) -> dict[str, list[Finding]]:
        prompt = number_lines(state["code"])
        msg = reviewer_llm.invoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        )
        return {"findings": parse_review(str(msg.content)).findings}

    return review


def verify(state: ReviewState) -> dict[str, list[Finding]]:
    candidates = state["findings"]
    if not candidates:
        return {"verified": []}
    payload = Review(findings=candidates).model_dump_json()
    user = f"CODE:\n{number_lines(state['code'])}\n\nCANDIDATES:\n{payload}"
    msg = reviewer_llm.invoke(
        [
            {"role": "system", "content": VERIFIER_SYSTEM},
            {"role": "user", "content": user},
        ]
    )
    return {"verified": parse_review(str(msg.content)).findings}


builder = StateGraph(ReviewState)
builder.add_node("verify", verify)
for category, focus in REVIEWERS.items():
    name = f"review_{category}"
    builder.add_node(name, make_reviewer(category, focus))
    builder.add_edge(START, name)
    builder.add_edge(name, "verify")
builder.add_edge("verify", END)
graph = builder.compile()

if __name__ == "__main__":
    code = Path("snippets/s04_auth.py").read_text()
    result = graph.invoke({"code": code, "findings": [], "verified": []})
    print("RESULT", result)
    print(f"NAIVE ({len(result['findings'])}):")
    for f in result["findings"]:
        print(f"  L{f.line_start}-{f.line_end} [{f.category}/{f.severity}] {f.message}")
    print(f"VERIFIED ({len(result['verified'])}):")
    for f in result["verified"]:
        print(f"  L{f.line_start}-{f.line_end} [{f.category}/{f.severity}] {f.message}")
