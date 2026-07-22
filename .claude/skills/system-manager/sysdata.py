#!/usr/bin/env python3
"""Canonical System-layer store resolver + id guard (SYS-025).

WHY THIS EXISTS — the worktree fork.
  The System Manager's stores — system/{backlog,ideas,audit-log}.yaml — are
  git-tracked files, so every git worktree checks out its OWN copy. The dashboard
  BUILDER already resolves them to the MAIN checkout (repo_paths.data_root); but a
  plain *editor* edit made from a `.claude/worktrees/*` checkout writes the
  WORKTREE's copy, which then diverges from main and re-allocates ids main has
  already taken. That is the 2026-06-29 SYS-018/019 id collision: the Retro-5 branch
  and main both minted SYS-018/019 for different tickets.

WHAT THIS DOES.
  One source of truth for WHERE the stores live and WHAT the next free id is, so the
  agent (and any helper) never edits the wrong copy or reuses an id — regardless of
  which checkout it runs from. The System Manager skill calls this BEFORE any
  capture / triage / retro write.

  - `paths`   prints the canonical absolute store paths (always the MAIN checkout),
              and shouts a WARNING when invoked from a worktree so the agent edits
              those absolute paths, not the worktree-local copy.
  - `next-id` prints the next free id for a prefix, scanning backlog + ideas + audit
              (so an id that was promoted/removed from one file but lives on in the
              append-only audit log can never be reused).
  - `check`   guards against an id that has ALREADY collided — duplicate `id:` within
              backlog or ideas, or an id live in both — and exits non-zero so it can
              gate a render or a commit.

CLI:
  python sysdata.py paths
  python sysdata.py next-id SYS
  python sysdata.py next-id IDEA
  python sysdata.py check
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Keep output ASCII-clean below; reconfigure as a belt so a stray glyph never raises
# UnicodeEncodeError under the non-interactive scheduled-task interpreter (cp1252 console).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — older/odd streams: leave as-is
        pass

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths

    DATA_ROOT = repo_paths.data_root(ROOT)
    _IN_WORKTREE = repo_paths.is_worktree(ROOT)
except Exception:  # noqa: BLE001 — fall back to the running checkout if the helper is absent
    DATA_ROOT = ROOT
    _IN_WORKTREE = False

SYSTEM_DIR = DATA_ROOT / "system"
STORES = {
    "backlog": SYSTEM_DIR / "backlog.yaml",
    "ideas": SYSTEM_DIR / "ideas.yaml",
    "audit": SYSTEM_DIR / "audit-log.yaml",
}
DASHBOARD = SYSTEM_DIR / "dashboard.html"

# Numeric ids only — SYS-NNN / IDEA-NNN. SYS-D1/D2 (legacy lettered ids) are
# deliberately excluded from id allocation: they are historical, never re-minted.
_ID_RE = {
    "SYS": re.compile(r"\bSYS-(\d+)\b"),
    "IDEA": re.compile(r"\bIDEA-(\d+)\b"),
}

# Only ALLOCATION-bearing fields count toward the next id — an `id:` (backlog/ideas)
# or a `ref:` (audit). An id mentioned in free text (`detail:`, `summary:`, `source:`,
# a description) must NOT inflate the counter, or prose like "next=SYS-030" silently
# burns ids. Going too HIGH never collides, but it erodes trust in the allocator.
_FIELD_RE = re.compile(r"^\s*-?\s*(?:id|ref):\s*(.+?)\s*$")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _scan_max(prefix: str) -> int:
    """Highest numeric id for `prefix` across the allocation-bearing fields of ALL
    stores (`id:` in backlog/ideas, `ref:` in the audit log) — never free text, so an
    id quoted in a detail/description can't burn a number."""
    rx = _ID_RE[prefix]
    found = -1
    for path in STORES.values():
        for line in _read(path).splitlines():
            fm = _FIELD_RE.match(line)
            if fm:
                for hit in rx.finditer(fm.group(1)):
                    found = max(found, int(hit.group(1)))
    return found


def next_id(prefix: str) -> str:
    prefix = prefix.upper()
    if prefix not in _ID_RE:
        raise SystemExit(f"unknown id prefix {prefix!r} (use SYS or IDEA)")
    return f"{prefix}-{_scan_max(prefix) + 1:03d}"


