import json
import sys
import time
from pathlib import Path

from graph import build_graph
from llm import bootstrap
from models import Finding

MIN_PRECISION = 0.35
MIN_RECALL = 0.65
SLEEP_SECONDS = 40


def metrics(rows: list[tuple[int, int, int]]) -> tuple[int, int, int, float, float]:
    tp = sum(r[0] for r in rows)
    fp = sum(r[1] for r in rows)
    fn = sum(r[2] for r in rows)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return tp, fp, fn, precision, recall


def is_match(finding: Finding, seeded: dict) -> bool:
    return (
        finding.category == seeded["category"]
        and finding.line_start <= seeded["line_end"]
        and seeded["line_start"] <= finding.line_end
    )


def score(findings: list[Finding], seeded: list[dict]) -> tuple[int, int, int]:
    tp = sum(any(is_match(f, s) for f in findings) for s in seeded)
    fn = len(seeded) - tp
    fp = sum(not any(is_match(f, s) for s in seeded) for f in findings)
    return tp, fp, fn


if __name__ == "__main__":
    bootstrap()
    graph = build_graph()

    golden = [
        json.loads(line)
        for line in Path("golden_bugs.jsonl").read_text().splitlines()
        if line.strip()
    ]

    naive_rows, verified_rows = [], []
    for entry in golden:
        code = Path(entry["file"]).read_text()
        t0 = time.monotonic()
        result = graph.invoke({"code": code, "findings": [], "verified": []})
        was_cached = time.monotonic() - t0 < 3  # instantáneo ⇒ vino del caché
        naive_rows.append(score(result["findings"], entry["bugs"]))
        verified_rows.append(score(result["verified"], entry["bugs"]))
        tag = " (cached)" if was_cached else ""
        print(
            f"{entry['id']}: naive={len(result['findings'])} verified={len(result['verified'])}{tag}"
        )
        if not was_cached:  # solo throttlea cuando la llamada fue real
            time.sleep(SLEEP_SECONDS)

    print()
    for label, rows in [("NAIVE", naive_rows), ("VERIFIED", verified_rows)]:
        tp, fp, fn, p, r = metrics(rows)
        print(f"{label:9} TP={tp} FP={fp} FN={fn}  P={p:.2f}  R={r:.2f}")

    # GATE: el build falla si verified cae bajo el umbral
    _, _, _, p, r = metrics(verified_rows)
    if p < MIN_PRECISION or r < MIN_RECALL:
        print(
            f"GATE FAILED: verified P={p:.2f} R={r:.2f} < "
            f"min P={MIN_PRECISION} R={MIN_RECALL}"
        )
        sys.exit(1)
    print("GATE PASSED")
