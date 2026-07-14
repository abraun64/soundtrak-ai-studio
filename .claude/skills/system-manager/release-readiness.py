#!/usr/bin/env python3
"""SYS-063 — scheduled release-readiness cadence.

Cutting a public "Seed" release is manual, so system-layer fixes pile up in the
CHANGELOG `[Unreleased]` section and the public Seed lags master. This cadence runs on a
timer (mirroring the weekly digest), DETECTS whether a SYSTEM-LAYER change is pending
release, and — if so — auto-cuts + auto-validates a Seed to a STAGING dir and writes a
"a release is ready to push" notification the operator reads. If nothing is pending it
no-ops with a clear "nothing to release" line.

  python .claude/skills/system-manager/release-readiness.py            # detect (+ stage if pending)
  python .claude/skills/system-manager/release-readiness.py --notify-only   # detect only, never stage

Change-detection keys on SYSTEM-LAYER only:
  (1) a non-empty CHANGELOG.md `[Unreleased]` section, AND/OR
  (2) a git diff of build_seed-allowlisted paths since the last vX.Y.Z tag.
The allowlist is imported LIVE from .claude/lib/build_seed.py (SHIP_DIRS/SHIP_FILES + the
per-dir exclude substrings), so "what counts as system" can never drift from "what ships".
Auto-backup commits and tenant/campaign churn are excluded by construction — they aren't on
the allowlist.

GOVERNANCE — this cadence is release-*readiness*, not release:
  * It NEVER pushes master-derived content to the public repo (push stays human-gated).
  * It runs NO git writes (git READ only: tag -l, diff). It does not tag or commit.
  * It cuts the Seed to a STAGING dir only; it does not cut a real tagged release.
  * NO external notifications — local file (system/release-readiness/<date>.md) + print only.

Designed to run on a schedule (SYS-063); safe to run by hand anytime. Worktree-aware:
resolves system/ to the main checkout via repo_paths, but reads CODE (build_seed allowlist,
CHANGELOG, git history) from the running checkout.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / ".claude" / "lib"
sys.path.insert(0, str(LIB))
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)
except Exception:
    DATA = ROOT
SYSTEM_DIR = DATA / "system"
SKILLS = ROOT / ".claude" / "skills"
CHANGELOG = ROOT / "CHANGELOG.md"

# Auto-backup commits are excluded by construction (they touch DATA dirs off the allowlist),
# but we also skip them explicitly by subject so a stray allowlisted file in a backup commit
# doesn't read as a genuine pending change.
BACKUP_COMMIT_RE = re.compile(r"auto[- ]?backup|nightly backup|stop-hook backup", re.IGNORECASE)


def _safe_print(s: str) -> None:
    """Print without dying on a cp1252 Windows console (scheduled tasks run non-interactive).
    The report is UTF-8 on disk; the console echo degrades any un-encodable glyph."""
    try:
        print(s)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        sys.stdout.write(s.encode(enc, errors="replace").decode(enc) + "\n")


def _import_allowlist():
    """Import the LIVE ship-allowlist from build_seed so detection == what actually ships.
    Returns (ship_dirs, ship_files) or (None, None) if build_seed can't be imported."""
    try:
        import build_seed  # noqa: WPS433 — build_seed.py lives in .claude/lib (already on sys.path)
        return build_seed.SHIP_DIRS, build_seed.SHIP_FILES
    except Exception:
        return None, None


def _path_is_shipped(rel: str, ship_dirs: dict, ship_files: list) -> bool:
    """Does this repo-relative path (forward slashes) land inside the ship-set? Mirrors
    build_seed.copy_ship: a file ships if it's under a SHIP_DIR and matches no exclude
    substring for that dir, OR it's an exact SHIP_FILE."""
    if rel in ship_files:
        return True
    for d, excludes in ship_dirs.items():
        prefix = d.rstrip("/") + "/"
        if rel == d or rel.startswith(prefix):
            if any(x in rel for x in excludes):
                return False
            return True
    return False


