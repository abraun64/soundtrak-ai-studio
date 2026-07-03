#!/usr/bin/env python3
"""
Asset gallery builder — produces campaigns/<slug>/gallery.html.

Walks a campaign's assets/ directory, classifies + thumbnails every renderable
visual artifact (HTML, PNG), emits a channel-grouped gallery with:
  - filterable by Status + Channel
  - thumbnail tiles grouped by Channel with a short summary under each heading
  - click any tile → lightbox modal with full preview + source links + related docs

MD files do NOT get their own tiles. Instead they're attached as "related docs"
to the nearest visual tile in the same asset folder, accessible via the lightbox.
MDs with no visual sibling are grouped at the bottom in a "Foundation docs" list.

Usage: python build-gallery.py --campaign <slug>

Optional per-campaign override: campaigns/<slug>/gallery-config.yaml with channel
summaries customised for the tenant. Falls back to system defaults below.

Dependencies: playwright (sync). Install: pip install playwright && playwright install chromium
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
# campaigns/ is canonical in the MAIN checkout; resolve via the shared helper so the
# builder + --check also work from a .claude/worktrees/* checkout (SYS-002).
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    CAMPAIGNS = repo_paths.data_root(ROOT) / "campaigns"
except Exception:
    CAMPAIGNS = ROOT / "campaigns"
try:
    import operator_nav
except Exception:
    operator_nav = None

THUMB_W, THUMB_H = 560, 560
THUMB_W_VERTICAL, THUMB_H_VERTICAL = 360, 640

# === Status taxonomy (operator-set 2026-06-02) ===
STATUS_ORDER = ["In Production", "For Human Review", "Approved", "Archived", "Declined"]
STATUS_PATTERNS = [
    # most-specific first
    (re.compile(r"Status.*Archived|archived 20", re.I),                       "Archived"),
    (re.compile(r"Status.*Declined|Status.*Killed|Status.*Rejected", re.I),   "Declined"),
    # Approved — checkmark emoji OR explicit Status: Approved line OR yaml value
    (re.compile(r"✅\s*Approved|\*\*Status\*\*:\s*✅|Status.*✅?\s*Approved|status:\s*['\"]?approved", re.I), "Approved"),
    # For Human Review — natural language variants AND yaml value variants
    (re.compile(
        r"Brand[- ]cleared|Pass-with-Required|Pass-with-Notes"
        r"|ready[\s_]for[\s_](?:brand|operator)"   # handles underscores OR spaces
        r"|ready\s+for\s+Brand\s+verdict"
        r"|awaiting\s+(?:operator|your)\s+(?:gate|approval|review)"
        r"|Brand.*Pass-with"
        r"|For\s+Human\s+Review",
        re.I), "For Human Review"),
    (re.compile(r"Draft|in flight|in progress|cycle [0-9]|Status.*Drafted|Status.*Draft", re.I), "In Production"),
]

# Normalise a raw status string (from asset.yaml `status:` field) to gallery vocabulary
def _normalise_yaml_status(raw: str) -> str:
    r = raw.lower().strip().strip("'\"")
    # Re-opened / in-production states FIRST — a status like "re-opened (was approved)"
    # must NOT be caught by the bare "approved" substring below. Also lets the yaml
    # status declare In Production directly instead of falling through to text-detection
    # of the asset record (which may still carry historical "Approved" verdicts).
    if any(x in r for x in ["re-open", "reopen", "in production", "in progress", "in flight", "drafting", "redraft", "rework", "revising"]):
        return "In Production"
    if "approved" in r:
        return "Approved"
    if any(x in r for x in ["review", "human", "gate", "brand pass", "pass-with", "awaiting"]):
        return "For Human Review"
    if any(x in r for x in ["archived", "archive"]):
        return "Archived"
    if any(x in r for x in ["declined", "killed", "rejected"]):
        return "Declined"
    return ""   # empty = fall back to text detection

# === Channel grouping ===
# Authoritative source: per-campaign gallery-config.yaml `channels:` ordered list.
# When the config is missing, fall back to a generic skeleton — the script LOUDLY
# warns so the operator authors a config rather than shipping a misclassified gallery.
# Tenant-specific channels (Email/LinkedIn/Retail/Adviser Pack/etc.) MUST be declared
# in the per-campaign config, never in the default fallback.
CHANNEL_ORDER_FALLBACK = ["Foundation", "Misc"]
CHANNEL_ORDER = CHANNEL_ORDER_FALLBACK  # mutable; overridden from gallery-config.yaml in main()

# === Artifact types — answers the operator's "what am I reviewing?" question ===
TYPE_ORDER = ["Foundation", "Template", "Instance"]
TYPE_META = {
    "Foundation": {
        "icon": "📄",
        "label": "Reference",
        "review_prompt": "Reference material — no approval needed here. Accessible via the Edit copy button or related docs panel.",
    },
    "Template": {
        "icon": "📋",
        "label": "Approve template",
        "review_prompt": "Approve this template — all instances generated from it inherit approval automatically. Judge the shell: brand discipline, slot placement, structural integrity, and whether the system as a whole holds.",
    },
    "Instance": {
        "icon": "🖼️",
        "label": "Approve output",
        "review_prompt": "Approve this specific deliverable — full stop. This is what ships (or what gets sent to the printer / platform / client). Approve it as-is or send back with feedback.",
    },
}

def markdown_lite(text: str) -> str:
    """Lightweight markdown→HTML conversion for asset-record operator sections.

    Handles: bold, italic, code, ordered/unordered lists, paragraphs. Not full markdown.
    """
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*([^*]+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*_])\*([^*\n]+?)\*(?![*_])", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)

    lines = text.split("\n")
    out: list[str] = []
    in_ol = in_ul = False

    def close_lists():
        nonlocal in_ol, in_ul
        if in_ol:
            out.append("</ol>"); in_ol = False
        if in_ul:
            out.append("</ul>"); in_ul = False

    for line in lines:
        m_ol = re.match(r"^\s*(\d+)\.\s+(.*)", line)
        m_ul = re.match(r"^\s*[-*]\s+(.*)", line)
        if m_ol:
            if in_ul: close_lists()
            if not in_ol:
                out.append("<ol>"); in_ol = True
            out.append(f"<li>{m_ol.group(2)}</li>")
        elif m_ul:
            if in_ol: close_lists()
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{m_ul.group(1)}</li>")
        else:
            close_lists()
            if line.strip():
                out.append(f"<p>{line}</p>")
    close_lists()
    return "\n".join(out)

def render_clean_copy(copy_md: Path, out_html: Path) -> bool:
    """Render a copy markdown file to a CHROME-FREE HTML (base template) for the gallery
    preview of TEXT deliverables (emails, scripts, etc.). Text assets ship the asset-RECORD
    render (asset.html) as their preview, which carries operator-panel chrome (Edit-copy /
    For-your-action aside); screenshotting that duplicates the lightbox meta pane. Rendering
    the copy clean gives the operator the deliverable alone in the left pane."""
    render_py = Path(__file__).resolve().parent.parent / "render-html" / "render.py"
    if not render_py.exists() or not copy_md.exists():
        return False
    try:
        subprocess.run(
            [sys.executable, str(render_py), "--markdown", str(copy_md),
             "--template", "base", "--output", str(out_html)],
            check=True, capture_output=True, timeout=60,
        )
        return out_html.exists()
    except Exception as e:
        print(f"  (clean-copy render failed for {copy_md.name}: {e})", file=sys.stderr)
        return False


def extract_operator_sections(md_path: Path) -> list[dict]:
    """Parse an asset record MD for operator-facing sections (open questions, next steps, etc.).

    Returns list of {header, body_html, question_count, kind}.
    """
    if not md_path.exists():
        return []
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return []

    # Operator-facing only — explicitly NOT including "flags for brand" (internal Brand-vs-Producer discipline)
    operator_keywords = ["operator", "open question", "next step", "decision"]
    # Exclude headers that are explicitly Brand-facing
    exclusion_keywords = ["brand manager", "flags for brand", "self-qa", "brand verdict"]

    h2_pattern = re.compile(r"^##\s+(.+?)$", re.MULTILINE)
    matches = list(h2_pattern.finditer(text))
    sections: list[dict] = []

    for i, m in enumerate(matches):
        header = m.group(1).strip()
        header_lower = header.lower()
        if any(ex in header_lower for ex in exclusion_keywords):
            continue
        if not any(kw in header_lower for kw in operator_keywords):
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body_md = text[start:end].strip()
        # Strip auto-injection markers (STATUS_AUTO / COMPLIANCE_AUTO / RESONANCE_AUTO /
        # …) — render.py owns these; here they'd leak as visible text because
        # markdown_lite escapes "<". A bottom-of-record marker otherwise lands in the
        # last operator section's body.
        body_md = re.sub(r"<!--\s*\w+_AUTO\s*-->", "", body_md).strip()
        if not body_md:
            continue
        question_count = 0
        kind = "info"
        if "question" in header_lower:
            kind = "questions"
            # Count numbered list items (1. / 2. / etc) OR bullet items
            question_count = len(re.findall(r"^\s*\d+\.\s", body_md, re.MULTILINE)) or \
                             len(re.findall(r"^\s*[-*]\s", body_md, re.MULTILINE))
        elif "next" in header_lower or "action" in header_lower:
            kind = "next-steps"
        sections.append({
            "header": header,
            "body_html": markdown_lite(body_md),
            "question_count": question_count,
            "kind": kind,
        })
    return sections

def load_asset_yamls(assets_dir: Path) -> dict[Path, dict]:
    """Walk assets_dir for any asset.yaml files. Returns {asset_folder_path: parsed_yaml}.

    Falls back gracefully if pyyaml not installed (returns empty dict + prints once).
    """
    try:
        import yaml
    except ImportError:
        print("  WARN pyyaml not installed; asset.yaml metadata ignored. Install: pip install pyyaml", file=sys.stderr)
        return {}

    result: dict[Path, dict] = {}
    if not assets_dir.exists():
        return result
    for yml in assets_dir.glob("*/asset.yaml"):
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8"))
            if data:
                result[yml.parent] = data
        except Exception as e:
            print(f"  WARN failed to parse {yml}: {e}", file=sys.stderr)
    return result

def parse_plan_asset_table(plan_md_path: Path) -> dict[str, dict]:
    """Parse Plan asset list table(s). Returns {asset_id: {column_name: value, ...}}.

    Walks the markdown line-by-line. When it sees a header line starting with
    `| # | Asset |`, captures columns from that line then consumes the separator
    line + subsequent table rows until the table ends.
    """
    result: dict[str, dict] = {}
    if not plan_md_path.exists():
        return result
    try:
        lines = plan_md_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return result

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and re.match(r"\|\s*#\s*\|\s*Asset\s*\|", line, re.IGNORECASE):
            # Found header — parse columns
            cells = [c.strip() for c in line.strip("|").split("|")]
            columns = cells
            i += 1
            # Skip separator line
            if i < len(lines) and re.match(r"\|[-:\s|]+\|", lines[i].strip()):
                i += 1
            # Consume data rows until non-table line
            while i < len(lines):
                row_line = lines[i].strip()
                if not row_line.startswith("|"):
                    break
                row_cells = [c.strip() for c in row_line.strip("|").split("|")]
                if len(row_cells) == len(columns):
                    asset_id = re.sub(r"\*+", "", row_cells[0]).strip()
                    if asset_id and asset_id.lower() not in ("#", "—", "-"):
                        row = {col: re.sub(r"\*+", "", val) for col, val in zip(columns, row_cells)}
                        # Strip markdown link syntax
                        for k, v in row.items():
                            row[k] = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", v)
                        result[asset_id] = row
                i += 1
        else:
            i += 1
    return result

def classify_type(rel_path: str, file_path: Path) -> str:
    """Heuristic — does this file represent a parametric template, a concrete instance, or foundation material?"""
    lower = rel_path.lower()
    suffix = file_path.suffix.lower()

    # MDs are foundation by default (but most get folded as related docs, not standalone tiles)
    if suffix == ".md":
        return "Foundation"

    # PNGs in templates-preview/ are renders of templates → Instance
    if suffix == ".png" and "templates-preview" in lower:
        return "Instance"

    # Worked examples in cookbook examples/ subfolder → Instance
    if "/examples/" in lower or "\\examples\\" in lower:
        # treatment-b/c.html are reusable templates even though they live in examples/
        if "treatment" in lower:
            return "Template"
        return "Instance"

    # Worked instance files → Instance
    if "example-instance" in lower or "example_instance" in lower:
        return "Instance"

    # HTML files: check for parametric slot syntax to decide
    if suffix == ".html":
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            # Strong signal: any "{{SLOT}}" style placeholders
            if re.search(r"\{\{[A-Z_][A-Z0-9_]*\}\}", text):
                return "Template"
            # Files with "template" in the name and no slots = template-with-baked-sample
            if "template" in lower or "master-" in lower:
                return "Template"
        except Exception:
            pass
        # Default for HTML: Instance (it has concrete content)
        return "Instance"

    return "Instance"

# GENERIC channel summary fallbacks. These are tenant-agnostic + intentionally bland.
# Each campaign MUST author its own campaigns/<slug>/gallery-config.yaml to override
# with tenant-specific framing. If gallery-config.yaml is missing, build-gallery.py
# WARNS LOUDLY (see warn_loudly() below) — operator should not see these generic
# strings in production.
DEFAULT_CHANNEL_SUMMARIES = {
    "Email": "Email channel assets — newsletters, digests, sends, templates.",
    "LinkedIn": "LinkedIn channel assets — firm-page + personal-profile posts, anchor tiles, pull-quotes.",
    "YouTube": "YouTube channel assets — Shorts + long-form video.",
    "Audio": "Audio channel assets — podcast clips, audiograms.",
    "Adviser Pack": "Adviser-mediated channel — internal sales-enablement pack for 1:1 conversations.",
    "Foundation": "Foundation channel — source content, design rationale, runbooks. Not published artifacts; every cycle inherits from these.",
    "Misc": "Unclassified assets.",
}

# Channel routing rules (most-specific first; first match wins)
# Each rule: (regex against rel_path, primary_channel)
CHANNEL_RULES = [
    (re.compile(r"0a-email|sb-talks-weekly\.html|sb-news-monthly\.html|master-template\.html|stock-photo-facelift|examples/0[0-9]-|template-treatment", re.I), "Email"),
    (re.compile(r"T1-sb-talks-episode|T2-friday-note-pull-quote|T5-quote-card", re.I), "LinkedIn"),
    (re.compile(r"T4-youtube-shorts", re.I), "YouTube"),
    (re.compile(r"T3-sb-talks-audiogram", re.I), "Audio"),
    (re.compile(r"0c-friday-pack|pack-template|example-instance|adviser-lead-in|T6-pack-chart", re.I), "Adviser Pack"),
    (re.compile(r"0d-transcript|workflow|transcript|boeing-beef|markets-in-orbit|design-system|design\.md|templates-inventory|setup-cookbook", re.I), "Foundation"),
]

ASSET_CLASS_RULES = [
    (re.compile(r"sb-talks-weekly|sb-news-monthly|master-template", re.I), "Email template"),
    (re.compile(r"facelift|cookbook", re.I), "Cookbook"),
    (re.compile(r"examples/0[0-9]-", re.I), "Worked example"),
    (re.compile(r"template-treatment", re.I), "Reusable treatment"),
    (re.compile(r"pack-template", re.I), "Pack shell"),
    (re.compile(r"example-instance", re.I), "Worked instance"),
    (re.compile(r"adviser-lead-in", re.I), "Compliance guidance"),
    (re.compile(r"T1-sb-talks-episode", re.I), "LinkedIn anchor tile"),
    (re.compile(r"T2-friday-note-pull-quote", re.I), "Pull-quote tile"),
    (re.compile(r"T3-sb-talks-audiogram", re.I), "Audiogram"),
    (re.compile(r"T4-youtube-shorts", re.I), "Vertical Shorts"),
    (re.compile(r"T5-quote-card", re.I), "Quote card (generic)"),
    (re.compile(r"T6-pack-chart-card", re.I), "Pack chart-card"),
    (re.compile(r"transcript", re.I), "Transcript"),
    (re.compile(r"workflow|render-template", re.I), "Workflow runbook"),
    (re.compile(r"design-system|design\.md|templates-inventory", re.I), "Design rationale"),
    (re.compile(r"setup-cookbook", re.I), "Setup cookbook"),
    (re.compile(r"0[a-e]-.*\.md", re.I), "Asset record"),
]

def classify_channel(rel_path: str) -> str:
    for pat, ch in CHANNEL_RULES:
        if pat.search(rel_path):
            return ch
    return "Foundation"

def classify_class(rel_path: str) -> str:
    for pat, cls in ASSET_CLASS_RULES:
        if pat.search(rel_path):
            return cls
    return "Other"

def detect_status(asset_dir: Path, file_path: Path) -> str:
    """Look in the asset record (matching slug.md in same dir) for status text.

    Checks multiple common naming conventions for the asset record MD:
    - <numeric-prefix>-*.md (Acme Co pattern: 0a-foo.md, 17-bar.md, etc.)
    - preview.md (legacy convention)
    - asset-record.md (generic fallback)
    """
    if asset_dir.is_dir():
        candidates: list[Path] = []
        # Prefer the file matching the folder slug — disambiguates from any other
        # numeric-prefix .md files inside the asset folder (e.g. 01-welcome.md
        # inside the 13-email-infrastructure asset, which is an email file not
        # the asset record). Without this, alphabetical glob picks 01-welcome.md
        # before 13-email-infrastructure.md and reads the wrong file.
        named_record = asset_dir / f"{asset_dir.name}.md"
        if named_record.exists():
            candidates.append(named_record)
        candidates.extend(asset_dir.glob("[0-9]*-*.md"))   # Acme Co convention: 0a-foo.md / 17-bar.md
        candidates.extend(asset_dir.glob("asset.md"))      # Soundtrak / generic convention
        candidates.extend(asset_dir.glob("preview.md"))    # legacy convention
        candidates.extend(asset_dir.glob("asset-record.md"))
        for md in candidates:
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")[:5000]
                for pat, label in STATUS_PATTERNS:
                    if pat.search(text):
                        return label
            except Exception:
                pass
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")[:5000]
        for pat, label in STATUS_PATTERNS:
            if pat.search(text):
                return label
    except Exception:
        pass
    return "In Production"

def thumb_for_html(playwright_page, html_path: Path, out_path: Path, full_out_path: Path | None = None, vertical: bool = False) -> bool:
    """Render an HTML page to a thumbnail (cropped top area for tile) AND optionally
    a full-page screenshot (for lightbox review).
    """
    w, h = (THUMB_W_VERTICAL, THUMB_H_VERTICAL) if vertical else (THUMB_W, THUMB_H)
    try:
        playwright_page.set_viewport_size({"width": w * 2, "height": h * 2})
        playwright_page.goto(html_path.as_uri(), wait_until="networkidle", timeout=15000)
        # Thumb: clipped to viewport-size square/rect (top of page)
        playwright_page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": w * 2, "height": h * 2})
        # Full-page: capture entire scroll-height for the lightbox
        if full_out_path is not None:
            # Use a more email-like viewport width for full render
            playwright_page.set_viewport_size({"width": 1200, "height": 900})
            playwright_page.goto(html_path.as_uri(), wait_until="networkidle", timeout=15000)
            playwright_page.screenshot(path=str(full_out_path), full_page=True)
        return True
    except Exception as e:
        print(f"  WARN thumb-html fail {html_path.name}: {e}", file=sys.stderr)
        return False

def thumb_for_png(src_png: Path, out_path: Path) -> bool:
    try:
        import shutil
        shutil.copyfile(src_png, out_path)
        return True
    except Exception as e:
        print(f"  WARN thumb-png fail {src_png.name}: {e}", file=sys.stderr)
        return False

def thumb_for_mp4(playwright_page, mp4_path: Path, out_path: Path, vertical: bool = False, seek_seconds: float = 9.0) -> bool:
    """Render an MP4 poster frame via Playwright.

    Loads the MP4 in a minimal HTML wrapper, seeks to `seek_seconds`
    (default 9.0 — picks the final-hold frame for our 12s noise-to-signal
    videos so the poster shows the *resolved* state, not the noise floor),
    then screenshots the video element. No ffmpeg dependency.
    """
    w, h = (THUMB_W_VERTICAL, THUMB_H_VERTICAL) if vertical else (THUMB_W, THUMB_H)
    try:
        # Inline HTML wrapper — file:// URL so the video loads from disk
        wrapper_html = f"""<!doctype html><html><head><style>
