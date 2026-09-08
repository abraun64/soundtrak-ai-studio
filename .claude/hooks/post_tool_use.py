#!/usr/bin/env python3
"""
PostToolUse hook — Layer 1 of the state-drift enforcement system.

Job: after every Write/Edit/MultiEdit/NotebookEdit/Bash, classify whether the
tool touched any campaign artifact. If yes, append the touch to a per-campaign
ledger at `.claude/state/dirty-campaigns.json`.

Mechanical. No judgment. No LLM. Never blocks. Never errors out loud.

The ledger gets drained by the Stop hook on turn-end (Layer 2).
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Latency measurement — E12 from AI Marketing System Retro 002 (2026-06-08)
# Tracks per-call wall-clock time. If average >50ms or peak >200ms over a session,
# investigate lazy-loading or matcher-narrowing in classify_path().
# Log lives at .claude/state/hook-latency.json — inspect after long sessions.
LATENCY_LOG = None  # set in main() after PROJECT_ROOT is known

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = PROJECT_ROOT / ".claude" / "state" / "dirty-campaigns.json"
# campaigns/ is canonical in the MAIN checkout — resolve via the shared helper so a worktree
# session's edits to main's campaigns/ are still classified into the ledger (SYS-008 / IDEA-007).
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "lib"))
# SYS-126 — FAIL LOUD, never silently. If repo_paths can't import, this checkout's hooks
# cannot resolve the canonical campaigns/ dir, so nothing gets classified into the dirty
# ledger and the Stop hook rebuilds nothing — the operator silently reviews STALE surfaces
# (the 2026-07-27 stale-worktree-hooks bug: a frozen worktree copy shipped without .claude/lib).
# The warning below (emitted once per degraded streak) turns that silent failure into a signal.
# It is self-contained on purpose — it must NOT depend on .claude/lib, which is the thing missing.
_AUTOREBUILD_OK = True
_DEGRADE_REASON = ""
try:
    import repo_paths
    CAMPAIGNS_DIR = repo_paths.data_root(PROJECT_ROOT) / "campaigns"
    SYSTEM_DIR = repo_paths.data_root(PROJECT_ROOT) / "system"
except Exception as _e:  # noqa: BLE001
    _AUTOREBUILD_OK = False
    _DEGRADE_REASON = f"{type(_e).__name__}: {_e}"
    CAMPAIGNS_DIR = PROJECT_ROOT / "campaigns"
    SYSTEM_DIR = PROJECT_ROOT / "system"

_DEGRADE_FLAG = PROJECT_ROOT / ".claude" / "state" / "autorebuild-degraded.flag"
_AUTOREBUILD_MSG = (
    "[auto-rebuild OFF] This checkout's hooks can't import repo_paths (.claude/lib) — "
    "operator surfaces will NOT auto-refresh, so the gallery/dashboard may show STALE data or a "
    "FALSE status with no other signal. You are likely in a stale/frozen worktree. Fix: run from "
    "the MAIN checkout, or rebuild by hand:  python .claude/skills/asset-gallery/build-gallery.py "
    "--campaign <slug>  &&  python .claude/lib/surface_freshness.py --heal"
)


def _flag_autorebuild_degraded() -> None:
    """Warn ONCE per degraded streak (per-tool-call hook — don't spam 800x a session). Writes a
    sentinel so subsequent calls stay quiet until the condition clears (Stop hook clears it)."""
    try:
        if _DEGRADE_FLAG.exists():
            return
        _DEGRADE_FLAG.parent.mkdir(parents=True, exist_ok=True)
        _DEGRADE_FLAG.write_text(_DEGRADE_REASON or "repo_paths import failed", encoding="utf-8")
    except OSError:
        pass
    print(f"{_AUTOREBUILD_MSG}  (reason: {_DEGRADE_REASON})", file=sys.stderr)

# SYS-016: a write to the System Manager's data (backlog/ideas/audit) marks a flag the
# Stop hook drains by re-rendering system/dashboard.html — mirrors how campaign writes mark
# the dirty-campaigns ledger, so the system board can't go stale waiting for a manual render.
SYSTEM_DIRTY_FLAG = PROJECT_ROOT / ".claude" / "state" / "system-dirty"
SYSTEM_DATA_FILES = {"backlog.yaml", "ideas.yaml", "audit-log.yaml"}


def touched_system_data(paths) -> bool:
    try:
        sd = SYSTEM_DIR.resolve()
    except (OSError, ValueError):
        return False
    for p in paths:
        try:
            rp = p.resolve()
        except (OSError, ValueError):
            continue
        if rp.parent == sd and rp.name in SYSTEM_DATA_FILES:
            return True
    return False


def classify_path(p: Path):
    """
    Given an absolute path, return (campaign_slug, reason) or (None, None) if
    the path isn't a tracked campaign artifact.

    Reason taxonomy (drives what Layer 2 needs to rebuild):
      - dashboard_md         : <slug>/<slug>.md (the campaign dashboard MD)
      - tasks_md             : campaigns/tasks.md (cross-campaign queue)
      - index_md             : campaigns/index.md (all-campaigns directory)
      - asset_record_md      : <slug>/assets/**/*.md
      - asset_artifact       : <slug>/assets/**/* (non-MD; PNG/HTML/YAML/SVG)
      - plan_md / brief_md   : <slug>/plan.md / brief.md
      - concept_artifact     : <slug>/concepts/**/*
      - gallery_config       : <slug>/gallery-config.yaml
      - campaign_other       : any other file under <slug>/
    """
    try:
        rel = p.resolve().relative_to(CAMPAIGNS_DIR.resolve())
    except (ValueError, OSError):
        return None, None

    parts = rel.parts
    if not parts:
        return None, None

    # campaigns/tasks.md or campaigns/index.md (no slug)
    if len(parts) == 1:
        if parts[0] == "tasks.md":
            return "_cross", "tasks_md"
        if parts[0] == "index.md":
            return "_cross", "index_md"
        return None, None

    slug = parts[0]
    tail = parts[1:]

    if len(tail) == 1 and tail[0] == f"{slug}.md":
        return slug, "dashboard_md"
    if len(tail) == 1 and tail[0] == "plan.md":
        return slug, "plan_md"
    if len(tail) == 1 and tail[0] == "brief.md":
        return slug, "brief_md"
    if len(tail) == 1 and tail[0] == "gallery-config.yaml":
        return slug, "gallery_config"

    if tail[0] == "assets":
        if rel.suffix.lower() == ".md":
            return slug, "asset_record_md"
        return slug, "asset_artifact"

    if tail[0] == "concepts":
        return slug, "concept_artifact"

    return slug, "campaign_other"


def extract_paths_from_bash(command: str):
    """Best-effort: pull file-path-looking tokens out of a Bash command."""
    paths = []
    cleaned = re.sub(r"""["']""", " ", command)
    tokens = re.split(r"[\s;&|<>]+", cleaned)
    for tok in tokens:
        if not tok:
            continue
        if "campaigns" in tok.replace("\\", "/"):
            try:
                p = Path(tok)
                if not p.is_absolute():
                    p = (PROJECT_ROOT / tok).resolve()
                paths.append(p)
            except (OSError, ValueError):
                continue
    return paths


def collect_touched_paths(tool_name: str, tool_input: dict):
    """Per-tool extraction of file paths."""
    paths = []
    if tool_name in ("Write", "Edit", "NotebookEdit", "MultiEdit"):
        fp = tool_input.get("file_path")
        if fp:
            paths.append(Path(fp))
    elif tool_name == "Bash":
        cmd = tool_input.get("command") or ""
        # Only consider Bash commands that smell write-ish — avoid logging
        # every `ls` or `cat` as a state change.
        write_signals = (
            "cp ", "mv ", " > ", ">>", "mkdir", "rm ", "rmdir", "touch",
            "python ", "tee ", "sed -i", "render-template", "build-gallery",
            "render.py", "Out-File", "Set-Content", "Write-File",
        )
        if any(s in cmd for s in write_signals):
            paths.extend(extract_paths_from_bash(cmd))
    return paths


def update_ledger(touches):
    """touches = list of (campaign_slug, reason, file_path_str)."""
    if not touches:
        return

    try:
        ledger = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        ledger = {"campaigns": {}}

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for slug, reason, file_path in touches:
        entry = ledger.setdefault("campaigns", {}).setdefault(slug, {
            "first_dirty_at": now,
            "reasons": [],
            "files_touched": [],
        })
        entry["last_dirty_at"] = now
        if reason not in entry["reasons"]:
            entry["reasons"].append(reason)
        if file_path not in entry["files_touched"]:
            entry["files_touched"].append(file_path)
        entry["files_touched"] = entry["files_touched"][-50:]

    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    except OSError:
        pass


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    global LATENCY_LOG
    LATENCY_LOG = PROJECT_ROOT / ".claude" / "state" / "hook-latency.json"

    # SYS-126 — fail loud if the auto-rebuild machinery is degraded; clear the flag when healthy.
    if not _AUTOREBUILD_OK:
        _flag_autorebuild_degraded()
    else:
        try:
            _DEGRADE_FLAG.unlink()
        except OSError:
            pass

    t_start = time.perf_counter()

    tool_name = event.get("tool_name") or ""
    tool_input = event.get("tool_input") or {}

    paths = collect_touched_paths(tool_name, tool_input)
    touches = []
    for p in paths:
        slug, reason = classify_path(p)
        if slug and reason:
            touches.append((slug, reason, str(p)))

    update_ledger(touches)

    # SYS-016: flag a system-data write so the Stop hook re-renders the system dashboard.
    if touched_system_data(paths):
        try:
            SYSTEM_DIRTY_FLAG.parent.mkdir(parents=True, exist_ok=True)
            SYSTEM_DIRTY_FLAG.write_text("1", encoding="utf-8")
        except OSError:
            pass

    # Record latency (non-blocking — failure is silent)
    elapsed_ms = (time.perf_counter() - t_start) * 1000
    try:
        try:
            log = json.loads(LATENCY_LOG.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            log = {"calls": [], "total": 0, "peak_ms": 0.0}
        log["total"] = log.get("total", 0) + 1
        log["peak_ms"] = max(log.get("peak_ms", 0.0), elapsed_ms)
        log["calls"].append(round(elapsed_ms, 2))
        log["calls"] = log["calls"][-200:]  # keep last 200 calls only
        avg = sum(log["calls"]) / len(log["calls"]) if log["calls"] else 0
        log["avg_ms"] = round(avg, 2)
        if elapsed_ms > 200:
            log["last_spike"] = {"ms": round(elapsed_ms, 2), "tool": tool_name,
                                 "ts": datetime.now(timezone.utc).isoformat()}
        LATENCY_LOG.parent.mkdir(parents=True, exist_ok=True)
        LATENCY_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
    except Exception:
        pass  # never block on latency logging

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
