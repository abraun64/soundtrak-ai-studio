#!/usr/bin/env python3
"""SYS-087 — operator-surface readability lint (the deterministic half of the CM
"review-ready" gate). Flags internal-system jargon a marketer-who-didn't-write-it
cannot be expected to parse. Pair with the LLM "cold-reader" pass (see SKILL.md) for
the author-context opacity a denylist can't catch.

The gate's two rules (its contract):
  1. Assume the reader is a MARKETER but NOT the author (no reliance on author context).
  2. No jargon unless it is marketing-industry-accepted.

Usage:
  python jargon_lint.py <file.md|.html> [<file> ...]   # report; exit 1 if any jargon
  python jargon_lint.py <file> --quiet                 # exit code only, no output
"""
import re
import sys
import html as _html
from pathlib import Path

# (regex, label, suggested plain rewrite) — internal-system jargon. Seeded from the
# 2026-07-15 operator-feedback pass; extend as new jargon is caught. Case-insensitive.
DENYLIST = [
    (r"§\s?\d+\w*",                      "§-section cross-ref", "name the section in plain words, don't cross-ref by number"),
    (r"\bclean[- ]?room\b",              "clean-room",          "'built fresh — nothing reused from the old campaign'"),
    (r"\bgrill[- ]?me\b",                "grill-me",            "'the intake interview'"),
    (r"\bgraduate[- ]then[- ]cite\b",    "graduate-then-cite",  "'saved to the playbook, then referenced'"),
    (r"\braw[- ]?voice\b",               "raw-voice",           "'direct customer quotes'"),
    (r"\bgate[- ]?cleared\b",            "gate-cleared",        "'passed review' / 'approved'"),
    (r"\bfoundation[- ]?shaped\b",       "foundation-shaped",   "spell out what it means for the reader"),
    (r"\bCM[- ]?inferred\b",             "CM-inferred",         "'we inferred' / 'our read'"),
    (r"\bWave\s?\d+\b",                  "Wave N",              "name what the batch is, not its internal wave number"),
    (r"\bSDT\b",                         "SDT",                 "plain-language the behavioural driver (not the acronym)"),
    (r"\bmoral[- ]disgust\b",            "moral-disgust",       "plain-language the driver"),
    (r"\bTBD\b",                         "TBD-as-status",       "say what's pending + when it resolves, not a bare 'TBD'"),
]

# Marketing-industry-accepted — documented so the cold-reader + humans know the bar.
# These are NOT flagged (the denylist is disjoint from this list by design).
ALLOWLIST = [
    "KPI", "CTA", "positioning", "single-minded proposition", "top-of-funnel",
    "mental availability", "funnel", "awareness", "CPA", "CTR", "95:5",
    "call to action", "conversion", "engagement", "reach",
]


def visible_text(raw: str, is_html: bool) -> str:
    if is_html:
        raw = re.sub(r"<style.*?</style>|<script.*?</script>", " ", raw, flags=re.S)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = _html.unescape(raw)
    return raw


def lint(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    is_html = path.suffix.lower() == ".html"
    findings = []
    for i, line in enumerate(raw.splitlines(), 1):
        text = visible_text(line, is_html)
        for pat, label, fix in DENYLIST:
            for m in re.finditer(pat, text, re.I):
                findings.append({"line": i, "term": m.group(0).strip(), "label": label, "fix": fix})
    return findings


def main() -> int:
    quiet = "--quiet" in sys.argv
    files = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not files:
        print("usage: jargon_lint.py <file> [<file> ...] [--quiet]")
        return 2
    total = 0
    for f in files:
        p = Path(f)
        if not p.exists():
            print(f"not found: {p}")
            return 2
        found = lint(p)
        total += len(found)
        if quiet:
            continue
        if not found:
            print(f"OK   {p.name}: no internal jargon flagged.")
        else:
            print(f"FLAG {p.name}: {len(found)} internal-jargon hit(s) — plain-language before surfacing:")
            for x in found:
                print(f"     L{x['line']}: '{x['term']}' [{x['label']}] -> {x['fix']}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
