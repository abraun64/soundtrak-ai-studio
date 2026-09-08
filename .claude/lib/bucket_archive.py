#!/usr/bin/env python3
"""Bucket a tenant's FLAT post archive into per-edition folders (SYS-042).

A flat source folder holds many files whose names start with a zero-padded
edition number, e.g.::

    06_The-Wrong-Conversation_Substack-Article_Final.docx
    06_The-Wrong-Conversation_LinkedIn-Post.md
    06_hero.png
    07_...

Files that share the leading ``NN_`` (or ``NN-``) prefix belong to edition NN.
This tool groups the flat folder by that numeric prefix and lays out one folder
per edition under ``--dest``:  ``<dest>/NN-slug/`` plus a per-edition
``README.md`` manifest listing the planned members.

The tool is GENERIC — it buckets by numeric prefix; nothing is hardcoded to any
particular newsletter. The slug is best-effort, derived from the most common
title stem across an edition's files.

SAFETY (this runs over irreplaceable files):
  - DRY-RUN is the default. It prints the full plan and MOVES NOTHING.
  - ``--apply`` actually creates folders and moves files (``shutil.move``).
  - On a destination collision: SKIP + warn. Never overwrite.
  - NEVER deletes anything, in either mode.

Usage:
    # DRY-RUN (prints the plan, moves nothing) — always do this first:
    python .claude/lib/bucket_archive.py --src "<flat dir>" --dest "<editions dir>"

    # Execute the move (skip-on-collision, never-delete):
    python .claude/lib/bucket_archive.py --src "<flat dir>" --dest "<editions dir>" --apply

Options:
    --src DIR          Flat source folder of archive files (required).
    --dest DIR         Editions folder to create NN-slug/ subfolders under (required).
    --prefix-len N     Digits in the leading edition number (default 2).
    --apply            Actually move files. Omit for DRY-RUN.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Slug / prefix derivation
# ---------------------------------------------------------------------------

# Markers that signal the end of a title and the start of an asset-type tag.
# Used to trim a stem like "The-Wrong-Conversation_Substack-Article_Final" down
# to its title portion. Best-effort; lowercased compare.
_TYPE_MARKERS = {
    "substack-article", "substack", "article", "linkedin-post", "linkedin",
    "twitter", "thread", "twitter-thread", "image-prompt", "image", "prompt",
    "hero", "tile", "email", "newsletter", "blog", "instagram", "carousel",
    "tiktok", "script", "video", "ad", "final", "draft", "v1", "v2", "v3",
    "post", "asset", "copy", "headline", "caption", "og", "thumbnail",
}


def _slugify(text: str) -> str:
    """Lowercase, collapse to [a-z0-9-], trim repeated/edge hyphens."""
    text = text.strip().lower()
    # spaces, underscores and any non-alphanumeric -> hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def _is_type_field(field: str) -> bool:
    """True if a field is an asset-type tag rather than title text.

    Matches when the whole slugified field is a known marker, OR when a leading
    run of its hyphen-delimited tokens is — so ``Image-Prompt-A`` (marker
    ``image-prompt`` + trailing ``A``) and ``Email Final`` (marker ``email``)
    are both recognised as type tags, not title words.
    """
    slug = _slugify(field)
    if not slug:
        return False
    if slug in _TYPE_MARKERS:
        return True
    tokens = slug.split("-")
    # longest-prefix-first so "image-prompt" beats "image"
    for n in range(len(tokens), 0, -1):
        if "-".join(tokens[:n]) in _TYPE_MARKERS:
            return True
    return False


def title_stem(filename: str, prefix_len: int) -> str:
    """Best-effort title portion of a filename, before any asset-type marker.

    ``06_The-Wrong-Conversation_Substack-Article_Final.docx`` -> ``The-Wrong-Conversation``
    Returns "" when no title text can be recovered.
    """
    stem = Path(filename).stem  # drop extension
    # strip the leading NN_ / NN- prefix
    m = re.match(rf"^(\d{{{prefix_len}}})[_\-](.*)$", stem)
    body = m.group(2) if m else stem
    if not body:
        return ""
    # split on underscores first (the primary field separator), then walk
    # fields, keeping title fields until we hit a known type marker.
    parts = re.split(r"[_]+", body)
    kept: list[str] = []
    for part in parts:
        if not part:
            continue
        if _is_type_field(part):
            break
        kept.append(part)
    candidate = "_".join(kept) if kept else body
    return _slugify(candidate)


def numeric_prefix(filename: str, prefix_len: int) -> str | None:
    """Return the zero-padded NN prefix if the name starts with one, else None."""
    m = re.match(rf"^(\d{{{prefix_len}}})[_\-]", Path(filename).name)
    return m.group(1) if m else None


def derive_slug(filenames: list[str], prefix_len: int) -> str:
    """Most common non-empty title stem across an edition's files.

    Falls back to "" when nothing usable is found (caller then uses bare NN).
    """
    stems = [title_stem(f, prefix_len) for f in filenames]
    stems = [s for s in stems if s]
    if not stems:
        return ""
    # most common; ties broken by the longest (more descriptive) stem
    counts = Counter(stems)
    top = max(counts.items(), key=lambda kv: (kv[1], len(kv[0])))
    return top[0]


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

class Edition:
    def __init__(self, prefix: str, slug: str, files: list[Path]):
        self.prefix = prefix
        self.slug = slug
        self.files = files

    @property
    def folder_name(self) -> str:
        return f"{self.prefix}-{self.slug}" if self.slug else self.prefix


def build_plan(src: Path, prefix_len: int) -> tuple[list[Edition], list[Path]]:
    """Group files in `src` by numeric prefix.

    Returns (editions sorted by prefix, unbucketed files sorted by name).
    Only the immediate files in `src` are considered (no recursion); existing
    subfolders are ignored so re-runs are safe.
    """
    groups: dict[str, list[Path]] = defaultdict(list)
    unbucketed: list[Path] = []

    for entry in sorted(src.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_dir():
            continue  # leave any already-bucketed subfolders alone
        prefix = numeric_prefix(entry.name, prefix_len)
        if prefix is None:
            unbucketed.append(entry)
        else:
            groups[prefix].append(entry)

    editions: list[Edition] = []
    for prefix in sorted(groups):
        files = sorted(groups[prefix], key=lambda p: p.name.lower())
        slug = derive_slug([f.name for f in files], prefix_len)
        editions.append(Edition(prefix, slug, files))

    return editions, unbucketed


def manifest_text(edition: Edition) -> str:
    """README.md content listing the planned members of an edition."""
    lines = [
        f"# Edition {edition.prefix}"
        + (f" — {edition.slug}" if edition.slug else ""),
        "",
        f"Folder: `{edition.folder_name}/`",
        "",
        f"{len(edition.files)} file(s):",
        "",
    ]
    for f in edition.files:
        lines.append(f"- `{f.name}`")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rendering / applying
# ---------------------------------------------------------------------------

def run(src: Path, dest: Path, prefix_len: int, apply: bool) -> int:
    if not src.is_dir():
        print(f"ERROR: --src is not a directory: {src}", file=sys.stderr)
        return 2

    editions, unbucketed = build_plan(src, prefix_len)

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"=== bucket_archive [{mode}] ===")
    print(f"src:  {src}")
    print(f"dest: {dest}")
    print(f"prefix-len: {prefix_len}")
    print("")

    moved = 0
    skipped = 0

    for ed in editions:
        target_dir = dest / ed.folder_name
        print(f"[{ed.prefix}] -> {target_dir.name}/   (slug: {ed.slug or '(none — bare NN)'}, {len(ed.files)} file(s))")

        if apply:
            target_dir.mkdir(parents=True, exist_ok=True)
            # write manifest (skip-on-collision; never overwrite an existing one)
            readme = target_dir / "README.md"
            if readme.exists():
                print(f"      SKIP manifest (exists): {readme}")
            else:
                readme.write_text(manifest_text(ed), encoding="utf-8")
                print(f"      manifest: {readme.name}")

        for f in ed.files:
            destination = target_dir / f.name
            print(f"      {f.name}  ->  {target_dir.name}/{f.name}")
            if apply:
                if destination.exists():
                    print(f"      WARN: destination exists, SKIPPING: {destination}")
                    skipped += 1
                    continue
                shutil.move(str(f), str(destination))
                moved += 1
        print("")

    if unbucketed:
        print(f"--- unbucketed ({len(unbucketed)} file(s), left in place) ---")
        for f in unbucketed:
            print(f"      {f.name}")
        print("")

    # summary
    n_files = sum(len(e.files) for e in editions)
    print("=== summary ===")
    print(f"editions:   {len(editions)}")
    print(f"files:      {n_files} (in editions)")
    print(f"unbucketed: {len(unbucketed)}")
    if apply:
        print(f"moved:      {moved}")
        print(f"skipped (collision): {skipped}")
    else:
        print("(DRY-RUN — nothing was moved. Re-run with --apply to execute.)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bucket_archive.py",
        description="Bucket a flat archive into per-edition folders by numeric prefix. "
                    "DRY-RUN by default; pass --apply to move files (skip-on-collision, never-delete).",
    )
    parser.add_argument("--src", required=True, help="Flat source folder of archive files.")
    parser.add_argument("--dest", required=True, help="Editions folder; NN-slug/ subfolders go here.")
    parser.add_argument("--prefix-len", type=int, default=2,
                        help="Digits in the leading edition number (default 2).")
    parser.add_argument("--apply", action="store_true",
                        help="Actually create folders + move files. Omit for DRY-RUN.")
    args = parser.parse_args(argv)

    if args.prefix_len < 1:
        print("ERROR: --prefix-len must be >= 1", file=sys.stderr)
        return 2

    src = Path(args.src).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve()
    return run(src, dest, args.prefix_len, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
