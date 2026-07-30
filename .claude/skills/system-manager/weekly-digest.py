#!/usr/bin/env python3
"""SYS-005 (minimal) — weekly System Manager digest.

Runs the read-only diagnostics, summarises the current backlog + inbox, auto-files any
genuinely-new diagnostic FAILURE as a deduped idea, writes a digest the operator reads,
and re-renders the dashboard. It SURFACES — it never triages or changes the backlog
itself (the operator still triages the inbox).

  python .claude/skills/system-manager/weekly-digest.py

Designed to run on a weekly schedule (SYS-005); safe to run by hand anytime. Worktree-
aware (resolves system/ + campaigns/ to the main checkout via repo_paths).
"""
from __future__ import annotations
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)
except Exception:
    DATA = ROOT
SYSTEM_DIR = DATA / "system"
SKILLS = ROOT / ".claude" / "skills"
DIAG_STATE = SYSTEM_DIR / ".diag-state.json"   # SYS-010: consecutive-fail count per diagnostic
ESCALATE_AFTER = 2                              # consecutive RED runs before idea -> ticket


def load_items(path: Path, key: str) -> list:
    try:
        import yaml
    except ImportError:
        return []
    if not path.exists():
        return []
    try:
        return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(key, []) or []
    except Exception:
        return []


def run_diag(label: str, script: Path, args: list | None = None) -> tuple[str, bool, str]:
    if not script.exists():
        return label, True, "(not present — skipped)"
    try:
        r = subprocess.run([sys.executable, str(script), *(args or [])], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=180)
        tail = ""
        for line in reversed((r.stdout or r.stderr or "").splitlines()):
            if line.strip():
                tail = line.strip()
                break
        return label, r.returncode == 0, tail
    except Exception as e:  # noqa: BLE001
        return label, False, str(e)[:120]


def file_new_ideas(ideas: list, new_titles: list, today: str) -> list:
    """Append deduped idea entries to ideas.yaml as TEXT (preserves the file's header +
    formatting — never safe_dump, which would drop comments). Returns the ids filed."""
    if not new_titles:
        return []
    nums = [int(str(i.get("id", "IDEA-0")).split("-")[-1]) for i in ideas
            if str(i.get("id", "")).startswith("IDEA-")]
    nxt = (max(nums) + 1) if nums else 1
    chunks, filed = [], []
    for t in new_titles:
        iid = f"IDEA-{nxt:03d}"
        nxt += 1
        filed.append(iid)
        safe_t = t.replace('"', "'")            # title is controlled, but be defensive
        chunks.append(
            f"\n  - id: {iid}\n"
            f'    title: "{safe_t}"\n'           # QUOTED — titles contain colons (invalid unquoted)
            f"    raised_by: weekly-digest\n"
            f"    date: {today}\n"
            f"    source: diagnostic\n"
            f"    summary: Auto-filed by the weekly digest; triage to confirm or kill.\n"
            f"    description: >-\n"
            f"      The weekly digest found {safe_t.lower()}. Investigate and triage.\n"
        )
    ideas_path = SYSTEM_DIR / "ideas.yaml"
    existing = ideas_path.read_text(encoding="utf-8")
    if not existing.endswith("\n"):
        existing += "\n"
    ideas_path.write_text(existing + "".join(chunks), encoding="utf-8")
    # Safety net: NEVER leave ideas.yaml unparseable. If the append broke it, roll back.
    try:
        import yaml as _y
        _y.safe_load(ideas_path.read_text(encoding="utf-8"))
    except Exception:
        ideas_path.write_text(existing, encoding="utf-8")
        return []
    return filed