def latest_version_tag() -> str | None:
    """Newest vX.Y.Z tag by semver, or None. git READ only."""
    try:
        r = subprocess.run(["git", "tag", "-l", "v*.*.*", "--sort=-v:refname"],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=30)
        for line in r.stdout.splitlines():
            t = line.strip()
            if re.fullmatch(r"v\d+\.\d+\.\d+", t):
                return t
    except Exception:
        pass
    return None


def changed_since_tag(tag: str, ship_dirs: dict, ship_files: list) -> list[str]:
    """Allowlisted, non-backup files changed since `tag`. git READ only (log + diff).

    Walk each commit since the tag, skip auto-backup commits by subject, collect the
    allowlisted files each remaining commit touched. This excludes backup + tenant/campaign
    churn: backups by subject, non-system files because they aren't on the allowlist."""
    if ship_dirs is None:
        return []
    try:
        log = subprocess.run(
            ["git", "log", "--no-merges", "--format=%H%x1f%s", f"{tag}..HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60)
    except Exception:
        return []
    changed: set[str] = set()
    for line in log.stdout.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        if BACKUP_COMMIT_RE.search(subject):
            continue
        try:
            files = subprocess.run(
                ["git", "show", "--no-renames", "--name-only", "--format=", sha],
                cwd=str(ROOT), capture_output=True, text=True, timeout=30)
        except Exception:
            continue
        for f in files.stdout.splitlines():
            rel = f.strip().replace("\\", "/")
            if rel and _path_is_shipped(rel, ship_dirs, ship_files):
                changed.add(rel)
    return sorted(changed)


def unreleased_section() -> tuple[bool, list[str]]:
    """Read CHANGELOG.md `[Unreleased]` (up to the next `## ` heading). Returns
    (non_empty, content_lines). Non-empty = has any content beyond blank lines/headings."""
    if not CHANGELOG.exists():
        return False, []
    text = CHANGELOG.read_text(encoding="utf-8")
    m = re.search(r"^##\s*\[Unreleased\]\s*$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return False, []
    body = m.group(1)
    lines = [ln.rstrip() for ln in body.splitlines()]
    content = [ln for ln in lines if ln.strip()]
    return (len(content) > 0), content


def stage_and_validate(today: str) -> tuple[bool, str, Path]:
    """Auto-cut + auto-validate a Seed to a STAGING dir via validate_seed.py --cut, which
    runs build_seed (leak scan) then cold-clones + runs doctor/Phase-0/render. NEVER pushes;
    NEVER tags. Returns (validated_ok, tail_output, staging_path)."""
    staging = SYSTEM_DIR / "release-readiness" / "staging" / today
    validate = LIB / "validate_seed.py"
    if not validate.exists():
        return False, "validate_seed.py not present — cannot stage.", staging
    try:
        if staging.exists():
            # re-runnable: hand the recreate to build_seed (it force-rmtrees --out itself)
            pass
        staging.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            [sys.executable, str(validate), "--cut", "--out", str(staging), "--keep"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=900,
            encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0
        # Keep a compact tail for the notification: the verdict + leak line if present.
        tail_lines = []
        for ln in out.splitlines():
            s = ln.strip()
            if any(k in s for k in ("VERDICT:", "LEAK SCAN", "[PASS]", "[FAIL]", "copied ", "sanitised ")):
                tail_lines.append(s)
        tail = "\n".join(tail_lines[-12:]) if tail_lines else out.strip()[-600:]
        return ok, tail, staging
    except subprocess.TimeoutExpired:
        return False, "staging cut timed out (>900s).", staging
    except Exception as e:  # noqa: BLE001
        return False, f"staging cut errored: {type(e).__name__}: {e}", staging


def main() -> int:
    ap = argparse.ArgumentParser(description="Scheduled release-readiness cadence (SYS-063).")
    ap.add_argument("--notify-only", action="store_true",
                    help="detect only; never cut/validate a staging Seed (fast, pure-read).")
    a = ap.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    ship_dirs, ship_files = _import_allowlist()

    unreleased_nonempty, unreleased_lines = unreleased_section()
    tag = latest_version_tag()
    changed = changed_since_tag(tag, ship_dirs, ship_files) if tag else []
    pending = unreleased_nonempty or bool(changed)

    lines = [f"# Release readiness — {today}", ""]
    lines.append(f"- Last release tag: **{tag or '(none found)'}**")
    if ship_dirs is None:
        lines.append("- WARNING: could not import the build_seed allowlist - path-diff detection skipped "
                     "(CHANGELOG `[Unreleased]` still checked).")
    lines.append("")

    if not pending:
        lines += [
            "## Nothing to release",
            "",
            f"The CHANGELOG `[Unreleased]` section is empty and no build_seed-allowlisted "
            f"(system-layer) files have changed since `{tag or 'the last tag'}`. No Seed cut needed.",
            "",
            "_(Auto-backup commits and tenant/campaign churn are excluded — they aren't on the "
            "ship allowlist.)_",
        ]
        report = "\n".join(lines) + "\n"
        _write_and_render(report, today)
        _safe_print(report)
        print("[release-readiness] nothing to release.")
        return 0

    # --- pending ---
    lines.append("## A release is pending")
    lines.append("")
    lines.append("**Triggers:**")
    if unreleased_nonempty:
        lines.append(f"- CHANGELOG `[Unreleased]` is non-empty ({len(unreleased_lines)} content line(s)).")
    else:
        lines.append("- CHANGELOG `[Unreleased]` is EMPTY — but allowlisted files changed since the last "
                     "tag, so the changelog is likely behind. **Add the entries before cutting.**")
    if changed:
        lines.append(f"- {len(changed)} build_seed-allowlisted (system-layer) file(s) changed since "
                     f"`{tag}`.")
    lines.append("")

    if changed:
        lines.append("<details><summary>Changed system-layer files</summary>")
        lines.append("")
        for f in changed[:100]:
            lines.append(f"- `{f}`")
        if len(changed) > 100:
            lines.append(f"- … and {len(changed) - 100} more")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    if unreleased_lines:
        lines.append("<details><summary>CHANGELOG [Unreleased] content</summary>")
        lines.append("")
        lines += [f"    {ln}" for ln in unreleased_lines]
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # Auto-cut + auto-validate a staging Seed (unless notify-only).
    if a.notify_only:
        lines += ["## Staging", "",
                  "_Skipped (--notify-only). Re-run without the flag to auto-cut + validate a staging Seed._"]
    else:
        ok, tail, staging = stage_and_validate(today)
        verdict = "VALIDATED — this staging Seed runs cold" if ok else "NOT validated — see tail"
        lines += [
            "## Staging Seed (cut + cold-run validation)",
            "",
            f"- Staging dir: `{staging}`",
            f"- Result: **{verdict}**",
            "",
            "```",
            tail or "(no output captured)",
            "```",
        ]

    lines += [
        "",
        "## Next (human-gated — this cadence never pushes)",
        "",
        "1. Make sure `[Unreleased]` lists every system-layer change above.",
        "2. Rename `[Unreleased]` -> the new `vX.Y.Z` with today's date; add a fresh empty "
        "`[Unreleased]`.",
        "3. Tag: `git tag -a vX.Y.Z -m \"Soundtrak AI Studio vX.Y.Z\"`.",
        "4. Cut + validate for real: `python .claude/lib/validate_seed.py --cut --out <dir>`.",
        "5. Eyeball it, then **push the Seed to the public repo — the human-gated step.**",
        "",
        "_This cadence stages + notifies only. It runs no git writes and pushes nothing._",
    ]

    report = "\n".join(lines) + "\n"
    _write_and_render(report, today)
    _safe_print(report)
    print("[release-readiness] a release is PENDING - notification written.")
    return 0


def _write_and_render(report: str, today: str) -> None:
    out_dir = SYSTEM_DIR / "release-readiness"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{today}.md"
    out.write_text(report, encoding="utf-8")
    # render to HTML so it's viewable, matching the digest convention (best-effort).
    try:
        subprocess.run([sys.executable, str(SKILLS / "render-html" / "render.py"),
                        "--markdown", str(out), "--template", "base",
                        "--output", str(out.with_suffix(".html"))],
                       cwd=str(ROOT), capture_output=True, timeout=60)
    except Exception:
        pass
    print(f"[release-readiness] wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
