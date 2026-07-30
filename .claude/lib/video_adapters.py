#!/usr/bin/env python3
"""video_adapters.py — the pipeline-specific PRODUCTION front-ends for the video-export engine (SYS-111b).

**Production ≠ delivery.** Each pipeline produces a raw MP4 its OWN way (three different tools — they
can't be unified); then all three hand that MP4 to `video_export.finalize_video()` for the SHARED
delivery step (spec-scaled MP4 + GIF + poster + upload-pack manifest). Front-ends:

  - html      Playwright frame-grab of an HTML/CSS animation → raw MP4. Generalises the launch-video's
              capture-stills.py + make-mp4.py — parameterised html / dims / fps / duration (real-time
              capture of an animation that "plays on load").
  - remotion  thin wrap over `npx remotion render <composition> <out>` (needs Node + `npm i` in the project).
  - recording pass-through — a screen recording is already an MP4; finalize it straight.

    python .claude/lib/video_adapters.py html      --source anim.html --out ./delivery --seconds 20
    python .claude/lib/video_adapters.py remotion   --project ./remotion --composition Main --out ./delivery
    python .claude/lib/video_adapters.py recording  --source screencap.mp4 --out ./delivery
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from video_export import DeliverySpec, finalize_video  # noqa: E402


def capture_html(html_path: Path, out_mp4: Path, *, width=1080, height=1080, fps=30,
                 seconds: float = 20.0) -> Path:
    """Play an HTML/CSS animation headless (Playwright) and screenshot it frame-by-frame into an MP4.
    Real-time capture, matching the launch-video pattern ("the build IS the video; plays on load")."""
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    from playwright.sync_api import sync_playwright  # type: ignore

    html_uri = Path(html_path).resolve().as_uri()
    n = int(fps * seconds)
    writer = None
    for tag in ("avc1", "mp4v"):
        w = cv2.VideoWriter(str(out_mp4), cv2.VideoWriter_fourcc(*tag), fps, (width, height))
        if w.isOpened():
            writer = w
            break
    if writer is None:
        raise RuntimeError("no working OpenCV MP4 codec (avc1/mp4v) for HTML capture")
    interval = 1.0 / fps
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            pg.goto(html_uri, wait_until="load")
            for _ in range(n):
                png = pg.screenshot(type="png")
                frame = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    if frame.shape[1] != width or frame.shape[0] != height:
                        frame = cv2.resize(frame, (width, height))
                    writer.write(frame)
                time.sleep(interval)
            b.close()
    finally:
        writer.release()
    return Path(out_mp4)


def render_remotion(project_dir: Path, composition: str, out_mp4: Path, *, props: dict | None = None) -> Path:
    """Wrap `npx remotion render <composition> <out>` in a Remotion project dir."""
    npx = shutil.which("npx")
    if not npx:
        raise RuntimeError("remotion adapter needs Node.js/npx on PATH — install Node and run `npm i` "
                           "in the remotion project before rendering")
    out_mp4 = Path(out_mp4).resolve()
    cmd = [npx, "--yes", "remotion", "render", composition, str(out_mp4)]
    if props:
        cmd += ["--props", json.dumps(props)]
    subprocess.run(cmd, cwd=str(project_dir), check=True)
    return out_mp4


def from_recording(mp4_path: Path) -> Path:
    """A screen recording is already an MP4 — nothing to produce; finalize it straight."""
    p = Path(mp4_path)
    if not p.exists():
        raise FileNotFoundError(p)
    return p


def produce_and_finalize(kind: str, out_dir: Path, spec: DeliverySpec, *, source=None, project=None,
                         composition=None, seconds: float = 20.0, props=None, name=None):
    """Dispatch to the right production front-end, then run the shared finalize/delivery step."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="vidraw-"))
    if kind == "html":
        raw = capture_html(source, tmp / "raw.mp4", width=spec.width, height=spec.height,
                           fps=spec.fps, seconds=seconds)
    elif kind == "remotion":
        raw = render_remotion(project, composition, tmp / "raw.mp4", props=props)
    elif kind == "recording":
        raw = from_recording(source)
    else:
        raise ValueError(f"unknown pipeline kind: {kind!r} (html | remotion | recording)")
    return finalize_video(raw, out_dir, spec, name=name)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Produce a video via one pipeline, then run the shared finalize step.")
    ap.add_argument("kind", choices=["html", "remotion", "recording"])
    ap.add_argument("--source", help="html file (html) or existing mp4 (recording)")
    ap.add_argument("--project", help="remotion project dir (remotion)")
    ap.add_argument("--composition", help="remotion composition id (remotion)")
    ap.add_argument("--props", help="remotion props as JSON (remotion)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seconds", type=float, default=20.0, help="html capture duration")
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--destination", default="")
    ap.add_argument("--name", default=None)
    a = ap.parse_args(argv)
    spec = DeliverySpec(width=a.width, height=a.height, fps=a.fps, gif=a.gif, destination=a.destination)
    try:
        r = produce_and_finalize(a.kind, Path(a.out), spec, source=a.source, project=a.project,
                                 composition=a.composition, seconds=a.seconds,
                                 props=(json.loads(a.props) if a.props else None), name=a.name)
    except Exception as e:  # noqa: BLE001
        print(f"video_adapters ({a.kind}) failed: {e}", file=sys.stderr)
        return 1
    print(f"[{a.kind} → {r.backend}] mp4={r.mp4.name}"
          + (f" poster={r.poster.name}" if r.poster else "")
          + (f" gif={r.gif.name}" if r.gif else "") + f" manifest={r.manifest.name}")
    for n in r.notes:
        print(f"  note: {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
