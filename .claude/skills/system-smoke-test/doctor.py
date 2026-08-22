#!/usr/bin/env python3
"""Install doctor (Retro-5) - fresh-machine prerequisite check for the Marketing AI System.

Where system-smoke-test asks "is the system working?", the doctor asks "is THIS MACHINE
set up to run it?" - the first thing a new operator runs after cloning the Seed. Each
failed check prints a one-line remediation. Read-only, ASCII output (cp1252-safe).

  python .claude/skills/system-smoke-test/doctor.py
Exit 0 = ready; exit 1 = one or more blocking prerequisites missing.
"""
from __future__ import annotations
import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .claude/skills/system-smoke-test/ -> root


def run() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []  # (level ok|warn|fail, label, remediation)

    # Python version
    v = sys.version_info
    rows.append(("ok" if v >= (3, 10) else "warn",
                 f"Python {v.major}.{v.minor}.{v.micro}",
                 "" if v >= (3, 10) else "Python 3.10+ recommended"))

    # The Stop / PostToolUse hooks in .claude/settings.json invoke the interpreter as the literal
    # `python`. On macOS/Linux that command often doesn't exist (only `python3`) - in which case
    # the hooks silently never fire and NO operator surface ever auto-updates. Check it directly.
    if shutil.which("python"):
        rows.append(("ok", "`python` on PATH (the .claude hooks invoke it)", ""))
    elif shutil.which("python3"):
        rows.append(("fail", "`python` NOT on PATH (only `python3`) - hooks will silently never run",
                     "alias/symlink `python` -> python3 (e.g. ln -s $(which python3) ~/.local/bin/python), "
                     "or the auto-render/backup engine won't fire"))
    else:
        rows.append(("fail", "no `python` on PATH",
                     "install Python 3.10+ and ensure the `python` command is on PATH"))

    # Required importable libraries
    for mod, fix in (("markdown", "pip install markdown"), ("yaml", "pip install pyyaml")):
        if importlib.util.find_spec(mod):
            rows.append(("ok", f"python module: {mod}", ""))
        else:
            rows.append(("fail", f"python module: {mod} MISSING", fix))

    # Playwright + chromium — OPTIONAL: only build-gallery.py (thumbnail images) needs it.
    # Campaigns run fine without it, so a miss is a WARNING, not a blocker — don't force a
    # ~150 MB chromium download before the doctor will go green.
    if importlib.util.find_spec("playwright"):
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                exe = p.chromium.executable_path
            if exe and Path(exe).exists():
                rows.append(("ok", "playwright + chromium", ""))
            else:
                rows.append(("warn", "playwright: chromium not installed (optional - gallery thumbnails)",
                             "playwright install chromium"))
        except Exception as e:
            rows.append(("warn", "playwright present but unusable (optional - gallery thumbnails)",
                         f"playwright install chromium  ({str(e)[:70]})"))
    else:
        rows.append(("warn", "playwright missing (optional - only for gallery thumbnails)",
                     "pip install playwright && playwright install chromium"))

    # git — recommended for local version history + the auto-backup safety net, but the studio
    # runs without it (a ZIP download has no git), so a miss is a WARNING, not a blocker.
    rows.append(("ok" if shutil.which("git") else "warn", "git (recommended - backup/history)",
                 "" if shutil.which("git") else "install Git to enable version history + auto-backup"))
    rows.append(("ok" if shutil.which("git-lfs") else "warn", "git-lfs (optional - video assets)",
                 "" if shutil.which("git-lfs") else "install git-lfs only if shipping MP4 assets"))
    # ffmpeg - OPTIONAL, for best-quality video delivery (video_export.py finalize). Falls back to
    # OpenCV when absent, so it's a warning, not a blocker.
    rows.append(("ok" if shutil.which("ffmpeg") else "warn", "ffmpeg (recommended - video delivery)",
                 "" if shutil.which("ffmpeg") else "install ffmpeg for true H.264/+faststart MP4 + GIF (optional; OpenCV is the fallback)"))

    # Credential env vars referenced in tenant integrations.yaml
    refs: dict[str, list[str]] = {}
    for p in ROOT.glob("tenant/*/integrations.yaml"):
        try:
            for m in re.findall(r"\$\{([A-Z0-9_]+)\}", p.read_text(encoding="utf-8")):
                refs.setdefault(m, []).append(p.parent.name)
        except OSError:
            continue
    unset = sorted(k for k in refs if not os.environ.get(k))
    if not refs:
        rows.append(("ok", "credential env vars", "none referenced yet"))
    elif unset:
        rows.append(("warn", f"credential env vars: {len(unset)} unset",
                     "set before publishing: " + ", ".join(unset)))
    else:
        rows.append(("ok", f"credential env vars ({len(refs)} all set)", ""))

    rows.extend(_team_rows())
    return rows


