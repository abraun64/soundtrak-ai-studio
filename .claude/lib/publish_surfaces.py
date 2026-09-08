#!/usr/bin/env python3
"""
publish_surfaces — put the rendered surfaces where stakeholders can read them (§11).

People without a Claude Code seat still need the dashboards, galleries and asset previews.
Under `profile: team` the HTML is derived locally and never committed, so there has to be
one place it is published TO.

  python .claude/lib/publish_surfaces.py --to "<synced SharePoint library folder>"
  python .claude/lib/publish_surfaces.py --check      # what would be published
  MAS_PUBLISH_DIR=... python .claude/lib/publish_surfaces.py

MECHANISM, deliberately boring: copy into a locally SYNCED SharePoint library folder and let
the sync client do the upload. No Graph app registration, no tenant admin consent, nothing to
get approved before a pilot can run. The Graph route stays available later if this proves
fragile — better auth and audit, at the cost of involving IT.

ONE WRITER. This is the nominated publisher (one machine or a CI job), NOT every operator.
That is the whole reason it is safe: the multi-writer problems that killed the shared-folder
design (conflict copies, render races) need two writers, and there is exactly one.

STRICTLY ONE-WAY. Nothing here reads FROM SharePoint. Published output is a read-only view;
the authoritative store is git. Reading it back is the design decision #1 rejected.
"""
from __future__ import annotations
import argparse
import filecmp
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))

ENV_VAR = "MAS_PUBLISH_DIR"
# What a stakeholder reads. Deliberately NOT the whole tree: markdown sources, yaml state and
# per-asset working files are not a stakeholder surface, and copying them to SharePoint would
# put campaign internals somewhere with a different access list.
PUBLISH_GLOBS = ("campaigns/**/*.html", "tenant-brand/*.html", "index.html", "*.html")


def _data_root() -> Path:
    try:
        import repo_paths
        return repo_paths.data_root(ROOT)
    except ImportError:
        return ROOT


def collect(data: Path | None = None) -> list[Path]:
    data = data or _data_root()
    seen: list[Path] = []
    for pattern in PUBLISH_GLOBS:
        for p in sorted(data.glob(pattern)):
            if p.is_file() and p not in seen:
                seen.append(p)
    return seen


def publish(dest: Path, data: Path | None = None, dry_run: bool = False) -> dict:
    data = data or _data_root()
    files = collect(data)
    copied = skipped = 0
    for src in files:
        rel = src.relative_to(data)
        out = dest / rel
        # Unchanged files are skipped so the sync client is not handed thousands of identical
        # writes on every publish — that is what turns a sync folder into a storm.
        if out.is_file() and filecmp.cmp(src, out, shallow=False):
            skipped += 1
            continue
        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
        copied += 1
    if not dry_run and files:
        stamp = (f"Published {datetime.now().astimezone().isoformat(timespec='seconds')} — "
                 f"{len(files)} surfaces.\nRead-only view. The authoritative store is the "
                 f"DATA git repo; changes made here are not read back.\n")
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "_PUBLISHED.txt").write_text(stamp, encoding="utf-8")
    return {"total": len(files), "copied": copied, "skipped": skipped}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to", default=os.environ.get(ENV_VAR, ""),
                    help=f"destination folder (default: ${ENV_VAR})")
    ap.add_argument("--check", action="store_true", help="report what would be published")
    a = ap.parse_args()

    data = _data_root()
    files = collect(data)
    if a.check or not a.to:
        print(f"data root : {data}")
        print(f"surfaces  : {len(files)}")
        for p in files[:15]:
            print(f"  {p.relative_to(data)}")
        if len(files) > 15:
            print(f"  ... and {len(files) - 15} more")
        if not a.to:
            print(f"\nNo destination. Pass --to <folder> or set ${ENV_VAR} to a locally synced "
                  f"SharePoint library folder.")
            return 0 if a.check else 1
        return 0

    dest = Path(a.to).expanduser()
    if not dest.parent.exists():
        print(f"destination parent does not exist: {dest.parent}", file=sys.stderr)
        return 1
    res = publish(dest, data)
    print(f"published {res['copied']} changed / {res['skipped']} unchanged "
          f"of {res['total']} surfaces -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
