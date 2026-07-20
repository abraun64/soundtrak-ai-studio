#!/usr/bin/env python3
"""
System Manager dashboard builder — produces system/dashboard.html.

Reads the System-layer data store:
  system/backlog.yaml    — tickets (todo / in_progress / done / killed)
  system/ideas.yaml      — untriaged idea inbox
  system/audit-log.yaml  — append-only state-change log

Emits one self-contained HTML (inlining render-html/system.css so it matches every
other operator surface) with:
  - a kanban: To Do (P1/P2/P3 swimlanes) · In Progress · Done
  - priority filter chips (P1/P2/P3) that hide/show live
  - an inbox chip → triage lightbox with full per-idea context + promote/merge/kill
  - audit history below
  - "Run a retro" + "Capture an idea" buttons at the top

A standalone HTML file can't call Claude, so every action button copies the exact
/system-manager chat command to the clipboard and shows a toast — the read surface
hands off to chat, same as the campaign gallery.

Usage:  python .claude/skills/system-manager/build-dashboard.py
"""
from __future__ import annotations
import html
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# The system/ data store is authoritative in the MAIN checkout, so running this from a
# .claude/worktrees/* checkout still reads/writes the real board, not a worktree-local
# copy (SYS-002). CODE/template paths stay on ROOT.
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    DATA_ROOT = repo_paths.data_root(ROOT)
except Exception:  # noqa: BLE001
    DATA_ROOT = ROOT
try:
    import operator_nav
except Exception:  # noqa: BLE001
    operator_nav = None
SYSTEM_DIR = DATA_ROOT / "system"
SYSTEM_CSS = ROOT / ".claude/skills/render-html/templates/styles/system.css"

PRIORITIES = ["P1", "P2", "P3"]
PRIORITY_LABEL = {"P1": "P1 · urgent", "P2": "P2 · debt", "P3": "P3 · opportunistic"}
DONE_LIMIT = 8


def esc(value) -> str:
    return html.escape(str(value if value is not None else "")).strip()


def load_yaml(path: Path, key: str) -> list:
    try:
        import yaml
    except ImportError:
        print("  ERROR pyyaml not installed. Install: pip install pyyaml", file=sys.stderr)
        return []
    if not path.exists():
        print(f"  WARN {path.name} not found — treating as empty.", file=sys.stderr)
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR failed to parse {path.name}: {exc}", file=sys.stderr)
        return []
    return data.get(key, []) or []


def load_system_css() -> str:
    try:
        return SYSTEM_CSS.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"  WARN system.css load fail: {exc}", file=sys.stderr)
        return ""


def meta_line(item: dict) -> str:
    bits = []
    if item.get("raised_by"):
        bits.append(f'<span class="who"><i>{esc(item["raised_by"])}</i></span>')
    if item.get("date"):
        bits.append(esc(item["date"]))
    if item.get("source"):
        bits.append(esc(item["source"]))
    return " · ".join(bits)


def pr_chip(item: dict) -> str:
    pr = item.get("pr") or {}
    num = pr.get("number")
    if not num:
        return ""
    url = esc(pr.get("url", ""))
    inner = f"PR #{esc(num)}"
    if url:
        return f'<a class="pr-chip" href="{url}" target="_blank" rel="noopener">{inner}</a>'
    return f'<span class="pr-chip">{inner}</span>'


PRIO_RANK = {"P1": 0, "P2": 1, "P3": 2}


def needs_of(item: dict) -> str:
    """Who an open item is waiting on: 'you' (operator decision) or 'ai' (the System
    Manager can just do it). Defaults to 'you' when unset — nothing is silently scoped
    AI-actionable without an explicit call."""
    v = str(item.get("needs") or "you").strip().lower()
    return "ai" if v in ("ai", "system", "auto") else "you"


def render_open_card(item: dict) -> str:
    prio = item.get("priority", "P3")
    title = esc(item.get("title", "(untitled)"))
    tid = esc(item.get("id", ""))
    summary = esc(item.get("summary", ""))
    summary_html = f'<div class="card-summary">{summary}</div>' if summary else ""
    benefit = esc(item.get("benefit", ""))
    benefit_html = f'<div class="card-benefit"><b>Benefit &middot;</b> {benefit}</div>' if benefit else ""
    wip = '<span class="tag">in progress</span>' if item.get("status") == "in_progress" else ""
    layer = esc(item.get("layer", "system"))
    return (
        f'<div class="card" data-priority="{prio}">'
        f'<div class="card-id">{tid}{wip}</div>'
        f'<div class="card-title">{title}</div>'
        f"{summary_html}"
        f"{benefit_html}"
        f'<div class="card-meta"><span>{meta_line(item)}</span>'
        f'<span class="card-tags"><span class="layer-tag">{layer}</span>'
        f'<span class="prio prio-{prio.lower()}">{prio}</span></span></div>'
        f"{pr_chip(item)}"
        f"</div>"
    )


