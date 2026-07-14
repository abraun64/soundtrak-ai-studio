#!/usr/bin/env python3
"""
System smoke test — structured, read-only validation of the AI Marketing System's
core machinery (NOT campaign content quality). Implements the check tables in
SKILL.md. Fast (<30s), non-destructive, stdlib + PyYAML only.

  python .claude/skills/system-smoke-test/smoke_test.py

Exit 0 = all green; exit 1 = one or more failures (details printed inline).
Built 2026-06-15 (scaffold promoted to implementation when system changes landed
that this test would validate — per SKILL.md's build-when-needed rule).
"""
from __future__ import annotations
import ast
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
# campaigns/ (+ system/, tenant-brand/) are canonical in the MAIN checkout; from a
# .claude/worktrees/* checkout they're absent, so resolve DATA dirs to the main checkout
# (SYS-002). CODE paths (render.py, gallery, hooks) stay on the running checkout's ROOT.
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)
    WORKTREE = repo_paths.is_worktree(ROOT)
except Exception:
    DATA, WORKTREE = ROOT, False
CAMP = DATA / "campaigns"
RENDER = ROOT / ".claude" / "skills" / "render-html" / "render.py"
GALLERY = ROOT / ".claude" / "skills" / "asset-gallery" / "build-gallery.py"

results: list[tuple[str, str, bool, str]] = []  # (layer, label, ok, detail)


def check(layer: str, label: str, ok: bool, detail: str = "") -> None:
    results.append((layer, label, bool(ok), detail))


def _run_ok(args: list[str], timeout: int = 30) -> tuple[bool, str]:
    try:
        r = subprocess.run([sys.executable, *args], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stderr or r.stdout or "").strip()[-200:]
    except Exception as e:
        return False, str(e)[:200]


def _git_ok(args: list[str]) -> bool:
    try:
        return subprocess.run(["git", *args], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=20).returncode == 0
    except Exception:
        return False


# ── Layer 1 — Render pipeline ────────────────────────────────────────────────
ok, err = _run_ok([str(RENDER), "--help"])
check("L1", "render.py callable", ok, err if not ok else "")

tmp = Path(tempfile.gettempdir()) / "_smoke_render.html"
ok, err = _run_ok([str(RENDER), "--markdown", str(ROOT / "docs" / "workflow.md"),
                   "--template", "spec", "--output", str(tmp)])
ok_render = ok and tmp.exists() and tmp.stat().st_size > 0
check("L1", "MD -> HTML render", ok_render, err if not ok_render else "")
try:
    tmp.unlink()
except OSError:
    pass

ok, err = _run_ok([str(GALLERY), "--help"])
check("L1", "build-gallery.py callable", ok, err if not ok else "")

# Builder pure-function regression tests — the fiddly string parsers that drive the
# Plan<->gallery reconciliation (_plan_ships_count, _normalize_asset_id). Guards the
# 2026-07-08 class: a silent parser mis-parse (e.g. `256×256` read as a 256x multiplier)
# that only surfaced inside a live campaign. RED here = caught before it reaches a campaign.
_HELPERS_TEST = ROOT / ".claude" / "skills" / "asset-gallery" / "test_helpers.py"
if _HELPERS_TEST.exists():
    ok, err = _run_ok([str(_HELPERS_TEST)])
    check("L1", "build-gallery parser tests", ok, err if not ok else "")


# ── Layer 2 — Operator-quartet per active campaign ───────────────────────────
try:
    import yaml
except ImportError:
    yaml = None


def _is_active(cdir: Path) -> bool:
    y = cdir / "campaign.yaml"
    if not y.exists() or yaml is None:
        return True
    try:
        d = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
    except Exception:
        return True
    return not (bool(d.get("archived")) or str(d.get("status") or "").lower() == "archived")