# ── Team-deployment environment checks (team-deployment.md §14) ──────────────────────────
# These began as questions to answer once. That is wrong for a product installed at many
# organisations: "does THIS org permit hooks?" cannot be answered in advance, and an install
# that assumes it fails silently at the third customer. So each is a check, run here, at the
# moment it matters, with a written remediation.
#
# Every row is a NO-OP under `profile: small-business` — a single-operator Seed must not be
# told it is missing a SharePoint target it was never going to use.

def _team_rows() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    sys.path.insert(0, str(ROOT / ".claude" / "lib"))
    try:
        import deployment_profile as dp
    except ImportError:
        return rows
    try:
        if not dp.is_team():
            return rows
    except Exception as e:  # noqa: BLE001 — a broken config.yaml is itself the finding
        return [("fail", f"config.yaml unreadable: {str(e)[:90]}",
                 "fix `profile:` in the DATA repo's config.yaml")]

    rows.append(("ok", "deployment profile: team", ""))

    # §14.1 — the largest blast radius. The sync (§6) and freshness (§10) architecture both
    # run on PostToolUse/Stop hooks. If a managed-settings policy overrides .claude/settings.json
    # the hooks never fire, and every operator surface silently stops updating. We cannot read
    # the org's policy, but we CAN verify the hooks this install depends on are declared and
    # their scripts exist and parse — the failure this actually produces.
    settings = ROOT / ".claude" / "settings.json"
    try:
        import json as _json
        declared = _json.loads(settings.read_text(encoding="utf-8")).get("hooks", {})
    except (OSError, ValueError) as e:
        declared = {}
        rows.append(("fail", f".claude/settings.json unreadable ({str(e)[:60]})",
                     "restore it from the code repo — without it NO hook fires"))
    missing = [h for h in ("PostToolUse", "Stop") if h not in declared]
    if declared and missing:
        rows.append(("fail", f"hooks not declared: {', '.join(missing)}",
                     "a managed-settings policy may be overriding .claude/settings.json — "
                     "confirm with IT. Fallback: operators run /sync by hand (§6)."))
    elif declared:
        bad = [s for s in (ROOT / ".claude" / "hooks" / n
                           for n in ("post_tool_use.py", "stop.py")) if not s.is_file()]
        if bad:
            rows.append(("fail", "hook script(s) missing: " + ", ".join(p.name for p in bad),
                         "re-pull the code repo at its release tag"))
        else:
            rows.append(("ok", "PostToolUse + Stop hooks declared and present", ""))

    # §14.4 — nothing works without the DATA remote.
    try:
        import repo_paths
        data = repo_paths.data_root(ROOT)
    except Exception as e:  # noqa: BLE001
        data = None
        rows.append(("fail", f"DATA root unresolved: {str(e)[:80]}",
                     "python .claude/lib/provision.py --data <path to the data clone>"))
    if data is not None:
        if data.resolve() == ROOT.resolve():
            rows.append(("fail", "DATA root is this checkout — not provisioned",
                         "python .claude/lib/provision.py --data <path to the data clone>"))
        else:
            rows.append(("ok", f"DATA root -> {data}", ""))
            ok_remote = subprocess.run(["git", "remote"], cwd=str(data), capture_output=True,
                                       text=True).stdout.strip()
            rows.append(("ok" if ok_remote else "fail",
                         "DATA repo has a remote" if ok_remote else "DATA repo has NO remote",
                         "" if ok_remote else "nothing syncs between operators without one"))

    # §14.5 — media in LFS matters only once the DATA repo declares it.
    if data is not None and (data / ".gitattributes").is_file():
        try:
            wants_lfs = "filter=lfs" in (data / ".gitattributes").read_text(encoding="utf-8")
        except OSError:
            wants_lfs = False
        if wants_lfs:
            rows.append(("ok" if shutil.which("git-lfs") else "fail",
                         "git-lfs (DATA repo tracks media in LFS)",
                         "" if shutil.which("git-lfs") else
                         "install git-lfs then `git lfs install` — without it media commits as pointer text"))

    # §14.2 — attribution has no machine answer, but an unset identity is a real defect:
    # every audit entry would name nobody.
    who = subprocess.run(["git", "config", "user.email"], cwd=str(ROOT),
                         capture_output=True, text=True).stdout.strip()
    rows.append(("ok" if who else "fail", f"operator identity: {who or 'UNSET'}",
                 "" if who else "git config --global user.email you@example.com — "
                                "attribution is required under profile: team (§4)"))

    # §14.3 — publishing is optional; the system runs locally without it.
    if dp.publish_to_sharepoint():
        target = os.environ.get("MAS_PUBLISH_DIR", "").strip()
        if not target:
            rows.append(("warn", "publish target unset (SharePoint publishing off)",
                         "set MAS_PUBLISH_DIR to a synced SharePoint library folder (§11)"))
        else:
            p = Path(target)
            rows.append(("ok" if p.is_dir() else "warn",
                         f"publish target: {target}" if p.is_dir() else
                         f"publish target does not exist: {target}",
                         "" if p.is_dir() else "create it, or unset MAS_PUBLISH_DIR"))
    return rows


