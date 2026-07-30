#!/usr/bin/env python3
"""video_export.py — the shared VIDEO delivery/finalize engine (SYS-111b, export-OUT video).

**authoring ≠ delivery.** HOW a video is produced stays pipeline-specific — there is no unifying
them because they're three different tools:
  1. HTML/CSS-animation capture (Playwright frame-grab of an HTML animation → MP4; the launch-video)
  2. Remotion (React/TSX → `remotion render` → MP4 natively)
  3. screen-recording (OS capture → edited → MP4)
What they ALL share, and what this module generalises (3 real instances → not over-fitting), is the
DELIVERY step: take any produced MP4 + a delivery spec and emit the validated delivery bundle the
destination actually needs, plus a manifest the gallery's SYS-105 "Upload pack" section reads.

`finalize_video(source_mp4, out_dir, spec)` →
  - delivery MP4  (scaled to spec dims; H.264 + `+faststart` + silent where ffmpeg is available)
  - GIF fallback  (short, spec-scaled)                        [optional]
  - poster JPG    (a representative frame)                    [optional]
  - upload-manifest.json  ({file → destination}, for the gallery Upload pack)

Backend: prefers **ffmpeg** on PATH (true H.264 / +faststart / clean GIF). Falls back to **OpenCV
(cv2)** — already a repo dependency (the launch-video pipeline uses it) — for the transcode + poster,
and **Pillow/imageio** for the GIF, so it runs with NO new dependency. The install doctor should add
ffmpeg as a recommended (not required) prereq for best-quality delivery.

The per-pipeline production front-ends live beside this and just hand it a produced MP4:
  html-capture  → generalise capture-stills.py + make-mp4.py (a future increment)
  remotion      → thin wrapper over `remotion render`         (a future increment)
  recording     → pass-through (the MP4 already exists)

    python .claude/lib/video_export.py --source clip.mp4 --out ./delivery --width 1080 --height 1080 --gif
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DeliverySpec:
    """What the destination needs. Sensible silent-social defaults (the launch-video shape)."""
    width: int = 1080
    height: int = 1080
    fps: int = 30
    codec: str = "h264"        # ffmpeg libx264; cv2 falls back to avc1/mp4v
    faststart: bool = True      # move moov atom to front for web streaming (ffmpeg only)
    silent: bool = True         # strip audio
    gif: bool = False
    gif_seconds: float = 4.0
    gif_width: int = 480
    poster: bool = True
    poster_at: float = 0.5      # fraction through the clip
    destination: str = ""       # where this delivery goes (LinkedIn / Substack Note / …)


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


# ── ffmpeg backend (preferred) ────────────────────────────────────────────────
def _ff_transcode(ff: str, src: Path, out: Path, spec: DeliverySpec) -> None:
    scale = f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=decrease," \
            f"pad={spec.width}:{spec.height}:(ow-iw)/2:(oh-ih)/2"
    cmd = [ff, "-y", "-i", str(src), "-vf", scale, "-r", str(spec.fps),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20"]
    if spec.faststart:
        cmd += ["-movflags", "+faststart"]
    cmd += (["-an"] if spec.silent else [])
    cmd += [str(out)]
    subprocess.run(cmd, check=True, capture_output=True)


def _ff_gif(ff: str, src: Path, out: Path, spec: DeliverySpec) -> None:
    vf = f"fps=12,scale={spec.gif_width}:-1:flags=lanczos"
    subprocess.run([ff, "-y", "-t", str(spec.gif_seconds), "-i", str(src),
                    "-vf", vf, "-loop", "0", str(out)], check=True, capture_output=True)


def _ff_poster(ff: str, src: Path, out: Path, spec: DeliverySpec) -> None:
    dur = _probe_duration(src) or 2.0
    subprocess.run([ff, "-y", "-ss", str(max(0.0, dur * spec.poster_at)), "-i", str(src),
                    "-frames:v", "1", "-q:v", "3", str(out)], check=True, capture_output=True)


def _probe_duration(src: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(src)], capture_output=True, text=True, check=True)
        return float(r.stdout.strip())
    except Exception:
        return None


# ── OpenCV fallback (no ffmpeg) ───────────────────────────────────────────────
def _cv2():
    try:
        import cv2  # type: ignore
        return cv2
    except Exception:
        return None


def _cv_transcode(src: Path, out: Path, spec: DeliverySpec) -> None:
    cv2 = _cv2()
    if cv2 is None:
        raise RuntimeError("neither ffmpeg nor OpenCV (cv2) is available — install one to finalize video")
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {src}")
    writer = None
    for tag in ("avc1", "mp4v"):
        w = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*tag), spec.fps, (spec.width, spec.height))
        if w.isOpened():
            writer = w
            break
    if writer is None:
        cap.release()
        raise RuntimeError("no working OpenCV MP4 codec (avc1/mp4v)")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(_letterbox(cv2, frame, spec.width, spec.height))
    finally:
        cap.release()
        writer.release()


def _letterbox(cv2, frame, w: int, h: int):
    ih, iw = frame.shape[:2]
    s = min(w / iw, h / ih)
    nw, nh = int(iw * s), int(ih * s)
    resized = cv2.resize(frame, (nw, nh))
    import numpy as np
    canvas = np.zeros((h, w, 3), dtype=resized.dtype)
    x, y = (w - nw) // 2, (h - nh) // 2
    canvas[y:y + nh, x:x + nw] = resized
    return canvas


def _cv_poster(src: Path, out: Path, spec: DeliverySpec) -> None:
    cv2 = _cv2()
    if cv2 is None:
        return
    cap = cv2.VideoCapture(str(src))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * spec.poster_at))
    ok, frame = cap.read()
    cap.release()
    if ok:
        cv2.imwrite(str(out), _letterbox(cv2, frame, spec.width, spec.height))


def _cv_gif(src: Path, out: Path, spec: DeliverySpec) -> bool:
    """GIF via imageio or Pillow if importable; returns False (with a note) if neither is present."""
    cv2 = _cv2()
    if cv2 is None:
        return False
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or spec.fps
    step = max(1, int(fps / 12))
    frames, i, maxframes = [], 0, int((spec.gif_seconds) * 12)
    while len(frames) < maxframes:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            f = _letterbox(cv2, frame, spec.gif_width, int(spec.gif_width * spec.height / spec.width))
            frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        i += 1
    cap.release()
    if not frames:
        return False
    try:
        import imageio  # type: ignore
        imageio.mimsave(str(out), frames, duration=1 / 12, loop=0)
        return True
    except Exception:
        pass
    try:
        from PIL import Image  # type: ignore
        imgs = [Image.fromarray(f) for f in frames]
        imgs[0].save(str(out), save_all=True, append_images=imgs[1:], duration=int(1000 / 12), loop=0)
        return True
    except Exception:
        return False


# ── public API ────────────────────────────────────────────────────────────────
@dataclass
class DeliveryResult:
    mp4: Path
    poster: Path | None = None
    gif: Path | None = None
    manifest: Path | None = None
    backend: str = ""
    notes: list = field(default_factory=list)


def finalize_video(source_mp4: Path, out_dir: Path, spec: DeliverySpec | None = None,
                   name: str | None = None) -> DeliveryResult:
    """Turn a produced MP4 (from ANY pipeline) into the destination-ready delivery bundle."""
    spec = spec or DeliverySpec()
    source_mp4 = Path(source_mp4)
    if not source_mp4.exists():
        raise FileNotFoundError(source_mp4)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = name or source_mp4.stem
    mp4 = out_dir / f"{stem}.mp4"
    poster = out_dir / f"{stem}-poster.jpg"
    gif = out_dir / f"{stem}.gif"
    res = DeliveryResult(mp4=mp4)
    ff = _ffmpeg()
    res.backend = "ffmpeg" if ff else "opencv"

    if ff:
        _ff_transcode(ff, source_mp4, mp4, spec)
        if spec.poster:
            _ff_poster(ff, source_mp4, poster, spec); res.poster = poster
        if spec.gif:
            _ff_gif(ff, source_mp4, gif, spec); res.gif = gif
    else:
        res.notes.append("ffmpeg not found — used OpenCV fallback (no true H.264/+faststart). "
                         "Install ffmpeg for best-quality web delivery.")
        _cv_transcode(source_mp4, mp4, spec)
        if spec.poster:
            _cv_poster(source_mp4, poster, spec)
            res.poster = poster if poster.exists() else None
        if spec.gif:
            res.gif = gif if _cv_gif(source_mp4, gif, spec) else None
            if res.gif is None:
                res.notes.append("GIF skipped — install imageio or Pillow (or ffmpeg) to produce it.")

    # Upload-pack manifest (SYS-105 shape): the gallery reads this to show file → destination.
    manifest = out_dir / "upload-manifest.json"
    manifest.write_text(json.dumps({
        "kind": "video-delivery", "source": source_mp4.name, "backend": res.backend,
        "destination": spec.destination,
        "spec": {"width": spec.width, "height": spec.height, "fps": spec.fps, "silent": spec.silent},
        "files": [p.name for p in (mp4, res.poster, res.gif) if p],
        "notes": res.notes,
    }, indent=2), encoding="utf-8")
    res.manifest = manifest
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Finalize a produced MP4 into a destination-ready delivery bundle.")
    ap.add_argument("--source", required=True, help="the produced MP4 (from any pipeline)")
    ap.add_argument("--out", required=True, help="output dir for the delivery bundle")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--gif", action="store_true", help="also emit a GIF fallback")
    ap.add_argument("--no-poster", action="store_true")
    ap.add_argument("--destination", default="", help="label: where this delivery goes")
    ap.add_argument("--name", default=None)
    a = ap.parse_args(argv)
    spec = DeliverySpec(width=a.width, height=a.height, fps=a.fps, gif=a.gif,
                        poster=not a.no_poster, destination=a.destination)
    try:
        r = finalize_video(Path(a.source), Path(a.out), spec, name=a.name)
    except Exception as e:  # noqa: BLE001
        print(f"video_export failed: {e}", file=sys.stderr)
        return 1
    print(f"[{r.backend}] mp4={r.mp4.name}"
          + (f" poster={r.poster.name}" if r.poster else "")
          + (f" gif={r.gif.name}" if r.gif else "")
          + f" manifest={r.manifest.name}")
    for n in r.notes:
        print(f"  note: {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
