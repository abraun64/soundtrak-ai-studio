#!/usr/bin/env python3
"""publish_release — put a Studio release into an ORGANISATION's own code repo.

This is stage one of the two-stage upgrade (team-deployment.md §7). An organisation keeps its
own copy of the Studio, so a release published by the vendor reaches nobody until an
administrator puts it there. Until now the guide described that by hand — delete the contents,
copy the new ones in, commit, tag, push — which is four chances to get it wrong, on the step
whose failures are silent:

  * a tag not written exactly vX.Y.Z is IGNORED. Operators are never offered the update and
    no error is produced anywhere, because nothing is looking for a malformed tag;
  * copying into the wrong repo (the DATA repo) would replace an organisation's campaigns
    with an empty scaffold;
  * a copy that half-fails leaves the repo committed in a broken state, and every operator
    pulls it.

  python .claude/lib/publish_release.py --to <org code repo url> --tag v1.11.0
  python .claude/lib/publish_release.py --to <url> --tag v1.11.0 --push

Pushing is OPT-IN. Everything up to the push is reversible; the push is what every operator
in the organisation then takes, so it is a decision, not a default.
"""
from __future__ import annotations
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SOURCE = "https://github.com/abraun64/soundtrak-ai-studio-team.git"
SEMVER = re.compile(r"^v\d+\.\d+\.\d+$")
# A target only counts as a CODE repo if it looks like one. Guessing wrong here means
# overwriting an organisation's campaigns, so require real evidence.
CODE_MARKERS = (".claude/lib/provision.py", ".claude/skills", "CHANGELOG.md")
DATA_MARKERS = ("campaigns", "tenant-brand", "config.yaml")


def _git(args: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd) if cwd else None,
                           capture_output=True, text=True, timeout=600)
        return r.returncode == 0, (r.stdout or r.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)


def looks_like_code_repo(p: Path) -> tuple[bool, str]:
    hits = [m for m in CODE_MARKERS if (p / m).exists()]
    data_hits = [m for m in DATA_MARKERS if (p / m).exists()]
    if len(data_hits) >= 2 and not hits:
        return False, ("this looks like the DATA repo (found " + ", ".join(data_hits) +
                       "). Publishing here would replace your campaigns and brands")
    if len(hits) < 2:
        return False, f"does not look like the code repo (found only: {', '.join(hits) or 'nothing'})"
    return True, "ok"


def replace_contents(src: Path, dst: Path) -> None:
    """Replace dst's contents with src's, leaving dst/.git alone."""
    for child in dst.iterdir():
        if child.name == ".git":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    for child in src.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.copytree(child, dst / child.name)
        else:
            shutil.copy2(child, dst / child.name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to", required=True, help="your organisation's CODE repo (url or path)")
    ap.add_argument("--tag", required=True, help="release to publish, e.g. v1.11.0")
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="where the release comes from")
    ap.add_argument("--push", action="store_true", help="push it (otherwise stops before)")
    a = ap.parse_args()

    if not SEMVER.match(a.tag):
        print(f"'{a.tag}' is not a release number. It must look exactly like v1.11.0 — three\n"
              "numbers with a leading v. Anything else is ignored entirely, and your people are\n"
              "never offered the update, with no error to tell you why.", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        rel, org = work / "release", work / "org"

        print(f"[1/5] fetching {a.tag}")
        ok, out = _git(["clone", "--depth", "1", "--branch", a.tag, a.source, str(rel)])
        if not ok:
            print(f"      could not fetch {a.tag} from {a.source}\n{out}", file=sys.stderr)
            return 1
        # the team distribution carries code/ and data/; an organisation's CODE repo takes code/
        payload = rel / "code" if (rel / "code").is_dir() else rel
        print(f"      {sum(1 for _ in payload.rglob('*') if _.is_file())} files")

        print(f"[2/5] cloning your code repo")
        ok, out = _git(["clone", a.to, str(org)])
        if not ok:
            print(f"      could not clone {a.to}\n{out}", file=sys.stderr)
            return 1

        print(f"[3/5] checking the target")
        # An EMPTY clone is the default-branch trap, not a wrong repo: if the repository's
        # default branch is not the one the contents are on, git clones nothing and every
        # later symptom is misleading. Say which it is.
        if not any(c.name != ".git" for c in org.iterdir()):
            print("      REFUSING: that repository cloned EMPTY.", file=sys.stderr)
            print("      Its default branch is probably not the branch your files are on.",
                  file=sys.stderr)
            print("      Fix the default branch on the repository settings page, then re-run.",
                  file=sys.stderr)
            return 1
        ok, why = looks_like_code_repo(org)
        if not ok:
            print(f"      REFUSING: {why}", file=sys.stderr)
            return 1
        print("      ok — this is the code repo")

        replace_contents(payload, org)
        _git(["add", "-A"], org)
        counts: dict[str, int] = {}
        for line in _git(["status", "--porcelain"], org)[1].splitlines():
            if line.strip():
                counts[line.strip()[0]] = counts.get(line.strip()[0], 0) + 1
        print("[4/5] changes: " + (", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
                                   or "none — already on this release"))
        if not counts:
            print("      nothing to publish.")
            return 0
        if counts.get("D", 0) and not counts.get("M", 0) and not counts.get("A", 0):
            print("      REFUSING: this would only DELETE files, which means the release did not\n"
                  "      unpack as expected. Nothing has been committed.", file=sys.stderr)
            return 1

        _git(["commit", "-m", f"Update to {a.tag}"], org)
        ok, out = _git(["tag", "-a", a.tag, "-m", a.tag], org)
        if not ok and "already exists" not in out:
            print(f"      could not tag: {out}", file=sys.stderr)
            return 1

        if not a.push:
            print(f"[5/5] ready, NOT pushed (add --push).\n"
                  f"      Everything up to here is reversible; the push is what every operator\n"
                  f"      in your organisation then takes.")
            return 0
        print("[5/5] pushing")
        for args in (["push"], ["push", "origin", a.tag]):
            ok, out = _git(args, org)
            if not ok:
                print(f"      push failed: {out}", file=sys.stderr)
                return 1
        print(f"      published {a.tag}. Your people take it with:\n"
              f"      python .claude/lib/system_update.py --apply --to {a.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
