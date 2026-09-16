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

EVERY OPERATOR WRITES (revised 2026-09-16). This began as one nominated publisher, because
multi-writer problems — conflict copies, render races — need two writers and there was exactly
one. That reasoning held while publishing was optional. It does not hold once the published copy
IS the interface the whole organisation reads: a single publisher makes the company's only view
depend on one laptop being switched on, and it silently stops the week they are on leave.

So everyone publishes, and the one genuinely damaging multi-writer failure is prevented
directly: an operator whose DATA clone is behind would republish old pages over newer ones, and
everybody would watch the dashboards go BACKWARDS with no error anywhere. Each published page
carries its content date, and a page is only ever replaced by content at least as new as what is
already there — so a stale publisher is a no-op rather than a regression.

The remaining exposure is two machines writing the identical file in the same second, which the
sync client may resolve as a conflict copy. That is cosmetic and self-correcting on the next
publish, and a far smaller risk than an interface nobody is updating.

STRICTLY ONE-WAY. Nothing here reads FROM SharePoint. Published output is a read-only view;
the authoritative store is git. Reading it back is the design decision #1 rejected.
"""
from __future__ import annotations
import argparse
import filecmp
import os
import re
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


BANNER_MARK = "mas-published-stamp"


def _stamp(html: str, source_mtime: float) -> str:
    """Put the freshness ON the page the stakeholder opens.

    _PUBLISHED.txt records the publish, but it is a sidecar nobody opens. A colleague reading
    a dashboard has no repo, no health check and no way to tell a live page from one whose
    publisher laptop has been shut since Tuesday. Where an operator gets a loud failure, a
    stakeholder gets a plausible-looking page — which is worse, because it is believed.

    The stamp carries the SOURCE's last-changed time, not the publish time. That is both more
    honest (it answers "how current is this?", not "when did a script run?") and necessary:
    a publish-time stamp would change every byte of every page on every run, so nothing could
    ever be skipped and the sync client would be handed the whole tree each time.
    """
    from datetime import datetime
    when = datetime.fromtimestamp(source_mtime).astimezone()
    banner = (
        f'<div class="{BANNER_MARK}" data-mas-updated="{when.isoformat(timespec="seconds")}" '
        f'style="font:13px/1.5 system-ui,sans-serif;'
        f'background:#faf9f5;color:#55534e;border-top:1px solid #e5e3dd;'
        f'padding:10px 16px;margin-top:24px">'
        f'Read-only copy &middot; content last updated '
        f'<b>{when.strftime("%-d %b %Y, %H:%M") if os.name != "nt" else when.strftime("%#d %b %Y, %H:%M")}</b>'
        f' &middot; published from the Studio. Changes made here are not saved back.'
        f'</div>'
    )
    if BANNER_MARK in html:
        return html
    lower = html.lower()
    i = lower.rfind("</body>")
    return (html[:i] + banner + html[i:]) if i != -1 else (html + banner)


def published_date(html: str):
    """The content date of a page already in the destination, or None if it has no stamp."""
    from datetime import datetime
    m = re.search(r'data-mas-updated="([^"]+)"', html)
    if not m:
        return None
    try:
        return datetime.fromisoformat(m.group(1))
    except ValueError:
        return None


def publish(dest: Path, data: Path | None = None, dry_run: bool = False) -> dict:
    data = data or _data_root()
    files = collect(data)
    copied = skipped = kept_newer = 0
    for src in files:
        rel = src.relative_to(data)
        out = dest / rel
        # Unchanged files are skipped so the sync client is not handed thousands of identical
        # writes on every publish — that is what turns a sync folder into a storm.
        try:
            want = _stamp(src.read_text(encoding="utf-8", errors="replace"), src.stat().st_mtime)
        except OSError:
            want = None
        if want is None:                      # unreadable: fall back to a plain copy
            if out.is_file() and filecmp.cmp(src, out, shallow=False):
                skipped += 1
                continue
            if not dry_run:
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, out)
            copied += 1
            continue
        # Compare against what we would WRITE, not against the source — the published copy
        # carries a banner the source does not, so a source-to-dest compare never matches and
        # every page would be rewritten on every run.
        if out.is_file():
            try:
                existing = out.read_text(encoding="utf-8", errors="replace")
            except OSError:
                existing = None
            if existing == want:
                skipped += 1
                continue
            # MULTI-WRITER SAFETY. Every operator publishes, so the organisation's pages keep
            # updating when any one person is away — but that means somebody whose DATA clone is
            # behind would otherwise republish old pages over newer ones, and the whole company
            # would watch the dashboards go backwards with no error anywhere. A page is only ever
            # replaced by content at least as new as what is already there.
            if existing is not None:
                theirs = published_date(existing)
                mine = datetime.fromtimestamp(src.stat().st_mtime).astimezone()
                if theirs is not None and theirs > mine:
                    kept_newer += 1
                    continue
        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(want, encoding="utf-8")
        copied += 1
    if not dry_run and files:
        stamp = (f"Published {datetime.now().astimezone().isoformat(timespec='seconds')} — "
                 f"{len(files)} surfaces.\nRead-only view. The authoritative store is the "
                 f"DATA git repo; changes made here are not read back.\n")
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "_PUBLISHED.txt").write_text(stamp, encoding="utf-8")
    return {"total": len(files), "copied": copied, "skipped": skipped,
            "kept_newer": kept_newer}


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
    kept = res.get("kept_newer", 0)
    print(f"published {res['copied']} changed / {res['skipped']} unchanged "
          f"of {res['total']} surfaces -> {dest}")
    if kept:
        print(f"  {kept} page(s) left alone - a colleague had already published something newer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