def _live_ids(store: str) -> list[str]:
    """Top-level `id:` values declared in a store's item list (order preserved)."""
    ids: list[str] = []
    for line in _read(STORES[store]).splitlines():
        m = re.match(r"\s*-?\s*id:\s*([A-Za-z]+-[A-Za-z0-9]+)\s*$", line)
        if m:
            ids.append(m.group(1))
    return ids


def _duplicates(seq) -> list[str]:
    seen, dupes = set(), []
    for x in seq:
        if x in seen and x not in dupes:
            dupes.append(x)
        seen.add(x)
    return dupes


def _structural_problems(store: str) -> list[str]:
    """SYS-107 — catch malformations the line-based id scan is blind to:
      1. DUPLICATE KEYS within one item — a lost `- id:` line merges two tickets into a
         single mapping, and yaml.safe_load silently keeps the LAST value per key (the
         2026-07-22 Decompile incident: SYS-101 parsed as the Decompile ticket, clobbering
         its `done` status invisibly).
      2. an item with no `id:` at all.
    Returns problem strings; empty if the store parses cleanly (or pyyaml is unavailable —
    the line-based checks still run, so the guard degrades safely)."""
    try:
        import yaml
    except Exception:
        return []

    class _UniqueKeyLoader(yaml.SafeLoader):
        def construct_mapping(self, node, deep=False):
            seen = set()
            for k_node, _v in node.value:
                k = self.construct_object(k_node, deep=deep)
                if k in seen:
                    raise yaml.constructor.ConstructorError(
                        None, None,
                        f"duplicate key {k!r} in one item — a lost `- id:` line merging two items?",
                        k_node.start_mark,
                    )
                seen.add(k)
            return super().construct_mapping(node, deep=deep)

    text = _read(STORES[store])
    if not text.strip():
        return []
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as e:
        return [f"{store}: malformed — {str(e).splitlines()[0]}"]
    problems: list[str] = []
    for i, item in enumerate((data or {}).get("items") or []):
        if not isinstance(item, dict):
            problems.append(f"{store}: item #{i} is not a mapping")
        elif not item.get("id"):
            problems.append(
                f"{store}: an item has no `id:` (title: {str(item.get('title') or '')[:50]!r})"
            )
    return problems


def _worktree_banner() -> None:
    if _IN_WORKTREE:
        print(
            "  WARNING: WORKTREE CHECKOUT - the System Manager stores are canonical in the\n"
            "  MAIN checkout. Edit the absolute paths printed below, NEVER the worktree copy,\n"
            "  or the backlog forks and ids collide (SYS-025 / the 2026-06-29 incident).",
            file=sys.stderr,
        )


def cmd_paths() -> int:
    _worktree_banner()
    print(f"system_dir : {SYSTEM_DIR}")
    for name, path in STORES.items():
        flag = "" if path.exists() else "   (missing)"
        print(f"{name:<8}: {path}{flag}")
    print(f"dashboard: {DASHBOARD}")
    return 0


def cmd_next_id(prefix: str) -> int:
    _worktree_banner()
    print(next_id(prefix))
    return 0


def cmd_check() -> int:
    backlog_ids = _live_ids("backlog")
    idea_ids = _live_ids("ideas")
    problems: list[str] = []

    for store, ids in (("backlog.yaml", backlog_ids), ("ideas.yaml", idea_ids)):
        for dupe in _duplicates(ids):
            problems.append(f"duplicate id {dupe} appears more than once in {store}")

    overlap = sorted(set(backlog_ids) & set(idea_ids))
    for sid in overlap:
        problems.append(f"id {sid} is live in BOTH backlog.yaml and ideas.yaml")

    # SYS-107 — structural malformation (duplicate keys within one item / missing id)
    for store in ("backlog", "ideas"):
        problems.extend(_structural_problems(store))

    if problems:
        print("SYS-025 id guard: COLLISION", file=sys.stderr)
        for p in problems:
            print(f"  x {p}", file=sys.stderr)
        return 1

    print(
        f"SYS-025 id guard: OK - {len(backlog_ids)} tickets, {len(idea_ids)} ideas, "
        f"no duplicate or cross-store ids.\n"
        f"  next SYS = {next_id('SYS')} | next IDEA = {next_id('IDEA')}"
    )
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        return cmd_check()
    cmd, *rest = argv
    if cmd == "paths":
        return cmd_paths()
    if cmd == "next-id":
        if not rest:
            raise SystemExit("usage: sysdata.py next-id SYS|IDEA")
        return cmd_next_id(rest[0])
    if cmd == "check":
        return cmd_check()
    raise SystemExit(f"unknown command {cmd!r} (paths | next-id | check)")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