def render_section(sec_id: str, label: str, hint: str, items: list, count_id: str) -> str:
    ordered = sorted(items, key=lambda i: PRIO_RANK.get(i.get("priority", "P3"), 3))
    cards = "\n".join(render_open_card(i) for i in ordered) or '<div class="empty">Nothing here right now.</div>'
    return (
        f'<div class="sec" id="{sec_id}">'
        f'<div class="sec-head">{label} '
        f'<span class="ct">&middot; <span id="{count_id}">{len(ordered)}</span> &middot; {hint}</span></div>'
        f"{cards}</div>"
    )


def latest_digest_banner() -> str:
    """Surface the most recent weekly digest (SYS-005) as a banner link. Date-named
    files sort chronologically; prefer the rendered .html, fall back to the .md."""
    d = SYSTEM_DIR / "digests"
    if not d.is_dir():
        return ""
    mds = sorted(d.glob("*.md"))
    if not mds:
        return ""
    latest = mds[-1]
    html = latest.with_suffix(".html")
    href = f"digests/{html.name if html.exists() else latest.name}"
    return (f'<a class="digest-banner" href="{href}">Latest weekly digest '
            f'&middot; <b>{esc(latest.stem)}</b> &middot; view &#8250;</a>')


def render_idea_row(idea: dict) -> str:
    iid = esc(idea.get("id", ""))
    title = esc(idea.get("title", "(untitled idea)"))
    summary = esc(idea.get("summary", ""))
    description = esc(idea.get("description", "")) or "No further context recorded."
    benefit = esc(idea.get("benefit", ""))
    benefit_html = f'<div class="idea-benefit"><b>Benefit &middot;</b> {benefit}</div>' if benefit else ""
    actions = (
        '<div class="acts">'
        '<span class="acts-label">promote</span>'
        + "".join(
            f'<button class="pchip prio-{p.lower()}" '
            f"onclick=\"copyCmd('/system-manager triage {iid} promote {p}')\">{p}</button>"
            for p in PRIORITIES
        )
        + f'<button class="ibtn" title="Merge into an existing ticket" '
          f"onclick=\"copyCmd('/system-manager triage {iid} merge')\">merge</button>"
        + f'<button class="ibtn" title="Delete — remove this idea from the inbox" '
          f"onclick=\"copyCmd('/system-manager triage {iid} kill')\">delete</button>"
        + "</div>"
    )
    return (
        '<div class="trow">'
        '<div class="trow-main">'
        f'<div class="idea-title" onclick="tg(this)"><span class="chev">&#8250;</span><span class="idea-id">{iid}</span>{title}</div>'
        f'<div class="idea-summary">{summary}</div>'
        f"{benefit_html}"
        f'<div class="idea-meta">{meta_line(idea)}</div>'
        f'<div class="idea-desc">{description}</div>'
        "</div>"
        f"{actions}"
        "</div>"
    )


def render_audit(entries: list, recent: int = 20) -> str:
    def _row(entry: dict) -> str:
        return (
            '<div class="arow">'
            f'<span class="adate">{esc(entry.get("date", ""))}</span>'
            f'<span class="aref">{esc(entry.get("ref", ""))}</span>'
            f'<span class="adetail">{esc(entry.get("note") or entry.get("detail", ""))}</span>'
            f'<span class="aevent">{esc(entry.get("event", ""))}</span>'
            "</div>"
        )
    if not entries:
        return '<div class="empty">No history yet.</div>'
    head = "\n".join(_row(e) for e in entries[:recent])
    if len(entries) <= recent:
        return head
    older = "\n".join(_row(e) for e in entries[recent:])
    return (
        head
        + f'<details class="audit-older"><summary>Show {len(entries) - recent} older entries</summary>'
        + older + "</details>"
    )