if CAMP.is_dir():
    active = [c for c in sorted(CAMP.iterdir())
              if c.is_dir() and (c / "assets").is_dir() and _is_active(c)]
    for c in active:
        dash = (c / "dashboard.html").exists() or (c / f"{c.name}.html").exists()
        gal = (c / "gallery.html").exists()
        miss = []
        if not dash:
            miss.append("dashboard.html")
        if not gal:
            miss.append("gallery.html")
        check("L2", c.name, dash and gal, "missing: " + ", ".join(miss) if miss else "")
    check("L2", "campaigns/index.html", (CAMP / "index.html").exists())
    check("L2", "campaigns/tasks.html", (CAMP / "tasks.html").exists())

    # SYS-043 — a rendered operator surface must not ship with an unprocessed
    # *_AUTO / *_MARKER sentinel (a swallowed inject = a silently blank section).
    # The render guard now leaves a VISIBLE placeholder; this catches any surface
    # that still carries a raw marker structurally, not by the operator noticing.
    try:
        sys.path.insert(0, str(ROOT / ".claude" / "skills" / "render-html"))
        from render import scan_html_for_markers  # type: ignore
        blanked: list[str] = []
        for c in active:
            for hp in (c / "dashboard.html", c / f"{c.name}.html", c / "gallery.html"):
                if hp.exists():
                    blanked += [f"{c.name}/{hp.name}:{t}" for t in scan_html_for_markers(hp)]
        for hp in (CAMP / "index.html", CAMP / "tasks.html"):
            if hp.exists():
                blanked += [f"{hp.name}:{t}" for t in scan_html_for_markers(hp)]
        check("L2", "no unprocessed render markers", not blanked,
              "; ".join(blanked[:6]) if blanked else "")
    except Exception as e:
        check("L2", "no unprocessed render markers", False, f"scan failed: {e}"[:120])
else:
    check("L2", "campaigns/ dir", False, "campaigns/ not found")


# ── Layer 3 — Hook wiring ────────────────────────────────────────────────────
settings_text = ""
for name in ("settings.json", "settings.local.json"):
    p = ROOT / ".claude" / name
    if p.exists():
        settings_text += p.read_text(encoding="utf-8")
check("L3", "PostToolUse hook wired", "post_tool_use.py" in settings_text)
check("L3", "Stop hook wired", "stop.py" in settings_text)
for h in ("post_tool_use.py", "stop.py"):
    p = ROOT / ".claude" / "hooks" / h
    if not p.exists():
        check("L3", f"{h} syntax", False, "missing")
        continue
    try:
        ast.parse(p.read_text(encoding="utf-8"))
        check("L3", f"{h} syntax", True)
    except SyntaxError as e:
        check("L3", f"{h} syntax", False, str(e)[:120])

# Agent registration guard (SYS-050): every .claude/agents/*/AGENT.md frontmatter MUST
# parse as YAML — a ": " colon-space in an unquoted `description:` aborts the parse and
# the agent type silently fails to register (forcing a manual general-purpose fallback).
# Catch it here, not at dispatch time.
try:
    import re as _re
    import yaml as _yaml
    _bad_agents = []
    for _ap in sorted((ROOT / ".claude" / "agents").glob("*/AGENT.md")):
        _fm = _re.match(r"^---\n(.*?)\n---", _ap.read_text(encoding="utf-8"), _re.S)
        if not _fm:
            _bad_agents.append(f"{_ap.parent.name}: no frontmatter")
            continue
        try:
            _yaml.safe_load(_fm.group(1))
        except Exception as _e:
            _bad_agents.append(f"{_ap.parent.name}: {str(_e).splitlines()[0][:48]}")
    check("L3", "agent AGENT.md frontmatter parses (all register)", not _bad_agents,
          "; ".join(_bad_agents) if _bad_agents else "")
except Exception as _e:
    check("L3", "agent AGENT.md frontmatter parses (all register)", False, f"check errored: {_e}"[:100])


