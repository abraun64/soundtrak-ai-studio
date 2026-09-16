#!/usr/bin/env python3
"""Make a version mismatch between operators VISIBLE (team-deployment.md §7).

Everyone shares one DATA repo but each person keeps their own pinned CODE checkout, so a team
can drift onto different versions and nothing says so. That mostly works — generated pages are
never shared, and records round-trip unknown fields rather than stripping them. What does not
work is the part nobody sees:

  * every guard lives in the code half (large-file, credential scan, leak scan, the
    unprovisioned-clone check), so the team's real protection is the MINIMUM version anyone is
    running, not the maximum. Someone on an old version can commit into the shared repo what a
    newer machine would have blocked, and shared history is permanent;
  * the whole organisation reads dashboards rendered by ONE machine, so the publisher's version
    decides what everyone sees;
  * someone behind gets told to run commands their install does not have, which reads as a
    broken system rather than a version gap.

The deployment guide already says to agree a version as a team. That was unenforceable advice:
the only way to find a mismatch was to hit a confusing symptom and work backwards. This turns an
invisible condition into a visible one, which is all it needs to be.

ONE FILE PER OPERATOR, never a shared list. Each person writes only their own file, so two
people ending a session at once cannot conflict — the same reason claims are per-campaign files.

    python .claude/lib/operator_versions.py        # who is on what
"""
from __future__ import annotations
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))

REL = Path("system") / "operators"
# A colleague who has not worked for a month is not a mismatch worth nagging about; they will
# be told when they next open the Studio. Without this the warning only ever grows.
STALE_AFTER_DAYS = 30
UNPINNED = "unpinned"


def _data_root() -> Path:
    try:
        import repo_paths
        return repo_paths.data_root(ROOT)
    except Exception:  # noqa: BLE001
        return ROOT


def _slug(identity: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", identity.strip().lower()).strip("-") or "unknown"


def my_version(code_root: Path = ROOT) -> str:
    try:
        import system_update
        return system_update.current_tag(code_root) or UNPINNED
    except Exception:  # noqa: BLE001
        return UNPINNED


def record(code_root: Path = ROOT, data: Path | None = None, identity: str | None = None) -> Path | None:
    """Write (only) this operator's version. Best-effort: never raises at a caller."""
    try:
        if identity is None:
            import operator_identity
            identity = operator_identity.current(code_root) or "unknown"
        d = (data or _data_root()) / REL
        d.mkdir(parents=True, exist_ok=True)
        out = d / f"{_slug(identity)}.yaml"
        out.write_text(
            f"operator: {identity}\n"
            f"version: {my_version(code_root)}\n"
            f"last_seen: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n",
            encoding="utf-8")
        return out
    except Exception:  # noqa: BLE001
        return None


def _parse(p: Path) -> dict | None:
    try:
        rec = {}
        for line in p.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                rec[k.strip()] = v.strip()
        if not rec.get("operator"):
            return None
        rec["path"] = p
        return rec
    except OSError:
        return None


def everyone(data: Path | None = None, include_stale: bool = False) -> list[dict]:
    d = (data or _data_root()) / REL
    if not d.is_dir():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_AFTER_DAYS)
    out = []
    for p in sorted(d.glob("*.yaml")):
        rec = _parse(p)
        if not rec:
            continue
        if not include_stale:
            try:
                if datetime.fromisoformat(rec.get("last_seen", "")) < cutoff:
                    continue
            except ValueError:
                pass
        out.append(rec)
    return out


def _key(tag: str):
    m = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", tag or "")
    return tuple(int(x) for x in m.groups()) if m else None


def status(code_root: Path = ROOT, data: Path | None = None, identity: str | None = None) -> dict:
    """What to tell this operator. `level` is ok | behind | split."""
    mine = my_version(code_root)
    if identity is None:
        try:
            import operator_identity
            identity = operator_identity.current(code_root) or "unknown"
        except Exception:  # noqa: BLE001
            identity = "unknown"
    others = [r for r in everyone(data) if r.get("operator") != identity]
    versions = {r.get("version", UNPINNED) for r in others}
    versions.discard(mine)
    if not others or not versions:
        return {"level": "ok", "mine": mine, "others": others, "newest": mine}

    keyed = [v for v in versions | {mine} if _key(v)]
    newest = max(keyed, key=_key) if keyed else mine
    if _key(mine) and _key(newest) and _key(mine) < _key(newest):
        return {"level": "behind", "mine": mine, "others": others, "newest": newest}
    return {"level": "split", "mine": mine, "others": others, "newest": newest}


def describe(st: dict) -> str:
    who = ", ".join(f"{r.get('operator')} on {r.get('version')}" for r in st["others"][:4])
    if st["level"] == "behind":
        return (f"you are on {st['mine']}, colleagues are on {st['newest']} ({who}). "
                f"Being behind means weaker safety checks than theirs, on shared work")
    return f"the team is split across versions: you on {st['mine']}; {who}"


def main() -> int:
    st = status()
    print(f"this machine : {st['mine']}")
    rows = everyone(include_stale=True)
    if not rows:
        print("no other operators recorded yet")
        return 0
    print("recorded operators:")
    for r in rows:
        print(f"  {r.get('version','?'):>10}  {r.get('operator')}   last seen {r.get('last_seen','?')}")
    if st["level"] != "ok":
        print(f"\n{st['level'].upper()}: {describe(st)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
