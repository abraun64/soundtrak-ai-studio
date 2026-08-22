#!/usr/bin/env python3
"""SYS-138 Part 2 — the verification level runner.

Part 1 (docs/specs/system-verification.md) defines what "done" means for a change to the
system itself: four levels, a trigger table for choosing one, and repeatable steps. This is
the tool that makes L0/L1/L3 one command each, and that reports tickets closed WITHOUT a
recorded verification so a silent close can't pass as a verified one.

  python .claude/skills/system-manager/verify.py --criteria           # which level does this need?
  python .claude/skills/system-manager/verify.py --level 0 <file>...  # sanity: it parses
  python .claude/skills/system-manager/verify.py --level 1            # smoke: system runs end to end
  python .claude/skills/system-manager/verify.py --level 3            # unit: every test_*.py suite
  python .claude/skills/system-manager/verify.py --audit              # closures missing `verified:`

L2 (behavioural UAT) is deliberately NOT automatable here. Its whole point is running the real
entry point an operator would use and reading the rendered result — a script that stood in for
that would be the file-existence "UAT" all over again. `--criteria` prints its checklist; the
evidence goes in the ticket's `verified:` field.

Exit 0 = pass, 1 = fail. Worktree-aware: DATA (system/) resolves to the main checkout, CODE
runs from the checkout you invoke it in.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths

    DATA = repo_paths.data_root(ROOT)
except ImportError:  # noqa: BLE001
    DATA = ROOT
SYSTEM_DIR = DATA / "system"
SKILLS = ROOT / ".claude" / "skills"

# The framework went live on this date. Tickets closed BEFORE it are not expected to carry a
# `verified:` field — auditing 140 historical closures would be noise that trains the operator
# to ignore the report, which is the failure mode this whole area keeps producing.
ADOPTED = "2026-08-22"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

CRITERIA = """\
Choosing a verification level (docs/specs/system-verification.md)

  Take the HIGHEST level any criterion reaches — never the cheapest that applies.
  Levels stack: L2 includes L1, L1 includes L0.

  If the change...                                                       Minimum
  ---------------------------------------------------------------------  -------
  is prose / a comment / a doc link, and nothing executes it              L0
  touches shared code (render-html, .claude/hooks, .claude/lib, a skill)  L1
  goes into the SEED (a stranger runs it on a machine you can't see)      L1 + doctor + leak gate
  changes WHAT AN OPERATOR SURFACE SAYS                                   L2
  WRITES DATA the operator can't trivially undo (backlog, asset states)   L2
  is a GATE, GUARD or DIAGNOSTIC                                          L2
  contains LOGIC WITH CASES (parser, derivation, threshold, recursion)    L3
  REPEATS a class of bug that has shipped before                          L3 + reproduce it

L2 - behavioural UAT is run by hand. The checklist:
  1. Name the outcome first, in the operator's words.
  2. Put the system in the "before" state.
  3. Run the REAL entry point an operator would use - not a reimplementation.
  4. Read the RENDERED output (the .html they open, the text they'd see) - not the source.
  5. Assert the outcome sentence from step 1.
  6. Break the input, re-run, and watch it go red. A guard only ever seen green is untested.
  7. Record the command and the proving line in the ticket's `verified:` field.
"""


def _run(args: list[str], label: str) -> bool:
    print(f"  ... {label}")
    try:
        r = subprocess.run([sys.executable] + args, cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=600)
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL {label} — {e}")
        return False
    if r.returncode != 0:
        tail = [ln for ln in (r.stdout or r.stderr or "").splitlines() if ln.strip()][-3:]
        print(f"  FAIL {label}")
        for ln in tail:
            print(f"       {ln}")
        return False
    print(f"  PASS {label}")
    return True


def level0(files: list[str]) -> int:
    """Sanity — the change is loaded and parses. The floor, never the answer."""
    if not files:
        print("L0 needs the file(s) to check: --level 0 <path>...", file=sys.stderr)
        return 1
    import ast

    ok = True
    print("L0 · sanity")
    for f in files:
        p = Path(f)
        try:
            text = p.read_text(encoding="utf-8")
            if p.suffix == ".py":
                ast.parse(text)
            elif p.suffix in (".yaml", ".yml"):
                import yaml

                yaml.safe_load(text)
            print(f"  PASS {p.name} parses")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL {p.name} — {e}")
            ok = False
    return 0 if ok else 1


def level1() -> int:
    """Smoke — the system still runs end to end."""
    print("L1 · smoke")
    smoke = SKILLS / "system-smoke-test" / "smoke_test.py"
    if not smoke.exists():
        print("  FAIL system-smoke-test not present")
        return 1
    return 0 if _run([str(smoke)], "system smoke test") else 1


def unit_suites() -> list[Path]:
    """Every stdlib test suite in the repo. They live beside the module they guard, so the
    glob is the registry — a new suite is picked up with no wiring."""
    out: list[Path] = []
    for base in (ROOT / ".claude" / "lib", ROOT / ".claude" / "skills"):
        for p in sorted(base.rglob("test_*.py")):
            if "_archive" not in p.parts and "__pycache__" not in p.parts:
                out.append(p)
    return out


def level3() -> int:
    """Unit — every suite, at its boundaries."""
    print("L3 · unit")
    suites = unit_suites()
    if not suites:
        print("  FAIL no test_*.py suites found — that is itself the finding")
        return 1
    ok = all(_run([str(p)], p.relative_to(ROOT).as_posix()) for p in suites)
    print(f"  {len(suites)} suite(s) run")
    return 0 if ok else 1


def _closed_on(item: dict) -> str:
    """When the ticket was CLOSED — which is not `date:` (that is when it was RAISED). Every
    resolution in this backlog opens with its own date ("2026-08-22 — RESOLVED. ..."), so read
    that rather than adding a field the schema doesn't need. Falls back to `date:`."""
    import re

    m = re.match(r"\s*(\d{4}-\d{2}-\d{2})", str(item.get("resolution") or ""))
    return m.group(1) if m else str(item.get("date", ""))


def audit() -> int:
    """Report tickets closed since the framework was adopted that carry no `verified:`.

    This is the enforcement surface, and it is deliberately a REPORT, not a blocker. The agreed
    rule is "you may not close without RECORDING what you did; you may record a lower level with
    a stated reason" — a hard must-pass gate is what produced the file-existence UAT this
    framework exists to prevent. An unrecorded close is visible here and in the weekly digest.
    """
    try:
        import yaml

        items = (yaml.safe_load((SYSTEM_DIR / "backlog.yaml").read_text(encoding="utf-8"))
                 or {}).get("items") or []
    except Exception as e:  # noqa: BLE001
        print(f"verify: cannot read backlog.yaml — {e}", file=sys.stderr)
        return 1

    missing = [i for i in items
               if str(i.get("status", "")).strip().lower() == "done"
               and _closed_on(i) >= ADOPTED
               and not str(i.get("verified", "")).strip()]
    if not missing:
        print(f"verify: OK — every ticket closed since {ADOPTED} records how it was verified.")
        return 0
    print(f"verify: {len(missing)} ticket(s) closed since {ADOPTED} with no `verified:` field:",
          file=sys.stderr)
    for i in missing:
        print(f"  x {i.get('id')} — {str(i.get('title'))[:70]}", file=sys.stderr)
    print("  Add `verified: \"L<n> — <what was run> — <the line that proved it>\"` to each, "
          "or state the level you waived to and why.", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run a verification level (SYS-138).")
    ap.add_argument("--level", type=int, choices=(0, 1, 3),
                    help="0 sanity · 1 smoke · 3 unit (L2 is run by hand — see --criteria)")
    ap.add_argument("files", nargs="*", help="files to check (L0 only)")
    ap.add_argument("--criteria", action="store_true", help="print the level-choosing table + L2 checklist")
    ap.add_argument("--audit", action="store_true", help="report closures with no recorded verification")
    a = ap.parse_args(argv)

    if a.criteria:
        print(CRITERIA)
        return 0
    if a.audit:
        return audit()
    if a.level == 0:
        return level0(a.files)
    if a.level == 1:
        return level1()
    if a.level == 3:
        return level3()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
