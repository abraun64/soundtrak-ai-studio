#!/usr/bin/env python3
"""
Regression tests for _cadence_common.file_new_ideas — the deduper every scheduled cadence
files findings through.

Stdlib + PyYAML only (no pytest — it isn't installed). Run directly:
    python .claude/skills/cadences/test_cadence_dedup.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

The system smoke-test runs this. Tests write only to a temp dir — the real system/ is never
touched (the module's SYSTEM_DIR / TOMBSTONES globals are redirected per test).
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cadence_common as cc  # noqa: E402

_FAILED: list[str] = []
FP = "stale-sweep:parked-assets"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


class _System:
    """A throwaway system/ dir with the three stores a cadence reads and writes."""

    def __init__(self, ideas: str = "", backlog: str = ""):
        self._td = tempfile.TemporaryDirectory()
        self.dir = Path(self._td.name)
        (self.dir / "ideas.yaml").write_text("# inbox\nitems:\n" + ideas, encoding="utf-8")
        (self.dir / "backlog.yaml").write_text("# board\nitems:\n" + backlog, encoding="utf-8")
        (self.dir / "audit-log.yaml").write_text("# audit\nentries:\n", encoding="utf-8")

    def __enter__(self):
        self._saved = (cc.SYSTEM_DIR, cc.TOMBSTONES)
        cc.SYSTEM_DIR = self.dir
        cc.TOMBSTONES = self.dir / "cadence-tombstones.yaml"
        return self

    def __exit__(self, *a):
        cc.SYSTEM_DIR, cc.TOMBSTONES = self._saved
        self._td.cleanup()

    def file(self, title: str, fingerprint: str = FP) -> list:
        return cc.file_new_ideas([title], raised_by="stale-sweep", today="2026-08-22",
                                 summary="n/a", source="cadence (stale-sweep)",
                                 fingerprint=fingerprint)


def test_count_drift_does_not_refile() -> None:
    """Counts live in the title, so "31 asset(s)..." and "32 asset(s)..." are different strings.
    Under title-dedupe the same standing finding refiled every time the number moved
    (observed live 2026-08-22)."""
    with _System() as s:
        first = s.file("31 asset(s) parked in 'For Human Review' over 10 days")
        again = s.file("32 asset(s) parked in 'For Human Review' over 10 days")
        check("a count change does not refile the same finding",
              len(first) == 1 and again == [], f"first={first} again={again}")


def test_promoted_and_retitled_does_not_refile() -> None:
    """Triage MANDATES sharpening the title on promote — which under title-dedupe broke the
    match by construction, so every promoted cadence finding refiled on the next run. The two
    rules were in direct conflict; the fingerprint is what triage carries across."""
    promoted = ('  - id: SYS-143\n    title: "Freshness gate misses document surfaces"\n'
                f'    fingerprint: "{FP}"\n    status: todo\n')
    with _System(backlog=promoted) as s:
        check("a promoted, retitled finding does not refile",
              s.file("31 asset(s) parked in 'For Human Review' over 10 days") == [])


def test_killed_stays_killed() -> None:
    """A kill REMOVES the idea, leaving nothing to match on, so the finding returned forever.
    The tombstone is what makes a kill stick."""
    with _System() as s:
        cc.add_tombstone(FP, "IDEA-059", "2026-08-06", "Belongs in the tasks queue.")
        check("a killed finding is not raised again",
              s.file("31 asset(s) parked in 'For Human Review' over 10 days") == [])
        check("the tombstone store is readable back", FP in cc.load_tombstones())
        check("tombstoning the same fingerprint twice is a no-op",
              cc.add_tombstone(FP, "IDEA-059", "2026-08-06") is False)


def test_done_ticket_does_not_suppress() -> None:
    """A DONE ticket means the problem was FIXED. Detecting it again is a NEW occurrence and
    must be raised — otherwise "we fixed it once" quietly becomes "never tell me again"."""
    fixed = ('  - id: SYS-143\n    title: "Freshness gate misses document surfaces"\n'
             f'    fingerprint: "{FP}"\n    status: done\n')
    with _System(backlog=fixed) as s:
        check("a recurrence after a DONE ticket is still raised",
              len(s.file("31 asset(s) parked in 'For Human Review' over 10 days")) == 1)


def test_distinct_findings_still_file() -> None:
    """Suppression must be surgical: a different category, and a different tenant scope, are
    different findings."""
    with _System() as s:
        a = s.file("7 rendered surface(s) older than their source", "stale-sweep:stale-surfaces")
        b = s.file("gamma playbook 40d behind", "tenant-brand-drift:playbook-lag:gamma")
        c = s.file("acme playbook 40d behind", "tenant-brand-drift:playbook-lag:acme")
        check("a different category still files", len(a) == 1, f"got {a}")
        check("a different tenant scope still files", len(b) == 1 and len(c) == 1, f"{b} {c}")
        check("the filed ids are unique", len({*a, *b, *c}) == 3, f"{a} {b} {c}")


def test_fingerprint_is_written_to_the_record() -> None:
    """Triage can only carry the fingerprint onto the ticket if the idea actually stores it."""
    import yaml
    with _System() as s:
        filed = s.file("31 asset(s) parked in 'For Human Review' over 10 days")
        items = yaml.safe_load((s.dir / "ideas.yaml").read_text(encoding="utf-8"))["items"]
        rec = [i for i in items if i["id"] == filed[0]][0]
        check("the filed idea carries its fingerprint", rec.get("fingerprint") == FP,
              f"got {rec.get('fingerprint')!r}")
        check("ideas.yaml stays parseable after the append", len(items) == 1)


def test_titles_still_dedupe_without_a_fingerprint() -> None:
    """Records that predate fingerprints have none, so the title fallback has to keep working."""
    with _System() as s:
        first = s.file("some legacy finding", fingerprint=None)
        again = s.file("some legacy finding", fingerprint=None)
        check("title dedupe still applies when no fingerprint is given",
              len(first) == 1 and again == [], f"first={first} again={again}")


def test_a_merged_ticket_owns_every_finding_it_absorbed() -> None:
    """A MERGE folds records into one surviving ticket, so that ticket ends up tracking several
    findings at once (2026-08-22: SYS-146 absorbed IDEA-066's diagnosis and the killed SYS-145,
    ending up with three). A single-value `fingerprint:` would keep one and silently release the
    rest to refile on the next run. It also has to RELEASE them together: once the owning ticket
    is done the problem is fixed, so every finding it absorbed becomes raisable again."""
    owner = ('  - id: SYS-146\n    title: "Public docs behind the specs"\n'
             "    fingerprint:\n"
             '      - "weekly-digest:diagnostic:docs-audit"\n'
             '      - "weekly-digest:diagnostic:smoke-test"\n'
             '      - "docs-audit:public-behind-specs"\n'
             "    status: todo\n")
    with _System(backlog=owner) as s:
        for fp in ("weekly-digest:diagnostic:docs-audit",
                   "weekly-digest:diagnostic:smoke-test",
                   "docs-audit:public-behind-specs"):
            check(f"the merged ticket suppresses {fp.split(':')[-1]}",
                  s.file("some finding", fp) == [])
        check("an unrelated finding still files",
              len(s.file("unrelated", "stale-sweep:parked-assets")) == 1)

    with _System(backlog=owner.replace("    status: todo", "    status: done")) as s:
        check("all absorbed findings are released together when the owner closes",
              len(s.file("it came back", "weekly-digest:diagnostic:smoke-test")) == 1)


def test_a_string_fingerprint_still_works() -> None:
    """Every record on the board today stores a plain string; the list form is additive."""
    single = ('  - id: SYS-143\n    title: "One finding"\n'
              f'    fingerprint: "{FP}"\n    status: todo\n')
    with _System(backlog=single) as s:
        check("a plain string fingerprint still suppresses", s.file("a finding") == [])


def main() -> int:
    print("cadence dedupe regression tests")
    test_count_drift_does_not_refile()
    test_promoted_and_retitled_does_not_refile()
    test_killed_stays_killed()
    test_done_ticket_does_not_suppress()
    test_distinct_findings_still_file()
    test_fingerprint_is_written_to_the_record()
    test_titles_still_dedupe_without_a_fingerprint()
    test_a_merged_ticket_owns_every_finding_it_absorbed()
    test_a_string_fingerprint_still_works()
    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll cadence dedupe tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
