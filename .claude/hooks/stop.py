#!/usr/bin/env python3
"""
Stop hook — Layer 2 of the state-drift enforcement system.

Job: before the agent's response goes to the operator, drain the dirty ledger.
For every campaign that was touched this turn:
  1. Re-render the campaign dashboard MD -> HTML
  2. Re-render tasks.md -> tasks.html and index.md -> index.html (if any campaign dirty)
  3. Re-build the campaign gallery (if asset artifacts touched)

This hook is intentionally NON-BLOCKING. It auto-rebuilds HTML silently.
Prose-drift detection emits stderr advisories that surface in the operator's
log tail but do NOT force a follow-up turn.

On success: clears the ledger.
On failure: leaves the ledger intact + emits a stderr warning so next Stop retries.
Never crashes the agent.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = PROJECT_ROOT / ".claude" / "state" / "dirty-campaigns.json"
# campaigns/ is canonical in the MAIN checkout — resolve via the shared helper so a
# worktree session's edits to main's campaigns/ still re-render (SYS-104).
# SYS-116: the RENDER SCRIPTS that write those MAIN-canonical surfaces must ALSO come from
# the main checkout — not PROJECT_ROOT. From a worktree, PROJECT_ROOT's render code may be
# stale/unlanded, and rendering main's dashboard.html/gallery.html/tenant-home with it silently
# clobbers the surface (a worktree's stale code reverted a landed fix). data_root() is the main
# checkout root, so CODE_ROOT/.claude/... is main's canonical code. From main, CODE_ROOT==PROJECT_ROOT.
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "lib"))
try:
    import repo_paths
    CODE_ROOT = repo_paths.data_root(PROJECT_ROOT)
    CAMPAIGNS_DIR = CODE_ROOT / "campaigns"
except Exception:
    CODE_ROOT = PROJECT_ROOT
    CAMPAIGNS_DIR = PROJECT_ROOT / "campaigns"
RENDER_HTML = CODE_ROOT / ".claude" / "skills" / "render-html" / "render.py"
RENDER_TEMPLATE = CODE_ROOT / ".claude" / "skills" / "render-html" / "templates" / "base.html"
BUILD_GALLERY = CODE_ROOT / ".claude" / "skills" / "asset-gallery" / "build-gallery.py"
BUILD_TENANT_HOME = CODE_ROOT / ".claude" / "skills" / "render-html" / "build-tenant-home.py"

DASHBOARD_TRIGGER_REASONS = {
    "dashboard_md", "asset_record_md", "asset_artifact", "plan_md",
    "brief_md", "concept_artifact", "gallery_config", "campaign_other",
}
GALLERY_TRIGGER_REASONS = {
    "asset_artifact", "asset_record_md", "gallery_config",
}


def load_ledger():
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"campaigns": {}}


def save_ledger(ledger):
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    except OSError:
        pass


def clear_ledger():
    save_ledger({"campaigns": {}})


def run_python(args, cwd=None):
    """Run python <args>. Return (success, stderr_excerpt)."""
    try:
        result = subprocess.run(
            ["python"] + list(args),
            cwd=str(cwd or PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return False, (result.stderr or result.stdout)[-400:]
        return True, ""
    except Exception as e:
        return False, str(e)[:400]


def render_dashboard(slug):
    md_path = CAMPAIGNS_DIR / slug / f"{slug}.md"
    if not md_path.exists():
        alt = CAMPAIGNS_DIR / slug / "dashboard.md"
        if alt.exists():
            md_path = alt
        else:
            return True, ""
    # Canonical output is `dashboard.html` (operator_actions, breadcrumbs, tenant
    # home, smoke test all link there). Without --output, render.py defaults to
    # the source stem → `<slug>.html`, which leaves an orphan that drifts from
    # `dashboard.html` over time. Force the canonical path.
    out_path = CAMPAIGNS_DIR / slug / "dashboard.html"
    return run_python([
        str(RENDER_HTML),
        "--markdown", str(md_path),
        "--template", str(RENDER_TEMPLATE),
        "--output", str(out_path),
    ])


def render_all_campaign_root_mds(slug):
    """
    Render all *.md files at campaign root (brief.md, plan.md, phase-4-rollout.md,
    phase-5-cadence.md, operations.md, etc.) — sibling files to the dashboard MD.

    The earlier render_dashboard() only handles <slug>/<slug>.md. This catches
    everything else at the root so artifact-prose changes flow through.

    Concept/asset record MDs are NOT included here — those are inside
    concepts/ and assets/ subdirs and have their own render paths
    (concepts: usually triggered by hand or by CD; assets: gallery picks them up).
    """
    root = CAMPAIGNS_DIR / slug
    if not root.exists():
        return True, ""
    results = []
    failures = []
    # All *.md at depth 1; excludes the dashboard MD (already rendered) and
    # excludes assets/concepts subtree MDs.
    for md_path in root.glob("*.md"):
        if md_path.name == f"{slug}.md" or md_path.name == "dashboard.md":
            continue  # already rendered by render_dashboard
        ok, err = run_python([
            str(RENDER_HTML),
            "--markdown", str(md_path),
            "--template", str(RENDER_TEMPLATE),
        ])
        if ok:
            results.append(md_path.name)
        else:
            failures.append(f"{md_path.name}: {err}")
    if failures:
        return False, " | ".join(failures)
    return True, ""


def render_cross_surface(name):
    md_path = CAMPAIGNS_DIR / f"{name}.md"
    if not md_path.exists():
        return True, ""
    return run_python([
        str(RENDER_HTML),
        "--markdown", str(md_path),
        "--template", str(RENDER_TEMPLATE),
    ])


def build_gallery(slug):
    if not (CAMPAIGNS_DIR / slug).exists():
        return True, ""
    return run_python([
        str(BUILD_GALLERY),
        "--campaign", slug,
    ])


def gallery_check(slug):
    """SYS-094 (safe increment) — run the read-only pre-surface gallery QA (build-gallery
    --check / SYS-003) automatically after a rebuild, so the stale-mirror class (an asset's
    edit-copy left behind its rendered surface — the 2026-07-09 Edition-#1 bug) is caught
    BEFORE the asset reaches the operator, not only when --check is run by hand. Runs after
    the rebuild, so a transient 'gallery stale' clears and only genuine content drift
    remains. Returns (clean, detail). Non-blocking: the caller emits a stderr advisory."""
    if not (CAMPAIGNS_DIR / slug).exists():
        return True, ""
    try:
        result = subprocess.run(
            ["python", str(BUILD_GALLERY), "--campaign", slug, "--check"],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
        if result.returncode == 0:
            return True, ""
        return False, (result.stdout or result.stderr or "").strip()[-900:]
    except Exception:
        return True, ""  # a check failure must never crash the hook


def freshness_guarantee():
    """SYS-112 prong A — THE GUARANTEE. Verify every operator surface (dashboard · gallery ·
    tasks · index · tenant home) against the newest of its data inputs, and rebuild any that
    are behind — regardless of the dirty ledger. Runs EVERY turn, so a data change that was
    never flagged dirty (a hand edit, a dead subagent, a missed re-render) can't leave a
    stale surface for the operator. The cheap mtime check gates the rebuild, so quiet turns
    cost almost nothing. Non-fatal; a surface STILL behind its data after a rebuild is a loud
    hard-blocker (something is broken)."""
    try:
        import surface_freshness  # resolves DATA to the main checkout itself (SYS-103)
    except Exception:
        return
    try:
        healed, still = surface_freshness.heal()
    except Exception as e:
        print(f"[state-hook] surface-freshness pass errored (non-fatal): {e}", file=sys.stderr)
        return
    if healed:
        print(f"[state-hook] ✓ surface-freshness: rebuilt {len(healed)} surface(s) the "
              f"dirty-ledger missed: {', '.join(healed)} (SYS-112)", file=sys.stderr)
    if still:
        print(f"[state-hook] 🔴 SURFACE STILL STALE after rebuild — do NOT trust: "
              f"{', '.join(still)}. Investigate (SYS-112).", file=sys.stderr)


def newest_mtime_in_campaign(slug):
    root = CAMPAIGNS_DIR / slug
    if not root.exists():
        return 0.0
    newest = 0.0
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".md", ".html", ".yaml", ".yml", ".png", ".jpg", ".svg"):
            try:
                m = p.stat().st_mtime
                if m > newest:
                    newest = m
            except OSError:
                continue
    return newest


def parse_dashboard_last_updated(slug):
    md_path = CAMPAIGNS_DIR / slug / f"{slug}.md"
    if not md_path.exists():
        md_path = CAMPAIGNS_DIR / slug / "dashboard.md"
    if not md_path.exists():
        return None
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    head = "\n".join(text.splitlines()[:60])
    m = re.search(r"Last updated[^\d]*(\d{4}-\d{2}-\d{2})", head)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def detect_prose_drift(slug):
    last_updated = parse_dashboard_last_updated(slug)
    newest = newest_mtime_in_campaign(slug)
    if not last_updated or not newest:
        return None
    newest_dt = datetime.fromtimestamp(newest, tz=timezone.utc)
    drift_days = (newest_dt.date() - last_updated.date()).days
    if drift_days >= 1:
        return (
            f"campaign `{slug}`: dashboard 'Last updated' stamp is "
            f"{last_updated.date()}, but newest artifact mtime is "
            f"{newest_dt.date()} ({drift_days} day(s) behind) — "
            f"consider updating prose (Stage line / To Do / Done log)"
        )
    return None


SYSTEM_ROOT = PROJECT_ROOT          # ai-marketing-system repo
CAMPAIGNS_ROOT = PROJECT_ROOT / "campaigns"  # soundtrak-campaigns repo


def git_has_changes(repo_path: Path) -> bool:
    """Return True if there are uncommitted changes in this git repo."""
    try:
        r = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(repo_path), capture_output=True, text=True, timeout=10,
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


# SYS-108 — generated / derivable surfaces that must NOT ride a WORKTREE auto-backup onto
# the branch. In a worktree these are either main-owned (built from main's data via
# data_root) or transient; letting the blanket `git add .` sweep them into a branch commit
# is what let a broken tenant-home regeneration nearly reach main on a merge (2026-07-22
# near-miss). Sources (tenant-brand/*.yaml, everything under system/*.yaml) are NOT here —
# only the built artifacts. Excluded only in a worktree; main's backup is unchanged.
_WORKTREE_GENERATED_EXCLUDES = [
    "tenant-brand/*-home.md",     # tenant home pages — built by build-tenant-home.py
    "tenant-brand/*-home.html",
    "system/dashboard.html",      # System Manager board — built by build-dashboard.py
    ".claude/state",              # hook state (dirty ledger, latency log) — transient
]


def git_commit(repo_path: Path, message: str, exclude: list[str] | None = None) -> bool:
    """Stage all changes and commit. When `exclude` is given, those generated/derivable
    pathspecs are unstaged after `git add` so they don't ride the commit (SYS-108) — they
    stay dirty and rebuild from source. Returns True on success, False if nothing real was
    left to commit or on error (both non-fatal to the hook)."""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(repo_path), capture_output=True, timeout=15, check=True,
        )
        if exclude:
            subprocess.run(
                ["git", "reset", "-q", "--"] + exclude,
                cwd=str(repo_path), capture_output=True, timeout=15,
            )
            # if the only changes were excluded generated files, there's nothing to back up
            if subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=str(repo_path), capture_output=True, timeout=15,
            ).returncode == 0:
                return False
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(repo_path), capture_output=True, timeout=15, check=True,
        )
        return True
    except Exception:
        return False


def git_push_background(repo_path: Path):
    """Fire-and-forget push — runs in background, doesn't block the hook."""
    try:
        subprocess.Popen(
            ["git", "push"],
            cwd=str(repo_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def auto_backup(session_summary: str):
    """
    Auto-commit + push both repos at session end.
    Commit is synchronous (fast). Push is background (non-blocking).
    Non-fatal — failures just emit a stderr note and move on.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"auto-backup: {ts}\n\n{session_summary}" if session_summary else f"auto-backup: {ts}"

    # SYS-108 — in a worktree, keep generated surfaces out of the branch backup.
    try:
        _in_worktree = repo_paths.is_worktree(PROJECT_ROOT)
    except Exception:
        _in_worktree = False

    backed_up = []
    for label, path in [("system", SYSTEM_ROOT), ("campaigns", CAMPAIGNS_ROOT)]:
        if not (path / ".git").exists():
            continue
        exclude = _WORKTREE_GENERATED_EXCLUDES if (label == "system" and _in_worktree) else None
        if git_has_changes(path):
            if git_commit(path, commit_msg, exclude=exclude):
                git_push_background(path)
                backed_up.append(label)

    if backed_up:
        print(f"[state-hook] git auto-backup: committed + pushing {', '.join(backed_up)}", file=sys.stderr)


def main():
    try:
        _ = sys.stdin.read()
    except Exception:
        pass

    # Worktree boundary (SYS-002 / SYS-008): a .claude/worktrees/<name> checkout has no
    # campaigns/ (separate repo); campaign re-renders + auto-backup here target the worktree,
    # not the main checkout. Warn loudly so the blind spot isn't silent. Diagnostics +
    # System Manager build resolve data via .claude/lib/repo_paths.py.
    try:
        _lib = PROJECT_ROOT / ".claude" / "lib"
        if str(_lib) not in sys.path:
            sys.path.insert(0, str(_lib))
        import repo_paths
        if repo_paths.is_worktree(PROJECT_ROOT):
            print("[state-hook] ⚠ worktree mode: campaigns/ absent here; campaign re-renders "
                  "+ auto-backup target this worktree only — do campaign/data work from the "
                  "main checkout. (SYS-002)", file=sys.stderr)
    except Exception:
        pass

    # SYS-016: re-render the System Manager dashboard if its data (backlog/ideas/audit-log)
    # changed this turn. Runs BEFORE the campaign-dirty early-return so a pure-system turn
    # still refreshes the board. build-dashboard.py resolves system/ via data_root → correct
    # from a worktree too.
    try:
        _sys_flag = PROJECT_ROOT / ".claude" / "state" / "system-dirty"
        if _sys_flag.exists():
            _build_dash = PROJECT_ROOT / ".claude" / "skills" / "system-manager" / "build-dashboard.py"
            if _build_dash.exists():
                run_python([str(_build_dash)])
                print("[state-hook] re-rendered system/dashboard.html (SYS-016)", file=sys.stderr)
            _sys_flag.unlink(missing_ok=True)
    except Exception:
        pass

    ledger = load_ledger()
    dirty = ledger.get("campaigns", {})
    if not dirty:
        # No campaign re-render needed this turn — but STILL auto-save any uncommitted
        # work (system/tenant edits, fresh setup) so a session is never lost. (Retro-5,
        # operator-authorised: previously gated behind campaign-dirtiness, which silently
        # skipped pure-system turns — the reason a system-only branch never got pushed.)
        freshness_guarantee()   # SYS-112 — verify + heal surfaces even on a no-dirty turn
        auto_backup("")
        return 0

    rebuild_log = []
    failures = []

    cross_touched = "_cross" in dirty
    real_campaigns = [s for s in dirty if s != "_cross"]
    reasons_per_campaign = {s: set(dirty[s].get("reasons", [])) for s in real_campaigns}

    for slug in real_campaigns:
        reasons = reasons_per_campaign[slug]
        if reasons & DASHBOARD_TRIGGER_REASONS:
            ok, err = render_dashboard(slug)
            if ok:
                rebuild_log.append(f"dashboard:{slug}")
            else:
                failures.append(f"dashboard:{slug}: {err}")
            # Also render all other campaign-root MDs (brief, plan,
            # phase-4-rollout, phase-5-cadence) when any of the trigger reasons
            # fires — they live in the same triggers set.
            ok2, err2 = render_all_campaign_root_mds(slug)
            if ok2:
                rebuild_log.append(f"campaign-root-mds:{slug}")
            else:
                failures.append(f"campaign-root-mds:{slug}: {err2}")
        if reasons & GALLERY_TRIGGER_REASONS:
            ok, err = build_gallery(slug)
            if ok:
                rebuild_log.append(f"gallery:{slug}")
                # SYS-094 (safe increment) — auto-run the pre-surface QA so a stale
                # edit-copy / drifted representation is flagged BEFORE the operator
                # trusts the surface, not only on a manual --check. Non-blocking: the
                # Stop hook can't gate the response, so this is a loud stderr advisory.
                clean, detail = gallery_check(slug)
                if not clean:
                    print(f"[state-hook] ⚠ PRE-SURFACE QA — {slug}: stale / drifted asset "
                          f"representation detected. Sync the edit-copy to its shipped "
                          f"surface before trusting the gallery (SYS-094):\n{detail}",
                          file=sys.stderr)
            else:
                failures.append(f"gallery:{slug}: {err}")

    if real_campaigns or cross_touched:
        ok, err = render_cross_surface("tasks")
        if ok:
            rebuild_log.append("tasks.html")
        else:
            failures.append(f"tasks: {err}")
        ok, err = render_cross_surface("index")
        if ok:
            rebuild_log.append("index.html")
        else:
            failures.append(f"index: {err}")
        # Tenant homes (operator home per tenant) — rebuilt on the same trigger as
        # index/tasks so each tenant's campaign phase pills + asset counts stay
        # fresh. Cheap (one render per tenant.yaml) + non-fatal (a failure is
        # logged, never breaks the turn). No-op if no tenant-brand/*.yaml exist.
        ok, err = run_python([str(BUILD_TENANT_HOME), "--all"])
        if ok:
            rebuild_log.append("tenant-homes")
        else:
            failures.append(f"tenant-homes: {err}")

    prose_drift_warnings = []
    for slug in real_campaigns:
        reasons = reasons_per_campaign[slug]
        if "dashboard_md" not in reasons:
            warn = detect_prose_drift(slug)
            if warn:
                prose_drift_warnings.append(warn)

    # Drift GATE (ratchet): run gate.py on each touched campaign. gate.py wraps
    # check.py's detection but compares against an accepted baseline
    # (.claude/state/drift-baseline.json), so it surfaces ONLY drift introduced
    # THIS turn — not the known backlog. Loud + NON-BLOCKING: it appends an
    # advisory breadcrumb; it never blocks the rebuild or the turn.
    status_drift_warnings = []
    gate_script = PROJECT_ROOT / ".claude" / "skills" / "check-state" / "gate.py"
    if gate_script.exists():
        for slug in real_campaigns:
            try:
                result = subprocess.run(
                    [sys.executable, str(gate_script), "--campaign", slug],
                    capture_output=True, text=True, timeout=15,
                )
                if result.returncode != 0:
                    # gate.py exits 1 ONLY when NEW drift (beyond the baseline) appears
                    m = re.search(r'(\d+) NEW', result.stdout or "")
                    n = m.group(1) if m else "?"
                    status_drift_warnings.append(f"{slug}: {n} NEW")
            except Exception:
                pass  # advisory only; never crash the hook

    # SYS-112 — THE GUARANTEE: after the dirty-ledger drain (an optimisation), verify every
    # surface against its data and heal anything still behind, so a missed/unflagged change
    # can't leave a stale surface. Runs regardless of what the ledger did.
    freshness_guarantee()

    if failures:
        msg = (
            "[state-hook] auto-rebuild had failures:\n  - "
            + "\n  - ".join(failures)
            + "\n\nLedger NOT cleared; next Stop will retry."
        )
        print(msg, file=sys.stderr)
        return 0

    # Clean rebuild — clear the ledger
    clear_ledger()
    breadcrumb_parts = []
    if rebuild_log:
        breadcrumb_parts.append(f"rebuilt: {', '.join(rebuild_log)}")
    if prose_drift_warnings:
        breadcrumb_parts.append("prose-drift advisory: " + " | ".join(prose_drift_warnings))
    if status_drift_warnings:
        breadcrumb_parts.append("⚠ NEW drift introduced this turn: " + " | ".join(status_drift_warnings)
                                + " — run: python .claude/skills/check-state/gate.py --campaign <slug> for details "
                                + "(or --write-baseline to accept it)")
    if breadcrumb_parts:
        print(f"[state-hook] {' — '.join(breadcrumb_parts)}", file=sys.stderr)

    # Auto-backup to GitHub — commit + push both repos at session end.
    # Commit is synchronous; push is background (non-blocking).
    # Commit message uses rebuild_log so history is meaningful, not just timestamps.
    session_summary = ", ".join(rebuild_log) if rebuild_log else ""
    auto_backup(session_summary)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[state-hook] internal error (non-fatal): {e}", file=sys.stderr)
        sys.exit(0)
