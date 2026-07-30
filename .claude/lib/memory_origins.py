#!/usr/bin/env python3
"""SYS-046 — link memory rules back to the work that spawned them.

"Why does this rule exist?" should be a click-through, not a mystery. Each memory
file already carries origin *signals* (a `retro:` field, an `originSessionId:`, or a
body line like "Captured 2026-05-26 from operator question…"), but nothing ties a
rule to a backlog TICKET or gives the reverse view (which rules a ticket/retro
spawned). This tool derives that navigable map from the signals already present —
no guessing, no bulk rewrite of the user's memory store.

  # REPORT (read-only): the forward + reverse cross-reference + coverage
  python .claude/lib/memory_origins.py

  # BACKFILL a canonical `origin:` field, but ONLY where it is UNAMBIGUOUS
  # (a retro: field, or exactly one SYS-/IDEA- id cited in the body). Dry-run first.
  python .claude/lib/memory_origins.py --backfill            # show what it would set
  python .claude/lib/memory_origins.py --backfill --apply    # write it

Origin precedence (most authoritative first): an explicit `metadata.origin` →
`metadata.retro` → a single SYS-/IDEA- id cited in the body → a "Retro NN" mention.
Anything else is left UNATTRIBUTED (reported, never invented).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The report prints box-drawing + arrow glyphs; a cp1252 console (Windows) would crash
# on them. Reconfigure to UTF-8 with errors=replace so a print can never bring the tool down.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

SYS_RE = re.compile(r"\b(SYS-\d{3})\b")
IDEA_RE = re.compile(r"\b(IDEA-\d{3})\b")
RETRO_WORD_RE = re.compile(r"\bretro\s*0*([0-9]{1,3})\b", re.IGNORECASE)


def find_memory_dir(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.is_dir() else None
    base = Path.home() / ".claude" / "projects"
    cands = sorted(base.glob("*/memory")) if base.exists() else []
    for c in cands:
        if "Marketing-AI-System" in c.parent.name:
            return c
    return cands[0] if cands else None


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block, body). Empty frontmatter if the file has none."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            return text[:nl + 1] if nl != -1 else text, text[nl + 1:] if nl != -1 else ""
    return "", text


def parse_meta(fm: str) -> dict:
    try:
        import yaml
        d = yaml.safe_load(fm.strip().strip("-\n")) or {}
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def derive_origin(meta: dict, body: str) -> tuple[str | None, str]:
    """Return (origin, how). None origin = unattributed. `how` names the signal used."""
    md = meta.get("metadata") if isinstance(meta.get("metadata"), dict) else meta
    if md.get("origin"):
        return str(md["origin"]), "explicit origin field"
    if md.get("retro"):
        return str(md["retro"]), "retro field"
    sys_ids = sorted(set(SYS_RE.findall(body)) | set(IDEA_RE.findall(body)))
    if len(sys_ids) == 1:
        return sys_ids[0], "single ticket cited in body"
    m = RETRO_WORD_RE.search(body)
    if m:
        return f"retro-{int(m.group(1)):03d}", "retro mention in body"
    return None, "unattributed"


def backlog_titles(root: Path) -> dict:
    try:
        import yaml
        sys.path.insert(0, str(root / ".claude" / "lib"))
        import repo_paths
        data = repo_paths.data_root(root)
    except Exception:  # noqa: BLE001
        data = root
    out = {}
    for store in ("backlog.yaml", "ideas.yaml"):
        try:
            import yaml
            items = (yaml.safe_load((data / "system" / store).read_text(encoding="utf-8")) or {}).get("items", [])
            for it in items or []:
                if it.get("id"):
                    out[str(it["id"])] = str(it.get("title", ""))
        except Exception:  # noqa: BLE001
            continue
    return out


def collect(mem_dir: Path) -> list[dict]:
    rows = []
    for f in sorted(mem_dir.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        text = f.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        meta = parse_meta(fm)
        origin, how = derive_origin(meta, body)
        md = meta.get("metadata") if isinstance(meta.get("metadata"), dict) else meta
        rows.append({"file": f, "name": meta.get("name") or f.stem, "type": md.get("type", "?"),
                     "origin": origin, "how": how, "has_field": bool(md.get("origin"))})
    return rows


def backfill(mem_dir: Path, apply: bool) -> None:
    changed = 0
    for f in sorted(mem_dir.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        text = f.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        meta = parse_meta(fm)
        md = meta.get("metadata") if isinstance(meta.get("metadata"), dict) else meta
        if md.get("origin"):
            continue  # already attributed — never overwrite
        origin, how = derive_origin(meta, body)
        if not origin or how == "retro mention in body":
            continue  # only backfill the UNAMBIGUOUS signals (retro field / single cited id)
        # Insert `  origin: <value>` as the first key under `metadata:`.
        m = re.search(r"(?m)^metadata:\s*$", text)
        if not m:
            continue
        insert_at = text.find("\n", m.end()) + 1
        new = text[:insert_at] + f"  origin: {origin}\n" + text[insert_at:]
        try:
            import yaml
            nfm, _ = split_frontmatter(new)
            yaml.safe_load(nfm.strip().strip("-\n"))  # validate
        except Exception:  # noqa: BLE001
            continue
        print(f"  {'SET ' if apply else 'would set'} origin: {origin:<28} <- {f.name}  ({how})")
        if apply:
            f.write_text(new, encoding="utf-8")
        changed += 1
    print(f"\n{'Backfilled' if apply else 'Would backfill'} {changed} file(s)."
          + ("" if apply else "  Re-run with --apply to write."))


def report(mem_dir: Path, root: Path) -> None:
    rows = collect(mem_dir)
    titles = backlog_titles(root)
    attributed = [r for r in rows if r["origin"]]
    reverse: dict[str, list[str]] = {}
    for r in attributed:
        reverse.setdefault(r["origin"], []).append(r["name"])

    print(f"=== Memory origins — {len(rows)} memories in {mem_dir} ===\n")
    print(f"Attributed: {len(attributed)}/{len(rows)}   Unattributed: {len(rows) - len(attributed)}\n")

    print("── Reverse index: work → memory rules it spawned ──")
    for origin in sorted(reverse):
        title = titles.get(origin)
        label = f"  ({title})" if title else ""
        print(f"\n{origin}{label}")
        for name in sorted(reverse[origin]):
            print(f"    • {name}")

    unattr = [r for r in rows if not r["origin"]]
    if unattr:
        print(f"\n── Unattributed ({len(unattr)}) — no retro/ticket signal (mostly session-era feedback) ──")
        for r in sorted(unattr, key=lambda x: x["name"]):
            print(f"    • {r['name']}  [{r['type']}]")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-reference memory rules with the work that spawned them (SYS-046).")
    ap.add_argument("--memory-dir", help="path to the memory/ dir (default: auto-discover under ~/.claude/projects)")
    ap.add_argument("--backfill", action="store_true", help="set a canonical origin: field where UNAMBIGUOUS")
    ap.add_argument("--apply", action="store_true", help="with --backfill, actually write (default is dry-run)")
    args = ap.parse_args()

    mem_dir = find_memory_dir(args.memory_dir)
    if not mem_dir:
        print("ERROR: could not locate a memory/ dir (pass --memory-dir).", file=sys.stderr)
        return 1
    root = Path(__file__).resolve().parents[2]

    if args.backfill:
        print(f"Backfill{' (APPLY)' if args.apply else ' (dry-run)'} — {mem_dir}\n")
        backfill(mem_dir, args.apply)
    else:
        report(mem_dir, root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
