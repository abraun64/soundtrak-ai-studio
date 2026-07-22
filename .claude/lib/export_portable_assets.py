#!/usr/bin/env python3
"""
export_portable_assets — SYS-105. The INVERSE of render-html.

render-html: markdown -> HTML (the authoring / preview format).
this:        HTML     -> a PORTABLE PACK (clean copy + standalone PNGs), so a
                        non-website asset can be uploaded to an image-only /
                        WYSIWYG / CMS environment (Substack, Mailchimp, LinkedIn
                        native, most CMS rich-text editors) that does NOT accept
                        arbitrary HTML/CSS.

WHY: right-click "save image" only works on true <img>/SVG. It CANNOT capture an
HTML/CSS-composed graphic block (a masthead built from <div>s, an evidence card of
SVG + <div>s) — which is exactly where the brand design lives. So each such block is
rendered in headless chromium (brand fonts pinned) and screenshotted at 2x.

DATA-DRIVEN: reads the `portable:` manifest in the asset's asset.yaml — no per-asset
script. One tool, every campaign. Generalises the proven per-asset prototypes
(campaigns/*/_export-article-pngs.py, _render-header.py, _render-tile.py).

    portable:
      source_html: issue-header.html   # the HTML whose blocks are exported
      copy: copy.md                    # optional: the paste-ready body (a pointer)
      fonts: soundtrak                  # optional: tenant font set (default: none)
      images:
        - name: masthead
          selector: "header.masthead"  # CSS selector of the block to screenshot
          where: "Substack post header image"   # WHERE it goes on upload
          platform: Substack
        - name: evidence
          selector: ".art-evidence"
          where: "embed inline after the intro"
          platform: Substack

Output: <asset>/portable/<name>.png (@2x) for each image, beside a pointer to the copy.
The pack is production output (asset.yaml ship:false) — surfaced in the gallery
lightbox's "Upload pack" section, not as extra tiles.

Usage:
    python export_portable_assets.py --asset <asset_dir>
    python export_portable_assets.py --html <file> --out <dir> --selectors '[["header","masthead"]]'  # prototype fallback

Exit 0 on success (all declared blocks exported), 1 on a missing selector / no manifest.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Tenant font sets — pin brand fonts so a screenshot matches the shipped design exactly.
# Add a tenant here (or pass --fonts-dir). Missing dir → skip injection (HTML self-hosts).
_FONT_SETS = {
    "soundtrak": Path(r"C:/Users/<you>/OneDrive/Claude/Soundtrak-brand-guideline"),
}


def _font_css(fonts_dir: Path | None) -> str:
    if not fonts_dir or not fonts_dir.exists():
        return ""
    faces = []
    # discover every .ttf/.otf under the dir; name each face by its family folder/file stem
    for f in sorted(list(fonts_dir.rglob("*.ttf")) + list(fonts_dir.rglob("*.otf"))):
        fam = f.parent.name if f.parent != fonts_dir else f.stem.split("-")[0]
        faces.append(f"@font-face {{ font-family:'{fam}'; src:url('{f.as_uri()}'); font-weight:100 900; }}")
    if not faces:
        return ""
    return "\n".join(faces) + "\n* { text-rendering:geometricPrecision; -webkit-font-smoothing:antialiased; }"


def export_blocks(source_html: Path, out_dir: Path, blocks: list[dict],
                  fonts_dir: Path | None = None, prefix: str = "") -> tuple[int, list[str]]:
    """Render source_html headless and screenshot each block's selector to a PNG@2x.
    blocks: list of {name, selector}. Returns (exported_count, problems)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return 0, ["playwright not installed (pip install playwright && playwright install chromium)"]
    if not source_html.exists():
        return 0, [f"source_html not found: {source_html}"]
    out_dir.mkdir(parents=True, exist_ok=True)
    font_css = _font_css(fonts_dir)
    problems: list[str] = []
    exported = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--force-color-profile=srgb", "--font-render-hinting=none"])
        page = b.new_page(viewport={"width": 900, "height": 1400}, device_scale_factor=2)
        page.goto(source_html.resolve().as_uri(), wait_until="networkidle")
        if font_css:
            page.add_style_tag(content=font_css)
        page.wait_for_timeout(400)
        for blk in blocks:
            name, sel = blk.get("name"), blk.get("selector")
            if not name or not sel:
                problems.append(f"block missing name/selector: {blk!r}")
                continue
            loc = page.locator(sel).first
            if loc.count() == 0:
                problems.append(f"selector not found: {sel!r} (block '{name}')")
                continue
            loc.scroll_into_view_if_needed()
            page.wait_for_timeout(120)
            outp = out_dir / f"{prefix}{name}.png"
            loc.screenshot(path=str(outp))
            box = loc.bounding_box() or {"width": 0, "height": 0}
            print(f"  {outp.name:32} {int(box['width'])}x{int(box['height'])} css -> @2x")
            exported += 1
        b.close()
    return exported, problems


def run_asset(asset_dir: Path) -> int:
    try:
        import yaml
    except ImportError:
        print("pyyaml required", file=sys.stderr)
        return 1
    yml = asset_dir / "asset.yaml"
    if not yml.exists():
        print(f"no asset.yaml in {asset_dir}", file=sys.stderr)
        return 1
    meta = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    portable = meta.get("portable")
    if not portable:
        print(f"{asset_dir.name}: no `portable:` manifest in asset.yaml — nothing to export.", file=sys.stderr)
        return 1
    source_html = asset_dir / portable.get("source_html", "")
    images = portable.get("images") or []
    fonts_key = portable.get("fonts")
    fonts_dir = _FONT_SETS.get(str(fonts_key)) if fonts_key else None
    out_dir = asset_dir / "portable"
    print(f"Exporting portable pack for {asset_dir.name}  (source: {source_html.name}, {len(images)} image(s))")
    exported, problems = export_blocks(source_html, out_dir, images, fonts_dir=fonts_dir)
    copy_rel = portable.get("copy")
    if copy_rel and (asset_dir / copy_rel).exists():
        print(f"  copy: {copy_rel} (paste-ready body — pointer only, not re-exported)")
    for p in problems:
        print(f"  ! {p}", file=sys.stderr)
    if problems and exported == 0:
        return 1
    print(f"Done — {exported} image(s) in {out_dir.relative_to(asset_dir.parent.parent) if out_dir.exists() else out_dir}.")
    return 1 if problems else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Export an asset's portable pack (clean copy + block PNGs).")
    ap.add_argument("--asset", help="asset folder containing asset.yaml with a `portable:` manifest")
    ap.add_argument("--html", help="prototype fallback: source HTML file")
    ap.add_argument("--out", help="prototype fallback: output dir")
    ap.add_argument("--selectors", help="prototype fallback: JSON [[selector,name],...]")
    ap.add_argument("--fonts-dir", help="override brand fonts dir")
    args = ap.parse_args(argv)

    if args.asset:
        return run_asset(Path(args.asset))
    if args.html and args.out and args.selectors:
        blocks = [{"selector": s, "name": n} for s, n in json.loads(args.selectors)]
        fonts_dir = Path(args.fonts_dir) if args.fonts_dir else None
        exported, problems = export_blocks(Path(args.html), Path(args.out), blocks, fonts_dir=fonts_dir)
        for p in problems:
            print(f"  ! {p}", file=sys.stderr)
        return 1 if (problems and not exported) else 0
    ap.error("give --asset <dir>, or --html/--out/--selectors")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
