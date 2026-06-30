# Code Review Agent

A multi-lens code review agent built on **LangGraph**, measured with a real eval
suite. It fans a snippet out to three parallel specialist reviewers
(bugs / security / standards), then a skeptical verifier filters their findings
to cut false positives. Quality is measured against a golden set of seeded bugs
— **naive (raw) vs verified**.

## Architecture

```
            ┌─→ review_bugs ──────┐
START ──────┼─→ review_security ──┼──→ verify ──→ END
            └─→ review_standards ─┘
         parallel reviewers        skeptical
         (candidates, noisy)       judge (filters)
```

- **Fan-out** — three reviewers run concurrently, each bound to one category;
  their findings accumulate via a state reducer (`Annotated[list[Finding], add]`).
- **Verify** — an LLM-as-judge node drops false positives and duplicates,
  writing the confirmed subset to a separate channel.
- Output is structured (Pydantic) with **tolerant parsing**, so a weak model's
  malformed JSON never crashes the graph.

## Results

10-snippet golden set (7 seeded bugs, 3 clean), model `openai/gpt-5.4-nano`:

| pipeline     | precision | recall | TP  | FP  | FN  |
| ------------ | --------- | ------ | --- | --- | --- |
| naive (raw)  | 0.22      | 1.00   | 7   | 25  | 0   |
| **verified** | **0.38**  | 0.71   | 5   | 8   | 2   |

The verifier cut **17 of 25 false positives** (precision 0.22 → 0.38), at the
cost of recall (1.00 → 0.71 — it dropped 2 real bugs). That precision/recall
trade-off is exactly what the eval makes visible and gateable; tuning the judge
prompt or using a stronger model for the verify stage is the next lever.
_(Built deliberately on a weak model to keep a measurable naive baseline.)_

## How it's measured

Eval-first: `golden_bugs.jsonl` defines "correct" before the agent existed. A
finding matches a seeded bug when **category agrees and line ranges overlap**:

```python
def is_match(finding, seeded) -> bool:
    return (finding.category == seeded["category"]
            and finding.line_start <= seeded["line_end"]
            and seeded["line_start"] <= finding.line_end)
```

From that: TP / FP / FN → precision & recall. `eval.py` doubles as a **gate**
(exits non-zero below thresholds), run manually in CI via GitHub Actions.

## Run it

```bash
pip install -r requirements.txt
echo "AI_GATEWAY_API_KEY=..." > .env     # any OpenAI-compatible gateway
python graph.py     # demo on one snippet (prints naive vs verified)
python eval.py      # full eval + gate over the golden set
```

Optional tracing: set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` to see
every run in LangSmith.

## Layout

```
├── models.py          # Finding, Review, ReviewState
├── prompts.py         # reviewer + verifier prompts
├── parsing.py         # tolerant JSON -> Review
├── llm.py             # client, config, cache/env bootstrap
├── graph.py           # graph assembly (build_graph) + CLI
├── eval.py            # precision/recall + CI gate
├── golden_bugs.jsonl  # labeled golden set (the "test", written first)
├── snippets/          # s01..s10, no leaked hints
└── .github/workflows/eval.yml   # manual eval gate
```

## Stack

Python 3.13 · LangGraph · LangChain · Pydantic · OpenAI-compatible gateway
(Vercel AI Gateway) · LangSmith (tracing) · GitHub Actions (eval gate).
