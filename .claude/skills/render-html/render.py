#!/usr/bin/env python3
"""
render-html — converts markdown + template type → HTML for operator review.

Invoked by Campaign Manager after every markdown artifact write.

Usage:
  python render.py --markdown <path> --template <name> [--output <path>] [--extra-context <json>]

Dependencies:
  pip install markdown
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import markdown as md
except ImportError:
    print("ERROR: `markdown` library not installed. Run: pip install markdown", file=sys.stderr)
    sys.exit(1)

import html as html_lib

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_model  # shared canonical plan parser — also read by build-gallery.py


TEMPLATES_DIR = Path(__file__).parent / "templates"
STYLES_DIR = Path(__file__).parent / "templates" / "styles"

# Per-form default collapsed-state character cutoffs (mobile feed).
# Operator can override per variant via extra_context.variants[].collapsed_chars.
DEFAULT_COLLAPSED_CHARS = {
    "linkedin-post": 220,
    "twitter-post": 280,
    "instagram-post": 125,
    "email": 90,           # inbox preview snippet
    "substack-feed": 180,
}

KNOWN_FORMS = {"linkedin-post", "email", "twitter-post", "instagram-post", "substack-feed"}


def load_template(template_name: str) -> str:
    """Load a template by name. Falls back to base.html if specific template absent."""
    specific = TEMPLATES_DIR / f"{template_name}.html"
    if specific.exists():
        return specific.read_text(encoding="utf-8")
    # Fallback to base
    base = TEMPLATES_DIR / "base.html"
    return base.read_text(encoding="utf-8")


def load_styles() -> str:
    """Load all CSS into one inline <style> block."""
    css_files = sorted(STYLES_DIR.glob("*.css"))
    css = "\n".join(f.read_text(encoding="utf-8") for f in css_files)
    return css


def extract_title(markdown_text: str) -> str:
    """Pull the first H1 from the markdown as the page title."""
    match = re.search(r"^#\s+(.+)$", markdown_text, re.MULTILINE)
    return match.group(1).strip() if match else "Marketing AI System"


KNOWN_TEMPLATES = {
    "brief", "brand-context", "concept-trio", "plan", "asset-preview",
    "dashboard", "tasks", "index", "spec", "insight-brief",
}


def infer_template(markdown_path: Path) -> str:
    """Infer the canonical template name from a markdown file's path/name.

    The Stop hook passes the base.html PATH as --template, which would set a
    garbage <body> class and silently drop all template-scoped CSS (campaign
    cards, dashboard header strip, task groups). Inferring from the path makes
    rendering correct regardless of how --template was passed. Returns 'base'
    for files with no dedicated template (general .content styling applies)."""
    stem = markdown_path.stem
    parent = markdown_path.parent.name
    grandparent = markdown_path.parent.parent.name
    if parent == "campaigns" and stem == "index":
        return "index"
    if parent == "campaigns" and stem == "tasks":
        return "tasks"
    if grandparent == "campaigns" and stem == parent:
        return "dashboard"  # campaigns/<slug>/<slug>.md
    if stem == "dashboard":
        return "dashboard"
    if stem == "insight-brief":
        return "insight-brief"  # SYS-088 — its own (wide) template, not the narrow Brief column
    if stem == "brief":
        return "brief"
    if stem == "plan":
        return "plan"
    if stem in ("concept-trio", "selected", "safe", "smart", "wild"):
        return "concept-trio"  # all concept pages share the concept styling
    if parent == "tenant-brand" or ("brand" in stem and "context" in stem):
        return "brand-context"
    return "base"


def stylize_brief(body_html: str) -> str:
    """Brief-only HTML polish: turn the attribution markers and (HARD) mandatory
    flags into styled inline tags. Attribution markers are the brief's signature
    discipline ([the operator's read] / [AI extension] / [AI synthesis]); HARD flags
    mark non-negotiable mandatories. Additive + scoped — no effect if absent."""
    body_html = re.sub(r"\[the operator's read\]", '<span class="attr attr--operator">the operator’s read</span>', body_html)
    body_html = re.sub(r"\[AI extension\]", '<span class="attr attr--ext">AI extension</span>', body_html)
    body_html = re.sub(r"\[AI synthesis\]", '<span class="attr attr--syn">AI synthesis</span>', body_html)
    body_html = re.sub(r"\(HARD([^)]*)\)", lambda m: f'<span class="hard-tag">HARD{m.group(1)}</span>', body_html)
    return body_html


# Plan asset-table columns we recognise (lower-cased). The asset list is
# identified by a column literally named "asset" PLUS >=3 of these — so the
# small phasing / pre-flight / status-snapshot / showcase tables are left alone.
_PLAN_COLS = {
    "review format", "review shape", "form", "ships", "copy file", "owner", "owner agent",
    "phase", "target", "target date", "depends on", "depends", "notes",
    # v3 (2026-07): asset-list gains Type / Channel / Description. Their presence
    # (specifically a `type` column) switches the render to the v3 table below.
    "type", "channel", "description", "item",
}

# v3 plan table — the group-by (channel <-> wave) toggle. Runs at parse time (the
# <script> is emitted right after the table), so rows group before first paint;
# with JS off the table still shows every row + column, just ungrouped.
_PLAN_V3_JS = """<script>
(function(){
function build(root){
 var tb=root.querySelector('tbody'), btns=root.querySelectorAll('.pt-btn');
 var rows=[].slice.call(tb.querySelectorAll('tr[data-stage]'));
 var STAGES=['Launch','Ongoing'], NAMES={Launch:'Launch activities',Ongoing:'Ongoing management'};
 function render(key){
  btns.forEach(function(b){b.classList.toggle('is-on',b.dataset.group===key);});
  root.setAttribute('data-by',key); tb.innerHTML='';
  STAGES.forEach(function(stage){
   var sr=rows.filter(function(r){return r.dataset.stage===stage;});
   if(!sr.length)return;
   var sh=document.createElement('tr');sh.className='pv3-stage';
   sh.innerHTML='<td colspan="8">'+NAMES[stage]+'</td>';tb.appendChild(sh);
   var g={},ord=[];
   sr.forEach(function(r){
    var k=key==='wave'?('Wave '+(r.dataset.wave!=='0'?r.dataset.wave:'—')):(r.dataset.channel||'Other');
    if(!(k in g)){g[k]=[];ord.push(k);}g[k].push(r);
   });
   if(key==='wave')ord.sort(function(a,b){return (parseInt(a.replace(/\\D/g,''))||0)-(parseInt(b.replace(/\\D/g,''))||0);});
   ord.forEach(function(k){
    var gh=document.createElement('tr');gh.className='pv3-grp';
    var n=g[k].length,nl=(key==='wave'&&n>1)?(n+' in parallel'):(n+' item'+(n===1?'':'s'));
    gh.innerHTML='<td colspan="8">'+k+' <span class="pv3-grp__n">'+nl+'</span></td>';tb.appendChild(gh);
    g[k].sort(function(a,b){return (parseInt(a.dataset.wave)||0)-(parseInt(b.dataset.wave)||0);});
    g[k].forEach(function(r){tb.appendChild(r);});
   });
  });
 }
 btns.forEach(function(b){b.addEventListener('click',function(){render(b.dataset.group);});});
 render('channel');
}
document.querySelectorAll('.plan-v3').forEach(build);
})();
</script>"""


def _plan_text(frag: str) -> str:
    return re.sub(r"<[^>]+>", "", frag or "").replace("&amp;", "&").strip()


# State-cell text -> (css-class, label, emoji, is_archived). Order matters:
# transfer/cut are checked before the positive states.
def _classify_plan_state(state_txt: str):
    s = state_txt.lower()
    if "transfer" in s:           return ("transfer", "Transferred", "➡️", True)
    if "cut" in s:                return ("cut", "Cut", "❌", True)
    if "approv" in s:             return ("ok", "Approved", "✅", False)
    if "review" in s:             return ("review", "In review", "🟡", False)
    if "production" in s or "in progress" in s:
                                  return ("prog", "In production", "🔵", False)
    if "queued" in s or "pending" in s:
                                  return ("queued", "Queued", "⏸", False)
    if "shipped" in s or "live" in s:
                                  return ("shipped", "Shipped", "🟢", False)
    return None


def _build_plan_status_map(body_html: str) -> dict:
    """Parse the plan's "Status snapshot" table (header: State | Assets) into a
    {asset_number(str) -> (cls,label,emoji,archived)} map. This is the plan's
    own authoritative per-asset status source; the asset rows themselves carry
    no status column. Returns {} if no such table exists (other plans fall back
    to per-row keyword detection)."""
    smap = {}
    for tbl in re.findall(r"<table[^>]*>.*?</table>", body_html, re.DOTALL):
        thead = re.search(r"<thead>(.*?)</thead>", tbl, re.DOTALL)
        if not thead:
            continue
        hs = [_plan_text(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(1), re.DOTALL)]
        if "state" not in hs or "assets" not in hs:
            continue
        tbody = re.search(r"<tbody>(.*?)</tbody>", tbl, re.DOTALL)
        if not tbody:
            continue
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tbody.group(1), re.DOTALL):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            if len(cells) < 2:
                continue
            info = _classify_plan_state(_plan_text(cells[0]))
            if not info:
                continue
            assets_txt = _plan_text(cells[1])
            # #N, #N-#M ranges, #N/#M lists
            for a, b in re.findall(r"#(\d+)(?:\s*[-–]\s*#?(\d+))?", assets_txt):
                if b:
                    for n in range(int(a), int(b) + 1):
                        smap[str(n)] = info
                else:
                    smap[a] = info
    return smap


# Plan H2 section policy. Not matched -> OPEN (operator-facing). "open question"
# -> highlighted. History/audit sections -> collapsed AND moved to the bottom.
# Other process/AI-internal sections -> collapsed in place.
_PLAN_HISTORY_KW = (
    "version history", "what changed", "change log", "changelog", "freshness",
    "revision", "what happens on", "approve plan",
)
_PLAN_COLLAPSE_KW = (
    "roster", "fast-lane", "fast lane", "workflow detail", "multi-step",
    "internal workflow", "production protocol", "comparison run", "showcase thread",
    "system-feature", "operator guide", "step-by-step", "distribution mechanics",
    "trigger criteria", "kpi measurement", "readiness", "phase 5 + 6",
    "reference detail", "honesty discipline", "quality criteria",
)


def _classify_plan_section(title: str) -> str:
    """title = lower plain text of an H2 -> 'highlight'|'history'|'collapse'|'open'."""
    if "open question" in title:
        return "open" if "resolv" in title else "highlight"
    if any(k in title for k in _PLAN_HISTORY_KW):
        return "history"
    if any(k in title for k in _PLAN_COLLAPSE_KW):
        return "collapse"
    return "open"


# Asset channel/type buckets for the sign-off grouping. First match wins, so the
# tuple order is the disambiguation priority (more specific types first); matched
# against each asset's name + form + review-shape + ships (not notes, to cut
# noise). Tuned to the real campaign vocabulary — avoid keywords that collide with
# tenant products (e.g. "cookbook" is a tenant product, not a setup runbook).
_PLAN_TYPE_BUCKETS = (
    ("Video", ("video", " mp4", "remotion", "reel", "youtube", "shorts", "tiktok")),
    ("Ads & paid", ("display network", "gdn", "paid creative", "google ads",
        "google display", "paid li", "paid social", "boosted post")),
    ("Setup & tracking", ("tracking", "analytics", "posthog", "ga4", "gtm", "utm",
        "schema.org", "schema markup", "tracker", "spreadsheet", "checklist",
        "audit", "readiness", "tool packaging", "sub-edit tool", "sitemap")),
    ("Sales kit", ("pitch deck", "deck", "case study", "battle card",
        "leave-behind", "presenter notes", "sales kit")),
    ("Adviser outreach", ("adviser", "advisor", "intranet", "onboarding call",
        "1:1 call", "adviser onboarding", "advisor onboarding", "onboarding micro-doc")),
    ("Social", ("linkedin", "li post", "li tile", " li ", "substack", "instagram",
        "twitter", " x ", "thread", "tile", "organic post", "carousel", "amplifier",
        "feed post", "social")),
    ("Email & outreach", ("email", "e-mail", "nurture", "outreach", "partner brief",
        "press pitch", "food press", "pitch email", "drip", "sequence")),
    ("Article & long-form", ("article", "substack issue", "long-form", "whitepaper",
        "blog post", "essay", "newsletter issue")),
    ("Web & landing", ("landing", "signup page", "how-we-work", "website", " page",
        "microsite", "hero ")),
    ("Print", ("print", "bookmark", "postcard", "flyer", "poster")),
)

# Display order for the type groups (content channels first, infra last).
_PLAN_TYPE_ORDER = (
    "Web & landing", "Email & outreach", "Adviser outreach", "Social", "Video",
    "Ads & paid", "Sales kit", "Article & long-form", "Setup & tracking", "Print",
    "Other",
)

_TYPE_OUTPUT = {
    "Web & landing": "Web page (HTML)", "Email & outreach": "Email (HTML + copy)",
    "Adviser outreach": "Doc / page", "Social": "Social post + tile",
    "Video": "Video (MP4)", "Ads & paid": "Ad creative", "Sales kit": "Doc / deck",
    "Print": "Print-ready (PDF)", "Article & long-form": "Long-form (HTML)",
    "Setup & tracking": "Setup / tracking",
}

_FMT_TOKENS = ("HTML", "PNG", "JPG", "JPEG", "PDF", "SVG", "MP4", "PPTX", "DOCX",
               "CSV", "GIF")


def _plan_asset_type(text: str) -> str:
    """Bucket an asset into a channel/type from its name+form+review+ships text."""
    t = text.lower()
    for label, kws in _PLAN_TYPE_BUCKETS:
        if any(k in t for k in kws):
            return label
    return "Other"


def transform_plan(body_html: str) -> str:
    """Plan-only: normalise the plan into a decision-first operator surface.

    Three passes, applied uniformly regardless of how the markdown is nested:
      1. Un-bury any hand-authored "reference" <details> wrapper (some plans bury
         Budget / Open questions inside one giant collapsible).
      2. Rewrite the asset-list TABLE into per-asset CARDS, phase-grouped when the
         plan uses named phases. The markdown table stays authoritative upstream
         (check-state parses Plan Ships <-> asset.yaml ship:true <-> gallery
         tiles); per-asset status + cut/transferred routing come from the "Status
         snapshot" table (single source of truth) with a per-row keyword fallback.
      3. Apply a section policy: collapse AI/process-internal sections (roster,
         fast-lane, workflows, protocols, version history...), highlight Open
         questions, leave operator-facing sections (phasing, assets, budget) open.
    Defensive: any structure mismatch leaves that region untouched."""

    smap = _build_plan_status_map(body_html)
    workstreams = {}  # type_label -> [ {target, phase, cls} ] for the channel summary

    def _text(frag):
        return _plan_text(frag)

    def _is_dash(val):
        return _text(val) in ("", "—", "-", "–")

    def _norm_phase(phase_cell):
        """Normalise a Phase cell to a terse group key: keep the lead label, drop
        the parenthetical / colon-qualifier / bold (e.g. 'Sales kit (Wk 3)' ->
        'Sales kit'; 'Wk 1 demo: ASAP; actual ...' -> 'Wk 1 demo')."""
        t = re.split(r"\s*[(:;]\s*", _text(phase_cell))[0]
        return t.strip("* ").strip()

    def _build_card(cells, idx, group_label=None):
        def col(*names):
            for n in names:
                if n in idx and idx[n] < len(cells):
                    return cells[idx[n]].strip()
            return ""

        asset_raw = col("asset")
        num_txt = _text(col("#"))
        name_html = asset_raw.replace("~~", "").strip()
        ships = col("ships")
        owner = col("owner", "owner agent")
        phase = col("phase")
        target = col("target", "target date")
        review = col("review format", "review shape")
        copyf = col("copy file")
        deps = col("depends on")
        form = col("form")
        notes = col("notes")
        notes_txt = _text(notes)
        # A misaligned row (markdown pads short rows to header width, so a row
        # missing a cell silently shifts columns) — positional columns past the
        # first two become unreliable. Tell-tale: the NORMALISED phase is a bare
        # date (dates belong in Target; a real phase that merely mentions a date
        # in its parenthetical is fine — that's stripped before this check).
        phase_norm = _norm_phase(phase) if "phase" in idx else ""
        malformed = ("phase" in idx) and (
            len(cells) != len(idx) or bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", phase_norm))
        )

        kind, pill, status_cls = "live", "", ""
        sm = smap.get(num_txt) if num_txt.isdigit() else None
        if sm:
            cls, lbl, emo, archived = sm
            kind = "archived" if archived else "live"
            status_cls = cls
            pill = f'<span class="pill pill--{cls}">{emo} {lbl}</span>'
        else:
            # Fallback for plans with no Status-snapshot table.
            blob = (notes_txt + " " + _text(target)).lower()
            if "transfer" in blob:
                kind, pill, status_cls = "archived", '<span class="pill pill--transfer">➡️ Transferred</span>', "transfer"
            elif "cut" in blob or "~~" in asset_raw or (_is_dash(form) and _is_dash(owner)):
                kind, pill, status_cls = "archived", '<span class="pill pill--cut">❌ Cut</span>', "cut"
            elif _text(target).lower() == "shipped":
                pill, status_cls = '<span class="pill pill--shipped">🟢 Shipped</span>', "shipped"
            else:
                for emo, lbl, cls in (("✅", "Approved", "ok"), ("🟡", "In review", "review"),
                                      ("🔵", "In progress", "prog"), ("⏸", "Queued", "queued")):
                    if emo in notes_txt:
                        pill, status_cls = f'<span class="pill pill--{cls}">{emo} {lbl}</span>', cls
                        break

        num_badge = f"#{num_txt}" if num_txt.isdigit() else (num_txt or "•")

        # Channel/type bucket: prefer the asset table's own family heading (the Plan's
        # grouping) when present; else the keyword heuristic. Malformed -> Other.
        if malformed:
            type_label = "Other"
        elif group_label:
            type_label = group_label
        else:
            type_label = _plan_asset_type(" ".join((name_html, form, review, ships)))

        # 1) Description (the deliverable) + variation count from the review bracket.
        desc_html = ""
        if not malformed and not _is_dash(form):
            desc = form
            vb = re.search(r"\[([^\]]+)\]", review)
            if vb:
                desc += f' <span class="asset-card__vars">{vb.group(1)}</span>'
            desc_html = f'<div class="asset-card__desc">{desc}</div>'

        # 2) Output format(s): the Ships manifest, else file-format tokens from the
        #    form, else a coarse label from the type bucket. Always shows something.
        out_val = ""
        if not malformed:
            if not _is_dash(ships):
                out_val = ships
            else:
                src, fmts = f"{name_html} {form}", []
                for tok in _FMT_TOKENS:
                    if re.search(r"\b" + tok + r"\b", src, re.I) and tok not in fmts:
                        fmts.append(tok)
                out_val = ", ".join(fmts) or _TYPE_OUTPUT.get(type_label, "")
        out_html = (f'<div class="asset-card__out"><span class="asset-card__out-label">'
                    f'Output</span> {out_val}</div>') if out_val else ""

        # 3) Everything else -> lozenges.
        chips = []
        if not malformed:
            for label, val in (("Owner", owner), ("Phase", phase), ("Target", target),
                               ("Depends", deps), ("Copy", copyf)):
                if not _is_dash(val):
                    chips.append(f'<span class="asc-chip"><span class="asc-chip__k">{label}</span>{val}</span>')
        meta_html = f'<div class="asset-card__meta">{"".join(chips)}</div>' if chips else ""

        notes_html = ""
        if notes_txt:
            notes_html = ('<details class="asset-card__notes"><summary>Notes</summary>'
                          f'<div>{notes}</div></details>')

        card = (f'<div class="asset-card asset-card--{kind}">'
                '<div class="asset-card__head">'
                f'<span class="asset-card__num">{num_badge}</span>'
                f'<span class="asset-card__name">{name_html}</span>'
                f'{pill}</div>'
                f'{desc_html}{out_html}{meta_html}{notes_html}</div>')
        if kind == "live":
            workstreams.setdefault(type_label, []).append(
                {"target": _text(target), "phase": _text(phase), "cls": status_cls,
                 "name": _text(name_html)})
        return kind, type_label, card

    # ---- v3 asset table (2026-07): one list, Type/Channel/Wave, group-by toggle ----
    # Wave (dependency tier) + stage (Launch/Ongoing) come from the shared
    # `plan_model` — the single source of truth this renderer and the asset
    # gallery both read, so the two surfaces can never disagree.
    def _render_v3(idx, rows_cells):
        def cell(cells, *names):
            for n in names:
                if n in idx and idx[n] < len(cells):
                    return cells[idx[n]]
            return ""

        rows, seq = [], 0
        for cells in rows_cells:
            typ = _text(cell(cells, "type")).lower()
            is_setup = typ.startswith("setup") or typ.startswith("task") or typ == "s"
            rid = _text(cell(cells, "#")).lstrip("#").strip()
            if rid in ("", "—", "-", "–"):
                seq += 1
                rid = f"S{seq}"
            name = cell(cells, "asset", "item").replace("~~", "").strip()
            deps_txt = _text(cell(cells, "depends on", "depends", "deps"))
            deps = plan_model.parse_deps(deps_txt)
            phase = _text(cell(cells, "phase"))
            notes = cell(cells, "notes")
            notes_txt = _text(notes)
            # Stage classified from the PHASE cell only (Notes can say "weekly
            # template" on a Launch asset) — via the shared plan_model.
            stage = plan_model.classify_stage(phase)
            ships = cell(cells, "ships")
            channel = _text(cell(cells, "channel")) or _plan_asset_type(
                " ".join((name, _text(cell(cells, "form")), _text(ships))))
            rows.append({
                "id": rid, "is_setup": is_setup, "name": name,
                "desc": _text(cell(cells, "description", "desc")),
                "ships": ships, "owner": _text(cell(cells, "owner", "owner agent")),
                "channel": channel, "stage": stage, "deps": deps, "deps_txt": deps_txt,
                "form": _text(cell(cells, "form")), "review": _text(cell(cells, "review shape")),
                "copyf": _text(cell(cells, "copy file")),
                "target": _text(cell(cells, "target", "target date")),
                "phase": phase, "notes": notes, "notes_txt": notes_txt,
            })
        plan_model.compute_waves(rows)

        def _status(r):
            info = smap.get(r["id"]) if r["id"].isdigit() else None
            if info:
                cls, lbl = info[0], info[1]
            else:
                cls, lbl = "queued", "Queued"
                b = r["notes_txt"].lower()
                for k, c, l in (("approv", "ok", "Approved"), ("brand-pass", "ok", "Approved"),
                                ("in review", "review", "In review"), ("produced", "review", "In review"),
                                ("in prod", "prog", "In production"), ("production", "prog", "In production"),
                                ("in progress", "prog", "In production"), ("shipped", "shipped", "Shipped"),
                                ("live", "shipped", "Live"), ("pending", "queued", "Pending")):
                    if k in b:
                        cls, lbl = c, l
                        break
            return f'<span class="pill pill--{cls}">{lbl}</span>'

        body = []
        for r in rows:
            tp = ('<span class="tpill tpill--setup">Setup</span>' if r["is_setup"]
                  else '<span class="tpill tpill--asset">Asset</span>')
            rid_l = f' <span class="rid">#{r["id"]}</span>' if r["id"].isdigit() else ""
            item = f'<span class="rnm">{r["name"]}</span>{rid_l}'
            if r["desc"]:
                item += f'<span class="rds">{html_lib.escape(r["desc"])}</span>'
            extra = []
            for lab, val in (("Form", r["form"]), ("Review", r["review"]),
                             ("Copy file", r["copyf"]), ("Target", r["target"]),
                             ("Phase", r["phase"])):
                if val and val not in ("—", "-", "–", ""):
                    extra.append(f'<b>{lab}:</b> {html_lib.escape(val)}')
            if r["notes_txt"]:
                extra.append(f'<b>Notes:</b> {r["notes"]}')
            if extra:
                item += ('<details class="row-more"><summary>details</summary>'
                         f'<div>{" · ".join(extra)}</div></details>')
            out = r["ships"] if not _is_dash(r["ships"]) else "—"
            wv = f'Wave {r["wave"]}' if r["wave"] else "—"
            body.append(
                f'<tr data-stage="{r["stage"]}" data-channel="{html_lib.escape(r["channel"])}" '
                f'data-wave="{r["wave"] or 0}" data-type="{"setup" if r["is_setup"] else "asset"}" '
                f'data-id="{html_lib.escape(r["id"])}">'
                f'<td class="c-type">{tp}</td>'
                f'<td class="c-item">{item}</td>'
                f'<td class="c-out">{out}</td>'
                f'<td class="c-own">{html_lib.escape(r["owner"]) or "—"}</td>'
                f'<td class="c-chan">{html_lib.escape(r["channel"])}</td>'
                f'<td class="c-wave">{wv}</td>'
                f'<td class="c-dep">{html_lib.escape(r["deps_txt"]) or "—"}</td>'
                f'<td class="c-stat">{_status(r)}</td></tr>')

        head = ('<tr><th>Type</th><th>Item</th><th>Output</th><th>Owner</th>'
                '<th>Channel</th><th>Wave</th><th>Depends</th><th>Status</th></tr>')
        toggle = ('<div class="plan-toggle"><span class="plan-toggle__lbl">Group by</span>'
                  '<button type="button" class="pt-btn is-on" data-group="channel">Channel</button>'
                  '<button type="button" class="pt-btn" data-group="wave">Wave</button></div>')
        return (f'<div class="plan-v3" data-by="channel">{toggle}'
                f'<table class="pv3"><thead>{head}</thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>{_PLAN_V3_JS}')

    def _transform_table(table, group_label=None):
        thead = re.search(r"<thead>(.*?)</thead>", table, re.DOTALL)
        if not thead:
            return table
        headers = [_text(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(1), re.DOTALL)]
        if "asset" not in headers or sum(1 for h in headers if h in _PLAN_COLS) < 3:
            return table
        idx = {h: i for i, h in enumerate(headers)}
        tbody = re.search(r"<tbody>(.*?)</tbody>", table, re.DOTALL)
        if not tbody:
            return table
        # v3: a `type` column opts the plan into the one-list channel/wave table.
        # Legacy plans (no type column) keep the phase-grouped card view below.
        if "type" in idx:
            rc = [re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
                  for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tbody.group(1), re.DOTALL)]
            return _render_v3(idx, [c for c in rc if c])
        archived = []
        groups = {}  # type_label -> [cards]
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tbody.group(1), re.DOTALL):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            if not cells:
                continue
            kind, type_label, card = _build_card(cells, idx, group_label)
            if kind == "archived":
                archived.append(card)
            else:
                groups.setdefault(type_label, []).append(card)
        if not groups and not archived:
            return table
        # Group live cards by channel/type, in canonical display order.
        order = [t for t in _PLAN_TYPE_ORDER if t in groups]
        order += [t for t in groups if t not in _PLAN_TYPE_ORDER]
        out = ""
        for label in order:
            cards = groups[label]
            out += ('<div class="asset-group"><div class="asset-group__head">'
                    f'<span class="asset-group__title">{html_lib.escape(label)}</span>'
                    f'<span class="asset-group__count">{len(cards)}</span></div>'
                    f'<div class="asset-cards">{"".join(cards)}</div></div>')
        if archived:
            out += ('<details class="asset-cards-archived">'
                    f'<summary>Cut &amp; transferred — {len(archived)} not in the live build</summary>'
                    f'<div class="asset-cards">{"".join(archived)}</div></details>')
        return out

    def _ws_timing(items):
        """Derive a timing span for a channel: prefer 'Wk N' labels, else dates."""
        weeks = []
        for it in items:
            weeks += [int(w) for w in re.findall(r"[Ww]k\s*(\d+)", it["target"] + " " + it["phase"])]
        if weeks:
            lo, hi = min(weeks), max(weeks)
            return f"Wk {lo}" if lo == hi else f"Wk {lo}–{hi}"
        dates = [d for it in items for d in re.findall(r"\d{4}-\d{2}-\d{2}", it["target"])]
        if dates:
            lo, hi = min(dates), max(dates)
            return lo if lo == hi else f"{lo} → {hi}"
        return "—"

    def _ws_desc(items):
        """What's happening in this channel — the full asset names, untruncated.

        Operator directive 2026-06-15: "What's happening should not be truncated,
        rather use more description (not less)." So show EVERY asset in the channel
        at full length — no per-name char cap, no first-3 limit, no '+N more'
        elision. The .ws-row__desc CSS wraps (line-height 1.45), so a fuller cell
        just grows taller, which is what the operator wants."""
        names = []
        for it in items:
            nm = it["name"].strip()
            if nm and nm not in names:
                names.append(nm)
        if not names:
            return "—"
        return html_lib.escape(" · ".join(names))

    def _build_workstreams_html():
        if not workstreams:
            return ""
        order = [t for t in _PLAN_TYPE_ORDER if t in workstreams]
        order += [t for t in workstreams if t not in _PLAN_TYPE_ORDER]
        rows = ""
        for label in order:
            items = workstreams[label]
            rows += ('<div class="ws-row">'
                     f'<span class="ws-row__ch">{html_lib.escape(label)}</span>'
                     f'<span class="ws-row__desc">{_ws_desc(items)}</span>'
                     f'<span class="ws-row__n">{len(items)} asset{"s" if len(items) != 1 else ""}</span>'
                     f'<span class="ws-row__t">{html_lib.escape(_ws_timing(items))}</span></div>')
        return ('<div class="workstreams"><div class="ws-row ws-row--head">'
                '<span class="ws-row__ch">Channel</span><span class="ws-row__desc">What’s happening</span>'
                '<span class="ws-row__n">Assets</span><span class="ws-row__t">Timing</span></div>'
                + rows + '</div>')

    def _apply_section_policy(html):
        """Collapse AI/process sections, highlight Open questions, move history /
        audit sections to the bottom; leave operator-facing sections in place."""
        out, tail = [], []
        for part in re.split(r"(?=<h2)", html):
            hm = re.match(r"<h2[^>]*>(.*?)</h2>", part, re.DOTALL)
            if not hm:
                out.append(part)
                continue
            title_html = hm.group(1)
            rest = part[hm.end():]
            trail = ""  # keep trailing <hr> separators outside any wrapper
            tm = re.search(r"((?:<hr\s*/?>\s*)+)$", rest)
            if tm:
                trail, rest = tm.group(1), rest[:tm.start()]
            title_l = _text(title_html).lower()
            action = _classify_plan_section(title_l)
            collapsed = (f'<details class="plan-collapsed"><summary>{title_html}'
                         f'</summary>{rest}</details>')
            if "phasing" in title_l and workstreams_html:
                # Reframe the rollout-timeline Phasing table as channel workstreams;
                # keep the original rollout table as a collapsed reference.
                out.append('<h2>Channel workstreams</h2>' + workstreams_html
                           + '<details class="plan-collapsed"><summary>Rollout timeline (reference)'
                           f'</summary>{rest}</details>{trail}')
            elif action == "highlight":
                out.append(f'<div class="plan-oq"><h2>{title_html}</h2>{rest}</div>{trail}')
            elif action == "collapse":
                out.append(collapsed + trail)
            elif action == "history":
                tail.append(collapsed)
            else:
                out.append(part)
        if tail:
            out.append('<hr/><p class="plan-tail-label">📜 History &amp; audit trail</p>')
            out.extend(tail)
        return "".join(out)

    # 1) Un-bury any hand-authored "reference" <details> wrapper (runs before the
    #    card transform, so the generated archived-cards <details> is untouched).
    body_html = re.sub(r"<summary\b[^>]*>.*?</summary>", "", body_html, flags=re.DOTALL)
    body_html = re.sub(r"</?details\b[^>]*>", "", body_html)
    # 2) Asset table(s) -> channel-grouped cards (also fills `workstreams`). When an
    #    asset sub-table is directly preceded by its own <h3> family heading (the
    #    Plan's grouping), use that heading as the channel instead of the keyword
    #    heuristic — so the workstreams table + cards mirror the Plan's groups.
    def _clean_group(raw):
        t = _text(raw)
        t = re.sub(r"^[A-Za-z0-9]+\s*[·:.\-]\s*", "", t)   # drop a leading "A · " ordinal
        t = re.sub(r"\s*[\(（].*$", "", t)                   # drop a "(qualifier)" suffix
        return t.strip()
    def _table_with_heading(m):
        grp = m.group("grp")
        label = _clean_group(grp) if grp else None
        return (m.group("head") or "") + _transform_table(m.group("table"), label)
    body_html = re.sub(
        r"(?P<head><h3[^>]*>(?P<grp>.*?)</h3>\s*)?(?P<table><table[^>]*>.*?</table>)",
        _table_with_heading, body_html, flags=re.DOTALL)
    workstreams_html = _build_workstreams_html()
    # 3) Section policy: collapse/highlight, history -> bottom, Phasing -> workstreams.
    body_html = _apply_section_policy(body_html)
    return body_html


def stamp_last_updated(markdown_text: str) -> str:
    """Auto-stamp the `**Last updated**:` line with the current local date + time.

    The cross-surface index/tasks timestamps were hand-authored and drifted stale.
    Render fires on every state change (CM write + Stop hook), so render time is a
    faithful proxy for "last meaningfully updated". Format: YYYY-MM-DD HH:MM (local,
    24h). No-op if the file has no Last-updated line.
    """
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return re.sub(r"(\*\*Last updated\*\*:)[^\n]*", lambda m: f"{m.group(1)} {stamp}", markdown_text)


def extract_operator_panels(markdown_text: str) -> tuple[str, str]:
    """For asset-preview template — extract operator-action H2 sections into a
    sidebar panel and strip them from the body so they don't render twice.

    Detects H2 sections matching: "Open questions" / "What the operator does next" /
    "Operator review" / similar keywords (operator / open question / next step / decision).

    Returns (body_without_panels, panels_html). Body_without_panels is the original
    markdown with the operator H2 blocks removed; panels_html is the rendered HTML
    of those sections wrapped in a single `<div class="operator-panels-inner">`.

    Operator caught this 2026-06-04: "any questions and next steps go in the right
    hand panel, not the asset area".
    """
    operator_keywords = ["operator", "open question", "next step", "decision"]
    exclusion_keywords = ["brand manager", "flags for brand", "self-qa", "brand verdict"]

    # Find all H2 headers + their positions
    h2_pattern = re.compile(r"^##\s+(.+?)$", re.MULTILINE)
    matches = list(h2_pattern.finditer(markdown_text))
    if not matches:
        return markdown_text, ""

    panel_blocks: list[tuple[str, str]] = []  # (header, body_md)
    spans_to_strip: list[tuple[int, int]] = []  # (start, end) in markdown_text

    for i, m in enumerate(matches):
        header = m.group(1).strip()
        header_lower = header.lower()
        if any(ex in header_lower for ex in exclusion_keywords):
            continue
        if not any(kw in header_lower for kw in operator_keywords):
            continue
        # Section spans from this H2 to the next H2 (or EOF)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
        section_md = markdown_text[start:end]
        # The header line + body (without the leading ## line for re-rendering)
        body_part = re.sub(r"^##\s+.+\n", "", section_md, count=1)
        panel_blocks.append((header, body_part.strip()))
        spans_to_strip.append((start, end))

    if not panel_blocks:
        return markdown_text, ""

    # Strip the sections from the body (in reverse so positions stay valid)
    body_md = markdown_text
    for start, end in reversed(spans_to_strip):
        body_md = body_md[:start] + body_md[end:]

    # Build panels HTML
    panel_html_parts = ['<div class="operator-panels-inner">']
    panel_html_parts.append('<div class="operator-panels-title">For your action</div>')
    for header, body_md_part in panel_blocks:
        kind = "questions" if "question" in header.lower() else "next-steps"
        icon = "🟠" if kind == "questions" else "🎯"
        rendered_body = convert_markdown(body_md_part)
        panel_html_parts.append(
            f'<section class="operator-panel operator-panel--{kind}">'
            f'<h3 class="operator-panel__heading"><span class="operator-panel__icon" aria-hidden="true">{icon}</span> {header}</h3>'
            f'<div class="operator-panel__body">{rendered_body}</div>'
            f'</section>'
        )
    panel_html_parts.append('</div>')
    return body_md, "".join(panel_html_parts)


def convert_markdown(markdown_text: str) -> str:
    """Convert markdown body to HTML using extensions for tables, fenced code, etc.

    Pre-processes bare <details> tags to add markdown="1" so markdown inside the
    collapsible block (tables, lists, **bold**, etc.) actually parses. The
    python-markdown md_in_html extension (included in `extra`) requires this
    attribute explicitly — without it, the inside is treated as raw HTML and any
    markdown syntax leaks through unparsed.
    """
    # Add markdown="1" to bare <details> (preserves any tag that already has attributes)
    markdown_text = re.sub(r"<details>(\s)", r'<details markdown="1">\1', markdown_text)
    return md.markdown(
        markdown_text,
        extensions=["extra", "tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
    )


def _campaign_root_of(path: Path) -> "Path | None":
    """SYS-089 — the campaigns/<slug>/ dir a file lives under (else None). Used to inject the
    Campaign DNA header on artifact surfaces (brief/insight/concept/plan) from campaign.yaml."""
    p = path.resolve()
    for d in [p.parent, *p.parents]:
        if d.parent.name == "campaigns":
            return d
    return None


def find_project_root(path: Path) -> Path:
    """Walk up until we find the dir containing 'campaigns/' — the Marketing AI System root."""
    p = path.resolve()
    for parent in [p, *p.parents]:
        if (parent / "campaigns").is_dir() and (parent / "tenant-brand").is_dir():
            return parent
    return p.parent  # fallback


def humanize_slug(slug: str) -> str:
    """Turn 'the-signal-amp-2026q2' into 'The Signal Amp 2026q2'. Strip .html / .md."""
    name = slug.replace(".html", "").replace(".md", "")
    return " ".join(w.capitalize() for w in name.replace("_", "-").split("-"))


def build_breadcrumb(output_path: Path, project_root: Path) -> str:
    """Generate breadcrumb HTML from output_path relative to project_root.

    Conventions:
      - 🏠 All Campaigns → campaigns/index.html (always present)
      - tenant-brand/<slug>.html → 🏠 › Brand: <Slug>
      - campaigns/index.html → 🏠 (current, no link)
      - campaigns/tasks.html → 🏠 › Tasks Queue
      - campaigns/<slug>/dashboard.html → 🏠 › <Campaign> (current)
      - campaigns/<slug>/<file>.html → 🏠 › <Campaign> › <File>
      - campaigns/<slug>/concepts/concept-trio.html → 🏠 › <Campaign> › Concepts › Trio
      - campaigns/<slug>/assets/<asset-slug>/preview.html → 🏠 › <Campaign> › Assets › <Asset>
    """
    try:
        rel = output_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return f'<span class="crumb">Marketing AI System</span>'

    parts = rel.parts
    crumbs: list[tuple[str, str | None]] = []  # (label, href-relative-to-output or None)

    # Compute href from output_path to a target absolute-from-root path
    def href_to(target_rel: str) -> str:
        target = project_root / target_rel
        return os.path.relpath(target, output_path.parent).replace("\\", "/")

    # Always start with Home
    home_href = href_to("campaigns/index.html")
    crumbs.append(("🏠 All Campaigns", home_href if rel.as_posix() != "campaigns/index.html" else None))

    if parts[0] == "tenant-brand":
        if len(parts) >= 2:
            tenant = parts[1].replace(".html", "").replace(".md", "")
            crumbs.append((f"Brand: {humanize_slug(tenant)}", None))
    elif parts[0] == "campaigns":
        if len(parts) == 2 and parts[1] == "index.html":
            pass  # already home, current
        elif len(parts) == 2 and parts[1] == "tasks.html":
            crumbs.append(("Tasks Queue", None))
        elif len(parts) >= 2 and parts[1] not in ("index.html", "tasks.html"):
            # Inside a specific campaign
            campaign_slug = parts[1]
            campaign_label = humanize_slug(campaign_slug)
            dash_href = href_to(f"campaigns/{campaign_slug}/dashboard.html")
            # If this IS the dashboard, no link
            is_dashboard = len(parts) == 3 and parts[2] == "dashboard.html"
            crumbs.append((campaign_label, None if is_dashboard else dash_href))

            if not is_dashboard and len(parts) >= 3:
                sub = parts[2]
                if sub == "concepts" and len(parts) >= 4:
                    crumbs.append(("Concepts", None))
                    fname = parts[3].replace(".html", "")
                    if fname not in ("concept-trio",):
                        crumbs.append((humanize_slug(fname), None))
                    else:
                        crumbs.append(("Trio", None))
                elif sub == "assets" and len(parts) >= 5:
                    crumbs.append(("Assets", None))
                    asset_slug = parts[3]
                    asset_label = humanize_slug(asset_slug)
                    asset_preview_href = href_to(f"campaigns/{campaign_slug}/assets/{asset_slug}/preview.html")
                    is_preview = parts[4] == "preview.html"
                    crumbs.append((asset_label, None if is_preview else asset_preview_href))
                    if not is_preview:
                        crumbs.append((humanize_slug(parts[4]), None))
                else:
                    # Simple file inside campaign dir (brief.html, plan.html, etc.)
                    fname = sub.replace(".html", "")
                    crumbs.append((humanize_slug(fname), None))

    # Render
    html_parts = []
    for i, (label, href) in enumerate(crumbs):
        if i > 0:
            html_parts.append('<span class="crumb-sep">›</span>')
        if href:
            html_parts.append(f'<a class="crumb crumb-link" href="{href}">{label}</a>')
        else:
            html_parts.append(f'<span class="crumb crumb-current">{label}</span>')
    # (Help & guides now lives in the top-right pill nav alongside Library — see
    # build_library_nav — so every surface's header is consistent.)
    return "".join(html_parts)


# =============================================================================
# In-situ mockup rendering (per docs/specs/per-step-brief.md §9 dual-view rule)
# =============================================================================

def _esc(s) -> str:
    """HTML-escape a value, stringifying None as empty."""
    if s is None:
        return ""
    return html_lib.escape(str(s))


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Truncate to max_chars at the last word boundary inside the window, append ellipsis if cut."""
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    # Pull back to last whitespace so we don't cut a word
    space = cut.rfind(" ")
    if space > max_chars * 0.6:  # only honour the word boundary if it's not too aggressive
        cut = cut[:space]
    return cut.rstrip(",.;:— ") + "…"


def _strip_post_frontmatter(raw: str) -> str:
    """If a post file starts with a markdown # heading + metadata, strip everything up to and
    including the first standalone `---` separator. Treats the rest as the body. If no
    standalone separator is present, returns the file as-is (Producer convention is
    body-only files; but we tolerate annotated files like asset-03's shape-b/post.md)."""
    lines = raw.splitlines()
    # Look for a `---` line in the first ~12 lines that follows a `#`-heading line
    if not lines or not lines[0].lstrip().startswith("#"):
        return raw
    for i, line in enumerate(lines[:15]):
        if line.strip() == "---" and i > 0:
            return "\n".join(lines[i + 1:]).lstrip("\n")
    return raw


def _load_post_text(variant: dict, base_dir: Path) -> str:
    """Resolve a variant's post body — `post_text` inline wins, else read `post_path` / `body_path`."""
    if variant.get("post_text"):
        return variant["post_text"]
    path_key = "post_path" if variant.get("post_path") else ("body_path" if variant.get("body_path") else None)
    if path_key:
        p = (base_dir / variant[path_key]).resolve()
        if p.exists():
            raw = p.read_text(encoding="utf-8")
            return _strip_post_frontmatter(raw)
        print(f"WARN: {path_key} not found: {p}", file=sys.stderr)
    return ""


def _post_text_to_paragraphs(text: str) -> str:
    """Convert plain-text post body to <p>...</p> blocks. Preserves <br> for single line breaks within a paragraph."""
    if not text:
        return ""
    blocks = re.split(r"\n\s*\n", text.strip())
    out = []
    for block in blocks:
        if not block.strip():
            continue
        # Single newlines inside a block become <br>
        inner = _esc(block).replace("\n", "<br>")
        out.append(f"<p>{inner}</p>")
    return "\n".join(out)


def _li_header(common: dict) -> str:
    """LinkedIn post header (avatar + author + meta + ···)."""
    return (
        f'<div class="li-header">'
        f'  <div class="li-avatar">{_esc(common.get("author_initials") or "??")}</div>'
        f'  <div class="li-author">'
        f'    <div class="li-author-name">{_esc(common.get("author") or "Author")}</div>'
        f'    <div class="li-author-title">{_esc(common.get("author_title") or "")}</div>'
        f'    <div class="li-author-meta">{_esc(common.get("author_meta") or "")}</div>'
        f'  </div>'
        f'  <div class="li-more">···</div>'
        f'</div>'
    )


def _li_reactions_and_actions(common: dict) -> str:
    r = common.get("reactions") or {}
    names = r.get("names") or ""
    count = r.get("count")
    right = f"{count} comments" if (count := common.get("comments_count")) else ""
    summary = ""
    if names or r.get("count"):
        n = f"{_esc(names)}" if names else ""
        extra = f" and {r['count']} others" if r.get("count") else ""
        summary = f'<span style="margin-left:6px;">{n}{_esc(extra)}</span>'
    return (
        f'<div class="li-reactions">'
        f'  <div class="li-reactions-left">'
        f'    <span class="li-reaction-icons"><span class="li-r-like">👍</span><span class="li-r-insight">💡</span><span class="li-r-celebrate">🎉</span></span>'
        f'    {summary}'
        f'  </div>'
        f'  <div>{_esc(right)}</div>'
        f'</div>'
        f'<div class="li-actions">'
        f'  <div class="li-action">👍 Like</div>'
        f'  <div class="li-action">💬 Comment</div>'
        f'  <div class="li-action">🔁 Repost</div>'
        f'  <div class="li-action">📤 Send</div>'
        f'</div>'
    )


def _li_comments(common: dict) -> str:
    comments = common.get("comments") or []
    if not comments:
        return ""
    rows = []
    for c in comments:
        initials = (c.get("initials") or "".join(w[0].upper() for w in (c.get("author") or "A").split()[:2]))
        rows.append(
            f'<div class="li-comment">'
            f'  <div class="li-c-avatar">{_esc(initials)}</div>'
            f'  <div class="li-c-body">'
            f'    <div class="li-c-author">{_esc(c.get("author") or "")}</div>'
            f'    {_esc(c.get("body") or "")}'
            f'    <div class="li-c-meta">{_esc(c.get("meta") or "")}</div>'
            f'  </div>'
            f'</div>'
        )
    return f'<div class="li-comments">{"".join(rows)}</div>'


def _render_linkedin_post(variant: dict, common: dict, base_dir: Path) -> str:
    """One LinkedIn variant → collapsed + expanded card pair."""
    post_text = _load_post_text(variant, base_dir)
    collapsed_chars = variant.get("collapsed_chars") or DEFAULT_COLLAPSED_CHARS["linkedin-post"]
    teaser = _truncate_at_word(post_text, collapsed_chars)

    tile_path = variant.get("tile_path")
    tile_alt = variant.get("tile_alt") or "Asset tile"
    tile_html = (
        f'<img class="li-image" src="{_esc(tile_path)}" alt="{_esc(tile_alt)}">' if tile_path else ""
    )

    header = _li_header(common)
    reactions = _li_reactions_and_actions(common)
    comments = _li_comments(common)

    collapsed = (
        f'<div class="mock-state">'
        f'  <div class="mock-state__label">Collapsed · in feed</div>'
        f'  <div class="li-card">'
        f'    {header}'
        f'    <div class="li-body"><p>{_esc(teaser)}</p></div>'
        f'    <div class="li-see-more">…see more</div>'
        f'    {tile_html}'
        f'    {reactions}'
        f'  </div>'
        f'</div>'
    )
    expanded = (
        f'<div class="mock-state">'
        f'  <div class="mock-state__label">Expanded · clicked open</div>'
        f'  <div class="li-card">'
        f'    {header}'
        f'    <div class="li-body">{_post_text_to_paragraphs(post_text)}</div>'
        f'    {tile_html}'
        f'    {reactions}'
        f'    {comments}'
        f'  </div>'
        f'</div>'
    )
    return collapsed + expanded


def _email_inbox_row(variant: dict, common: dict) -> str:
    """Email collapsed state: inbox row (sender · subject — preview · date)."""
    subj = variant.get("subject") or "(no subject)"
    preview = _truncate_at_word(variant.get("preview_text") or "", DEFAULT_COLLAPSED_CHARS["email"])
    return (
        f'<div class="em-card">'
        f'  <div class="em-inbox-toolbar">Inbox</div>'
        f'  <div class="em-inbox-row">'
        f'    <div class="em-star">☆</div>'
        f'    <div class="em-from">{_esc(common.get("from_name") or "Sender")}</div>'
        f'    <div class="em-snippet"><b>{_esc(subj)}</b> <span class="em-preview">— {_esc(preview)}</span></div>'
        f'    <div class="em-date">{_esc(common.get("sent_date") or "")}</div>'
        f'  </div>'
        f'</div>'
    )


def _email_opened(variant: dict, common: dict, base_dir: Path) -> str:
    body_text = _load_post_text(variant, base_dir)
    if variant.get("body_html"):
        body_html = variant["body_html"]
    elif body_text:
        body_html = convert_markdown(body_text)
    else:
        body_html = "<p><em>(no body)</em></p>"
    initials = common.get("from_initials") or "".join(w[0].upper() for w in (common.get("from_name") or "S").split()[:2])
    return (
        f'<div class="em-card">'
        f'  <div class="em-opened-header">'
        f'    <h1 class="em-subject">{_esc(variant.get("subject") or "(no subject)")}</h1>'
        f'    <div class="em-meta-row">'
        f'      <div class="em-sender-avatar">{_esc(initials)}</div>'
        f'      <div>'
        f'        <div class="em-sender-name">{_esc(common.get("from_name") or "")}</div>'
        f'        <div class="em-sender-email">{_esc(common.get("from_email") or "")}</div>'
        f'      </div>'
        f'      <div class="em-sent-meta">{_esc(common.get("sent_date") or "")}</div>'
        f'    </div>'
        f'  </div>'
        f'  <div class="em-opened-body">{body_html}</div>'
        f'</div>'
    )


def _render_email(variant: dict, common: dict, base_dir: Path) -> str:
    collapsed = (
        f'<div class="mock-state">'
        f'  <div class="mock-state__label">Collapsed · inbox row</div>'
        f'  {_email_inbox_row(variant, common)}'
        f'</div>'
    )
    expanded = (
        f'<div class="mock-state">'
        f'  <div class="mock-state__label">Expanded · opened</div>'
        f'  {_email_opened(variant, common, base_dir)}'
        f'</div>'
    )
    return collapsed + expanded


def _render_twitter_post(variant: dict, common: dict, base_dir: Path) -> str:
    post_text = _load_post_text(variant, base_dir)
    teaser = _truncate_at_word(post_text, DEFAULT_COLLAPSED_CHARS["twitter-post"])
    tile = variant.get("tile_path")
    tile_html = f'<img class="tw-image" src="{_esc(tile)}" alt="{_esc(variant.get("tile_alt") or "")}">' if tile else ""
    header = (
        f'<div class="tw-header">'
        f'  <div class="tw-avatar">{_esc(common.get("author_initials") or "??")}</div>'
        f'  <div>'
        f'    <div class="tw-name">{_esc(common.get("author") or "")}</div>'
        f'    <div class="tw-handle">{_esc(common.get("author_handle") or common.get("author_meta") or "")}</div>'
        f'  </div>'
        f'</div>'
    )
    collapsed_card = f'<div class="tw-card">{header}<div class="tw-body">{_esc(teaser)}</div>{tile_html}</div>'
    expanded_card = f'<div class="tw-card">{header}<div class="tw-body">{_esc(post_text)}</div>{tile_html}</div>'
    return (
        f'<div class="mock-state"><div class="mock-state__label">Collapsed · in timeline</div>{collapsed_card}</div>'
        f'<div class="mock-state"><div class="mock-state__label">Expanded · tweet open</div>{expanded_card}</div>'
    )


def _render_instagram_post(variant: dict, common: dict, base_dir: Path) -> str:
    caption = _load_post_text(variant, base_dir)
    teaser = _truncate_at_word(caption, DEFAULT_COLLAPSED_CHARS["instagram-post"])
    tile = variant.get("tile_path")
    tile_html = f'<img class="ig-image" src="{_esc(tile)}" alt="{_esc(variant.get("tile_alt") or "")}">' if tile else ""
    handle = common.get("author_handle") or common.get("author") or ""
    header = (
        f'<div class="ig-header">'
        f'  <div class="ig-avatar">{_esc((common.get("author_initials") or "?")[:1])}</div>'
        f'  <div class="ig-handle">{_esc(handle)}</div>'
        f'</div>'
    )
    collapsed_card = (
        f'<div class="ig-card">{header}{tile_html}'
        f'<div class="ig-caption"><b>{_esc(handle)}</b>{_esc(teaser)} <span style="color:#8e8e8e;">more</span></div></div>'
    )
    expanded_card = (
        f'<div class="ig-card">{header}{tile_html}'
        f'<div class="ig-caption"><b>{_esc(handle)}</b>{_esc(caption)}</div></div>'
    )
    return (
        f'<div class="mock-state"><div class="mock-state__label">Collapsed · in feed</div>{collapsed_card}</div>'
        f'<div class="mock-state"><div class="mock-state__label">Expanded · post open</div>{expanded_card}</div>'
    )


def _render_substack_feed(variant: dict, common: dict, base_dir: Path) -> str:
    body_text = _load_post_text(variant, base_dir)
    subtitle = variant.get("subtitle") or _truncate_at_word(body_text, DEFAULT_COLLAPSED_CHARS["substack-feed"])
    tile = variant.get("tile_path")
    tile_html = f'<img class="sub-image" src="{_esc(tile)}" alt="{_esc(variant.get("tile_alt") or "")}">' if tile else ""
    title = variant.get("subject") or variant.get("label") or "(no title)"
    pub = common.get("publication") or common.get("author") or ""
    collapsed = (
        f'<div class="mock-state"><div class="mock-state__label">Collapsed · discover card</div>'
        f'<div class="sub-card">'
        f'  <div class="sub-pub">{_esc(pub)}</div>'
        f'  <h1 class="sub-title">{_esc(title)}</h1>'
        f'  <div class="sub-subtitle">{_esc(subtitle)}</div>'
        f'  {tile_html}'
        f'</div></div>'
    )
    body_html = convert_markdown(body_text) if body_text else ""
    expanded = (
        f'<div class="mock-state"><div class="mock-state__label">Expanded · full article</div>'
        f'<div class="sub-card">'
        f'  <div class="sub-pub">{_esc(pub)}</div>'
        f'  <h1 class="sub-title">{_esc(title)}</h1>'
        f'  <div class="sub-subtitle">{_esc(variant.get("subtitle") or "")}</div>'
        f'  {tile_html}'
        f'  <div class="sub-body">{body_html}</div>'
        f'</div></div>'
    )
    return collapsed + expanded


FORM_RENDERERS = {
    "linkedin-post": _render_linkedin_post,
    "email": _render_email,
    "twitter-post": _render_twitter_post,
    "instagram-post": _render_instagram_post,
    "substack-feed": _render_substack_feed,
}


def render_mockups(extra_context: dict, base_dir: Path) -> str:
    """Render the dual-view mockup zone from extra_context.

    extra_context shape:
      {
        "form": "linkedin-post" | "email" | ...,
        "variants": [{ label, post_path | post_text, tile_path, tile_alt, collapsed_chars, ... }],
        + form-specific common fields (author, author_title, from_name, subject, etc.)
      }

    Variants can be omitted; in that case the top-level keys are treated as a single variant.
    Returns the HTML to substitute into the {{ mockups }} placeholder.
    """
    form = extra_context.get("form")
    if not form:
        return ""
    if form not in KNOWN_FORMS:
        return (
            f'<div class="mock-stub-note">Unknown form: <code>{_esc(form)}</code>. '
            f'Supported forms: {", ".join(sorted(KNOWN_FORMS))}.</div>'
        )

    renderer = FORM_RENDERERS[form]
    common = {k: v for k, v in extra_context.items() if k not in ("form", "variants")}

    variants = extra_context.get("variants")
    if not variants:
        # Treat top-level as a single variant
        variants = [common]
        common = {}

    parts = []
    for idx, variant in enumerate(variants):
        label = variant.get("label") or (f"Variant {idx + 1}" if len(variants) > 1 else None)
        label_html = f'<div class="mock-variant__label">{_esc(label)}</div>' if label else ""
        states = renderer(variant, common, base_dir)
        parts.append(
            f'<div class="mock-variant mock-{form.split("-")[0]}">'
            f'  {label_html}'
            f'  <div class="mock-states">{states}</div>'
            f'</div>'
        )
    return "\n".join(parts)


# =============================================================================
# Core render
# =============================================================================

def build_library_nav(output_path: Path, project_root: Path) -> str:
    """Top-right pill nav, identical on every operator surface: Help & guides + Library.

    Both pills are RELATIVE to the output page (work served or opened from disk) and are
    rendered ONLY when their target file exists — so a link here can never 404. In a fresh
    client Seed the library ships EMPTY, so the Library pill is simply omitted until the
    operator builds one (/library-add creates tenant/library/INDEX.html); Help & guides
    (docs/guide/help.html) ships with every deployment, so it is always present. The pill
    for the page you are on gets the --current style.
    """
    def href_to(target_rel: str) -> str:
        target = project_root / target_rel
        return os.path.relpath(target, output_path.parent).replace("\\", "/")

    try:
        rel = output_path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        rel = ""

    links = []
    if (project_root / "docs/guide/help.html").exists():
        cur = " lib-link--current" if rel == "docs/guide/help.html" else ""
        links.append(
            f'<a class="lib-link{cur}" href="{href_to("docs/guide/help.html")}" '
            f'title="Help &amp; guides — deployment, operator guide, FAQ">📖 Help &amp; guides</a>'
        )
    if (project_root / "tenant/library/INDEX.html").exists():
        cur = " lib-link--current" if rel.startswith("tenant/library/") else ""
        links.append(
            f'<a class="lib-link{cur}" href="{href_to("tenant/library/INDEX.html")}" '
            f'title="Best-Practice Library — creative exemplars &amp; gold standards">📚 Best-Practice Library</a>'
        )
    if (project_root / "tenant/research-library/INDEX.html").exists():
        cur = " lib-link--current" if rel.startswith("tenant/research-library/") else ""
        links.append(
            f'<a class="lib-link{cur}" href="{href_to("tenant/research-library/INDEX.html")}" '
            f'title="Insights Library — the shared research corpus the Insights Manager cites">🔎 Insights Library</a>'
        )

    if not links:
        return ""
    return f'<nav class="library-nav" aria-label="Site links">{"".join(links)}</nav>'


# SYS-043 — a render that can't fill a section must SAY so (loudly + visibly),
# never ship an empty one. The operator_actions / cross-surface / status injects
# above each swallow their exception and leave their UPPER_CASE_AUTO sentinel
# un-replaced; as an HTML comment that sentinel then renders INVISIBLE — i.e. a
# silently blank operator section (this is what blanked the campaigns index once).
_RESIDUAL_MARKER_RE = re.compile(
    r"<!--\s*([A-Z0-9_]*(?:_AUTO|_MARKER|AUTO_INJECT)[A-Z0-9_]*)\s*-->"
)


def guard_residual_markers(rendered: str, output_path: Path) -> tuple[str, list[str]]:
    """Fail loud + visible, never silently blank. Scan the FINAL html for any
    left-over auto-inject sentinel; for each, emit a stderr WARN naming the file +
    marker and replace the (invisible) comment with a VISIBLE placeholder so a
    failed section announces itself. Returns (patched_html, [markers found])."""
    found: list[str] = []

    def _sub(m):
        token = m.group(1).strip()
        found.append(token)
        return (
            '<div class="render-warn" role="alert" style="background:#fdeaea;'
            'border:2px solid #e63c3c;color:#a01818;padding:10px 14px;margin:14px 0;'
            'border-radius:6px;font-weight:600;font-family:system-ui,-apple-system,sans-serif;">'
            f'⚠ This section failed to render (unprocessed <code>{html_lib.escape(token)}</code>). '
            'The underlying data is intact — re-render to fix. See the render log.</div>'
        )

    rendered = _RESIDUAL_MARKER_RE.sub(_sub, rendered)
    if found:
        names = ", ".join(dict.fromkeys(found))
        print(f"WARN render-guard: {output_path} shipped with unprocessed marker(s): {names} "
              f"— a section failed to render (now shown as a visible placeholder, not a blank).",
              file=sys.stderr)
    return rendered, found


# SYS-093 — the marker injections below (operator_actions.inject + STATUS/COMPLIANCE/
# RESONANCE) do plain string .replace() on the raw markdown, which also hits a marker
# written INSIDE a code span — e.g. a spec that DOCUMENTS `<!-- PHASES_AUTO -->` in
# backticks (docs/specs/dashboard.md is even classified as a live dashboard by filename).
# Stash code spans before the inject region and restore them before conversion, so a
# documented marker survives and renders as visible code instead of being consumed.
_CODE_SPAN_RE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)


def stash_code_spans(text: str) -> "tuple[str, dict]":
    stash: dict = {}

    def _repl(m):
        key = f"\x00CS{len(stash)}\x00"
        stash[key] = m.group(0)
        return key

    return _CODE_SPAN_RE.sub(_repl, text), stash


def restore_code_spans(text: str, stash: dict) -> str:
    for k, v in stash.items():
        text = text.replace(k, v)
    return text


def scan_html_for_markers(html_path: Path) -> list[str]:
    """Read-only: return any residual auto-inject markers left in an already-rendered
    .html (for the smoke test / a structural check). [] = clean."""
    try:
        return [m.group(1).strip()
                for m in _RESIDUAL_MARKER_RE.finditer(html_path.read_text(encoding="utf-8"))]
    except Exception:  # noqa: BLE001
        return []


def render(markdown_path: Path, template_name: str, output_path: Path, extra_context: dict | None = None) -> None:
    """Render markdown + template → HTML file."""
    # Normalize the template name. The Stop hook passes the base.html path as
    # --template; strip it to its stem, and if that isn't a real template name
    # (e.g. "base" or a path), infer the correct one from the markdown path so
    # template-scoped CSS isn't silently dropped on hook-driven re-renders.
    tn = Path(template_name).stem if template_name else ""
    if tn not in KNOWN_TEMPLATES:
        tn = infer_template(markdown_path)
    template_name = tn

    markdown_text = markdown_path.read_text(encoding="utf-8")
    # SYS-093: hide markers written inside code spans from the injection replaces
    # below (restored just before conversion) so documented markers aren't consumed.
    markdown_text, _code_span_stash = stash_code_spans(markdown_text)
    # Dashboard auto-injection: replace AUTO_INJECT_MARKER sentinels in the
    # markdown with auto-generated tables (operator_actions, asset list) sourced
    # from each asset.yaml. Triggered by EITHER (a) --template dashboard, OR
    # (b) the file being a campaign root dashboard MD (file basename == parent
    # folder name AND parent's parent is `campaigns/`). The filename heuristic
    # is robust against the Stop hook passing a full template path instead of
    # the template name.
    here = Path(__file__).parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    try:
        import operator_actions  # type: ignore
    except Exception as e:
        operator_actions = None  # type: ignore
        print(f"  (operator_actions import failed: {e})", file=sys.stderr)

    is_dashboard = (
        template_name == "dashboard"
        or (
            markdown_path.parent.parent.name == "campaigns"
            and markdown_path.stem == markdown_path.parent.name
        )
    )
    if is_dashboard and operator_actions is not None:
        try:
            campaign_dir = markdown_path.parent
            markdown_text = operator_actions.inject(markdown_text, campaign_dir)
        except Exception as e:
            print(f"  (operator_actions dashboard inject failed: {e})", file=sys.stderr)

    # SYS-089 — Campaign DNA header on artifact surfaces (brief/insight/concept/plan) that live
    # under campaigns/<slug>/. Injected from the sibling campaign.yaml so every artifact opens on
    # the same consistent "you are here" anchor instead of a bespoke crammed metadata paragraph.
    if operator_actions is not None and operator_actions.CAMPAIGN_DNA_MARKER in markdown_text:
        croot = _campaign_root_of(markdown_path)
        if croot is not None:
            try:
                markdown_text = markdown_text.replace(
                    operator_actions.CAMPAIGN_DNA_MARKER,
                    operator_actions.render_campaign_dna(croot))
            except Exception as e:
                print(f"  (campaign-dna inject failed: {e})", file=sys.stderr)

    # STATUS_AUTO marker — replace in any per-asset md (preview.md, NN-slug.md).
    # The marker pulls the canonical status from the same folder's asset.yaml.
    # This eliminates the last hand-authored copy of asset status across surfaces.
    if operator_actions is not None and "<!-- STATUS_AUTO -->" in markdown_text:
        try:
            asset_dir = markdown_path.parent
            if (asset_dir / "asset.yaml").exists():
                markdown_text = operator_actions.inject_asset_status_line(markdown_text, asset_dir)
        except Exception as e:
            print(f"  (operator_actions status inject failed: {e})", file=sys.stderr)

    # COMPLIANCE_AUTO marker — Governance Manager verdict on a per-asset md (W1).
    # No-op (marker stripped) when the asset.yaml has no `compliance:` block, so
    # existing assets render unchanged (NO-RETROFIT).
    if operator_actions is not None and "<!-- COMPLIANCE_AUTO -->" in markdown_text:
        try:
            asset_dir = markdown_path.parent
            markdown_text = operator_actions.inject_compliance_line(markdown_text, asset_dir)
        except Exception as e:
            print(f"  (operator_actions compliance inject failed: {e})", file=sys.stderr)

    # RESONANCE_AUTO marker — Insights Manager advisory resonance read on a per-asset md.
    # No-op (marker stripped) when the asset.yaml has no `resonance:` block, so internal/
    # Foundation assets + pre-Insights-Manager campaigns render unchanged (NO-RETROFIT).
    if operator_actions is not None and "<!-- RESONANCE_AUTO -->" in markdown_text:
        try:
            asset_dir = markdown_path.parent
            markdown_text = operator_actions.inject_resonance_line(markdown_text, asset_dir)
        except Exception as e:
            print(f"  (operator_actions resonance inject failed: {e})", file=sys.stderr)

    # Cross-surface markers (tasks.md, index.md at campaigns/ root). Detected by
    # the file being directly under campaigns/ rather than inside a campaign.
    if operator_actions is not None and markdown_path.parent.name == "campaigns":
        try:
            markdown_text = operator_actions.inject_cross_surface(markdown_text, markdown_path.parent)
        except Exception as e:
            print(f"  (operator_actions cross-surface inject failed: {e})", file=sys.stderr)

    # Auto-stamp "Last updated" with date + time on cross-surface files (index / tasks).
    # Replaces the hand-authored date that drifted stale; render ≈ last update.
    if markdown_path.parent.name == "campaigns":
        markdown_text = stamp_last_updated(markdown_text)
    # SYS-093: marker-injection region done — restore code spans for conversion.
    markdown_text = restore_code_spans(markdown_text, _code_span_stash)
    title = extract_title(markdown_text)
    # For asset-preview, extract operator-action H2 sections into a right-hand
    # sidebar panel so the reviewer sees the deliverable first + the actions on
    # the right. Codified 2026-06-04 per operator direction.
    # Also: if a sibling copy.md exists in the same folder, inject an "Edit copy"
    # quick-action link at the top of the operator-panels so the operator never
    # has to hunt for the editable surface.
    operator_panels_html = ""
    if template_name == "asset-preview":
        markdown_text_body, operator_panels_html = extract_operator_panels(markdown_text)
        body_html = convert_markdown(markdown_text_body)
        # Sibling copy.md quick-action injection
        copy_md_path = markdown_path.parent / "copy.md"
        if copy_md_path.exists() and copy_md_path != markdown_path:
            quick_actions_html = (
                '<div class="operator-quick-actions">'
                '<a class="quick-action quick-action--primary" href="copy.md" target="_blank">'
                '<span class="quick-action__icon">✏️</span>'
                '<span class="quick-action__label">Edit copy</span>'
                '<span class="quick-action__hint">copy.md (canonical editable source)</span>'
                '</a>'
                '</div>'
            )
            # Prepend quick actions above the operator-panels-inner div
            if operator_panels_html:
                operator_panels_html = quick_actions_html + operator_panels_html
            else:
                # No operator H2 sections — wrap quick actions in the panels-inner shell
                operator_panels_html = (
                    '<div class="operator-panels-inner">'
                    '<div class="operator-panels-title">For your action</div>'
                    + quick_actions_html + '</div>'
                )
    else:
        body_html = convert_markdown(markdown_text)
        if template_name == "brief":
            body_html = stylize_brief(body_html)
        elif template_name == "plan":
            body_html = transform_plan(body_html)
    template = load_template(template_name)
    styles = load_styles()

    project_root = find_project_root(output_path)
    breadcrumb_html = build_breadcrumb(output_path, project_root)
    library_nav_html = build_library_nav(output_path, project_root)
    # SYS-090 — relative prefix from this surface to the repo root, so the footer's
    # licence/notice links resolve from any depth (campaigns/<slug>/assets/... → ../../../).
    try:
        _depth = len(output_path.resolve().relative_to(project_root.resolve()).parts) - 1
        site_root = "../" * _depth
    except Exception:
        site_root = ""

    # Simple variable substitution
    rendered = template
    rendered = rendered.replace("{{ title }}", title)
    rendered = rendered.replace("{{ body }}", body_html)
    rendered = rendered.replace("{{ styles }}", styles)
    rendered = rendered.replace("{{ template_name }}", template_name)
    rendered = rendered.replace("{{ breadcrumb }}", breadcrumb_html)
    rendered = rendered.replace("{{ library_nav }}", library_nav_html)
    rendered = rendered.replace("{{ site_root }}", site_root)
    rendered = rendered.replace("{{ source_path }}", str(markdown_path.relative_to(markdown_path.parent.parent.parent) if markdown_path.is_absolute() else markdown_path))
    rendered = rendered.replace("{{ operator_panels }}", operator_panels_html if template_name == "asset-preview" else "")

    # In-situ mockups (asset-preview only; renders if extra_context.form is set).
    # Tile paths in extra_context are resolved relative to the markdown file's directory.
    mockups_html = ""
    if extra_context and extra_context.get("form"):
        mockups_html = render_mockups(extra_context, markdown_path.parent)
    rendered = rendered.replace("{{ mockups }}", mockups_html)

    # Extra-context scalar placeholders (anything else the template references by name).
    # Skip composite keys we've already handled (form / variants).
    if extra_context:
        for key, value in extra_context.items():
            if key in ("form", "variants", "reactions", "comments"):
                continue
            if isinstance(value, (dict, list)):
                continue
            rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))

    # SYS-043 — last line of defence: never write a surface with an unprocessed
    # marker silently. Warn loudly + leave a visible placeholder for any leftover.
    rendered, _residual = guard_residual_markers(rendered, output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Rendered: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Render markdown to HTML using a named template.")
    parser.add_argument("--markdown", required=True, help="Path to source markdown file")
    parser.add_argument("--template", required=True, help="Template name (brief / concept-trio / plan / asset-preview / dashboard / tasks / index / brand-context)")
    parser.add_argument("--output", help="Output HTML path (default: same folder, .html extension)")
    parser.add_argument("--extra-context", help="JSON object with extra template variables")
    args = parser.parse_args()

    markdown_path = Path(args.markdown).resolve()
    if not markdown_path.exists():
        print(f"ERROR: markdown file not found: {markdown_path}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = markdown_path.with_suffix(".html")

    extra_context = json.loads(args.extra_context) if args.extra_context else None

    render(markdown_path, args.template, output_path, extra_context)


if __name__ == "__main__":
    main()
