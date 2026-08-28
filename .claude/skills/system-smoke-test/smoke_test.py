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
_REPO_PATHS_OK = True
_REPO_PATHS_ERR = ""
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)
    WORKTREE = repo_paths.is_worktree(ROOT)
except Exception as _e:  # noqa: BLE001
    _REPO_PATHS_OK = False
    _REPO_PATHS_ERR = f"{type(_e).__name__}: {_e}"
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

# SYS-136 — operator_actions decides what the dashboard/tasks queue tell the operator to do.
# Its Phase-5 gap catch mutually recursed with the phase-completion derivation (~200 levels of
# full campaign scans), so a real campaign's render blew past the Stop hook's 60s budget, got
# killed, and the surface silently kept serving stale content. RED here = that class is back.
_OA_TEST = ROOT / ".claude" / "skills" / "render-html" / "test_operator_actions.py"
if _OA_TEST.exists():
    ok, err = _run_ok([str(_OA_TEST)])
    check("L1", "operator-actions regression tests", ok, err if not ok else "")

# SYS-143 — the freshness gate's ENUMERATION is the whole guarantee: a surface it doesn't list
# can go stale without tripping anything. These assert it covers the same-stem md->html pipeline
# outputs (brief / plan / phase docs / asset records) and still excludes hand-built Producer
# artifacts, and that it shares stale-sweep's discriminator so the two sensors can't disagree.
_SF_TEST = ROOT / ".claude" / "lib" / "test_surface_freshness.py"
if _SF_TEST.exists():
    ok, err = _run_ok([str(_SF_TEST)])
    check("L1", "surface-freshness enumeration tests", ok, err if not ok else "")

# SYS-141 — the weekly digest WRITES to backlog.yaml. Two diagnostics escalating in one run
# both computed their id off the same stale in-memory list and filed duplicate SYS-141s
# (2026-08-11, repaired by hand). It also never noticed a diagnostic recovering, so a green
# check's P1 ticket sat open indefinitely. RED here = the board can be corrupted again.
_WD_TEST = ROOT / ".claude" / "skills" / "system-manager" / "test_weekly_digest.py"
if _WD_TEST.exists():
    ok, err = _run_ok([str(_WD_TEST)])
    check("L1", "weekly-digest escalation tests", ok, err if not ok else "")

# SYS-144 — the cadences dedupe what they file by fingerprint. Regress that and the inbox
# starts regenerating findings the operator already promoted or killed, which teaches them to
# skim past it — and that is how a genuinely new finding gets missed.
_CD_TEST = ROOT / ".claude" / "skills" / "cadences" / "test_cadence_dedup.py"
if _CD_TEST.exists():
    ok, err = _run_ok([str(_CD_TEST)])
    check("L1", "cadence dedupe tests", ok, err if not ok else "")

# Team deployment §3 — data_root() gained an explicit override (env / per-machine config) so a
# multi-operator install can point DATA at a separate repo. Two properties must hold: with NO
# configuration the single-operator install is byte-identical to before, and a configured-but-
# broken root FAILS LOUD. Regress the second and a tool writes campaign/system data into the
# CODE checkout, where it would ride a code release — the SYS-103 blind spot, but shipped.
_RP_TEST = ROOT / ".claude" / "lib" / "test_repo_paths.py"
if _RP_TEST.exists():
    ok, err = _run_ok([str(_RP_TEST)])
    check("L1", "data-root resolution tests", ok, err if not ok else "")

# SYS-028 / team deployment §12 — the profile toggle changes DEFAULTS, not code paths. The
# load-bearing property is that with NO config.yaml every axis returns the small-business answer:
# a regression there would silently make a single-operator install demand attribution or stop
# committing its own surfaces. The fail-loud half matters too — an install that MEANT to be a team
# deployment but quietly ran single-operator would skip claim locks and attribution unnoticed.
_DP_TEST = ROOT / ".claude" / "lib" / "test_deployment_profile.py"
if _DP_TEST.exists():
    ok, err = _run_ok([str(_DP_TEST)])
    check("L1", "deployment-profile toggle tests", ok, err if not ok else "")