html,body{{margin:0;padding:0;background:#faf9f5;width:{w*2}px;height:{h*2}px;overflow:hidden;}}
video{{display:block;width:100%;height:100%;object-fit:cover;}}
</style></head><body>
<video id=v src="{mp4_path.as_uri()}" muted playsinline preload="auto"></video>
<script>
const v=document.getElementById('v');
v.addEventListener('loadedmetadata',()=>{{
  const t=Math.min({seek_seconds}, Math.max(0, (v.duration||12)-0.1));
  v.currentTime=t;
}});
v.addEventListener('seeked',()=>{{document.title='READY';}});
</script></body></html>"""
        # Write wrapper to a temp file next to the mp4 so file:// works
        tmp_wrapper = out_path.with_suffix(".tmp.html")
        tmp_wrapper.write_text(wrapper_html, encoding="utf-8")
        playwright_page.set_viewport_size({"width": w * 2, "height": h * 2})
        playwright_page.goto(tmp_wrapper.as_uri(), wait_until="load", timeout=15000)
        # Wait for the seeked event to fire (title becomes "READY")
        playwright_page.wait_for_function("document.title === 'READY'", timeout=10000)
        playwright_page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": w * 2, "height": h * 2})
        try:
            tmp_wrapper.unlink()
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"  WARN thumb-mp4 fail {mp4_path.name}: {e}", file=sys.stderr)
        return False

# Non-renderable binary deliverables — can't be screenshotted, so they get a
# format-card poster + a download action. They still flow through the ship
# filter (only ship:true / default-show files tile), so a stray foundation PDF
# won't surface. Added 2026-06-15 after the pitch deck's .pptx output was being
# silently dropped (gallery only thumbnailed .html/.png/.mp4).
DOC_DELIVERABLE_EXTS = {".pptx", ".key", ".pdf", ".docx", ".xlsx", ".csv"}
DOC_FORMAT_LABELS = {
    ".pptx": ("PPTX", "PowerPoint deck"),
    ".key":  ("KEY", "Keynote deck"),
    ".pdf":  ("PDF", "PDF document"),
    ".docx": ("DOCX", "Word document"),
    ".xlsx": ("XLSX", "Excel spreadsheet"),
    ".csv":  ("CSV", "Data table"),
}

def thumb_for_doc(playwright_page, doc_path: Path, out_path: Path, title: str, ext: str) -> bool:
    """Render a format-card poster for a non-renderable binary deliverable.

    .pptx/.pdf/.docx/.xlsx can't be screenshotted directly, so we render a
    clean system-palette card showing the format badge + title + a
    'download to open' hint. The tile carries a download action so the
    operator gets the real file. This guarantees a plan-declared ship output
    is never invisible in the gallery just because it isn't web-renderable.
    """
    w, h = THUMB_W, THUMB_H
    badge, kind = DOC_FORMAT_LABELS.get(ext.lower(), (ext.lstrip(".").upper() or "FILE", "Document"))
    safe_title = (title or doc_path.name).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    try:
        card_html = f"""<!doctype html><html><head><style>
html,body{{margin:0;padding:0;width:{w*2}px;height:{h*2}px;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,sans-serif;
  background:#faf9f5;display:flex;align-items:center;justify-content:center;}}
.card{{text-align:center;padding:0 80px;}}
.doc{{width:220px;height:286px;margin:0 auto 48px;background:#fff;
  border:3px solid #111110;border-radius:10px;position:relative;
  box-shadow:0 24px 60px rgba(17,17,16,0.20);
  display:flex;align-items:flex-end;justify-content:center;}}
.doc .fold{{position:absolute;top:-3px;right:-3px;width:64px;height:64px;
  background:#faf9f5;border-left:3px solid #111110;border-bottom:3px solid #111110;
  border-bottom-left-radius:10px;border-top-right-radius:10px;}}
.doc .badge{{margin-bottom:44px;font-size:48px;font-weight:800;letter-spacing:0.04em;color:#e63c3c;}}
.kind{{font-size:34px;color:#111110;font-weight:700;margin-bottom:18px;}}
.title{{font-size:26px;color:#57534e;line-height:1.4;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}}
.hint{{margin-top:36px;font-size:22px;color:#a8a29e;letter-spacing:0.08em;text-transform:uppercase;}}
</style></head><body>
<div class="card">
  <div class="doc"><div class="fold"></div><div class="badge">{badge}</div></div>
  <div class="kind">{kind}</div>
  <div class="title">{safe_title}</div>
  <div class="hint">Download to open</div>
</div></body></html>"""
        tmp = out_path.with_suffix(".card.html")
        tmp.write_text(card_html, encoding="utf-8")
        playwright_page.set_viewport_size({"width": w * 2, "height": h * 2})
        playwright_page.goto(tmp.as_uri(), wait_until="load", timeout=15000)
        playwright_page.screenshot(path=str(out_path), clip={"x": 0, "y": 0, "width": w * 2, "height": h * 2})
        try:
            tmp.unlink()
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"  WARN thumb-doc fail {doc_path.name}: {e}", file=sys.stderr)
        return False

def humanize_slug(slug: str) -> str:
    return " ".join(w.capitalize() for w in re.split(r"[-_]", slug) if w)

def build_breadcrumb(campaign_slug: str) -> str:
    """Match the breadcrumb pattern used by render-html templates."""
    campaign_label = humanize_slug(campaign_slug)
    return (
        f'<nav class="breadcrumb" aria-label="Breadcrumb">'
        f'<a class="crumb crumb-link" href="../index.html">🏠 All Campaigns</a>'
        f'<span class="crumb-sep">›</span>'
        f'<a class="crumb crumb-link" href="dashboard.html">{campaign_label}</a>'
        f'<span class="crumb-sep">›</span>'
        f'<span class="crumb crumb-current">Asset Gallery</span>'
        f'</nav>'
    )

def load_system_css() -> str:
    """Inline the render-html system.css so the gallery matches every other review page."""
    css_path = ROOT / ".claude/skills/render-html/templates/styles/system.css"
    try:
        return css_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  WARN system.css load fail: {e}", file=sys.stderr)
        return ""

def _resolve_copy_file(copy_file_val: str, asset_dir: Path, campaign_dir: Path) -> dict | None:
    """Resolve a copy_file declaration from asset.yaml into a gallery-ready dict.

    copy_file in asset.yaml can be:
      - a bare filename:  "copy.md"
      - a relative path:  "step-02-variants/variants.csv"

    Auto-detect (2026-06-04): if copy_file_val is empty BUT a sibling copy.md
    exists in the asset folder, treat as if the asset declared `copy_file: copy.md`.
    Operators don't need to remember to declare the convention; the system honours
    it by default.

    Returns {path: <relative-from-campaign-root>, label: <human label>, format: <ext>}
    or None if not declared and no sibling copy.md found.
    """
    if not copy_file_val:
        # Auto-detect sibling copy.md
        sibling_copy = asset_dir / "copy.md"
        if sibling_copy.exists():
            copy_file_val = "copy.md"
        else:
            return None
    full_path = asset_dir / copy_file_val
    if not full_path.exists():
        return None
    try:
        rel = full_path.relative_to(campaign_dir).as_posix()
    except ValueError:
        return None
    ext = full_path.suffix.lower().lstrip(".")
    labels = {
        "md":   "Edit copy (.md)",
        "csv":  "Edit variants (.csv)",
        "pptx": "Open deck (.pptx)",
        "docx": "Edit document (.docx)",
        "xlsx": "Edit spreadsheet (.xlsx)",
    }
    return {"path": rel, "label": labels.get(ext, f"Edit copy (.{ext})"), "format": ext,
            "open_uri": _gallery_open_uri(full_path)}


def _gallery_open_uri(p: Path) -> str:
    """gallery-open:<encoded-abs-path> — custom protocol registered via
    .claude/skills/asset-gallery/protocol/setup-protocol.ps1 (one-time, auto-detects the
    install path). Handler opens folders in File Explorer and files in VS Code/Notepad,
    refusing paths outside the system root. See protocol/setup-cookbook.md."""
    from urllib.parse import quote
    return "gallery-open:" + quote(str(p.resolve()).replace("\\", "/"))


def build_html(campaign_slug: str, tiles: list[dict], foundation_docs: list[dict],
               channel_summaries: dict[str, str], campaign_dna: dict, out_path: Path) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    n_total = len(tiles)
    by_status = defaultdict(int)
    for t in tiles:
        by_status[t["status"]] += 1
    by_channel_count = defaultdict(int)
    for t in tiles:
        by_channel_count[t["channel"]] += 1

    all_statuses = [s for s in STATUS_ORDER if s in {t["status"] for t in tiles}]
    all_channels = [c for c in CHANNEL_ORDER if c in {t["channel"] for t in tiles} or c == "Foundation" and foundation_docs]

    tiles_json = json.dumps(tiles, ensure_ascii=False)
    foundation_json = json.dumps(foundation_docs, ensure_ascii=False)

    counts_line = " · ".join(f"{n} {s}" for s, n in by_status.items())
    system_css = load_system_css()
    breadcrumb = build_breadcrumb(campaign_slug)
    # Top-right pill nav (Help & guides + Library) — identical to the render-html surfaces.
    library_nav = operator_nav.top_nav_pills(out_path.parents[2], "../../") if operator_nav else ""
    # Approval status string (replaces the phase-name pill): green tick when every
    # reviewable asset is Approved, else "In progress". Shown left of the Task list.
    pending = by_status.get("For Human Review", 0) + by_status.get("In Production", 0)
    approved_all = n_total > 0 and pending == 0
    status_badge = ('<span class="gallery-status gallery-status--ok">✅ Approved</span>'
                    if approved_all else
                    '<span class="gallery-status gallery-status--prog">🔄 In progress</span>')
    asset_numbers = (f"{n_total} visual assets" if approved_all
                     else f"{n_total} visual assets · {counts_line}")
    status_line_html = f'{status_badge}<span class="gallery-status-meta">{asset_numbers}</span>'

    # Campaign-strategy banner — the Big Idea / Key Message reminder, shown ONCE at the
    # top of the gallery (before Foundations), not repeated in every lightbox.
    _dna = campaign_dna or {}
    if _dna.get("big_idea") or _dna.get("key_message"):
        _concept_a = (f' · <a href="{_dna["concept_link"]}" target="_blank" style="color:var(--accent);text-decoration:none;">Full concept →</a>'
                      if _dna.get("concept_link") else "")
        _bi = (f'<p style="margin:0 0 6px;font-size:14px;line-height:1.5;"><strong>💡 Big idea:</strong> {_dna["big_idea"]}</p>'
               if _dna.get("big_idea") else "")
        _km = (f'<p style="margin:0;font-size:13px;line-height:1.5;color:var(--text-muted);"><strong style="color:var(--text);">Key message:</strong> {_dna["key_message"]}</p>'
               if _dna.get("key_message") else "")
        _extra = []
        if _dna.get("radio_pitch"):
            _extra.append(f'<p style="margin:6px 0 0;font-style:italic;color:var(--text-muted);"><strong style="font-style:normal;color:var(--text);">15-sec pitch:</strong> {_dna["radio_pitch"]}</p>')
        if _dna.get("kpi_floor"):
            _extra.append(f'<p style="margin:6px 0 0;color:var(--text-muted);"><strong style="color:var(--text);">KPI floor:</strong> {_dna["kpi_floor"]}</p>')
        _extra_html = (f'<details style="margin-top:6px;"><summary style="font-size:11px;color:var(--text-subtle);cursor:pointer;">More — pitch + KPI floor</summary>{"".join(_extra)}</details>'
                       if _extra else "")
        strategy_banner_html = f"""<div class="strategy-banner" style="background:var(--surface);border:1px solid var(--border);border-left:3px solid #6366f1;border-radius:6px;margin:14px 24px 0;padding:12px 16px;">
  <div style="font-size:10px;letter-spacing:0.08em;text-transform:uppercase;color:#4f46e5;font-weight:700;margin-bottom:6px;">🧭 Campaign strategy — the reminder{_concept_a}</div>
  {_bi}{_km}{_extra_html}
</div>"""
    else:
        strategy_banner_html = ""

    html = f"""<!DOCTYPE html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<title>{humanize_slug(campaign_slug)} — Asset Gallery</title>
<style>
{system_css}

/* === Gallery-specific additions — neutral system palette, NOT tenant-branded === */
.gallery-meta {{
  font-size: 12px; color: var(--text-muted); margin-top: 6px;
}}
/* Current-phase slug — matches the dashboard/index pill vocabulary (those are
   .content-scoped, so re-declare here for the gallery body). */
.gallery-summary__top {{
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap; margin-bottom: 6px;
}}
.gallery-status-wrap {{ display: inline-flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }}
.gallery-status {{
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 700;
}}
.gallery-status--ok   {{ color: var(--success); }}
.gallery-status--prog {{ color: var(--accent); }}
.gallery-status-meta {{ font-size: 12px; color: var(--text-muted); }}
.gallery-tasks-btn {{
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 6px;
  background: var(--accent); color: var(--surface); text-decoration: none;
  border: 1px solid var(--accent); white-space: nowrap;
}}
.gallery-tasks-btn:hover {{ background: #1d4ed8; }}
.filter-bar {{
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 14px 24px; position: sticky; top: 0; z-index: 50;
  display: flex; flex-wrap: wrap; gap: 20px; align-items: center;
}}
.filter-group {{
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-subtle);
}}
.filter-group label {{
  display: inline-flex; align-items: center; gap: 4px;
  cursor: pointer; padding: 3px 9px; border-radius: 12px;
  border: 1px solid var(--border); font-size: 11px; letter-spacing: 0.02em;
  text-transform: none; color: var(--text); font-weight: 500;
  background: var(--bg); user-select: none;
}}
.filter-group input {{ display: none; }}
.filter-group input:checked + span {{ background: var(--accent); color: var(--surface); padding: 1px 7px; border-radius: 10px; }}

.channel-section {{ margin-top: 28px; }}
.channel-head {{
  border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 16px;
}}
.channel-head h2 {{
  font-size: 18px; color: var(--text); margin: 0; font-weight: 600;
  display: flex; align-items: baseline; gap: 10px;
}}
.channel-head .count {{ font-size: 12px; color: var(--text-subtle); font-weight: 400; }}
.channel-head .summary {{
  margin: 6px 0 0; font-size: 13px; color: var(--text-muted);
  max-width: 920px; line-height: 1.55;
}}

.grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}}
.tile {{
  background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
  overflow: hidden; cursor: pointer; transition: transform 0.12s, box-shadow 0.12s;
  display: flex; flex-direction: column;
}}
.tile:hover {{ transform: translateY(-2px); box-shadow: 0 6px 18px rgba(17,24,39,0.08); border-color: var(--border-strong); }}
.tile-img {{
  background: var(--bg); aspect-ratio: 1 / 1;
  overflow: hidden; display: flex; align-items: center; justify-content: center;
}}
.tile-img.vertical {{ aspect-ratio: 9 / 16; }}
.tile-img img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }}
.tile-meta {{ padding: 10px 12px; }}
.tile-name {{ font-size: 13px; font-weight: 600; color: var(--text); margin: 0 0 3px;
              line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
              overflow: hidden; }}
.tile-subtitle {{ font-size: 11px; color: var(--text-subtle); margin: 0 0 4px; line-height: 1.35;
                  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
                  overflow: hidden; font-style: italic; }}
.tile-class {{ font-size: 10px; color: var(--text-subtle); letter-spacing: 0.06em; text-transform: uppercase; }}
.tile-badges {{ display: flex; gap: 4px; margin-top: 8px; flex-wrap: wrap; align-items: center; }}
.badge {{
  font-size: 9px; padding: 2px 7px; border-radius: 10px;
  letter-spacing: 0.04em; text-transform: uppercase; font-weight: 600;
}}
/* Status colours — conventional UI semantics, not tenant brand */
.badge-status-Approved          {{ background: #dcfce7; color: #166534; }}
.badge-status-For-Human-Review  {{ background: #fee2e2; color: #991b1b; }}
.badge-status-In-Production     {{ background: var(--accent-soft); color: var(--accent); }}
.badge-status-Archived          {{ background: var(--bg); color: var(--text-muted); border: 1px solid var(--border); }}
.badge-status-Declined          {{ background: var(--border); color: var(--text-muted); }}
.badge-docs {{
  background: var(--bg); color: var(--text-muted); border: 1px solid var(--border);
  font-size: 9px; font-weight: 500;
}}
.badge-questions {{
  background: #fef3c7; color: #92400e; border: 1px solid #fde68a;
  font-size: 9px; font-weight: 600;
}}
.badge-review-shape {{
  background: #f0f4ff; color: #3b4db8; border: 1px solid #c7d0f8;
  font-size: 9px; font-weight: 500; max-width: 160px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}}

/* Operator-action sections in lightbox */
.lb-operator-block {{
  width: 100%; margin-bottom: 10px; padding: 12px 14px;
  background: #fef9e7; border-left: 3px solid #f59e0b; border-radius: 0 4px 4px 0;
  font-size: 12px; line-height: 1.55;
}}
.lb-operator-block.kind-next-steps {{
  background: var(--accent-soft); border-left-color: var(--accent);
}}
.lb-operator-block.kind-info {{
  background: var(--bg); border-left-color: var(--text-muted);
}}
.lb-operator-block.kind-strategy {{
  background: var(--surface); border-left-color: #6366f1;
}}
.lb-operator-block.kind-strategy .lb-op-head {{ color: #4f46e5; }}
.lb-operator-block .lb-op-head {{
  font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
  font-weight: 700; margin-bottom: 6px; color: #92400e;
}}
.lb-operator-block.kind-next-steps .lb-op-head {{ color: var(--accent); }}
.lb-operator-block.kind-info .lb-op-head {{ color: var(--text-muted); }}
.lb-operator-block p {{ margin: 4px 0; }}
.lb-operator-block ol, .lb-operator-block ul {{ margin: 4px 0 4px 18px; padding: 0; }}
.lb-operator-block li {{ margin: 4px 0; }}
.lb-operator-block strong {{ color: var(--text); }}
.lb-operator-block code {{ font-size: 11px; background: rgba(0,0,0,0.06); padding: 1px 4px; border-radius: 3px; }}

/* Foundation section — grouped by asset, with full context */
.foundation-asset-group {{ margin: 12px 0 24px; padding: 14px 16px;
                            background: var(--surface); border: 1px solid var(--border);
                            border-radius: 6px; }}
.foundation-asset-head {{ display: flex; align-items: baseline; gap: 10px;
                          margin-bottom: 8px; padding-bottom: 8px;
                          border-bottom: 1px solid var(--border); }}
.foundation-asset-head .asset-id {{ font-family: 'SF Mono', Menlo, monospace;
                                     font-size: 11px; padding: 1px 6px;
                                     background: var(--accent-soft); color: var(--accent);
                                     border-radius: 3px; font-weight: 700; }}
.foundation-asset-head .asset-name {{ font-size: 14px; font-weight: 600; color: var(--text); }}
.foundation-asset-summary {{ font-size: 12px; color: var(--text-muted);
                              line-height: 1.55; margin-bottom: 10px; }}
.foundation-doc {{ padding: 10px 12px; margin: 6px 0;
                    background: var(--bg); border-left: 3px solid var(--border);
                    border-radius: 0 4px 4px 0; }}
.foundation-doc.role-primary_doc {{ border-left-color: #f59e0b; background: #fffbeb; }}
.foundation-doc.role-asset_record {{ opacity: 0.7; }}
.foundation-doc-head {{ display: flex; align-items: center; gap: 8px;
                         margin-bottom: 4px; flex-wrap: wrap; }}
.foundation-doc-head a {{ font-size: 13px; font-weight: 500; color: var(--text);
                          text-decoration: none; flex: 1; min-width: 200px; }}
.foundation-doc-head a:hover {{ color: var(--accent); }}
.foundation-doc-head .doc-name {{ font-size: 10px; color: var(--text-subtle);
                                   font-family: 'SF Mono', Menlo, monospace; }}
.foundation-doc-head .role-badge {{ font-size: 9px; padding: 2px 7px;
                                     border-radius: 10px; letter-spacing: 0.04em;
                                     text-transform: uppercase; font-weight: 600; }}
.role-badge.role-primary_doc {{ background: #fef3c7; color: #92400e; }}
.role-badge.role-asset_record {{ background: var(--bg); color: var(--text-subtle); border: 1px solid var(--border); }}
.role-badge.role-rationale,
.role-badge.role-how_to_use,
.role-badge.role-doc_index,
.role-badge.role-design_doc,
.role-badge.role-render_pipeline,
.role-badge.role-catalog {{ background: var(--accent-soft); color: var(--accent); }}
.foundation-doc-review {{ font-size: 12px; color: var(--text-muted);
                           line-height: 1.5; margin-top: 4px; }}

/* lightbox */
.lightbox {{
  position: fixed; inset: 0; background: rgba(17,24,39,0.85);
  display: none; align-items: center; justify-content: center;
  z-index: 100; padding: 40px;
}}
.lightbox.open {{ display: flex; }}
.lightbox-inner {{
  background: var(--surface); border-radius: 8px; max-width: 1500px;
  width: 100%; height: 94vh; display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}}
.lightbox-header {{
  padding: 14px 22px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  background: var(--surface);
}}
.lightbox-header h2 {{ margin: 0; font-size: 16px; font-weight: 600; color: var(--text); }}
.lightbox-header .actions {{ display: flex; gap: 6px; align-items: center; }}
.lightbox-header a, .lightbox-close {{
  font-size: 12px; padding: 6px 12px; border-radius: 4px;
  text-decoration: none; color: var(--surface); background: var(--accent);
  border: none; cursor: pointer; font-family: inherit;
}}
.lightbox-close {{ background: var(--text-muted); }}

/* Two-column body: asset (left, ~62%) + metadata (right, ~38%) */
.lightbox-body {{
  display: grid; grid-template-columns: 62% 38%; min-height: 0; overflow: hidden;
}}
.lb-asset-pane {{
  overflow: auto; padding: 24px; background: var(--bg); text-align: center;
  border-right: 1px solid var(--border);
}}
.lb-asset-pane img {{
  max-width: 100%; box-shadow: 0 6px 20px rgba(17,24,39,0.12);
  display: inline-block;
}}
.lb-meta-pane {{
  overflow: auto; padding: 18px 22px; background: var(--surface);
  font-size: 12px; line-height: 1.55;
}}

.lb-footer-meta {{
  margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border);
  font-size: 11px; color: var(--text-muted);
  display: flex; flex-direction: column; gap: 4px;
}}
.lb-footer-meta strong {{ color: var(--text); font-weight: 600; }}

.lightbox-related {{
  margin-top: 12px; padding: 10px 12px; background: var(--bg);
  border-radius: 4px; border: 1px solid var(--border); font-size: 12px;
}}
.lightbox-related strong {{ color: var(--text-subtle); letter-spacing: 0.08em; text-transform: uppercase; font-size: 10px; font-weight: 600; }}
.lightbox-related a {{ display: inline-block; margin: 4px 6px 0 0; padding: 3px 9px; background: var(--surface); border: 1px solid var(--border); border-radius: 4px; text-decoration: none; color: var(--text); font-size: 11px; }}
.lightbox-related a:hover {{ border-color: var(--accent); }}

/* Responsive: collapse to single column on narrow screens */
@media (max-width: 1100px) {{
  .lightbox-body {{ grid-template-columns: 1fr; grid-template-rows: 1fr 1fr; }}
  .lb-asset-pane {{ border-right: none; border-bottom: 1px solid var(--border); }}
}}

/* nav arrows */
.nav-arrow {{
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(255,255,255,0.92); color: var(--text);
  border: 1px solid var(--border); font-size: 22px;
  width: 48px; height: 48px; border-radius: 50%; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-family: inherit; padding: 0; line-height: 1;
  transition: background 0.12s, transform 0.12s; z-index: 102; user-select: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}}
.nav-arrow:hover {{ background: var(--surface); transform: translateY(-50%) scale(1.05); }}
.nav-arrow.prev {{ left: 22px; }}
.nav-arrow.next {{ right: 22px; }}
.nav-hint {{ font-size: 10px; color: var(--text-subtle); margin-left: 10px; letter-spacing: 0.04em; }}

main.page-main {{ padding: 24px 24px 64px; }}

/* Type subsections within each channel */
.type-subsection {{ margin: 14px 0 24px; }}
.type-head {{
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 10px; padding: 6px 10px;
  background: var(--bg); border-left: 3px solid var(--accent); border-radius: 0 4px 4px 0;
}}
.type-head strong {{ font-size: 12px; color: var(--text); letter-spacing: 0.04em; text-transform: uppercase; }}
.type-head .type-icon {{ font-size: 14px; }}
.type-head .type-count {{ font-size: 11px; color: var(--text-subtle); }}
.type-head .type-prompt {{
  font-size: 11px; color: var(--text-muted); font-style: italic;
  margin-left: 6px; flex: 1; min-width: 200px;
}}

/* Tile type badge — small icon top-right corner of thumbnail */
.tile-img {{ position: relative; }}
.tile-type-badge {{
  position: absolute; top: 6px; right: 6px;
  background: rgba(255,255,255,0.95); border: 1px solid var(--border);
  border-radius: 4px; padding: 2px 6px; font-size: 12px;
  line-height: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}

/* Subtle visual distinction by type */
.tile-type-Template .tile-img {{ background: repeating-linear-gradient(45deg, var(--bg), var(--bg) 6px, var(--surface) 6px, var(--surface) 12px); }}
.tile-type-Instance .tile-img {{ background: var(--bg); }}

/* Video tiles — play-button overlay on the poster frame */
.tile-video-overlay {{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 56px; height: 56px; border-radius: 50%;
  background: rgba(17,17,17,0.75); border: 2px solid rgba(255,255,255,0.95);
  display: flex; align-items: center; justify-content: center;
  pointer-events: none; transition: transform 0.12s;
}}
.tile-video-overlay::before {{
  content: ''; display: block;
  width: 0; height: 0; margin-left: 4px;
  border-left: 18px solid rgba(255,255,255,0.95);
  border-top: 12px solid transparent;
  border-bottom: 12px solid transparent;
}}
.tile:hover .tile-video-overlay {{ transform: translate(-50%, -50%) scale(1.08); }}
.tile-duration-badge {{
  position: absolute; bottom: 6px; right: 6px;
  background: rgba(17,17,17,0.78); color: #fff;
  border-radius: 3px; padding: 2px 6px; font-size: 11px; font-weight: 500;
  letter-spacing: 0.02em;
}}

/* Foundation section header — bigger marker since it sits at top */
.channel-section.foundation-section .channel-head {{ border-bottom-width: 2px; }}
</style>
</head>
<body class="template-gallery">
  <header class="page-header">
    <div class="page-header__inner">
      {breadcrumb}
      <div class="page-header__right">
        {library_nav}
        <button type="button" class="refresh-btn" onclick="location.reload()" title="Refresh this page" aria-label="Refresh">&#10227;</button>
        <span class="page-header__template" aria-hidden="true">gallery</span>
      </div>
    </div>
  </header>

  <div class="gallery-summary" style="background:var(--surface); border-bottom:1px solid var(--border); padding:14px 24px;">
    <div class="gallery-summary__top">
      <div class="gallery-status-wrap">{status_line_html}</div>
      <a class="gallery-tasks-btn" href="../tasks.html">📋 Task list</a>
    </div>
    <div style="font-size:11px; color:var(--text-subtle);">Last refreshed {now}</div>
  </div>

<div class="filter-bar">
  <div class="filter-group">
    <strong>Status</strong>
    {''.join(f'<label><input type="checkbox" class="f-status" value="{s}" checked><span>{s}</span></label>' for s in all_statuses)}
  </div>
  <div class="filter-group">
    <strong>Channel</strong>
    {''.join(f'<label><input type="checkbox" class="f-channel" value="{c}" checked><span>{c}</span></label>' for c in all_channels)}
  </div>
</div>

{strategy_banner_html}

<main id="gallery" class="page-main"></main>

<div class="lightbox" id="lightbox">
  <button class="nav-arrow prev" onclick="event.stopPropagation(); navigateLightbox(-1);" aria-label="Previous">‹</button>
  <div class="lightbox-inner" onclick="event.stopPropagation()">
    <div class="lightbox-header">
      <h2 id="lb-title">—</h2>
      <div class="actions">
        <a id="lb-source" href="#" target="_blank">View in full</a>
        <a id="lb-copy" href="#" target="_blank" style="display:none;">✏️ Edit copy</a>
        <a id="lb-production" href="#" download style="display:none;">📥 Download</a>
        <a id="lb-folder" href="#" target="_blank" title="Open asset folder in file browser">📁 Open folder</a>
        <button class="lightbox-close" onclick="closeLightbox()">Close (Esc)</button>
        <span class="nav-hint">← / → to navigate</span>
      </div>
    </div>
    <div class="lightbox-body">
      <div class="lb-asset-pane">
        <img id="lb-img" src="" alt="">
        <video id="lb-video" controls loop playsinline style="display:none; width:100%; height:auto; max-height:85vh; background:#000;"></video>
      </div>
      <div class="lb-meta-pane" id="lb-meta">—</div>
    </div>
  </div>
  <button class="nav-arrow next" onclick="event.stopPropagation(); navigateLightbox(1);" aria-label="Next">›</button>
</div>

<script>
const TILES = {tiles_json};
const FOUNDATION = {foundation_json};
const CHANNEL_SUMMARIES = {json.dumps(channel_summaries, ensure_ascii=False)};
const CHANNEL_ORDER = {json.dumps(all_channels)};
const TYPE_ORDER = {json.dumps(TYPE_ORDER)};
const TYPE_META = {json.dumps(TYPE_META, ensure_ascii=False)};
const CAMPAIGN_DNA = {json.dumps(campaign_dna, ensure_ascii=False)};
let lightboxIdx = -1;
let visibleIndices = [];  // refreshed by render() — global indices into TILES that pass the active filters

function render() {{
  const statuses = [...document.querySelectorAll('.f-status:checked')].map(e => e.value);
  const channels = [...document.querySelectorAll('.f-channel:checked')].map(e => e.value);

  const filteredTiles = TILES.filter(t => statuses.includes(t.status) && channels.includes(t.channel));
  visibleIndices = filteredTiles.map(t => TILES.indexOf(t));
  const filteredFoundation = channels.includes('Foundation') ? FOUNDATION : [];

  const byChannel = {{}};
  filteredTiles.forEach(t => {{
    byChannel[t.channel] = byChannel[t.channel] || [];
    byChannel[t.channel].push(t);
  }});

  let html = '';
  CHANNEL_ORDER.forEach(ch => {{
    const items = byChannel[ch] || [];
    const isFoundation = ch === 'Foundation';
    const foundationItems = isFoundation ? filteredFoundation : [];

    if (items.length === 0 && foundationItems.length === 0) return;

    html += `<section class="channel-section ${{isFoundation ? 'foundation-section' : ''}}">
      <div class="channel-head">
        <h2>${{ch}} <span class="count">${{items.length + foundationItems.length}} ${{items.length + foundationItems.length === 1 ? 'asset' : 'assets'}}</span></h2>
        <p class="summary">${{CHANNEL_SUMMARIES[ch] || ''}}</p>
      </div>`;

    if (items.length > 0) {{
      // Subsection by Type within channel
      const byType = {{}};
      items.forEach(t => {{
        const ty = t.type || 'Instance';
        byType[ty] = byType[ty] || [];
        byType[ty].push(t);
      }});

      TYPE_ORDER.forEach(ty => {{
        if (ty === 'Foundation') return;  // Foundation MDs render in their own dedicated section, not in channel subsections
        const list = byType[ty];
        if (!list || list.length === 0) return;
        const meta = TYPE_META[ty];
        html += `<div class="type-subsection">
          <div class="type-head">
            <span class="type-icon">${{meta.icon}}</span>
            <strong>${{meta.label}}s</strong>
            <span class="type-count">${{list.length}}</span>
            <span class="type-prompt">${{meta.review_prompt.split('.')[0]}}.</span>
          </div>`;
        html += '<div class="grid">';
        list.forEach((t) => {{
          const globalIdx = TILES.indexOf(t);
          const vClass = t.vertical ? 'vertical' : '';
          const statusKey = t.status.replace(/\\s/g, '-');
          const docsBadge = t.related_docs && t.related_docs.length > 0 ? `<span class="badge badge-docs">${{t.related_docs.length}} doc${{t.related_docs.length === 1 ? '' : 's'}}</span>` : '';
          const questionsBadge = t.open_question_count > 0 ? `<span class="badge badge-questions">🟠 ${{t.open_question_count}} question${{t.open_question_count === 1 ? '' : 's'}}</span>` : '';
          const reviewShapeRaw = (t.plan_row && t.plan_row["Review shape"]) || '';
          const reviewShapeBadge = reviewShapeRaw ? (() => {{
            const icon = reviewShapeRaw.startsWith('template') ? '📋' :
                         reviewShapeRaw.startsWith('variant-comp') ? '🎨' : '🖼';
            // Short label: strip bracket details for badge display
            const short = reviewShapeRaw.replace(/\\s*\\[.*\\]/, '').trim();
            return `<span class="badge badge-review-shape" title="${{reviewShapeRaw}}">${{icon}} ${{short}}</span>`;
          }})() : '';
          const typeClass = `tile-type-${{ty}}`;
          const videoOverlay = t.is_video ? '<span class="tile-video-overlay" aria-hidden="true"></span><span class="tile-duration-badge">▶ video</span>' : '';
          html += `
            <div class="tile ${{typeClass}}" onclick="openLightbox(${{globalIdx}})">
              <div class="tile-img ${{vClass}}">
                <img src="${{t.thumb}}" alt="${{t.title || t.asset_name || t.name}}" loading="lazy">
                <span class="tile-type-badge" title="${{meta.label}}">${{meta.icon}}</span>
                ${{videoOverlay}}
              </div>
              <div class="tile-meta">
                <div class="tile-name">${{t.asset_name || t.title || t.name}}</div>
                <div class="tile-subtitle">${{t.asset_name && t.title ? t.title : (t.asset_name ? t.name : '')}}</div>
                <div class="tile-class">${{meta.label}}</div>
                <div class="tile-badges">
                  <span class="badge badge-status-${{statusKey}}">${{t.status}}</span>
                  ${{reviewShapeBadge}}
                  ${{questionsBadge}}
                  ${{docsBadge}}
                </div>
              </div>
            </div>`;
        }});
        html += '</div></div>';
      }});
    }}

    if (foundationItems.length > 0) {{
      // Group foundation items by asset_id (so all 0d MDs cluster under one asset header)
      const byAsset = {{}};
      foundationItems.forEach(f => {{
        const aid = f.asset_id || 'misc';
        byAsset[aid] = byAsset[aid] || {{ items: [], asset_name: f.asset_name, asset_summary: f.asset_summary }};
        byAsset[aid].items.push(f);
      }});
      Object.entries(byAsset).forEach(([aid, group]) => {{
        // Sort by role_priority (primary docs first, asset_records last)
        group.items.sort((a, b) => (a.role_priority || 5) - (b.role_priority || 5));
        html += `<div class="foundation-asset-group">
          <div class="foundation-asset-head">
            <span class="asset-id">${{aid}}</span>
            <span class="asset-name">${{group.asset_name || 'Unattributed foundation docs'}}</span>
          </div>
          ${{group.asset_summary ? `<div class="foundation-asset-summary">${{group.asset_summary}}</div>` : ''}}`;
        group.items.forEach(f => {{
          const roleLabel = (f.role || 'reference').replace(/_/g, ' ');
          html += `<div class="foundation-doc role-${{f.role || 'reference'}}">
            <div class="foundation-doc-head">
              <a href="${{f.source}}" target="_blank">${{f.title || f.name}}</a>
              <span class="role-badge role-${{f.role || 'reference'}}">${{roleLabel}}</span>
              <span class="doc-name">${{f.name}}</span>
            </div>
            ${{f.review ? `<div class="foundation-doc-review">${{f.review}}</div>` : ''}}
          </div>`;
        }});
        html += '</div>';
      }});
    }}

    html += '</section>';
  }});

  document.getElementById('gallery').innerHTML = html || '<p style="color:var(--slate6); padding:24px;">No assets match current filters.</p>';
}}

function openLightbox(idx) {{
  lightboxIdx = idx;
  const t = TILES[idx];
  const lbImg = document.getElementById('lb-img');
  const lbVid = document.getElementById('lb-video');
  if (t.is_video) {{
    lbImg.style.display = 'none';
    lbImg.src = '';
    lbVid.style.display = '';
    lbVid.src = t.video_src;
    lbVid.muted = false;
    lbVid.load();
    lbVid.play().catch(() => {{ /* autoplay blocked — user can click play */ }});
  }} else {{
    try {{ lbVid.pause(); }} catch (e) {{}}
    lbVid.removeAttribute('src');
    lbVid.load();
    lbVid.style.display = 'none';
    lbImg.style.display = '';
    lbImg.src = t.full_render || t.thumb;
  }}
  // "View in full" — use view_source override if set (e.g. preview.html thumbnails
  // but "View in full" opens the actual production HTML)
  document.getElementById('lb-source').href = (t.view_source || t.source) || '#';
  document.getElementById('lb-title').textContent = t.title || t.name;

  // Copy file button — header, shown only when asset declares copy_file
  const copyEl = document.getElementById('lb-copy');
  if (t.copy_file) {{
    const copyIcon = t.copy_file.format === 'pptx' ? '📊' :
                     t.copy_file.format === 'docx' ? '📝' :
                     t.copy_file.format === 'csv'  ? '📋' : '✏️';
    // gallery-open: protocol opens the file in a text editor (VS Code/Notepad)
    // instead of rendering in-browser. Requires one-time protocol registration
    // (protocol/setup-cookbook.md); falls back to the relative path if absent.
    copyEl.href = t.copy_file.open_uri || t.copy_file.path;
    copyEl.title = 'Opens in text editor (one-time setup: .claude/skills/asset-gallery/protocol/setup-cookbook.md)';
    copyEl.textContent = copyIcon + ' ' + t.copy_file.label;
    copyEl.style.display = '';
  }} else {{
    copyEl.style.display = 'none';
  }}

  // Open folder — links to the DEPLOYABLE folder (file:// context).
  // If view_source is set (e.g. preview.html thumbnails but full-html-preview/index.html
  // is the real deliverable), open the folder CONTAINING index.html — that's the
  // deployment package. Otherwise fall back to the asset folder root.
  const folderEl = document.getElementById('lb-folder');
  if (t.folder_uri) {{
    // gallery-open: protocol launches File Explorer at the asset folder.
    // One-time setup: .claude/skills/asset-gallery/protocol/setup-cookbook.md
    folderEl.href = t.folder_uri;
    folderEl.title = 'Opens in File Explorer — index.html + images/ + copy.md + deploy cookbook all live here. (If nothing happens: run the one-time setup in .claude/skills/asset-gallery/protocol/setup-cookbook.md)';
  }} else if (t.rel_path) {{
    let deployFolder;
    if (t.view_source) {{
      // Deployable subfolder = parent of the view_source file (the folder with index.html)
      const vsParts = t.view_source.split('/');
      deployFolder = vsParts.length > 1 ? vsParts.slice(0, -1).join('/') + '/' : '';
    }}
    if (!deployFolder) {{
      // Asset folder root (e.g. assets/04-how-we-work/)
      deployFolder = t.rel_path.split('/').slice(0, 2).join('/') + '/';
    }}
    folderEl.href = deployFolder;
    folderEl.title = 'Open deployable folder — index.html + images/ + deploy cookbook. Drag-and-drop to Netlify, or follow the deploy cookbook inside for step-by-step instructions.';
  }}

  // Production file download — PDF, DOCX, etc. (the actual file to ship/print/send)
  const prodEl = document.getElementById('lb-production');
  if (t.production_file) {{
    const ext = t.production_file.split('.').pop().toLowerCase();
    const prodIcon = ext === 'pdf' ? '📄' : ext === 'docx' ? '📝' : '📥';
    prodEl.href = t.production_file;
    prodEl.setAttribute('download', t.production_file.split('/').pop());
    prodEl.textContent = prodIcon + ' Download ' + ext.toUpperCase();
    prodEl.style.display = '';
  }} else {{
    prodEl.style.display = 'none';
  }}

  // Three-block modal: Rationale · Gate questions · Next steps. Nothing else.
  // Rationale = combined description + why-this-exists (from asset.yaml rationale: field,
  //   falling back to legacy summary: field). Gate questions and next steps come from
  //   the asset record MD's ## Open questions / ## What the operator does next sections.
  //   All other sections (plan metadata, related docs, type metadata, footer) excluded.
  let metaHtml = '';

  // Block 1 — What this is (lead sentence prominent; the rest collapsed so the
  // rationale is scannable, not a wall of production history)
  const rationale = t.rationale || t.summary || '';
  if (rationale) {{
    const dot = rationale.indexOf('. ');
    const lead = dot > 0 ? rationale.slice(0, dot + 1) : rationale;
    const rest = dot > 0 ? rationale.slice(dot + 2).trim() : '';
    const moreHtml = rest
      ? `<details style="margin-top:6px;"><summary style="font-size:11px;color:var(--text-subtle);cursor:pointer;user-select:none;">More detail</summary><p style="margin:6px 0 0;color:var(--text-muted);">${{rest}}</p></details>`
      : '';
    metaHtml += `<div class="lb-operator-block kind-info">
      <div class="lb-op-head">What this is</div>
      <p style="margin:0;">${{lead}}</p>
      ${{moreHtml}}
    </div>`;
  }}

  // Folder access note — shown for all assets so operator knows where files are
  if (t.rel_path) {{
    const deployFolder = t.view_source
      ? (t.view_source.includes('/') ? t.view_source.split('/').slice(0, -1).join('/') + '/' : '')
      : t.rel_path.split('/').slice(0, 2).join('/') + '/';
    if (deployFolder) {{
      const folderHref = t.folder_uri || deployFolder;
      const fullPath = t.folder_abs || deployFolder;
      metaHtml += `<div style="font-size:11px;color:var(--text-muted);padding:6px 10px;background:var(--bg);border-radius:4px;margin-bottom:10px;line-height:1.5;">
        📁 <strong>Deployable folder:</strong> <a href="${{folderHref}}" title="Open in File Explorer" style="color:var(--accent);text-decoration:none;"><code style="font-size:10px;color:var(--accent);word-break:break-all;">${{fullPath}}</code></a>
        <br><span style="color:var(--text-subtle);">Contains <code>index.html</code> + <code>images/</code> + deploy cookbook — drag-and-drop to Netlify or follow the cookbook inside.</span>
      </div>`;
    }}
  }}

  // Review shape + Copy file row (from Plan)
  const rsRaw = (t.plan_row && t.plan_row["Review shape"]) || '';
  const cfRaw = (t.plan_row && t.plan_row["Copy file"]) || '';
  if (rsRaw || cfRaw) {{
    const rsIcon = rsRaw.startsWith('template') ? '📋' : rsRaw.startsWith('variant-comp') ? '🎨' : '🖼';
    const cfIcon = cfRaw === 'csv' ? '📊' : cfRaw === 'pptx' ? '📊' : cfRaw === 'docx' ? '📝' : cfRaw === 'md' ? '✏️' : '';
    metaHtml += `<div style="display:flex;gap:16px;flex-wrap:wrap;padding:8px 12px;background:var(--bg);border-radius:4px;margin-bottom:10px;font-size:11px;color:var(--text-muted);">
      ${{rsRaw ? `<span><strong style="color:var(--text);">${{rsIcon}} Review shape:</strong> ${{rsRaw}}</span>` : ''}}
      ${{cfRaw && cfRaw !== 'none' ? `<span><strong style="color:var(--text);">${{cfIcon}} Copy file:</strong> ${{cfRaw}}</span>` : ''}}
    </div>`;
  }}

  // Open gate questions inline; RESOLVED/answered questions → audit history (collapsed,
  // at the very bottom). Next-steps are dropped — they live in the deploy/verify cookbook.
  let auditHtml = '';
  if (t.operator_sections && t.operator_sections.length > 0) {{
    t.operator_sections.forEach(sec => {{
      if (sec.kind !== 'questions') return;  // drop next-steps + info kinds from the modal
      const countSuffix = sec.question_count > 0 ? ` · ${{sec.question_count}} item${{sec.question_count === 1 ? '' : 's'}}` : '';
      const isResolved = /answer|resolv|closed/i.test(sec.header);
      if (isResolved) {{
        auditHtml += `<div class="lb-operator-block kind-info" style="margin-bottom:8px;">
          <div class="lb-op-head">${{sec.header}}${{countSuffix}}</div>
          ${{sec.body_html}}
        </div>`;
      }} else {{
        metaHtml += `<div class="lb-operator-block kind-questions">
          <div class="lb-op-head">🟠 ${{sec.header}}${{countSuffix}}</div>
          ${{sec.body_html}}
        </div>`;
      }}
    }});
  }}

  // Insights Manager — advisory resonance read ("On Strategy" panel, per asset)
  if (t.resonance && t.resonance.read) {{
    const r = t.resonance;
    const rmap = {{'on-insight':['res--on','🎯 On-insight'],'mixed':['res--mixed','🟡 Mixed'],'off-key':['res--off','🔁 Off-key'],'n/a-by-design':['res--unknown','⚪ N/A by design']}};
    const m = rmap[r.read] || ['res--unknown', r.read];
    const seg = r.segment ? `<span style="color:var(--text-muted);"> · ${{r.segment}}</span>` : '';
    const anchor = (r.insight_ref && r.insight_ref !== '-') ? `<span style="color:var(--text-muted);"> · anchor §${{r.insight_ref}}</span>` : '';
    const fix = r.fix ? `<p style="margin:6px 0 0;"><strong>Fix:</strong> ${{r.fix}}</p>` : '';
    metaHtml += `<div class="lb-operator-block kind-strategy">
      <div class="lb-op-head">🧭 On Strategy — resonance read <span style="font-weight:400; text-transform:none; letter-spacing:0; color:var(--text-subtle);">(advisory · Insights Manager · never gates)</span></div>
      <p style="margin:0 0 4px;"><span class="resonance-read ${{m[0]}}">${{m[1]}}</span>${{seg}}${{anchor}}</p>
      <p style="margin:4px 0 0; color:var(--text-muted);">${{r.why || ''}}</p>
      ${{fix}}
    </div>`;
  }}

  // Audit history — resolved/answered questions, collapsed at the very bottom.
  // (Campaign strategy DNA now lives ONCE at the top of the gallery page, not per-modal.)
  if (auditHtml) {{
    metaHtml += `<details style="margin-top:10px; border-top:1px solid var(--border); padding-top:8px;">
      <summary style="font-size:10px; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-subtle); font-weight:600; cursor:pointer; user-select:none;">🗄 Audit history — resolved questions</summary>
      <div style="margin-top:8px;">${{auditHtml}}</div>
    </details>`;
  }}

  document.getElementById('lb-meta').innerHTML = metaHtml || '<p style="color:var(--text-muted); font-size:12px; padding:8px 0;">No review notes for this asset.</p>';
  document.getElementById('lightbox').classList.add('open');
}}

function closeLightbox() {{
  const lbVid = document.getElementById('lb-video');
  try {{ lbVid.pause(); lbVid.removeAttribute('src'); lbVid.load(); }} catch (e) {{}}
  document.getElementById('lightbox').classList.remove('open');
  lightboxIdx = -1;
}}

function navigateLightbox(delta) {{
  if (visibleIndices.length === 0) return;
  let pos = visibleIndices.indexOf(lightboxIdx);
  if (pos === -1) pos = 0;
  else pos = (pos + delta + visibleIndices.length) % visibleIndices.length;
  openLightbox(visibleIndices[pos]);
}}

document.addEventListener('keydown', (e) => {{
  if (!document.getElementById('lightbox').classList.contains('open')) return;
  if (e.key === 'Escape') closeLightbox();
  else if (e.key === 'ArrowRight') navigateLightbox(1);
  else if (e.key === 'ArrowLeft') navigateLightbox(-1);
}});

document.getElementById('lightbox').addEventListener('click', closeLightbox);
document.querySelectorAll('.filter-bar input').forEach(el => el.addEventListener('change', render));
render();

// Deep-link: gallery.html#<asset_id> auto-opens that asset's modal
// e.g. gallery.html#15 opens the tile with asset_id "15"
(function () {{
  const hash = window.location.hash.replace('#', '');
  if (!hash) return;
  const idx = TILES.findIndex(t => String(t.asset_id) === hash);
  if (idx >= 0) {{
    // Small delay so the gallery is fully rendered before opening the lightbox
    setTimeout(() => openLightbox(idx), 80);
  }}
}})();
</script>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")

VIEW_MODE = "ship"  # "ship" (default — deliverables only) or "all" (every visual file, debug)


def run_check(campaign_dir: Path) -> int:
    """SYS-003 — read-only pre-surface gallery QA. Validates the machine-checkable slice
    of docs/specs/gallery-qa.md so a stale or broken gallery can't reach the operator
    silently. Exit 0 = clean, 1 = drift (so the Stop hook / smoke test can gate on it).

    FAIL (hard) only on CERTAIN breakage:
      - an asset folder missing asset.yaml, or an asset.yaml that won't parse
      - a `ship: true` file declared in asset.yaml that doesn't exist on disk
      - a declared copy_file / production_file / view_source pointing at a missing file
      - gallery.html missing, or older than the newest ship-affecting file (stale)
    WARN (non-fatal): a For-Human-Review asset with no rationale (the modal leads with it).

    NOT auto-checked (needs fragile Plan-id <-> folder matching): exact tile-count vs
    Review-shape — eyeball that per gallery-qa.md.
    """
    try:
        import yaml as _yaml
    except ImportError:
        print("  pyyaml required for --check", file=sys.stderr)
        return 1
    from datetime import datetime as _dt

    assets_dir = campaign_dir / "assets"
    gallery = campaign_dir / "gallery.html"
    failures: list[str] = []
    warnings: list[str] = []
    newest_ship_mtime = 0.0

    folders = []
    if assets_dir.is_dir():
        folders = [d for d in sorted(assets_dir.iterdir()) if d.is_dir() and not d.name.startswith("_")]

    for d in folders:
        yml = d / "asset.yaml"
        if not yml.exists():
            failures.append(f"{d.name}: missing asset.yaml")
            continue
        try:
            meta = _yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        except Exception as e:  # noqa: BLE001
            failures.append(f"{d.name}: asset.yaml will not parse ({e})")
            continue
        if not isinstance(meta, dict):
            failures.append(f"{d.name}: asset.yaml is not a mapping")
            continue
        newest_ship_mtime = max(newest_ship_mtime, yml.stat().st_mtime)

        status = str(meta.get("status") or "")
        if ("review" in status.lower() or "human" in status.lower()) and not str(meta.get("rationale") or "").strip():
            warnings.append(f"{d.name}: status '{status}' but no rationale")

        files_block = meta.get("files") or {}
        if isinstance(files_block, dict):
            for rel, fmeta in files_block.items():
                fmeta = fmeta or {}
                if fmeta.get("ship") is True:
                    fp = d / rel
                    if not fp.exists():
                        failures.append(f"{d.name}: ship:true file missing on disk -> {rel}")
                    else:
                        newest_ship_mtime = max(newest_ship_mtime, fp.stat().st_mtime)
                for key in ("production_file", "view_source", "copy_file"):
                    v = fmeta.get(key)
                    if v and not (d / v).exists():
                        failures.append(f"{d.name}: {rel} {key} -> missing file {v}")
        for key in ("copy_file", "production_file", "view_source"):
            v = meta.get(key)
            if v and not (d / v).exists():
                failures.append(f"{d.name}: {key} -> missing file {v}")

    print(f"=== GALLERY QA CHECK — {campaign_dir.name} ===")
    if not folders:
        print("(no asset folders — nothing to check)")
        return 0
    if not gallery.exists():
        failures.append("gallery.html does not exist — run the builder before surfacing")
    elif newest_ship_mtime and gallery.stat().st_mtime < newest_ship_mtime - 1:
        failures.append(
            f"gallery.html is STALE — older than a ship-affecting file "
            f"(gallery {_dt.fromtimestamp(gallery.stat().st_mtime):%Y-%m-%d %H:%M} < "
            f"newest {_dt.fromtimestamp(newest_ship_mtime):%Y-%m-%d %H:%M}); rebuild it"
        )

    print(f"asset folders: {len(folders)} · gallery.html: {'present' if gallery.exists() else 'MISSING'}")
    for w in warnings:
        print(f"  WARN: {w}")
    if failures:
        print(f"\nFAIL ({len(failures)}):")
        for f in failures:
            print(f"  x {f}")
        print("\nRESULT: FAIL — fix before surfacing to the operator.")
        return 1
    suffix = f" (with {len(warnings)} warning(s))" if warnings else ""
    print(f"\nRESULT: PASS{suffix} — gallery matches the machine-checkable contract.")
    print("(Tile-count vs Review-shape not auto-checked — eyeball per gallery-qa.md.)")
    return 0


def main():
    global VIEW_MODE
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--view", choices=["ship", "all"], default="ship",
                        help="ship = only deliverables (default); all = every visual file (debug)")
    parser.add_argument("--check", action="store_true",
                        help="read-only pre-surface QA (SYS-003): validate the ship / declared-file "
                             "/ gallery-freshness contract and exit non-zero on drift; do not rebuild")
    args = parser.parse_args()
    VIEW_MODE = args.view

    campaign_dir = CAMPAIGNS / args.campaign
    if not campaign_dir.exists():
        print(f"ERROR: campaign dir not found: {campaign_dir}", file=sys.stderr)
        sys.exit(1)

    if args.check:
        sys.exit(run_check(campaign_dir))

    assets_dir = campaign_dir / "assets"
    thumbs_dir = campaign_dir / "gallery-thumbs"
    thumbs_dir.mkdir(exist_ok=True)
    out_path = campaign_dir / "gallery.html"

    # Per-campaign gallery config — channels + summaries
    # When missing, the gallery falls back to a generic skeleton and warns LOUDLY
    # so the operator authors a config rather than shipping a misclassified gallery.
    global CHANNEL_ORDER
    channel_summaries = dict(DEFAULT_CHANNEL_SUMMARIES)
    campaign_dna: dict = {}   # populated from gallery-config.yaml campaign_dna: block
    config_path = campaign_dir / "gallery-config.yaml"
    if config_path.exists():
        try:
            import yaml
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if cfg:
                if "channels" in cfg and isinstance(cfg["channels"], list) and cfg["channels"]:
                    CHANNEL_ORDER = list(cfg["channels"])
                    print(f"Loaded {len(CHANNEL_ORDER)} channels from gallery-config.yaml: {CHANNEL_ORDER}")
                else:
                    print(
                        "  ⚠️  WARNING: gallery-config.yaml has no `channels:` ordered list. "
                        "Falling back to generic CHANNEL_ORDER_FALLBACK = "
                        f"{CHANNEL_ORDER_FALLBACK}. Add a top-level `channels:` list to fix.",
                        file=sys.stderr,
                    )
                if "channel_summaries" in cfg:
                    channel_summaries.update(cfg["channel_summaries"])
                if "campaign_dna" in cfg and isinstance(cfg["campaign_dna"], dict):
                    campaign_dna.update(cfg["campaign_dna"])
        except Exception as e:
            print(f"  WARN gallery-config.yaml load fail: {e}", file=sys.stderr)
    else:
        print(
            "\n" + "=" * 78 + "\n"
            f"  ⚠️  WARNING: No gallery-config.yaml at {config_path}\n"
            f"  Falling back to generic CHANNEL_ORDER = {CHANNEL_ORDER_FALLBACK}.\n"
            f"  This will almost certainly misclassify your tenant's assets.\n"
            f"  Action: author {config_path.relative_to(ROOT)} with a `channels:`\n"
            f"  ordered list + `channel_summaries:` per-channel descriptions.\n"
            f"  See campaigns/acme-launch-2026q2/gallery-config.yaml for a working example.\n"
            + "=" * 78 + "\n",
            file=sys.stderr,
        )

    # Discovery
    skip_patterns = [r"\.tmp\.", r"node_modules", r"__pycache__", r"\.git/", r"venv/", r"gallery-thumbs/"]
    def skip(p: Path) -> bool:
        s = str(p).replace("\\", "/")
        return any(re.search(pat, s) for pat in skip_patterns)

    # Load asset.yaml + Plan asset table — declarative metadata source-of-truth
    asset_yamls = load_asset_yamls(assets_dir)
    print(f"Loaded {len(asset_yamls)} asset.yaml files for declarative metadata.")

    # Per-asset asset.yaml audit — warn loudly on missing
    if assets_dir.exists():
        asset_folders = [d for d in assets_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        missing_yaml = [d for d in asset_folders if not (d / "asset.yaml").exists()]
        if missing_yaml:
            missing_names = sorted(d.name for d in missing_yaml)
            print(
                "\n" + "=" * 78 + "\n"
                f"  ⚠️  WARNING: {len(missing_yaml)} of {len(asset_folders)} asset folders missing asset.yaml:\n"
                + "\n".join(f"    - {n}" for n in missing_names[:20])
                + (f"\n    ... and {len(missing_names) - 20} more" if len(missing_names) > 20 else "")
                + "\n\n  Without asset.yaml the gallery falls back to filename heuristics for\n"
                  "  channel routing, tile titles, type, and review prompts. Lightbox sections\n"
                  "  (operator-action extraction) also degrade. Ship-complete contract per\n"
                  "  docs/specs/asset.md §1 requires asset.yaml on every web / sales-kit / social\n"
                  "  asset. Re-fire Producer on these folders to author the missing yamls.\n"
                + "=" * 78 + "\n",
                file=sys.stderr,
            )

        # Per-asset deployment block audit (v2 — Rollout Architecture §7.1)
        # asset.yaml exists but lacks a deployment block → Producer skipped Step 4.6.
        missing_deployment = []
        for asset_dir in asset_folders:
            yaml_path = asset_dir / "asset.yaml"
            if not yaml_path.exists():
                continue  # already counted in missing_yaml above
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    parsed = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError):
                continue
            if not isinstance(parsed, dict):
                continue
            if "deployment" not in parsed:
                missing_deployment.append(asset_dir)
        if missing_deployment:
            missing_dep_names = sorted(d.name for d in missing_deployment)
            print(
                "\n" + "=" * 78 + "\n"
                f"  ⚠️  WARNING: {len(missing_deployment)} of {len(asset_folders)} asset folders have asset.yaml WITHOUT deployment: block:\n"
                + "\n".join(f"    - {n}" for n in missing_dep_names[:20])
                + (f"\n    ... and {len(missing_dep_names) - 20} more" if len(missing_dep_names) > 20 else "")
                + "\n\n  Producer Step 4.6 not completed (per docs/specs/asset.md §deployment +\n"
                  "  .claude/agents/producer/AGENT.md Step 4.6). Inheritance from\n"
                  "  tenant/<name>/integrations.yaml channel_defaults[<channel>] would auto-\n"
                  "  populate destination_type, platform, publish_method, location. Per-asset\n"
                  "  fields (format_requirements + verification + deployment_notes) require\n"
                  "  manual authoring.\n\n"
                  "  Fix: edit each asset.yaml; add deployment: block per spec.\n"
                  "  Pre-existing assets (Wave 0 of acme-podcast-2026q2)\n"
                  "  will be retrofitted in Phase 4 of the Rollout Architecture build sequence.\n"
                + "=" * 78 + "\n",
                file=sys.stderr,
            )
    plan_table = parse_plan_asset_table(campaign_dir / "plan.md")
    print(f"Parsed {len(plan_table)} rows from plan.md asset list.")

    # Extract operator-facing sections from each asset record MD
    operator_sections_by_dir: dict[Path, list[dict]] = {}
    for asset_dir in (assets_dir.iterdir() if assets_dir.exists() else []):
        if not asset_dir.is_dir():
            continue
        # Find the asset record MD — multiple naming conventions supported.
        # First match with operator sections wins.
        candidates: list[Path] = []
        candidates.extend(asset_dir.glob("[0-9]*-*.md"))   # Acme Co: 0a-foo.md / 17-bar.md
        candidates.extend(asset_dir.glob("asset.md"))      # Soundtrak / generic
        candidates.extend(asset_dir.glob("preview.md"))    # legacy convention
        candidates.extend(asset_dir.glob("asset-record.md"))  # generic fallback
        for record_md in candidates:
            sections = extract_operator_sections(record_md)
            if sections:
                operator_sections_by_dir[asset_dir] = sections
                break  # use first matching record
    total_sections = sum(len(s) for s in operator_sections_by_dir.values())
    print(f"Extracted {total_sections} operator-facing sections from {len(operator_sections_by_dir)} asset records.")

    visual_files: list[Path] = []
    md_files: list[Path] = []

    # === SHIP FILTER (2026-06-01) ===
    # Default gallery view ("ship" mode) hides production scaffolding so the
    # operator reviews actual deliverables, not the system chrome. Override
    # with --view all to see the full file dump (debug / audit).
    #
    # Hide precedence:
    #   1. asset.yaml file metadata `ship: false` → hidden
    #   2. asset.yaml file metadata `ship: true` → shown
    #   3. Hardcoded system-chrome names → hidden (asset.html / brief.html /
    #      plan.html / dashboard.html / concept-trio.html / safe.html / ...)
    #   4. asset.yaml `role` in {asset_record, design_doc, how_to_use, doc_index,
    #      render_pipeline, catalog} → hidden
    #   5. asset.yaml `type == Foundation` → hidden (cookbooks, raw captures, sources)
    #   6. Path contains comparison-runs/ or /cookbooks/ → hidden
    SYSTEM_CHROME_NAMES = {
        "asset.html",
        "brief.html",
        "plan.html",
        "dashboard.html",
        "concept-trio.html",
        "safe.html",
        "smart.html",
        "wild.html",
        "day-1-outline.html",
    }

    def is_ship_visible(file_path: Path, asset_dir: Path) -> tuple[bool, str]:
        if VIEW_MODE == "all":
            return True, "view=all"
        asset_meta = asset_yamls.get(asset_dir, {})
        files_block = asset_meta.get("files") or {}
        try:
            rel_to_asset = str(file_path.relative_to(asset_dir)).replace("\\", "/")
        except ValueError:
            rel_to_asset = file_path.name
        file_meta = files_block.get(rel_to_asset, {})

        # 1+2. Explicit ship flag wins outright
        if "ship" in file_meta:
            return bool(file_meta["ship"]), f"ship={file_meta['ship']}"

        # 2a. HTML/MD sibling inheritance: if this is X.html and X.md IS
        # declared in the files block, treat the HTML as the rendered preview
        # of the declared source markdown. Inherit visibility (ship) AND
        # metadata (asset_name + per-file title applied at tile-build time
        # via the sibling-lookup pattern used downstream).
        # IMPORTANT: also respect the sibling's role / type — if the MD is
        # role: asset_record / how_to_use / etc. OR type: Foundation, the
        # HTML render is ALSO non-ship (it's the rendered version of an
        # internal-only document, not a deliverable).
        # EXCEPTION: if the HTML itself is explicitly declared in the files
        # block with its own metadata, that explicit declaration takes
        # precedence — skip sibling inheritance entirely. The author's
        # explicit type/role on the HTML wins over the sibling's.
        if file_path.suffix.lower() == ".html" and rel_to_asset not in files_block:
            stem_rel = rel_to_asset[:-len(".html")] + ".md"
            if stem_rel in files_block:
                sibling_meta = files_block[stem_rel]
                if sibling_meta.get("ship") is False:
                    return False, f"sibling {stem_rel} declared ship:false"
                sibling_role = sibling_meta.get("role", "")
                if sibling_role in {"asset_record", "design_doc", "how_to_use", "doc_index", "render_pipeline", "catalog", "rationale"}:
                    return False, f"sibling {stem_rel} role={sibling_role} (non-ship)"
                if sibling_meta.get("type") == "Foundation":
                    return False, f"sibling {stem_rel} type=Foundation (non-ship)"
                return True, f"render of declared {stem_rel}"

        # 3. Strict declaration rule: if asset.yaml exists AND declares a files
        # block AND this file isn't in it → hidden. Producer's editorial
        # declaration is authoritative; unlisted files are production scaffolds.
        if files_block and rel_to_asset not in files_block:
            return False, f"not declared in {asset_dir.name}/asset.yaml files block"

        # 4. Hardcoded system-chrome names
        if file_path.name.lower() in SYSTEM_CHROME_NAMES:
            return False, f"system-chrome ({file_path.name})"

        # 5. asset.yaml role declares non-ship intent
        role = file_meta.get("role", "")
        if role in {"asset_record", "design_doc", "how_to_use", "doc_index", "render_pipeline", "catalog"}:
            return False, f"role={role}"

        # 6. asset.yaml type Foundation
        if file_meta.get("type") == "Foundation":
            return False, "type=Foundation"

        # 7. Path-based ignores (cookbooks, raw comparison captures)
        path_str = str(file_path).replace("\\", "/")
        if "/comparison-runs/" in path_str or path_str.endswith("comparison-runs"):
            return False, "comparison-runs raw capture"
        if "/cookbooks/" in path_str:
            return False, "cookbook (operational, not deliverable)"

        return True, "default-show"

    if assets_dir.exists():
        for p in assets_dir.rglob("*"):
            if p.is_file() and not skip(p):
                ext = p.suffix.lower()
                if ext in (".html", ".png", ".mp4") or ext in DOC_DELIVERABLE_EXTS:
                    visual_files.append(p)
                elif ext == ".md":
                    md_files.append(p)

    if VIEW_MODE != "all":
        kept, hidden = [], 0
        for f in visual_files:
            try:
                asset_folder = f.relative_to(assets_dir).parts[0]
            except (ValueError, IndexError):
                asset_folder = ""
            asset_dir_for_file = assets_dir / asset_folder if asset_folder else f.parent
            visible, _ = is_ship_visible(f, asset_dir_for_file)
            if visible:
                kept.append(f)
            else:
                hidden += 1
        print(f"Ship filter: {len(kept)} ship tiles kept, {hidden} production scaffolds hidden. Use --view all to see everything.")
        visual_files = kept

    # === Template ↔ sample-render PNG pair deduplication ===
    # When templates-html/X.html and templates-preview/X.png coexist for the same stem,
    # the PNG is the visual deliverable (review the brand discipline when populated);
    # the HTML template is just source code, linked from the lightbox.
    png_stems = {p.stem.lower() for p in visual_files if p.suffix.lower() == ".png" and "templates-preview" in str(p).lower()}
    html_template_path_by_stem = {p.stem.lower(): p for p in visual_files if p.suffix.lower() == ".html" and "templates-html" in str(p).lower()}

    suppressed_template_htmls: set[Path] = set()
    template_source_for_png: dict[Path, Path] = {}  # png_path -> template_html_path
    for stem, html_path in html_template_path_by_stem.items():
        if stem in png_stems:
            suppressed_template_htmls.add(html_path)
            # Find the matching png
            for p in visual_files:
                if p.suffix.lower() == ".png" and p.stem.lower() == stem and "templates-preview" in str(p).lower():
                    template_source_for_png[p] = html_path
                    break

    visual_files = [f for f in visual_files if f not in suppressed_template_htmls]
    print(f"Found {len(visual_files)} visual files + {len(md_files)} markdown files. "
          f"({len(suppressed_template_htmls)} template HTMLs suppressed in favour of sample-render PNG siblings)")

    # Group MDs by their containing asset folder for relate-to-tile logic
    mds_by_asset_dir: dict[Path, list[Path]] = defaultdict(list)
    for md in md_files:
        # Asset folder = first ancestor under assets/ (e.g. 0a-email-template-uplift)
        try:
            rel = md.relative_to(assets_dir)
            asset_root = assets_dir / rel.parts[0]
            mds_by_asset_dir[asset_root].append(md)
        except ValueError:
            pass

    tiles: list[dict] = []
    foundation_docs: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(device_scale_factor=2)
        page = ctx.new_page()

        # Build visual tiles first
        for f in visual_files:
            rel = f.relative_to(campaign_dir)
            rel_str = str(rel).replace("\\", "/")
            thumb_name = re.sub(r"[^a-zA-Z0-9._-]", "_", rel_str).rstrip(".") + ".png"
            thumb_path = thumbs_dir / thumb_name

            asset_folder_name = rel.parts[1] if len(rel.parts) > 1 else ""
            asset_dir = assets_dir / asset_folder_name if asset_folder_name else f.parent

            vertical = "T4" in f.name or "9-16" in f.name.lower() or "9x16" in f.name.lower() or "shorts" in f.name.lower()

            # Prefer asset.yaml metadata over heuristics
            asset_meta = asset_yamls.get(asset_dir, {})

            # Status: check asset.yaml `status:` field first (explicit, reliable),
            # fall back to text-scanning detect_status if not set.
            yaml_status_raw = asset_meta.get("status", "")
            status = _normalise_yaml_status(str(yaml_status_raw)) if yaml_status_raw else ""
            if not status:
                status = detect_status(asset_dir, f)
            files_block = asset_meta.get("files") or {}
            rel_to_asset = str(f.relative_to(asset_dir)).replace("\\", "/")
            file_meta = files_block.get(rel_to_asset, {})
            # HTML-MD sibling inheritance: if the HTML isn't declared but its
            # X.md sibling is, inherit the sibling's metadata (the HTML is the
            # rendered preview of the same artifact).
            if not file_meta and f.suffix.lower() == ".html":
                sibling_md_rel = rel_to_asset[:-len(".html")] + ".md"
                if sibling_md_rel in files_block:
                    file_meta = dict(files_block[sibling_md_rel])
                    # Override type from "Foundation" (which is right for the MD
                    # source) to "Instance" (the rendered HTML IS the deliverable view)
                    if file_meta.get("type") == "Foundation":
                        file_meta["type"] = "Instance"

            channel = (
                file_meta.get("channel")
                or asset_meta.get("default_channel")
                or classify_channel(rel_str)
            )
            tile_type_yaml = file_meta.get("type")
            review_prompt_yaml = file_meta.get("review")
            tile_title_yaml = file_meta.get("title")
            template_source_yaml = file_meta.get("template_source")
            # view_source: overrides the "View in full" URL (e.g. let preview.html thumbnail
            # while "View in full" opens full-html-preview/index.html)
            view_source_yaml = file_meta.get("view_source", "")
            view_source_rel = str((asset_dir / view_source_yaml).relative_to(campaign_dir)).replace("\\", "/") if view_source_yaml and (asset_dir / view_source_yaml).exists() else ""
            # production_file: binary deliverable (PDF, DOCX) downloadable from modal
            prod_file_yaml = file_meta.get("production_file", "")
            prod_file_rel = str((asset_dir / prod_file_yaml).relative_to(campaign_dir)).replace("\\", "/") if prod_file_yaml and (asset_dir / prod_file_yaml).exists() else ""
            cls = classify_class(rel_str)

            # Compute paired full-page render path (for HTML assets, used in lightbox)
            full_path = thumbs_dir / (thumb_name.rsplit(".", 1)[0] + ".full.png")
            is_doc_deliverable = f.suffix.lower() in DOC_DELIVERABLE_EXTS
            if f.suffix.lower() == ".png":
                ok = thumb_for_png(f, thumb_path)
                full_relative = rel_str  # PNG source is already full-fidelity
            elif f.suffix.lower() == ".mp4":
                ok = thumb_for_mp4(page, f, thumb_path, vertical=vertical)
                full_relative = rel_str  # lightbox plays the MP4 directly via <video>
            elif is_doc_deliverable:
                ok = thumb_for_doc(page, f, thumb_path,
                                   tile_title_yaml or asset_meta.get("asset_name", "") or f.name,
                                   f.suffix.lower())
                full_relative = rel_str  # the binary file IS the deliverable (download)
                # Ensure the download action appears even if no explicit production_file declared
                if not prod_file_rel:
                    prod_file_rel = rel_str
            else:
                # TEXT-deliverable assets ship the asset-RECORD render (asset.html /
                # preview.html) as their preview — that carries operator-panel chrome.
                # Screenshot a CHROME-FREE render of the copy instead, so the lightbox
                # left pane shows the clean deliverable, not the record + chrome.
                # GUARD: only for genuinely text-only assets. If the asset ALSO ships a
                # visual tile (PNG/MP4 — e.g. a social tile whose preview.html is an
                # in-situ mockup), the preview is a VISUAL surface — leave it alone, or we
                # break the in-situ social view (feedback_in_situ_dual_view_for_social).
                shoot = f
                copy_file_name = asset_meta.get("copy_file", "")
                asset_has_visual = any(
                    vf.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".mp4")
                    and (vf.parent == asset_dir or asset_dir in vf.parents)
                    for vf in visual_files
                )
                if (f.name in ("asset.html", "preview.html") and not asset_has_visual
                        and isinstance(copy_file_name, str) and copy_file_name.endswith(".md")):
                    copy_md = asset_dir / copy_file_name
                    clean_html = thumbs_dir / (thumb_name.rsplit(".", 1)[0] + ".clean.html")
                    if render_clean_copy(copy_md, clean_html):
                        shoot = clean_html
                        # View-in-full opens the clean copy too (the chrome'd record is
                        # still reachable via related docs / Open folder)
                        view_source_rel = f"gallery-thumbs/{clean_html.name}"
                ok = thumb_for_html(page, shoot, thumb_path, full_out_path=full_path, vertical=vertical)
                full_relative = f"gallery-thumbs/{full_path.name}"
            if not ok:
                continue

            related_docs = []
            for md in mds_by_asset_dir.get(asset_dir, []):
                md_rel = md.relative_to(campaign_dir).as_posix()
                # Pull yaml-declared title if available so lightbox shows
                # readable doc names instead of bare filenames
                md_rel_to_asset = str(md.relative_to(asset_dir)).replace("\\", "/")
                md_meta = files_block.get(md_rel_to_asset, {})
                md_title = md_meta.get("title") or md.name
                related_docs.append({
                    "name": md.name,
                    "title": md_title,
                    "source": md_rel,
                })

            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")

            tile_type = tile_type_yaml or classify_type(rel_str, f)

            # If this is a PNG with a suppressed sibling template HTML, add that as a "Source template" related link
            if f in template_source_for_png:
                tpl = template_source_for_png[f]
                tpl_rel = tpl.relative_to(campaign_dir).as_posix()
                related_docs.insert(0, {"name": f"{tpl.name} (source template)", "source": tpl_rel})
            # Also: if asset.yaml declared a template_source, attach it as related doc
            if template_source_yaml:
                # Resolve relative to asset_dir
                tpl_full = asset_dir / template_source_yaml
                if tpl_full.exists():
                    tpl_rel = tpl_full.relative_to(campaign_dir).as_posix()
                    # Avoid duplicate if already added above
                    if not any(d["source"] == tpl_rel for d in related_docs):
                        related_docs.insert(0, {"name": f"{Path(template_source_yaml).name} (source template)", "source": tpl_rel})

            # Pull Plan metadata if this asset_id appears in the Plan table
            asset_id = asset_meta.get("asset_id") or re.match(r"^(0[a-e]|\d+[a-z]?)", asset_folder_name)
            asset_id_str = asset_id.group(1) if hasattr(asset_id, "group") else str(asset_id) if asset_id else ""
            plan_row = plan_table.get(asset_id_str) if asset_id_str else None

            operator_sections = operator_sections_by_dir.get(asset_dir, [])
            # SYS-013: gate questions count ONLY while the asset is pre-approval. Once it's
            # Approved / Archived / Declined the gate is closed — its open questions were resolved
            # at approval, so they stop counting (no orange "N questions" badge on an approved
            # asset). A question still genuinely open post-approval must be re-homed as a Phase-5
            # operator_action (counted separately), not left in the record's gate section.
            gate_open = status in {"In Production", "For Human Review"}
            total_questions = (
                sum(s["question_count"] for s in operator_sections if s["kind"] == "questions")
                if gate_open else 0
            )

            is_video = f.suffix.lower() == ".mp4"
            tiles.append({
                "name": f.name,
                "rel_path": rel_str,
                "thumb": f"gallery-thumbs/{thumb_name}",
                "full_render": full_relative,  # Used in lightbox — full-page render for HTMLs, original PNG for images
                "source": rel_str,
                "is_video": is_video,
                "video_src": rel_str if is_video else "",
                "status": status,
                "channel": channel,
                "cls": cls,
                "type": tile_type,
                "vertical": vertical,
                "mtime": mtime,
                "related_docs": related_docs,
                "asset_id": asset_id_str,
                "asset_name": asset_meta.get("asset_name", ""),
                "title": tile_title_yaml,
                "review_prompt": review_prompt_yaml,
                "rationale": asset_meta.get("rationale", ""),   # preferred field (v2)
                "summary": asset_meta.get("summary", ""),       # legacy alias — rationale takes priority
                "copy_file": _resolve_copy_file(asset_meta.get("copy_file", ""), asset_dir, campaign_dir),
                "folder_uri": _gallery_open_uri(asset_dir),
                "folder_abs": str(asset_dir.resolve()),
                "view_source": view_source_rel,       # overrides "View in full" URL when set
                "production_file": prod_file_rel,     # binary deliverable to download (PDF etc.)
                "plan_row": plan_row or {},
                "operator_sections": operator_sections,
                "open_question_count": total_questions,
                "resonance": asset_meta.get("resonance") or {},
            })

        browser.close()

    # Foundation docs: MDs whose containing asset folder has NO visual tiles in any non-Foundation channel
    asset_dirs_with_visual_tiles = {(assets_dir / Path(t["rel_path"]).parts[1]) for t in tiles if Path(t["rel_path"]).parts[0] == "assets" and len(Path(t["rel_path"]).parts) > 1}
    # Actually rel_path starts with "assets/..." so parts[0] = "assets", parts[1] = asset folder
    tile_asset_dirs = set()
    for t in tiles:
        parts = Path(t["rel_path"]).parts
        if len(parts) >= 2 and parts[0] == "assets":
            tile_asset_dirs.add(assets_dir / parts[1])

    # Roles whose review priority maps to operator-facing weight
    ROLE_PRIORITY = {
        "primary_doc": 1,
        "rationale": 2,
        "how_to_use": 2,
        "doc_index": 3,
        "design_doc": 3,
        "render_pipeline": 3,
        "catalog": 3,
        "asset_record": 9,  # least visible — CM metadata
    }

    for asset_dir, mds in mds_by_asset_dir.items():
        if asset_dir not in tile_asset_dirs:
            # No visual sibling — these MDs become Foundation entries grouped under the asset
            asset_meta = asset_yamls.get(asset_dir, {})
            files_meta = asset_meta.get("files") or {}
            asset_id_str = asset_meta.get("asset_id", "")
            plan_row = plan_table.get(asset_id_str) if asset_id_str else None

            for md in mds:
                rel = md.relative_to(campaign_dir)
                rel_str = str(rel).replace("\\", "/")

                # Pull per-file metadata from asset.yaml first — needed for ship filter
                rel_to_asset_md = str(md.relative_to(asset_dir)).replace("\\", "/")
                file_meta = files_meta.get(rel_to_asset_md, {}) or files_meta.get(md.name, {})

                # Skip if explicitly ship: false or role marks it as internal-only
                if file_meta.get("ship") is False:
                    continue
                md_role = file_meta.get("role", "")
                # Infer role for undeclared files that match asset-record naming patterns
                if not md_role:
                    n = md.name
                    if (re.match(r"^0[a-e]-.*\.md$", n) or n == "asset.md"
                            or n == "asset-record.md" or n.endswith("-asset.md")):
                        md_role = "asset_record"
                # Extended exclusion set: internal/operational roles not useful in gallery
                if md_role in {"asset_record", "render_pipeline", "catalog",
                               "how_to_use", "design_doc", "rationale", "doc_index"}:
                    continue

                status = detect_status(asset_dir, md)
                cls = classify_class(rel_str)

                rel_to_asset = rel_to_asset_md
                role = file_meta.get("role", "primary_doc" if md.name.startswith("0") and md.name.endswith(".md") and "-" in md.name else "primary_doc")
                # Default role: asset record files match "0X-...md" pattern
                if re.match(r"^0[a-e]-.*\.md$", md.name):
                    role = file_meta.get("role", "asset_record")

                foundation_docs.append({
                    "name": md.name,
                    "rel_path": rel_str,
                    "source": rel_str,
                    "status": status,
                    "channel": "Foundation",
                    "cls": cls,
                    "title": file_meta.get("title", ""),
                    "review": file_meta.get("review", ""),
                    "role": role,
                    "role_priority": ROLE_PRIORITY.get(role, 5),
                    "asset_id": asset_id_str,
                    "asset_name": asset_meta.get("asset_name", ""),
                    "asset_summary": asset_meta.get("summary", ""),
                    "asset_dir": asset_dir.name,
                    "plan_row": plan_row or {},
                })

    tiles.sort(key=lambda x: (CHANNEL_ORDER.index(x["channel"]) if x["channel"] in CHANNEL_ORDER else 99, x["rel_path"]))
    foundation_docs.sort(key=lambda x: x["rel_path"])

    build_html(args.campaign, tiles, foundation_docs, channel_summaries, campaign_dna, out_path)
    print(f"OK  {out_path}  ({len(tiles)} tiles + {len(foundation_docs)} foundation docs)")

if __name__ == "__main__":
    main()