DASHBOARD_CSS = """
/* === System Manager dashboard — kanban + triage, neutral system palette === */
body.template-system { background: var(--bg); }
.sm-main { max-width: var(--max-width-wide); margin: 28px auto 64px; padding: 0 32px; }

.sm-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 18px; }
.sm-title { font-size: 26px; font-weight: 700; letter-spacing: -0.02em; margin: 0; }
.sm-updated { font-size: 12px; color: var(--text-subtle); margin-top: 4px; }
.sm-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.sm-btn { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500;
  padding: 7px 14px; border-radius: 999px; border: 1px solid var(--border); background: var(--surface);
  color: var(--text); cursor: pointer; transition: background .15s, color .15s, border-color .15s; }
.sm-btn:hover { background: var(--accent-soft); color: var(--accent); border-color: var(--accent-soft); }
.sm-btn.is-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.sm-btn.is-primary:hover { background: #1d4ed8; color: #fff; }

.sm-bar { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 18px; }
.inbox-cta { display: inline-flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 600;
  padding: 12px 22px; border-radius: 999px; border: none; background: var(--accent); color: #fff;
  cursor: pointer; box-shadow: var(--shadow-sm); }
.inbox-cta:hover { background: #1d4ed8; box-shadow: var(--shadow-md); }
.inbox-cta__n { background: #fff; color: var(--accent); font-weight: 700; border-radius: 999px;
  padding: 1px 10px; font-size: 13px; }
.filter { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.filter-label { font-size: 12px; color: var(--text-muted); }
.fchip { font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 999px; cursor: pointer;
  border: 1px solid transparent; }
.fchip.off { background: transparent !important; color: var(--text-subtle) !important;
  border-color: var(--border) !important; }
.fchip.reset { background: transparent; color: var(--text-muted); border-color: var(--border); }

/* priority colour family — mirrors the system .prio--now/next/later vocabulary */
.prio-p1, .fchip.prio-p1 { background: var(--danger-soft);  color: var(--danger); }
.prio-p2, .fchip.prio-p2 { background: var(--warning-soft); color: var(--warning); }
.prio-p3, .fchip.prio-p3 { background: var(--code-bg);      color: var(--text-muted); }

.sec { margin: 0 0 22px; max-width: 820px; }
.sec-head { font-size: 14px; font-weight: 700; color: var(--text); margin: 0 0 10px;
  padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.sec-head .ct { font-size: 12px; font-weight: 400; color: var(--text-subtle); }
#sec-you .sec-head { border-bottom-color: var(--accent); }
#sec-you .card { border-left: 2px solid var(--accent); }
.tag { font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 6px; margin-left: 8px;
  background: var(--accent-soft); color: var(--accent); }
.digest-banner { display: inline-flex; align-items: center; gap: 6px; margin: 0 0 18px; font-size: 13px;
  padding: 8px 14px; border-radius: var(--radius); background: var(--accent-soft); color: var(--accent);
  text-decoration: none; border: 1px solid transparent; }
.digest-banner:hover { border-color: var(--accent); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 11px 13px; margin-bottom: 9px; box-shadow: var(--shadow-sm); }
.card:hover { box-shadow: var(--shadow-md); }
.card-id { font-family: ui-monospace, "SF Mono", monospace; font-size: 11px; color: var(--text-subtle); }
.card-title { font-size: 14px; font-weight: 600; color: var(--text); line-height: 1.35; margin: 2px 0 0; }
.card-summary { font-size: 12px; color: var(--text-muted); line-height: 1.5; margin-top: 6px; }
.card-benefit, .idea-benefit { font-size: 12px; color: var(--text-muted); line-height: 1.5; margin-top: 6px; }
.card-benefit b, .idea-benefit b { color: var(--accent); }
.card-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 10px; }
.card-meta > span:first-child { font-size: 11px; color: var(--text-subtle); }
.prio { font-size: 11px; font-weight: 700; padding: 1px 8px; border-radius: 6px; white-space: nowrap; }
.card-tags { display: inline-flex; align-items: center; gap: 6px; }
.layer-tag { font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 6px;
  background: var(--code-bg); color: var(--text-muted); }
.done-tick { font-size: 11px; font-weight: 600; padding: 1px 9px; border-radius: 6px;
  background: var(--success-soft); color: var(--success); }
.pr-chip { display: inline-block; margin-top: 8px; font-size: 11px; padding: 2px 9px; border-radius: 6px;
  background: var(--accent-soft); color: var(--accent); text-decoration: none; }
.empty { font-size: 12px; color: var(--text-subtle); padding: 8px 2px; }

.audit { margin-top: 30px; }
.audit h2 { font-size: 16px; font-weight: 600; color: var(--text-muted); margin: 0 0 4px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.arow { display: grid; grid-template-columns: 92px 92px 1fr auto; gap: 12px; align-items: baseline;
  padding: 9px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.arow:last-child { border-bottom: none; }
.adate { font-family: ui-monospace, monospace; font-size: 12px; color: var(--text-subtle); }
.aref { font-family: ui-monospace, monospace; font-size: 12px; color: var(--text-muted); }
.adetail { color: var(--text); }
.aevent { font-size: 11px; color: var(--text-subtle); text-transform: uppercase; letter-spacing: .04em; }

/* triage lightbox */
.overlay { position: fixed; inset: 0; background: rgba(17,24,39,0.55); display: none;
  align-items: flex-start; justify-content: center; padding: 40px 18px; z-index: 100; overflow: auto; }
.overlay.open { display: flex; }
.modal { width: 100%; max-width: 860px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-md); padding: 18px 22px; }
.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px; }
.modal-title { font-size: 17px; font-weight: 700; }
.modal-sub { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.modal-close { background: none; border: none; font-size: 20px; cursor: pointer; color: var(--text-muted); }
.trow { display: flex; align-items: flex-start; gap: 14px; padding: 12px 0; border-top: 1px solid var(--border);
  flex-wrap: wrap; }
.trow-main { flex: 1; min-width: 220px; }
.idea-title { font-size: 14px; font-weight: 600; color: var(--text); cursor: pointer; line-height: 1.4;
  display: flex; align-items: baseline; gap: 7px; }
.chev { color: var(--text-subtle); font-size: 16px; transition: transform .12s; display: inline-block; }
.idea-summary { font-size: 12px; color: var(--text-muted); margin: 3px 0 3px; line-height: 1.5; }
.idea-meta { font-size: 11px; color: var(--text-subtle); }
.idea-id { font-family: ui-monospace, "SF Mono", monospace; font-size: 11px; color: var(--text-subtle); margin-right: 6px; }
.idea-desc { font-size: 12.5px; color: var(--text); line-height: 1.6; margin-top: 9px; padding: 10px 12px;
  background: var(--bg); border-radius: var(--radius); }
.acts { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.acts-label { font-size: 11px; color: var(--text-subtle); }
.pchip { font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 6px; cursor: pointer; border: none; }
.ibtn { font-size: 12px; padding: 4px 9px; border-radius: 6px; cursor: pointer; background: transparent;
  border: 1px solid var(--border); color: var(--text-muted); }
.ibtn:hover { border-color: var(--accent); color: var(--accent); }
.modal-foot { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border-strong);
  display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.modal-foot .hint { font-size: 11px; color: var(--text-subtle); }

/* toast */
.toast { position: fixed; bottom: 26px; left: 50%; transform: translateX(-50%) translateY(20px);
  background: var(--text); color: #fff; font-size: 13px; padding: 10px 18px; border-radius: 999px;
  opacity: 0; pointer-events: none; transition: opacity .2s, transform .2s; z-index: 200; }
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

.audit-older { margin-top: 2px; border: none; background: transparent; }
.audit-older summary { cursor: pointer; font-size: 12px; color: var(--accent); padding: 8px 0; list-style: revert; }
"""