# team-deployment §9.2 — a secret committed to a SHARED repo is permanent: it is in every
# clone's history and rotation is the only real remedy. Scan the tracked tree. This also
# guards the scanner itself: patterns broad enough to cry wolf get bypassed, and a bypassed
# scanner protects nothing — so a false positive HERE is a real failure, not noise.
# The ORGANISATION guide carries style.css INLINE (it is the page sent to a prospective customer,
# before they have a repo, where a linked stylesheet would arrive unstyled). That is a duplicate,
# and a duplicate nobody checks is drift waiting to happen - so check it.
_CSS_SYNC = ROOT / ".claude" / "lib" / "inline_guide_css.py"
if _CSS_SYNC.exists():
    ok, err = _run_ok([str(_CSS_SYNC), "--check"])
    check("L1", "org guide CSS in step with style.css", ok, err if not ok else "")

# SYS-149 - the leak scan is the gate between the master and anything public. It has two
# failure modes: too lax ships a client name, too noisy trains people to wave it through.
# These pin the allowlist in BOTH deployment shapes and prove the scan can still fail.
_LS_TEST = ROOT / ".claude" / "lib" / "test_build_seed_leakscan.py"
if _LS_TEST.exists():
    ok, err = _run_ok([str(_LS_TEST)])
    check("L1", "leak-scan allowlist tests", ok, err if not ok else "")

_SECRETS = ROOT / ".claude" / "lib" / "secret_scan.py"
if _SECRETS.exists():
    ok, err = _run_ok([str(_SECRETS), str(ROOT / ".claude"), str(DATA / "tenant"),
                       str(DATA / "tenant-brand")], timeout=120)
    check("L1", "no credentials in the tracked tree", ok, err if not ok else "")

# SYS-138 — verify.py --audit is the only thing between "closed" and "closed without anyone
# checking". If its close-date parsing or suite discovery regresses it reports a cheerful green
# having audited nothing, which is worse than not having it.
_V_TEST = ROOT / ".claude" / "skills" / "system-manager" / "test_verify.py"
if _V_TEST.exists():
    ok, err = _run_ok([str(_V_TEST)])
    check("L1", "verification runner tests", ok, err if not ok else "")


# ── Layer 1b — Auto-rebuild machinery (SYS-126/127): a seed must FAIL LOUD and must actually
# rebuild surfaces on a data edit. These catch the 2026-07-27 stale-hooks class (a frozen
# checkout missing repo_paths silently rebuilt nothing) BEFORE a broken seed is distributed.
check("L1", "repo_paths imports (hooks can resolve canonical dirs)", _REPO_PATHS_OK,
      (f"repo_paths import FAILED — auto-rebuild is OFF for this checkout: {_REPO_PATHS_ERR}. "
       "A shipped seed in this state silently serves stale surfaces.") if not _REPO_PATHS_OK else "")

def _fn_defs(pyfile: str) -> set:
    try:
        return {n.name for n in ast.walk(ast.parse((ROOT / pyfile).read_text(encoding="utf-8")))
                if isinstance(n, ast.FunctionDef)}
    except Exception:  # noqa: BLE001
        return set()

_need_stop = {"report_autorebuild_health", "freshness_guarantee"}
_have_stop = _fn_defs(".claude/hooks/stop.py")
check("L1", "stop.py fail-loud + freshness wired", _need_stop <= _have_stop,
      "missing: " + ", ".join(sorted(_need_stop - _have_stop)) if not _need_stop <= _have_stop else "")
check("L1", "post_tool_use.py fail-loud wired",
      "_flag_autorebuild_degraded" in _fn_defs(".claude/hooks/post_tool_use.py"))

