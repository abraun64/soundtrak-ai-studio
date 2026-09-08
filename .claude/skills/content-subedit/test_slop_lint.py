#!/usr/bin/env python3
"""
Regression tests for slop_lint.py — the deterministic half of the anti-slop gate.

Stdlib only (no pytest — it isn't installed). Run directly:
    python .claude/skills/content-subedit/test_slop_lint.py
Exit 0 = all pass; exit 1 = one or more failed.

The system smoke-test runs this.

ON THE FIXTURES. SYS-154 says the fix has a ready-made regression corpus: the Acme Co library at
2026-08-28 (known-bad, passed both existing gates) and its corrected version (known-good). Only
half of that survived — the known-bad text was never committed, and a single auto-backup is that
campaign's entire git history, so it cannot be re-run. What the ticket DID record is the
measurements: "rather than" x95 = 3.4 per 1000 words, worst page 7.8 per 1000, five instances in
five consecutive sentences, ~18% short declarative fragments. KNOWN_BAD below reproduces that
signature. It is a stand-in for the lost corpus and is labelled as one — not evidence that the
original text would have flagged, but a guarantee that text with the recorded shape does.
"""
from __future__ import annotations
import importlib.util
import sys
import tempfile
from pathlib import Path

_SL = Path(__file__).resolve().parent / "slop_lint.py"
_spec = importlib.util.spec_from_file_location("_slop_lint", _SL)
_sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sl)

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


# The recorded signature: one construction over and over, including five in five consecutive
# sentences, and sentences that never change gear.
KNOWN_BAD = "\n\n".join([
    "Show the child what to do rather than what to stop.",
    "Offer a choice rather than an instruction.",
    "Name the feeling rather than the behaviour.",
    "Sit beside them rather than opposite them.",
    "Use your body rather than your voice.",
    "The noise goes up, the bodies come down, and the breathing lands.",
    "Bringing a room down only holds if there is somewhere for it to land.",
    "Three things sit underneath all eight.",
    "That is the win, and it is the whole thing.",
    "The point is the rhythm rather than the words.",
    "Getting low is the trick rather than getting loud.",
    "The work is the setup rather than the session.",
    "The difference is the pause rather than the prompt.",
    "The result is calm rather than quiet.",
    "The outcome is trust rather than compliance.",
    "The answer is presence rather than pressure.",
    "The challenge is patience rather than technique.",
    "Offer water rather than juice.",
    "Choose one book rather than three.",
    "Set out two trays rather than six.",
])

# Plain instructional prose: a person or a named thing acts, lengths vary, no repeated frame.
KNOWN_GOOD = "\n\n".join([
    "Put out two shallow trays of water on the deck before the children come outside.",
    "Add a few cups.",
    "Ask one child to pour for another, and watch what they do with the turn-taking; most "
    "groups sort this out themselves within a minute or two, and the ones that do not usually "
    "need a second cup rather than an adult.",
    "Bring the trays in when the water goes cloudy.",
    "Educators often find the first ten minutes are the loudest, and then it settles.",
    "If a child tips a tray, hand them the cloth and wait.",
    "You are teaching the clean-up, not preventing the spill.",
    "Dry the deck before nap so nobody slips on the way in.",
    "One educator can run this for eight children; two makes it calmer, though it is not "
    "required if the space is enclosed and you can see every child from where you stand.",
    "Pack the cups in the same tub each time so the next person can find them.",
    "Ask the room leader where the spare towels live.",
    "Check the water temperature with your wrist first.",
    "Toddlers will drink it, so use fresh water every session.",
    "Tell families at pick-up if their child got soaked; a spare set of clothes solves it "
    "tomorrow.",
    "Write the date on the tub when you refill the cups.",
    "Some children will only watch for the first few sessions, and that is fine.",
])


def _lint(text: str, name: str = "sample.md", **over):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / name
        p.write_text(text, encoding="utf-8")
        cfg = dict(_sl.DEFAULTS)
        cfg.update(over)
        return _sl.analyse([p], cfg, [])["per_file"][p]["findings"]


def test_known_bad_is_flagged() -> None:
    """The whole point. Both existing gates passed this texture: content-subedit reported clean
    and the Brand Manager scored tone 5/5, because neither counts."""
    f = _lint(KNOWN_BAD)
    checks = {x["check"] for x in f}
    check("the known-bad signature is flagged at all", bool(f), "nothing flagged")
    check("its repeated construction is named", "construction repetition" in checks, f"{checks}")
    check("the finding cites the offending lines",
          any(x["worst"] for x in f if x["check"] == "construction repetition"))


def test_known_good_passes() -> None:
    """A gate that fires on good prose gets ignored exactly like one that never fires."""
    f = _lint(KNOWN_GOOD)
    check("plain instructional prose passes", not f, f"flagged: {[x['detail'] for x in f]}")


def test_clustering_is_caught_even_when_the_rate_is_low() -> None:
    """"Five in five consecutive sentences" was the operator's loudest complaint, and it can hide
    under a healthy overall rate — which is exactly why the raw count is not enough."""
    padding = " ".join(f"Educators set out the {n} tub before lunch and check it after."
                       for n in range(120))
    f = _lint(KNOWN_BAD.split("\n\n")[0] + "\n\n"
              + "\n\n".join(KNOWN_BAD.split("\n\n")[1:5]) + "\n\n" + padding)
    clustered = [x for x in f if "consecutive sentences" in x["detail"]]
    check("a cluster is caught even when the overall rate is fine", bool(clustered),
          f"got {[x['detail'] for x in f]}")


def test_exemption_silences_a_named_brand_device() -> None:
    """A deliberate device is not a defect. content-subedit already lets the tenant Brand Context
    override its baseline; the same must hold here or the gate becomes something to route around."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sample.md"
        p.write_text(KNOWN_BAD, encoding="utf-8")
        f = _sl.analyse([p], dict(_sl.DEFAULTS), ["rather than"])["per_file"][p]["findings"]
        check("an exempt phrase stops being counted",
              not any('"rather than"' in x["detail"] for x in f),
              f"{[x['detail'] for x in f]}")


def test_it_never_reports_ok_having_read_nothing() -> None:
    """A linter that finds no files must not exit 0. That is the failure this system keeps
    producing — a green check that examined nothing."""
    check("no readable files is an error, not a pass", _sl.main(["/no/such/path/at/all"]) == 2)


def test_prose_zones_only() -> None:
    """Code blocks and <details> are not prose and must not skew the statistics."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sample.md"
        p.write_text("Real prose here, of a normal length, written by a person.\n\n"
                     "```\nrather than rather than rather than rather than\n```\n\n"
                     "<details>\nrather than rather than rather than\n</details>\n",
                     encoding="utf-8")
        lines = [s for _, s in _sl.prose_lines(p)]
        check("fenced code is excluded", not any("rather than rather" in s for s in lines))
        check("details blocks are excluded", not any("rather than rather" in s for s in lines))


def main() -> int:
    print("slop-lint regression tests")
    test_known_bad_is_flagged()
    test_known_good_passes()
    test_clustering_is_caught_even_when_the_rate_is_low()
    test_exemption_silences_a_named_brand_device()
    test_it_never_reports_ok_having_read_nothing()
    test_prose_zones_only()
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll slop-lint tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
