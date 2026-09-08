#!/usr/bin/env python3
"""
campaign_claim — one active operator per campaign (team-deployment.md §5).

Two operators in one campaign is last-writer-wins on structured YAML, which is where
silent data loss hides. A claim PREVENTS the collision instead of repairing it.

  campaigns/<slug>/claim.yaml
    operator: jane.smith@example.com
    claimed:  2026-08-22T09:14:00+10:00
    expires:  2026-08-22T17:14:00+10:00     # TTL, default 8h
    session:  <claude-session-id>

  python .claude/lib/campaign_claim.py --list
  python .claude/lib/campaign_claim.py --claim <slug>
  python .claude/lib/campaign_claim.py --release <slug>

NOT A LOCK IN THE MUTEX SENSE. It cannot stop a determined writer, and it is not meant
to — it is a WARNING that another human is mid-flight, plus a record of who. The
override path is deliberate and audited rather than hidden, because a claim that cannot
be broken becomes a claim nobody dares rely on the moment someone goes on holiday.

EXPIRY IS THE POINT. A colleague who closes their laptop must not block the campaign
until Monday, so a claim ages out (8h default). The cost of a stale claim being
overridden is a warning nobody needed; the cost of a permanent one is a blocked team.

Inert under `profile: small-business` — claim_locks is off, so claim()/check() are
no-ops and no claim.yaml is ever written. A single-operator install sees nothing.
"""
from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))

CLAIM_NAME = "claim.yaml"
DEFAULT_TTL_HOURS = 8


def _enabled() -> bool:
    try:
        import deployment_profile as dp
        return dp.claim_locks_enabled()
    except Exception:  # noqa: BLE001 — never break a write path over an unresolvable profile
        return False


def _data_root() -> Path:
    try:
        import repo_paths
        return repo_paths.data_root(ROOT)
    except ImportError:
        return ROOT


def _campaigns() -> Path:
    return _data_root() / "campaigns"


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _parse_dt(v) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v))
    except ValueError:
        return None


def path_for(slug: str) -> Path:
    return _campaigns() / slug / CLAIM_NAME


def read(slug: str) -> dict | None:
    p = path_for(slug)
    if not p.is_file():
        return None
    try:
        import yaml
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 — an unparseable claim is treated as absent, not fatal
        return None
    return data if isinstance(data, dict) else None


def is_expired(claim: dict, now: datetime | None = None) -> bool:
    exp = _parse_dt(claim.get("expires"))
    if exp is None:
        return True                      # no/!parseable expiry -> treat as free
    return (now or _now()) >= exp


def holder(slug: str) -> dict | None:
    """The LIVE claim on this campaign, or None if unclaimed / expired / disabled."""
    if not _enabled():
        return None
    c = read(slug)
    if not c or is_expired(c):
        return None
    return c


def check(slug: str) -> tuple[bool, str]:
    """(may_write, message). may_write is False ONLY when someone else holds a live claim.

    The caller decides what to do with False — the Stop hook warns, an interactive flow
    should surface it before writing. Nothing here blocks by itself.
    """
    if not _enabled():
        return True, ""
    import operator_identity as who
    c = holder(slug)
    if not c:
        return True, ""
    owner = str(c.get("operator") or "").strip()
    me = who.current()
    if me and owner and owner.lower() == me.lower():
        return True, f"you hold this claim (expires {c.get('expires')})"
    return False, (f"{slug} is claimed by {owner or 'an unnamed operator'} until "
                   f"{c.get('expires')}. Co-editing a campaign is last-writer-wins on "
                   f"asset.yaml/campaign.yaml. Coordinate, or override deliberately.")


def claim(slug: str, ttl_hours: int = DEFAULT_TTL_HOURS, force: bool = False) -> tuple[bool, str]:
    if not _enabled():
        return True, "claim locks are off under this profile - nothing written"
    camp = _campaigns() / slug
    if not camp.is_dir():
        return False, f"no such campaign: {camp}"
    import operator_identity as who
    me = who.stamp()

    existing = holder(slug)
    if existing and not force:
        owner = str(existing.get("operator") or "")
        if owner.lower() != (who.current() or "").lower():
            return False, (f"held by {owner} until {existing.get('expires')} - "
                           f"re-run with --force to override (the override is recorded)")

    now = _now()
    body = (
        "# Campaign claim (docs/specs/team-deployment.md 5). Written by campaign_claim.py.\n"
        "# One active operator per campaign; this ages out so a closed laptop never blocks the team.\n"
        f"operator: {me}\n"
        f"claimed: {now.isoformat(timespec='seconds')}\n"
        f"expires: {(now + timedelta(hours=ttl_hours)).isoformat(timespec='seconds')}\n"
        f"session: {os.environ.get('CLAUDE_SESSION_ID', '')}\n"
    )
    if existing and force:
        body += (f"overridden_from: {existing.get('operator')}\n"
                 f"overridden_at: {now.isoformat(timespec='seconds')}\n")
    path_for(slug).write_text(body, encoding="utf-8")
    return True, f"claimed {slug} until {(now + timedelta(hours=ttl_hours)).isoformat(timespec='seconds')}"


def release(slug: str) -> tuple[bool, str]:
    p = path_for(slug)
    if not p.is_file():
        return True, f"{slug}: no claim to release"
    import operator_identity as who
    c = read(slug) or {}
    owner = str(c.get("operator") or "")
    me = who.current()
    if owner and me and owner.lower() != me.lower() and not is_expired(c):
        return False, f"{slug} is held by {owner}, not you - not releasing"
    p.unlink()
    return True, f"released {slug}"


def release_mine() -> list[str]:
    """Release every live claim this operator holds. Called at session end."""
    if not _enabled():
        return []
    import operator_identity as who
    me = (who.current() or "").lower()
    if not me:
        return []
    freed = []
    camps = _campaigns()
    if not camps.is_dir():
        return []
    for d in sorted(camps.iterdir()):
        if not d.is_dir():
            continue
        c = read(d.name)
        if c and str(c.get("operator", "")).lower() == me:
            try:
                path_for(d.name).unlink()
                freed.append(d.name)
            except OSError:
                pass
    return freed


def listing() -> str:
    if not _enabled():
        return "claim locks are OFF under this deployment profile (single-operator)."
    camps = _campaigns()
    if not camps.is_dir():
        return f"no campaigns dir at {camps}"
    rows = []
    for d in sorted(camps.iterdir()):
        if not d.is_dir():
            continue
        c = read(d.name)
        if not c:
            continue
        state = "EXPIRED" if is_expired(c) else "live"
        rows.append(f"  {d.name:44} {str(c.get('operator','?')):32} {state}  expires {c.get('expires')}")
    return "\n".join(["campaign claims:"] + rows) if rows else "no campaigns are claimed."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--claim", metavar="SLUG")
    ap.add_argument("--release", metavar="SLUG")
    ap.add_argument("--check", metavar="SLUG")
    ap.add_argument("--force", action="store_true", help="override a live claim (recorded in the file)")
    ap.add_argument("--ttl", type=int, default=DEFAULT_TTL_HOURS)
    a = ap.parse_args()

    if a.claim:
        ok, msg = claim(a.claim, a.ttl, a.force)
    elif a.release:
        ok, msg = release(a.release)
    elif a.check:
        ok, msg = check(a.check)
        msg = msg or f"{a.check} is free"
    else:
        print(listing())
        return 0
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