DASHBOARD_JS = """
(function () {
  window.tg = function (el) {
    var d = el.parentNode.querySelector('.idea-desc');
    var c = el.querySelector('.chev');
    var open = d.style.display === 'block';
    d.style.display = open ? 'none' : 'block';
    if (c) c.style.transform = open ? 'rotate(0deg)' : 'rotate(90deg)';
  };
  window.openTriage = function () { document.getElementById('triage').classList.add('open'); };
  window.closeTriage = function (e) {
    if (!e || e.target === document.getElementById('triage') || e.target.classList.contains('modal-close'))
      document.getElementById('triage').classList.remove('open');
  };
  var toastT;
  window.copyCmd = function (cmd) {
    if (navigator.clipboard) { navigator.clipboard.writeText(cmd).catch(function () {}); }
    var el = document.getElementById('toast');
    el.textContent = 'Copied: ' + cmd + '  — paste into Claude Code';
    el.classList.add('show');
    clearTimeout(toastT);
    toastT = setTimeout(function () { el.classList.remove('show'); }, 2600);
  };
  document.querySelectorAll('.idea-desc').forEach(function (d) { d.style.display = 'none'; });
})();
"""


def warn_id_collisions(backlog: list, ideas: list) -> None:
    """SYS-025 belt-and-braces: shout if two records share an id, or an id is live in
    both stores. The board rebuilds after every change, so a worktree fork that re-mints
    an id surfaces here the moment it lands — non-fatal so the operator is never blocked."""
    b_ids = [i.get("id") for i in backlog if i.get("id")]
    i_ids = [i.get("id") for i in ideas if i.get("id")]
    problems = []
    for store, ids in (("backlog.yaml", b_ids), ("ideas.yaml", i_ids)):
        local = set()
        for x in ids:
            if x in local:
                problems.append(f"id {x} appears more than once in {store}")
            local.add(x)
    for x in sorted(set(b_ids) & set(i_ids)):
        problems.append(f"id {x} is live in BOTH backlog.yaml and ideas.yaml")
    for p in problems:
        print(f"  WARN SYS-025 id collision: {p}", file=sys.stderr)