# ── Layer 4 — Git repos ──────────────────────────────────────────────────────
check("L4", "system repo status", _git_ok(["status", "--short"]))
if (CAMP / ".git").exists():
    check("L4", "campaigns repo status", _git_ok(["-C", str(CAMP), "status", "--short"]))


# ── Layer 5 — Doc index freshness ────────────────────────────────────────────
# nav-audit exits 1 on real drift (specs/skills/agents/playbooks on disk but not in
# NAVIGATION_INDEX, or dead links). A stale-stamp-only run still exits 0 (it's a nudge).
NAVAUDIT = ROOT / ".claude" / "skills" / "nav-audit" / "nav_audit.py"
if NAVAUDIT.exists():
    ok, err = _run_ok([str(NAVAUDIT)])
    check("L5", "nav-index matches disk", ok, "drift — run nav-audit to see what's missing" if not ok else "")
else:
    check("L5", "nav-audit present", False, "missing")


# ── Layer 6 — Doc content + structure ────────────────────────────────────────
# docs-audit is the CONTENT layer over nav-audit (presence). It exits 1 on stale
# agent-count language, a class table missing an expected column, docs/public
# behind the roster/specs, or a §9/§10/§11 coverage mismatch — the drift class
# nav-audit's presence-only check can't see (SYS-018/SYS-026).
DOCSAUDIT = ROOT / ".claude" / "skills" / "docs-audit" / "docs_audit.py"
if DOCSAUDIT.exists():
    ok, err = _run_ok([str(DOCSAUDIT)])
    check("L6", "doc content + structure", ok, "drift — run docs-audit to see what's stale" if not ok else "")
else:
    check("L6", "docs-audit present", False, "missing")


# ── Layer 7 — Behavioural evals ──────────────────────────────────────────────
# Presence/currency (L1-L6) prove surfaces EXIST and are CURRENT. They do NOT prove a
# skill DID THE RIGHT THING on a representative input — the class of every recurring
# failure here (a fake ✅, a blank per-phase cost cell, a dropped render marker). The
# per-skill eval harness (SYS-061) feeds known inputs through render.py / ledger.py and
# the content-subedit voice rules and asserts on the concrete output. Deterministic +
# offline (no API/LLM). A red eval makes the smoke-test red.
EVALS_RUNNER = ROOT / ".claude" / "evals" / "run.py"
if EVALS_RUNNER.exists():
    ok, err = _run_ok([str(EVALS_RUNNER)], timeout=60)
    check("L7", "per-skill behavioural evals", ok,
          "eval FAIL — run `python .claude/evals/run.py` to see which" if not ok else "")
else:
    check("L7", "eval harness present", False, "missing .claude/evals/run.py")


# ── Report ───────────────────────────────────────────────────────────────────
LAYERS = {
    "L1": "LAYER 1 - Render pipeline",
    "L2": "LAYER 2 - Operator-quartet",
    "L3": "LAYER 3 - Hook wiring",
    "L4": "LAYER 4 - Git repos",
    "L5": "LAYER 5 - Doc index",
    "L6": "LAYER 6 - Doc content + structure",
    "L7": "LAYER 7 - Behavioural evals",
}
print("=== SYSTEM SMOKE TEST ===")
print(f"Date: {datetime.now():%Y-%m-%d %H:%M}")
if WORKTREE:
    print(f"(worktree mode — data dirs resolved to main checkout: {DATA})")
print()
all_pass = True
for lk, ltitle in LAYERS.items():
    rows = [r for r in results if r[0] == lk]
    if not rows:
        continue
    print(ltitle)
    for _, label, ok, detail in rows:
        dots = "." * max(3, 34 - len(label))
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        line = f"  {label} {dots} {status}"
        if detail and not ok:
            line += f"  ({detail})"
        print(line)
    print()
print("RESULT:", "ALL GREEN" if all_pass else "FAILURES — see above")
sys.exit(0 if all_pass else 1)
