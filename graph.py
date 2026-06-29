from typing import Literal, cast, TypedDict
from pydantic import BaseModel, Field, SecretStr
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pathlib import Path
from langgraph.graph import START, END, StateGraph


class Finding(BaseModel):
    category: Literal["bug", "security", "standards"]
    line_start: int = Field(description="first line of the issue (1-indexed)")
    line_end: int
    severity: Literal["low", "medium", "high"]
    message: str = Field(description="what is wrong and how to fix it")


class Review(BaseModel):
    findings: list[Finding]


class ReviewState(TypedDict):
    code: str
    findings: list[Finding]


load_dotenv()


reviewer_llm = ChatOpenAI(
    model="google/gemma-4-26b-a4b-it:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
).with_structured_output(Review, method="json_schema")


REVIEWER_SYSTEM = (
    "You are a meticulous code reviewer. Find real bugs, security issues, "
    "and standards violations in the snippet below. The code is shown with "
    "line numbers as 'N | code'. Report every issue you find with its exact "
    "line range, a category (bug | security | standards), a severity "
    "(low | medium | high), and a short message. Do not invent issues; if a "
    "line is correct, do not report it."
)


def number_lines(code: str) -> str:
    return "\n".join(f"{i} | {line}" for i, line in enumerate(code.splitlines(), 1))


def review_bugs(state: ReviewState) -> dict:
    prompt = number_lines(state["code"])
    review = cast(
        Review,
        reviewer_llm.invoke(
            [
                {"role": "system", "content": REVIEWER_SYSTEM},
                {"role": "user", "content": prompt},
            ]
        ),
    )
    return {"findings": review.findings}


builder = StateGraph(ReviewState)
builder.add_node("review_bugs", review_bugs)
builder.add_edge(START, "review_bugs")
builder.add_edge("review_bugs", END)
graph = builder.compile()

if __name__ == "__main__":
    code = Path("snippets/s08_slugify.py").read_text()
    initial: ReviewState = {"code": code, "findings": []}
    result = graph.invoke(initial)
    for f in result["findings"]:
        print(f"L{f.line_start}-{f.line_end} [{f.category}/{f.severity}] {f.message}")