def build() -> Path:
    backlog = load_yaml(SYSTEM_DIR / "backlog.yaml", "items")
    ideas = load_yaml(SYSTEM_DIR / "ideas.yaml", "items")
    audit = load_yaml(SYSTEM_DIR / "audit-log.yaml", "entries")
    warn_id_collisions(backlog, ideas)

    open_items = [i for i in backlog if i.get("status") in ("todo", "in_progress")]
    needs_you = [i for i in open_items if needs_of(i) == "you"]
    needs_ai = [i for i in open_items if needs_of(i) == "ai"]
    sec_you = render_section("sec-you", "&#9203; Needs you", "a decision is blocking these", needs_you, "you-count")
    sec_ai = render_section("sec-ai", "&#129302; AI can action", "no operator input needed", needs_ai, "ai-count")
    digest_banner = latest_digest_banner()

    idea_rows = "\n".join(render_idea_row(i) for i in ideas)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    library_nav = operator_nav.top_nav_pills(DATA_ROOT, "../") if operator_nav else ""

    body = f"""
  <header class="page-header">
    <div class="page-header__inner">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a class="crumb crumb-link" href="../docs/NAVIGATION_INDEX.html">&#127968; System</a>
        <span class="crumb-sep">&#8250;</span>
        <span class="crumb crumb-current">Operator dashboard</span>
      </nav>
      <div class="page-header__right">{library_nav}<button type="button" class="refresh-btn" onclick="location.reload()" title="Refresh this page" aria-label="Refresh">&#10227;</button><span class="page-header__template">system</span></div>
    </div>
  </header>

  <main class="sm-main">
    <div class="sm-top">
      <div>
        <h1 class="sm-title">System operator dashboard</h1>
        <div class="sm-updated">Updated {now}</div>
      </div>
      <div class="sm-actions">
        <button class="sm-btn is-primary" onclick="copyCmd('/system-manager retro')">Run a retro</button>
        <button class="sm-btn" onclick="copyCmd('/system-manager capture: ')">Capture an idea</button>
      </div>
    </div>

    <div class="sm-bar">
      <button class="inbox-cta" onclick="openTriage()">&#128229; Inbox &mdash; <span class="inbox-cta__n">{len(ideas)}</span> untriaged &middot; triage &#8594;</button>
    </div>

    {digest_banner}

    {sec_you}
    {sec_ai}

    <div class="audit">
      <h2>Audit history <span style="font-weight:400;color:var(--text-subtle);font-size:13px;">— the record of done</span></h2>
      {render_audit(audit)}
    </div>
  </main>

  <div class="overlay" id="triage" onclick="closeTriage(event)">
    <div class="modal">
      <div class="modal-head">
        <span class="modal-title">Triage inbox &middot; {len(ideas)} untriaged</span>
        <button class="modal-close" onclick="closeTriage()" aria-label="Close">&times;</button>
      </div>
      <div class="modal-sub">Click an idea to read the full context. Promote to the board, merge into an existing ticket, or delete. Each action copies the command — paste it into Claude Code to apply.</div>
      {idea_rows}
      <div class="modal-foot">
        <span class="hint">Prefer a walkthrough? Copy a guided-triage session.</span>
        <button class="sm-btn" onclick="copyCmd('/system-manager triage')">Guided triage &#8599;</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>
"""

    page = (
        "<!DOCTYPE html>\n<html lang=\"en-AU\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>System operator dashboard</title>\n<style>\n"
        + load_system_css() + "\n" + DASHBOARD_CSS
        + "\n</style>\n</head>\n<body class=\"template-system\">\n"
        + body
        + "\n<script>\n" + DASHBOARD_JS + "\n</script>\n</body>\n</html>\n"
    )

    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    out = SYSTEM_DIR / "dashboard.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = build()
    print(f"Built {path}")
