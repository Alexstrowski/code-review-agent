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
