#!/usr/bin/env python3
"""
Self-contained unit test for the surface-honesty guard (SYS-059).

No filesystem writes to real campaigns — builds a throwaway campaign tree in a temp
dir, injects both honest and fabricated ✅s, and asserts the guard flags exactly the
fabricated ones. Also unit-tests the classifier directly.

    python .claude/skills/cm-audit/test_surface_honesty.py

Exit 0 = all assertions passed; exit 1 = a failure (printed).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

try:  # Windows consoles default to cp1252, which can't encode ✅
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import surface_honesty as sh  # noqa: E402

CHECK = "✅"
failures: list[str] = []


def expect(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


# ── classifier ───────────────────────────────────────────────────────────────
for name in ("Brief", "Selected concept", "Plan", "Plan ✅", "Gallery",
             "A4 · Edition #1", "Phase 5 launch plan"):
    expect(sh.classify(name) == "gated", f"expected GATED: {name!r} -> {sh.classify(name)}")

for name in ("Concept trio", "Trio", "concept moodboard",
             "Editorial backlog", "Influencer targets", "Research notes"):
    expect(sh.classify(name) == "ungated", f"expected UNGATED: {name!r} -> {sh.classify(name)}")

# SYS-067: the Insight Brief is no longer a flat deny — it's approved AS PART OF the Brief,
# handled conditionally in the scanners. classify() alone returns 'unknown' for it.
expect(sh.classify("Insight Brief") == "unknown", "Insight Brief should be conditional, not flat-ungated")


# ── end-to-end scan over a throwaway campaign tree ───────────────────────────
def _build(root: Path) -> None:
    slug = "scratch-campaign"
    c = root / "campaigns" / slug
    (c / "assets").mkdir(parents=True)

    # Dashboard md: 2 honest ✅ (Brief, Selected) + 2 FABRICATED (Insight Brief, Trio)
    # + a bare ✅ in a status/history cell that must be IGNORED (not an artifact link).
    (c / f"{slug}.md").write_text(
        "# Dashboard\n\n"
        "| 1 | Fact-Find | ✅ Approved | [Brief ✅](brief.html) · "
        "[Insight Brief ✅](insight-brief.html) |\n"
        "| 2 | Concept | ✅ Approved | [Selected ✅](concepts/selected.html) · "
        "[Trio ✅](concepts/concept-trio.html) |\n"
        "| hist | thing done | ✅ |\n",
        encoding="utf-8",
    )

    # campaign.yaml: 1 honest gated title + 1 fabricated ungated title.
    (c / "campaign.yaml").write_text(
        "tenant: scratch\n"
        "phases:\n"
        "  - id: 1\n"
        "    artifacts:\n"
        "      - { title: \"Brief ✅\", href: brief.html }\n"
        "      - { title: \"Editorial backlog ✅\", href: backlog.html }\n",
        encoding="utf-8",
    )


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    _build(root)
    violations = sh.scan(root)
    offenders = sorted(v.offending for v in violations)

    # Exactly 3 fabricated ✅s: Insight Brief (md), Trio (md), Editorial backlog (yaml).
    expect(len(violations) == 3, f"expected 3 violations, got {len(violations)}: {offenders}")
    expect(any("Insight Brief" in o for o in offenders), "missed fabricated 'Insight Brief ✅' in md")
    expect(any("Trio" in o for o in offenders), "missed fabricated 'Trio ✅' in md")
    expect(any("Editorial backlog" in o for o in offenders), "missed fabricated title in yaml")

    # The honest gated ✅s and the bare status ✅ must NOT be flagged.
    expect(not any("Brief ✅" == o or o == "✅ Brief" for o in offenders), "false-flagged the honest Brief ✅")
    expect(not any("Selected" in o for o in offenders), "false-flagged the honest Selected ✅")

    # A fully clean tree yields zero violations.
    with tempfile.TemporaryDirectory() as td2:
        clean = Path(td2)
        cc = clean / "campaigns" / "clean-camp"
        (cc / "assets").mkdir(parents=True)
        (cc / "clean-camp.md").write_text(
            "| 1 | Brief | ✅ | [Brief ✅](brief.html) · [Insight Brief](insight-brief.html) |\n",
            encoding="utf-8",
        )
        (cc / "campaign.yaml").write_text(
            "phases:\n  - id: 1\n    artifacts:\n      - { title: \"Brief ✅\", href: b.html }\n",
            encoding="utf-8",
        )
        expect(sh.scan(clean) == [], "clean tree should have zero violations")


# ── SYS-067: Insight Brief ✅ is CONDITIONAL on Brief approval ────────────────
# Legitimate once the Phase-1 Brief is approved…
with tempfile.TemporaryDirectory() as td3:
    ap = Path(td3)
    ca = ap / "campaigns" / "approved-camp"
    (ca / "assets").mkdir(parents=True)
    (ca / "approved-camp.md").write_text(
        "| 1 | Brief | ✅ Approved | [Brief ✅](brief.html) · [Insight Brief ✅](insight-brief.html) |\n",
        encoding="utf-8",
    )
    (ca / "campaign.yaml").write_text(
        'phases:\n  - id: 1\n    status: "✅ Approved"\n    artifacts:\n'
        '      - { title: "Insight Brief ✅", href: ib.html }\n',
        encoding="utf-8",
    )
    av = sh.scan(ap)
    expect(av == [], f"approved Brief: Insight Brief ✅ must be ALLOWED, got {[v.offending for v in av]}")

# …but flagged while the Brief is still pending.
with tempfile.TemporaryDirectory() as td4:
    pp = Path(td4)
    cp = pp / "campaigns" / "pending-camp"
    (cp / "assets").mkdir(parents=True)
    (cp / "pending-camp.md").write_text(
        "| 1 | Brief | 🟡 Draft | [Insight Brief ✅](insight-brief.html) |\n", encoding="utf-8",
    )
    (cp / "campaign.yaml").write_text(
        'phases:\n  - id: 1\n    status: "🟡 Draft"\n    artifacts: []\n', encoding="utf-8",
    )
    pv = sh.scan(pp)
    expect(len(pv) == 1 and "Insight Brief" in pv[0].offending,
           f"pending Brief: Insight Brief ✅ must be FLAGGED, got {[v.offending for v in pv]}")


# ── Plain-language title: the Insight Brief is identified by its link target ──
# Surfaces now call it "Audience research"; "research" alone is an ungated input, so the
# guard must recognise insight-brief.html and apply the SYS-067 condition (2026-10-02).
with tempfile.TemporaryDirectory() as td5:
    for status, want in (('"✅ Approved"', 0), ('"🟡 Draft"', 1)):
        rp = Path(td5) / f"r{want}"
        cr = rp / "campaigns" / "renamed-camp"
        (cr / "assets").mkdir(parents=True)
        (cr / "campaign.yaml").write_text(
            f'phases:\n  - id: 1\n    status: {status}\n    artifacts:\n'
            '      - { title: "Audience research ✅", href: "insight-brief.html" }\n',
            encoding="utf-8",
        )
        rv = sh.scan(rp)
        expect(len(rv) == want,
               f"'Audience research' -> insight-brief.html with Brief {status}: expected {want} "
               f"violation(s), got {[v.offending for v in rv]}")
    # A research input that is NOT the Insight Brief is still an ungated input.
    op = Path(td5) / "other"
    co = op / "campaigns" / "other-camp"
    (co / "assets").mkdir(parents=True)
    (co / "campaign.yaml").write_text(
        'phases:\n  - id: 1\n    status: "✅ Approved"\n    artifacts:\n'
        '      - { title: "Audience research ✅", href: "research/raw-voice.html" }\n',
        encoding="utf-8",
    )
    expect(len(sh.scan(op)) == 1, "research input that is not the Insight Brief must stay FLAGGED")

if failures:
    print(f"FAIL — {len(failures)} assertion(s):")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("PASS — surface-honesty guard: classifier + scan (catches fabricated ✅, "
      "ignores honest ✅ + bare status ✅ + clean tree)")
sys.exit(0)
