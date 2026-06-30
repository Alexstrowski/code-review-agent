"""Assemble the review graph: parallel specialist reviewers + a skeptical verifier."""

from pathlib import Path

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from llm import bootstrap, make_llm
from models import Finding, Review, ReviewState
from parsing import number_lines, parse_review
from prompts import REVIEWER_TEMPLATE, REVIEWERS, VERIFIER_SYSTEM


def make_reviewer(llm: ChatOpenAI, category: str, focus: str):
    """One specialist reviewer node, bound to a single category."""
    system = REVIEWER_TEMPLATE.format(focus=focus, category=category)

    def review(state: ReviewState) -> dict[str, list[Finding]]:
        msg = llm.invoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": number_lines(state["code"])},
            ]
        )
        return {"findings": parse_review(str(msg.content)).findings}

    return review


def make_verifier(llm: ChatOpenAI):
    """The skeptical judge node: filters the accumulated candidates."""

    def verify(state: ReviewState) -> dict[str, list[Finding]]:
        candidates = state["findings"]
        if not candidates:
            return {"verified": []}
        payload = Review(findings=candidates).model_dump_json()
        user = f"CODE:\n{number_lines(state['code'])}\n\nCANDIDATES:\n{payload}"
        msg = llm.invoke(
            [
                {"role": "system", "content": VERIFIER_SYSTEM},
                {"role": "user", "content": user},
            ]
        )
        return {"verified": parse_review(str(msg.content)).findings}

    return verify


def build_graph(llm: ChatOpenAI | None = None):
    """Compile the fan-out -> verify graph. Pass a custom llm to override the default."""
    llm = llm or make_llm()
    builder = StateGraph(ReviewState)
    builder.add_node("verify", make_verifier(llm))
    for category, focus in REVIEWERS.items():
        name = f"review_{category}"
        builder.add_node(name, make_reviewer(llm, category, focus))
        builder.add_edge(START, name)  # fan-out: parallel reviewers
        builder.add_edge(name, "verify")  # fan-in: verify waits for all
    builder.add_edge("verify", END)
    return builder.compile()


def main() -> None:
    bootstrap()
    graph = build_graph()
    code = Path("snippets/s04_auth.py").read_text()
    result = graph.invoke({"code": code, "findings": [], "verified": []})
    for channel in ("findings", "verified"):
        print(f"{channel.upper()} ({len(result[channel])}):")
        for f in result[channel]:
            print(f"  L{f.line_start}-{f.line_end} [{f.category}/{f.severity}] {f.message}")


if __name__ == "__main__":
    main()
