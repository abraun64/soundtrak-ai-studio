#!/usr/bin/env python3
"""
system_update — get a system release onto every operator's machine (team-deployment.md §7).

Operators sit on a PINNED TAG, never a moving branch, so the system cannot change under
someone mid-campaign. Updating is an explicit act, and rollback is checking out the
previous tag — the property the "shared code folder" alternative could not offer.

  python .claude/lib/system_update.py --check      # is a newer release available?
  python .claude/lib/system_update.py --apply      # fetch + checkout the newest tag
  python .claude/lib/system_update.py --apply --to v1.4.0
  python .claude/lib/system_update.py --rollback   # back to the previous tag

HOST-NEUTRAL (decision #6). Plain git only — no `gh`, no `az`. The remote URL is
configuration, so the same code works against Azure DevOps Repos and GitHub Enterprise.
Release AUTHORING may be host-specific; the operator UPDATE path may not.

Refuses to touch a dirty working tree or a checkout with local commits: under a team
deployment the code repo is PULL-ONLY, and quietly discarding someone's edits would be
worse than refusing. If an operator has local changes, that is a conversation, not a
merge.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def _git(args: list[str], cwd: Path = ROOT) -> tuple[bool, str]:
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                           text=True, timeout=180)
        return r.returncode == 0, (r.stdout or r.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)


def _key(tag: str):
    m = SEMVER.match(tag)
    return tuple(int(x) for x in m.groups()) if m else None


def tags(cwd: Path = ROOT) -> list[str]:
    ok, out = _git(["tag", "--list"], cwd)
    if not ok:
        return []
    return sorted((t for t in out.split() if _key(t)), key=_key)


def current_tag(cwd: Path = ROOT) -> str | None:
    """The tag this checkout is ON, or None if it is on a branch / detached elsewhere."""
    ok, out = _git(["describe", "--tags", "--exact-match"], cwd)
    return out.strip() if ok and _key(out.strip()) else None


def is_clean(cwd: Path = ROOT) -> tuple[bool, str]:
    ok, out = _git(["status", "--porcelain"], cwd)
    if not ok:
        return False, "git status failed"
    dirty = [l for l in out.splitlines() if l.strip()]
    return (not dirty), (f"{len(dirty)} uncommitted change(s)" if dirty else "clean")


def check(cwd: Path = ROOT, fetch: bool = True) -> dict:
    if fetch:
        _git(["fetch", "--tags", "--quiet"], cwd)
    all_tags = tags(cwd)
    cur = current_tag(cwd)
    latest = all_tags[-1] if all_tags else None
    behind = []
    if cur and latest and _key(cur) < _key(latest):
        behind = [t for t in all_tags if _key(t) > _key(cur)]
    return {"current": cur, "latest": latest, "available": behind, "tags": all_tags}


def _changelog_for(tags_wanted: list[str], cwd: Path = ROOT) -> str:
    """The CHANGELOG sections for the releases an operator is about to take. An update whose
    contents the operator cannot read is one they postpone indefinitely.

    Read from the NEWEST TARGET TAG, not the working tree. An operator pinned at v1.6.0 has a
    CHANGELOG that stops at 1.6.0 — it cannot describe the releases they do not have yet, which
    is precisely the set they need to read about. `git show <tag>:CHANGELOG.md` gets the version
    that ships with the update.
    """
    if not tags_wanted:
        return ""
    ok, text = _git(["show", f"{tags_wanted[-1]}:CHANGELOG.md"], cwd)
    if not ok or not text.strip():
        path = cwd / "CHANGELOG.md"          # fallback: local copy (older, may not have them)
        if not path.is_file():
            return ""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
    out = []
    for tag in tags_wanted:
        ver = tag.lstrip("v")
        m = re.search(rf"^##\s*\[{re.escape(ver)}\].*?$(.*?)(?=^##\s*\[|\Z)",
                      text, re.M | re.S)
        if m:
            body = "\n".join(l for l in m.group(1).strip().splitlines() if l.strip())[:800]
            out.append(f"  {tag}:\n" + "\n".join(f"    {l}" for l in body.splitlines()))
    return "\n".join(out)


def apply(to: str | None = None, cwd: Path = ROOT) -> tuple[bool, str]:
    clean, why = is_clean(cwd)
    if not clean:
        return False, (f"refusing to update: working tree has {why}. Under a team deployment "
                       "the code repo is PULL-ONLY — commit or discard your changes first. "
                       "Campaign and tenant work belongs in the DATA repo.")
    info = check(cwd)
    target = to or info["latest"]
    if not target:
        return False, "no release tags found on this remote"
    if target not in info["tags"]:
        return False, f"unknown release {target}. Available: {', '.join(info['tags'][-8:]) or 'none'}"
    if info["current"] == target:
        return True, f"already on {target}"
    ok, out = _git(["checkout", "--quiet", target], cwd)
    if not ok:
        return False, f"checkout failed: {out}"
    return True, f"updated {info['current'] or '(untagged)'} -> {target}"


def rollback(cwd: Path = ROOT) -> tuple[bool, str]:
    info = check(cwd, fetch=False)
    cur, all_tags = info["current"], info["tags"]
    if not cur:
        return False, "not on a release tag — nothing to roll back from"
    older = [t for t in all_tags if _key(t) < _key(cur)]
    if not older:
        return False, f"{cur} is the earliest release — nothing to roll back to"
    return apply(older[-1], cwd)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--rollback", action="store_true")
    ap.add_argument("--to", metavar="TAG")
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()

    if a.rollback:
        ok, msg = rollback()
        print(msg)
        return 0 if ok else 1
    if a.apply:
        ok, msg = apply(a.to)
        print(msg)
        return 0 if ok else 1

    info = check(fetch=not a.no_fetch)
    print(f"current release : {info['current'] or '(not on a release tag)'}")
    print(f"latest release  : {info['latest'] or '(none found)'}")
    if info["available"]:
        print(f"\nUPDATE AVAILABLE — {len(info['available'])} release(s) newer than yours:")
        print("  " + ", ".join(info["available"]))
        notes = _changelog_for(info["available"])
        if notes:
            print("\n" + notes)
        print("\n  apply with: python .claude/lib/system_update.py --apply")
    elif info["current"]:
        print("\nup to date.")
    else:
        print("\nThis checkout is not on a release tag. A team deployment pins operators to a "
              "tag so the system cannot change under them mid-campaign:\n"
              "  python .claude/lib/system_update.py --apply")
    clean, why = is_clean()
    if not clean:
        print(f"\n  NOTE: working tree is not clean ({why}) — an update will refuse until it is.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