def attempt_fix() -> None:
    """Install any missing Python prerequisites. Idempotent — safe to re-run."""
    print("=== doctor --fix: installing prerequisites (safe to re-run) ===")
    pkgs = []
    if not importlib.util.find_spec("markdown"):
        pkgs.append("markdown")
    if not importlib.util.find_spec("yaml"):
        pkgs.append("pyyaml")
    if not importlib.util.find_spec("playwright"):
        pkgs.append("playwright")
    if pkgs:
        subprocess.run([sys.executable, "-m", "pip", "install", *pkgs])
    # Chromium browser for Playwright (downloads only if missing)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    # macOS/Linux: the .claude hooks invoke the literal `python`. If only `python3` exists, the
    # hooks silently never fire. Best-effort: symlink `python`->python3 into a user-writable PATH
    # dir so the auto-render/backup engine resolves. Windows ships `python`, so skip there.
    if os.name == "posix" and not shutil.which("python") and shutil.which("python3"):
        target = shutil.which("python3")
        for d in (Path.home() / ".local" / "bin", Path("/usr/local/bin")):
            try:
                d.mkdir(parents=True, exist_ok=True)
                link = d / "python"
                if not link.exists():
                    link.symlink_to(target)
                print(f"  linked `python` -> {target}  (at {link})")
                if str(d) not in os.environ.get("PATH", "").split(os.pathsep):
                    print(f"  NOTE: add {d} to your PATH (shell profile) so the hooks find `python`.")
                break
            except Exception as e:
                print(f"  (couldn't create a `python` symlink in {d}: {e})")
    print("=== fix attempt done; re-checking below ===\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Install doctor - check (and optionally fix) prerequisites.")
    ap.add_argument("--fix", action="store_true", help="attempt to install any missing prerequisites")
    ap.add_argument("--accept-license", action="store_true",
                    help="accept the license non-interactively (first-run gate)")
    a = ap.parse_args()

    # First-run license gate (SYS-048): show the disclaimer + require acceptance before any
    # setup work runs. Accepted once per install; recorded locally (never shipped in the Seed).
    sys.path.insert(0, str(ROOT / ".claude" / "lib"))
    try:
        import accept_license
        if not accept_license.require(ROOT, auto_accept=a.accept_license,
                                      interactive=sys.stdin.isatty()):
            print("\nInstall doctor halted: accept the license to continue.")
            return 2
    except Exception as e:  # noqa: BLE001 — a gate failure must never brick the doctor
        print(f"(license gate skipped: {e})", file=sys.stderr)

    if a.fix:
        attempt_fix()
    sym = {"ok": "[ OK ]", "warn": "[WARN]", "fail": "[FAIL]"}
    rows = run()
    print("=== Marketing AI System - install doctor ===")
    for level, label, fix in rows:
        print(f"{sym[level]} {label}" + (f"  -> {fix}" if fix else ""))
    fails = sum(1 for r in rows if r[0] == "fail")
    warns = sum(1 for r in rows if r[0] == "warn")
    print(f"\n{fails} blocking, {warns} warning(s).")
    print("READY." if not fails else "NOT READY - resolve the [FAIL] items above.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
