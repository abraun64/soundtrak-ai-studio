#!/usr/bin/env python3
"""
storyboard_frames — SYS-121. Generate the per-beat "Frame column" stills a
storyboard must ship (operator rule feedback_storyboards_show_image_and_text).

A storyboard is reviewable as PICTURE + WORDS, not prose. Every beat/scene needs a
thumbnail beside its text. This helper produces those thumbnails DETERMINISTICALLY so
they regenerate on every rebuild, from whichever source exists for a beat:

  1. actual footage  — if the beat names a clip file that exists, extract a
                        representative frame with OpenCV (cv2.VideoCapture — already a
                        repo dependency; NO ffmpeg, which is not installed here).
  2. rendered still  — else if the beat names a keyframe HTML/SVG, render it to PNG in
                        headless chromium via Playwright (same pattern as
                        capture-stills.py / export_portable_assets.py).
  3. FAIL LOUD       — else the beat has no source: report it and exit non-zero.
                        NEVER emit an empty / placeholder image (a blank frame that
                        pretends a still exists is exactly the failure this prevents).

Deterministic output name, per beat:  <thumbs_dir>/beat-<n>-<slug>.png

INPUTS (one of):
  --storyboard <dir>   a storyboard folder. Looks for a beats manifest
                       (beats.yaml / storyboard-frames.yaml) in that dir; if absent,
                       PARSES a storyboard.md / *storyboard*.html in the dir for its
                       beat table (beat number + slug + optional clip/keyframe).
  --manifest <yaml>    an explicit beats manifest (schema below).

MANIFEST schema (YAML):
    thumbs_dir: thumbs            # optional, default "thumbs" (relative to manifest dir)
    width: 1920                   # optional default render width  (keyframe rendering)
    height: 1080                  # optional default render height
    beats:
      - n: 0
        slug: intro
        clip: launch-video.mp4    # optional — extract a frame if the file exists
        at_frac: 0.5              # optional — 0..1 fraction of the clip (default mid)
        # at_sec: 3.2             # optional — absolute seconds (overrides at_frac)
      - n: 1
        slug: brief
        keyframe: keyframes/brief.svg   # rendered when there is no clip
        width: 1080               # optional per-beat override
        height: 1080

All relative paths resolve against the manifest / storyboard directory.

    python .claude/lib/storyboard_frames.py --manifest path/to/beats.yaml
    python .claude/lib/storyboard_frames.py --storyboard campaigns/<c>/assets/<a>

Exit 0 = every beat's still was produced; exit 1 = at least one beat failed (missing
source, unreadable clip, or a missing render dependency) — the offending beats are
named. cv2 / Playwright are imported lazily so this module compiles and `--help`
works even when those deps are absent; a dep is only required when a beat actually
needs it, and its absence FAILS LOUD (never a faked frame).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
CLIP_EXTS = {".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv"}
KEYFRAME_EXTS = {".html", ".htm", ".svg"}


class BeatError(Exception):
    """A single beat could not be turned into a still (no source / unreadable / no dep)."""


# ── slug + name helpers ──────────────────────────────────────────────────────
def slugify(text: str, maxlen: int = 40) -> str:
    """A file-safe slug: lowercase, alnum + single hyphens, capped length."""
    text = re.sub(r"[^\w\s-]", "", str(text).lower())
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    text = re.sub(r"-{2,}", "-", text) or "beat"
    if len(text) > maxlen:
        text = text[:maxlen].rstrip("-")
    return text or "beat"


def out_name(n, slug: str) -> str:
    return f"beat-{n}-{slugify(slug)}.png"


# ── frame extraction (footage) ───────────────────────────────────────────────
def extract_frame_from_clip(clip: Path, out: Path, at_sec=None, at_frac=None) -> None:
    """Extract ONE representative frame from a video clip via OpenCV. No ffmpeg."""
    try:
        import cv2  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        raise BeatError(
            f"OpenCV (cv2) is required to extract a frame from {clip.name} but is not "
            f"importable ({e}). Install it (pip install opencv-python-headless)."
        ) from e

    cap = cv2.VideoCapture(str(clip))
    try:
        if not cap.isOpened():
            raise BeatError(f"could not open clip {clip} (unreadable / unsupported codec)")
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0

        if at_sec is not None and fps > 0:
            target = int(float(at_sec) * fps)
        elif at_frac is not None and total > 0:
            target = int(total * min(max(float(at_frac), 0.0), 1.0))
        else:
            target = total // 2 if total > 0 else 0
        if total > 0:
            target = min(max(target, 0), total - 1)

        cap.set(cv2.CAP_PROP_POS_FRAMES, float(target))
        ok, frame = cap.read()
        if not ok or frame is None:
            # Some containers mis-report the count / fail a seek — fall back to frame 0.
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0.0)
            ok, frame = cap.read()
        if not ok or frame is None:
            raise BeatError(f"could not read any frame from {clip}")
        out.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(out), frame):
            raise BeatError(f"cv2.imwrite failed for {out}")
    finally:
        cap.release()


# ── keyframe rendering (SVG / HTML) ──────────────────────────────────────────
def render_keyframe(src: Path, out: Path, width: int = 1920, height: int = 1080) -> None:
    """Render an HTML / SVG keyframe to PNG in headless chromium (Playwright)."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        raise BeatError(
            f"Playwright is required to render keyframe {src.name} but is not importable "
            f"({e}). Install it (pip install playwright && playwright install chromium)."
        ) from e

    out.parent.mkdir(parents=True, exist_ok=True)
    uri = src.resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--force-color-profile=srgb", "--font-render-hinting=none"])
        try:
            pg = b.new_page(viewport={"width": int(width), "height": int(height)},
                            device_scale_factor=2)
            pg.goto(uri, wait_until="load")
            try:
                pg.evaluate("() => document.fonts.ready")
            except Exception:  # noqa: BLE001
                pass
            # Freeze any animation to its first painted state for a stable still.
            try:
                pg.add_style_tag(content="*{animation-play-state:paused !important;}")
            except Exception:  # noqa: BLE001
                pass
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": int(width), "height": int(height)})
        finally:
            b.close()