# End-to-end: a data edit MUST trigger a rebuild. Build a throwaway campaign, render its
# dashboard, AGE the rendered surface into the past (so the source is newer), and prove
# surface_freshness both DETECTS it stale and HEALS it. Fully isolated (temp dir + scoped).
import os as _os
_e2e_ok, _e2e_detail = False, ""
try:
    import surface_freshness as _sf
    with tempfile.TemporaryDirectory() as _td:
        _slug = "_smoke-autorebuild"
        _cd = Path(_td) / "campaigns" / _slug
        _cd.mkdir(parents=True)
        (_cd / "campaign.yaml").write_text("campaign_name: Smoke\ntenant: smoke\nstatus: Active\n", encoding="utf-8")
        _md = _cd / f"{_slug}.md"
        _md.write_text("# Smoke\n\nbody\n", encoding="utf-8")
        _dash = _cd / "dashboard.html"
        _r = subprocess.run([sys.executable, str(RENDER), "--markdown", str(_md),
                             "--template", "base", "--output", str(_dash)],
                            capture_output=True, text=True, timeout=30)
        if not _dash.exists():
            _e2e_detail = f"temp dashboard render failed: {((_r.stderr or _r.stdout) or '')[-200:]}"
        else:
            _past = _md.stat().st_mtime - 100          # age the surface behind its source
            _os.utime(_dash, (_past, _past))
            _orig = _sf.CAMPAIGNS
            _sf.CAMPAIGNS = Path(_td) / "campaigns"
            try:
                detected = any("dashboard.html" in s["surface"] for s in _sf.stale_surfaces(_slug))
                _sf.heal(_slug)
                healed = not any("dashboard.html" in s["surface"] for s in _sf.stale_surfaces(_slug))
            finally:
                _sf.CAMPAIGNS = _orig
            _e2e_ok = detected and healed
            _e2e_detail = ("" if _e2e_ok else
                           "edit not detected as stale (freshness broken)" if not detected else
                           "detected stale but heal() did NOT rebuild")
except Exception as _e:  # noqa: BLE001
    _e2e_detail = f"harness error: {type(_e).__name__}: {_e}"
check("L1", "data edit -> surface auto-rebuilds (SYS-112 end-to-end)", _e2e_ok, _e2e_detail)


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
    # index.html / tasks.html only exist once there's at least one campaign. On a fresh,
    # pre-onboarding install (empty campaigns/) their absence is EXPECTED, not a failure —
    # don't show a brand-new deployment a wall of red.
    if active:
        check("L2", "campaigns/index.html", (CAMP / "index.html").exists())
        check("L2", "campaigns/tasks.html", (CAMP / "tasks.html").exists())
    else:
        check("L2", "campaigns (none yet - fresh install)", True, "")

    # SYS-112 — the dashboard's phases table MUST be auto-derived via <!-- PHASES_AUTO -->,
    # never hand-authored, or the phase Status / Human Time / AI Cost / Artifacts drift
    # silently (the reopened-SYS-112 bug: a hand table never sees the derive). Flag any
    # dashboard md that hand-authors a "| Phase | … |" table instead of the marker.
    import re as _phre
    _hand_phases = []
    for c in active:
        md = c / f"{c.name}.md"
        if not md.exists():
            continue
        txt = md.read_text(encoding="utf-8", errors="replace")
        if "<!-- PHASES_AUTO -->" in txt:
            continue
        if _phre.search(r"(?im)^\s*\|\s*Phase\s*\|", txt):
            _hand_phases.append(c.name)
    check("L2", "phases tables auto-derived (SYS-112 <!-- PHASES_AUTO -->)", not _hand_phases,
          ("hand-authored phases table — convert to <!-- PHASES_AUTO -->: " + ", ".join(_hand_phases))
          if _hand_phases else "")

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
# A freshly-downloaded Seed isn't a git repo until the operator runs setup (git init). Only
# check repo status once .git exists — "no repo yet" on a fresh install is expected, not a fail.
if (ROOT / ".git").exists():
    check("L4", "system repo status", _git_ok(["status", "--short"]))
else:
    check("L4", "system repo (not initialised yet - fresh install)", True, "")
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
    # The behavioural-eval harness is a vendor/dev QA tool, not shipped in the Seed. Its
    # absence on a customer install is expected, not a failure.
    check("L7", "behavioural evals (dev harness - not shipped in Seed)", True, "")


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