def _load_diag_state() -> dict:
    import json
    try:
        return json.loads(DIAG_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_diag_state(s: dict) -> None:
    import json
    try:
        DIAG_STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")
    except Exception:
        pass


def escalate_to_ticket(label: str, fails: int, backlog: list, today: str):
    """SYS-010 — append a deduped P1 ticket for a PERSISTENT diagnostic failure. Text-append
    + YAML-validation rollback so backlog.yaml can never be left unparseable. Returns the new
    SYS id, or None if one is already open / on error."""
    title = f"Persistent diagnostic failure: {label}"
    if any(str(b.get("title", "")).lower() == title.lower()
           and b.get("status") in ("todo", "in_progress") for b in backlog):
        return None
    nums = [int(str(b.get("id", "")).split("-")[-1]) for b in backlog
            if str(b.get("id", "")).startswith("SYS-") and str(b.get("id", "")).split("-")[-1].isdigit()]
    iid = f"SYS-{((max(nums) + 1) if nums else 11):03d}"
    block = (
        f"\n  - id: {iid}\n"
        f'    title: "{title}"\n'
        f"    status: todo\n"
        f"    priority: P1\n"
        f"    needs: you\n"
        f"    layer: system\n"
        f"    raised_by: weekly-digest\n"
        f"    date: {today}\n"
        f"    source: diagnostic (SYS-010 escalation)\n"
        f'    summary: "{label} RED for {fails} consecutive digest runs — escalated idea to ticket."\n'
        f"    description: >-\n"
        f"      The weekly digest's {label} check has been RED for {fails} consecutive runs\n"
        f"      (SYS-010 persistence escalation — single transient blips are NOT escalated).\n"
        f"      Investigate the diagnostic output, fix the root cause, then close.\n"
    )
    p = SYSTEM_DIR / "backlog.yaml"
    existing = p.read_text(encoding="utf-8")
    if not existing.endswith("\n"):
        existing += "\n"
    p.write_text(existing + block, encoding="utf-8")
    try:
        import yaml as _y
        _y.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        p.write_text(existing, encoding="utf-8")   # never leave backlog.yaml broken
        return None
    return iid


def main() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    diagnostics = [
        ("smoke-test", SKILLS / "system-smoke-test" / "smoke_test.py", None),
        ("nav-audit", SKILLS / "nav-audit" / "nav_audit.py", None),
        # docs-audit: CONTENT/STRUCTURE layer over nav-audit's presence check —
        # stale agent-count prose, dropped index columns, public docs behind the
        # roster (SYS-018/SYS-026). Persistent RED auto-files per SYS-010.
        ("docs-audit", SKILLS / "docs-audit" / "docs_audit.py", None),
        ("cm-audit", SKILLS / "cm-audit" / "cm_audit.py", None),
        # SYS-038: board-currency / world-↔-data drift — gate.py flags NEW pending-but-
        # -moved-past actions vs the accepted baseline; persistent ones escalate (SYS-010).
        ("drift-gate", SKILLS / "check-state" / "gate.py", ["--all-campaigns"]),
    ]
    results = [run_diag(label, script, args) for label, script, args in diagnostics]

    backlog = load_items(SYSTEM_DIR / "backlog.yaml", "items")
    ideas = load_items(SYSTEM_DIR / "ideas.yaml", "items")
    open_items = [i for i in backlog if i.get("status") in ("todo", "in_progress")]
    by_p = {p: len([i for i in open_items if i.get("priority") == p]) for p in ("P1", "P2", "P3")}
    needs_you = len([i for i in open_items if str(i.get("needs", "you")).strip().lower() != "ai"])

    # RED diagnostics: track persistence (SYS-010). First failure → deduped idea; a failure
    # that PERSISTS (>= ESCALATE_AFTER consecutive runs) → deduped P1 ticket. Transient single
    # blips never escalate (that's what bit ideas.yaml before — surface, don't over-react).
    seen = {str(i.get("title", "")).lower() for i in ideas} | {str(b.get("title", "")).lower() for b in backlog}
    state = _load_diag_state()
    new_titles, escalated = [], []
    for label, ok, _tail in results:
        if ok:
            state[label] = 0
            continue
        state[label] = state.get(label, 0) + 1
        if state[label] >= ESCALATE_AFTER:
            tid = escalate_to_ticket(label, state[label], backlog, today)
            if tid:
                escalated.append((tid, label, state[label]))
        else:
            title = f"Diagnostic failing: {label}"
            if title.lower() not in seen:
                new_titles.append(title)
                seen.add(title.lower())
    _save_diag_state(state)
    filed = file_new_ideas(ideas, new_titles, today)

    lines = [f"# System weekly digest — {today}", ""]
    lines.append("## Health")
    for label, ok, tail in results:
        mark = "PASS" if ok else "FAIL"
        lines.append(f"- **{mark}** — {label}" + (f" — {tail}" if (not ok and tail) else ""))
    lines += [
        "", "## Open work",
        f"- To Do: {len(open_items)} open ({by_p['P1']} P1 · {by_p['P2']} P2 · {by_p['P3']} P3) — {needs_you} need you",
        f"- Inbox: {len(ideas) + len(filed)} untriaged ideas",
    ]
    if filed:
        lines += ["", "## Filed this run (deduped — triage to confirm)"]
        lines += [f"- {iid}: {t}" for iid, t in zip(filed, new_titles)]
    if escalated:
        lines += ["", "## Escalated to tickets (persistent failures — SYS-010)"]
        lines += [f"- {tid}: {label} (RED {n} runs)" for tid, label, n in escalated]
    lines += ["", "## Next",
              "Run `/system-manager` to groom, or `/system-manager triage` to clear the inbox."]
    digest = "\n".join(lines) + "\n"

    digests_dir = SYSTEM_DIR / "digests"
    digests_dir.mkdir(parents=True, exist_ok=True)
    out = digests_dir / f"{today}.md"
    out.write_text(digest, encoding="utf-8")

    # render the digest to HTML so the dashboard can link a viewable version
    try:
        subprocess.run([sys.executable, str(SKILLS / "render-html" / "render.py"),
                        "--markdown", str(out), "--template", "base",
                        "--output", str(out.with_suffix(".html"))],
                       cwd=str(ROOT), capture_output=True, timeout=60)
    except Exception:
        pass

    print(digest)
    print(f"[weekly-digest] wrote {out}" + (f" · filed {len(filed)} idea(s)" if filed else ""))

    # Re-render the dashboard so any filed ideas show in the inbox
    try:
        subprocess.run([sys.executable, str(SKILLS / "system-manager" / "build-dashboard.py")],
                       cwd=str(ROOT), capture_output=True, timeout=60)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