# ── manifest loading + storyboard parsing ────────────────────────────────────
def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"PyYAML is required to read {path.name}: {e}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


_MANIFEST_NAMES = ("beats.yaml", "beats.yml", "storyboard-frames.yaml",
                   "storyboard-frames.yml", "frames.yaml")


def _beat_tables_from_markdown(text: str):
    """Yield beat tables parsed from markdown: (headers, rows) where rows are cell lists."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]) and "-" in lines[i + 1]:
            headers = [c.strip() for c in line.strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            yield headers, rows
            i = j
        else:
            i += 1


def beats_from_storyboard_dir(sb_dir: Path) -> tuple[list[dict], Path]:
    """Return (beats, base_dir). Prefer a manifest; else parse a storyboard.md beat table."""
    for name in _MANIFEST_NAMES:
        mf = sb_dir / name
        if mf.exists():
            data = _load_yaml(mf)
            return _normalise_beats(data.get("beats") or []), sb_dir

    # Parse a markdown storyboard's beat table for beat number + slug (+ inline clip/keyframe
    # if a cell names one). This gives slugs/numbers; sources still come from the cells.
    md = None
    for cand in sorted(sb_dir.glob("*storyboard*.md")) + sorted(sb_dir.glob("storyboard*.md")):
        md = cand
        break
    if not md:
        raise SystemExit(
            f"No beats manifest ({' / '.join(_MANIFEST_NAMES)}) and no *storyboard*.md in "
            f"{sb_dir}. Pass --manifest, or add a beats manifest."
        )
    text = md.read_text(encoding="utf-8", errors="replace")
    beats: list[dict] = []
    for headers, rows in _beat_tables_from_markdown(text):
        info = _classify_beat_header(headers)
        if not info["is_beat_table"]:
            continue
        for r in rows:
            n = _cell(r, info["num_idx"])
            n = re.sub(r"[^\w.-]", "", n) or str(len(beats))
            # slug from a label / caption column if present, else the beat id
            label_idx = info.get("label_idx")
            slug_src = _cell(r, label_idx) if label_idx is not None else n
            beat = {"n": n, "slug": slugify(slug_src or n)}
            # inline source references, if the frame cell already names a file
            fcell = _cell(r, info.get("frame_idx"))
            m = re.search(r"\(([^)]+\.(?:png|jpg|jpeg|gif|webp|svg|html?))\)", fcell, re.I) or \
                re.search(r'src=["\']([^"\']+)["\']', fcell, re.I)
            if m:
                ref = m.group(1)
                if Path(ref).suffix.lower() in KEYFRAME_EXTS:
                    beat["keyframe"] = ref
            beats.append(beat)
        break  # first beat table wins
    if not beats:
        raise SystemExit(f"Could not find a beat table in {md}.")

    # Convenience for the common "one master clip drives N beats" case: if no beat named its
    # own source and exactly one primary clip sits in the folder, assign it to every beat with
    # evenly-spaced representative frames. Precise per-beat timings still come via a manifest.
    if not any(b.get("clip") or b.get("keyframe") for b in beats):
        clips = [c for c in sorted(sb_dir.iterdir())
                 if c.is_file() and c.suffix.lower() in CLIP_EXTS]
        if len(clips) == 1:
            clip_rel = clips[0].name
            total = len(beats)
            for i, b in enumerate(beats):
                b["clip"] = clip_rel
                b["at_frac"] = round((i + 0.5) / total, 4)
    return beats, sb_dir


def _normalise_beats(raw: list) -> list[dict]:
    beats = []
    for i, b in enumerate(raw or []):
        if not isinstance(b, dict):
            continue
        n = b.get("n", b.get("beat", i))
        slug = b.get("slug") or b.get("label") or str(n)
        beat = {"n": n, "slug": slugify(slug)}
        for k in ("clip", "keyframe", "at_sec", "at_frac", "width", "height"):
            if b.get(k) is not None:
                beat[k] = b[k]
        beats.append(beat)
    return beats


# ── beat-table header classification (shared with the lint's intent) ─────────
_NUM_HEADERS = {"#", "beat", "beat #", "scene", "scene #", "shot", "segment", "frame #"}
# Short-label columns only — a beat's name/id, never a prose column (on-screen text /
# caption / VO), so auto-derived slugs stay short + stable.
_LABEL_HEADERS = {"beat", "segment", "scene", "shot", "label", "name"}


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", h or "").strip().lower())


def _classify_beat_header(headers: list[str]) -> dict:
    norm = [_norm_header(h) for h in headers]
    frame_idx = next((i for i, h in enumerate(norm) if "frame" in h), None)
    num_idx = next((i for i, h in enumerate(norm) if h in _NUM_HEADERS or h == "#"), None)
    label_idx = next((i for i, h in enumerate(norm)
                      if h in _LABEL_HEADERS and i != num_idx), None)
    first_is_beatish = bool(norm) and norm[0] in {"#", "beat", "scene", "shot", "segment"}
    is_beat_table = (frame_idx is not None) or first_is_beatish
    if num_idx is None and first_is_beatish:
        num_idx = 0
    return {
        "is_beat_table": is_beat_table,
        "frame_idx": frame_idx,
        "num_idx": num_idx if num_idx is not None else 0,
        "label_idx": label_idx,
    }


def _cell(row: list, idx) -> str:
    if idx is None or idx >= len(row):
        return ""
    return row[idx]


# ── the lint: does a storyboard surface carry a still per beat? (SYS-121) ─────
# Shared by build-gallery --check so authoring (the generator) and enforcement (the
# lint) agree on what a "beat table" and a "Frame still" are.
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_IMG_TAG_RE = re.compile(r"<img\b", re.I)
_SVG_TAG_RE = re.compile(r"<svg\b", re.I)
# A beat can legitimately have NO captured clip (a brand card / animated title). Such a
# Frame cell declares that deliberately; it is NOT the accidental omission the rule targets.
_NOCLIP_RE = re.compile(
    r"no\s+(?:screen\s+)?clip|no\s+footage|animated\s+card|title\s+card|card\s+only|brand\s+card",
    re.I,
)


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "").replace("&amp;", "&").strip()


def _beat_tables_from_html(text: str):
    """Yield (headers, rows) for each <table>; rows keep RAW cell HTML (to spot <img>/<svg>)."""
    for tbl in re.findall(r"<table\b.*?</table>", text, re.I | re.S):
        trs = re.findall(r"<tr\b.*?</tr>", tbl, re.I | re.S)
        if not trs:
            continue
        headers: list[str] = []
        header_idx = None
        for idx, tr in enumerate(trs):
            ths = re.findall(r"<th\b[^>]*>(.*?)</th>", tr, re.I | re.S)
            if ths:
                headers = [_strip_tags(h) for h in ths]
                header_idx = idx
                break
        rows = []
        for idx, tr in enumerate(trs):
            if idx == header_idx:
                continue
            tds = re.findall(r"<td\b[^>]*>(.*?)</td>", tr, re.I | re.S)
            if tds:
                rows.append(tds)
        if headers:
            yield headers, rows


def _cell_has_still(cell: str) -> bool:
    return bool(_IMG_TAG_RE.search(cell) or _SVG_TAG_RE.search(cell) or _MD_IMG_RE.search(cell))


def storyboard_frame_violations(path) -> list[str]:
    """Return violation strings if a storyboard surface's beat table lacks per-beat stills.

    Enforces feedback_storyboards_show_image_and_text: every beat/scene row must carry a
    Frame still (a captured frame or a rendered keyframe) beside its text. Flags:
      - a beat table with NO Frame column at all, or
      - a beat table whose Frame column has empty cells for one or more beats.
    Returns [] when the surface has no beat table (nothing to enforce) or every beat is framed.
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    is_html = p.suffix.lower() in {".html", ".htm"}
    tables = _beat_tables_from_html(text) if is_html else _beat_tables_from_markdown(text)
    problems: list[str] = []
    for headers, rows in tables:
        info = _classify_beat_header(headers)
        if not info["is_beat_table"]:
            continue
        n = len(rows)
        if n == 0:
            continue
        fidx = info["frame_idx"]
        if fidx is None:
            problems.append(
                f"beat table with {n} beats has NO Frame column — every beat needs a rendered "
                f"still beside its text (thumbs/beat-<n>-<slug>.png); see storyboard_frames.py"
            )
            continue
        missing = sum(
            1 for r in rows
            if not (_cell_has_still(_cell(r, fidx)) or _NOCLIP_RE.search(_cell(r, fidx)))
        )
        if missing:
            problems.append(
                f"beat table has {n} beats but {n - missing} carry a Frame still — {missing} "
                f"beat(s) missing a frame (regenerate with storyboard_frames.py)"
            )
    return problems


# ── the generator ────────────────────────────────────────────────────────────
def generate(beats: list[dict], base_dir: Path, thumbs_dir: str = "thumbs",
             width: int = 1920, height: int = 1080) -> tuple[list[Path], list[str]]:
    """Produce a deterministic still per beat. Returns (written, failures)."""
    out_dir = (base_dir / thumbs_dir)
    written: list[Path] = []
    failures: list[str] = []
    for b in beats:
        n, slug = b["n"], b["slug"]
        out = out_dir / out_name(n, slug)
        try:
            clip = b.get("clip")
            keyframe = b.get("keyframe")
            clip_path = (base_dir / clip) if clip else None
            kf_path = (base_dir / keyframe) if keyframe else None
            if clip_path and clip_path.exists():
                extract_frame_from_clip(clip_path, out, at_sec=b.get("at_sec"),
                                        at_frac=b.get("at_frac"))
            elif kf_path and kf_path.exists():
                render_keyframe(kf_path, out, width=int(b.get("width", width)),
                                height=int(b.get("height", height)))
            else:
                # No usable source. FAIL LOUD — never write a placeholder.
                want = []
                if clip:
                    want.append(f"clip '{clip}' (not found)")
                if keyframe:
                    want.append(f"keyframe '{keyframe}' (not found)")
                if not want:
                    want.append("no clip and no keyframe declared")
                raise BeatError("; ".join(want))
            written.append(out)
        except BeatError as e:
            failures.append(f"beat {n} ({slug}): {e}")
    return written, failures


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate per-beat storyboard Frame stills (SYS-121).")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--storyboard", help="storyboard folder (manifest or *storyboard*.md inside)")
    src.add_argument("--manifest", help="explicit beats manifest YAML")
    ap.add_argument("--thumbs", default=None, help="thumbs dir (default: thumbs, or manifest value)")
    ap.add_argument("--width", type=int, default=1920, help="default keyframe render width")
    ap.add_argument("--height", type=int, default=1080, help="default keyframe render height")
    args = ap.parse_args(argv)

    thumbs = args.thumbs
    width, height = args.width, args.height
    if args.manifest:
        mf = Path(args.manifest).resolve()
        if not mf.exists():
            print(f"ERROR: manifest not found: {mf}", file=sys.stderr)
            return 1
        data = _load_yaml(mf)
        beats = _normalise_beats(data.get("beats") or [])
        base_dir = mf.parent
        thumbs = thumbs or data.get("thumbs_dir") or "thumbs"
        width = int(data.get("width", width))
        height = int(data.get("height", height))
    else:
        sb_dir = Path(args.storyboard).resolve()
        if not sb_dir.is_dir():
            print(f"ERROR: storyboard dir not found: {sb_dir}", file=sys.stderr)
            return 1
        beats, base_dir = beats_from_storyboard_dir(sb_dir)
        thumbs = thumbs or "thumbs"

    if not beats:
        print("ERROR: no beats found to render.", file=sys.stderr)
        return 1

    written, failures = generate(beats, base_dir, thumbs_dir=thumbs, width=width, height=height)
    for w in written:
        print(f"  wrote {w}")
    if failures:
        print(f"\nFAIL ({len(failures)}) — these beats have no usable source (no placeholder written):",
              file=sys.stderr)
        for f in failures:
            print(f"  x {f}", file=sys.stderr)
        return 1
    print(f"\nOK — {len(written)} beat still(s) written to {base_dir / thumbs}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
