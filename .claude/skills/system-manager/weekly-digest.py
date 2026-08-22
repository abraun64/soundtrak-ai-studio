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
except ImportError:
    DATA = ROOT
SYSTEM_DIR = DATA / "system"
SKILLS = ROOT / ".claude" / "skills"
DIAG_STATE = SYSTEM_DIR / ".diag-state.json"   # SYS-010: consecutive-fail count per diagnostic
ESCALATE_AFTER = 2                              # consecutive RED runs before idea -> ticket
# SYS-138 — diagnostics that REPORT but never escalate. The verification audit lists closures
# that recorded no `verified:`; auto-filing a P1 "persistent verification failure" would be
# circular (a ticket about unverified tickets, itself needing verification) and would turn a
# nudge into board noise. It still shows RED in Health, which is the whole point.
NO_ESCALATE = {"verification"}


# SYS-144 — the digest files ideas and tickets the same way the cadences do, so it inherits
# the same defect: dedupe by TITLE breaks the moment triage sharpens the title on promote, and a
# KILLED finding leaves nothing to match at all. The stable key is a fingerprint. The digest's
# only finding category is "this diagnostic is failing", scoped by which diagnostic.
def diag_fingerprint(label: str) -> str:
    return f"weekly-digest:diagnostic:{label}"


def _fingerprints_of(record) -> set:
    """The finding(s) a record owns. `fingerprint:` is a string OR a list — a MERGE hands the
    surviving ticket everything the records folded into it were tracking, and a single-value
    field would silently drop all but one, releasing the rest to refile."""
    fp = record.get("fingerprint")
    values = fp if isinstance(fp, list) else [fp]
    return {str(v).strip() for v in values if v and str(v).strip()}


def suppressed_fingerprints(include_ideas: bool = True) -> set:
    """Fingerprints that must not be raised again. Shares the cadences' tombstone store so a
    finding killed there stays killed here — one decision, one place, whichever surface raised it.

    `include_ideas` is the important argument. Filing a NEW IDEA must not duplicate a standing
    one, so ideas count. ESCALATING to a ticket must NOT be blocked by the idea it is promoting —
    that is the escalation's entire job, and counting ideas there silently killed the SYS-010
    path: the idea filed on failure #1 suppressed the ticket on failure #2, so a diagnostic could
    stay RED forever with nothing but an inbox row to show for it."""
    out = set()
    # An OPEN ticket means it is already on the board; a KILLED one means the operator decided
    # against it. A DONE ticket does NOT suppress — the problem was fixed, so detecting it again
    # is a new occurrence that must be raised.
    suppressing = ("todo", "in_progress", "killed")
    if include_ideas:
        for rec in load_items(SYSTEM_DIR / "ideas.yaml", "items"):
            out |= _fingerprints_of(rec)
    for rec in load_items(SYSTEM_DIR / "backlog.yaml", "items"):
        if str(rec.get("status", "todo")).strip().lower() in suppressing:
            out |= _fingerprints_of(rec)
    try:
        import yaml as _y
        tomb = SYSTEM_DIR / "cadence-tombstones.yaml"
        if tomb.exists():
            for e in (_y.safe_load(tomb.read_text(encoding="utf-8")) or {}).get("entries") or []:
                out |= _fingerprints_of(e or {})
    except Exception:  # noqa: BLE001 — a malformed tombstone file must not stop the digest
        pass
    return out


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


def _decode(raw: bytes) -> str:
    """Decode a diagnostic's output without mangling it.

    These scripts print ✅ / — / × and they do NOT agree on an encoding: some reconfigure their
    stream to UTF-8, some write the console default (cp1252 on this machine). Decoding
    everything as cp1252 turned em-dashes into "â€”" in the digest the operator reads
    (2026-07-27). Decoding everything as UTF-8 with errors="replace" fixed those and broke the
    others into U+FFFD — which then CRASHED this script on `print(digest)` against a cp1252
    console. So try UTF-8 strictly first and fall back, rather than picking a side."""
    for enc in ("utf-8", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def run_diag(label: str, script: Path, args: list | None = None) -> tuple[str, bool, str]:
    if not script.exists():
        return label, True, "(not present — skipped)"
    try:
        # BYTES, decoded by _decode above — see why there.
        r = subprocess.run([sys.executable, str(script), *(args or [])], cwd=str(ROOT),
                           capture_output=True, timeout=180)
        tail = ""
        for line in reversed(_decode(r.stdout or r.stderr or b"").splitlines()):
            if line.strip():
                tail = line.strip()
                break
        return label, r.returncode == 0, tail
    except Exception as e:  # noqa: BLE001
        return label, False, str(e)[:120]


def file_new_ideas(ideas: list, new_titles: list, today: str,
                   fingerprints: list | None = None) -> list:
    """Append deduped idea entries to ideas.yaml as TEXT (preserves the file's header +
    formatting — never safe_dump, which would drop comments). Returns the ids filed."""
    if not new_titles:
        return []
    nums = [int(str(i.get("id", "IDEA-0")).split("-")[-1]) for i in ideas
            if str(i.get("id", "")).startswith("IDEA-")]
    nxt = (max(nums) + 1) if nums else 1
    chunks, filed = [], []
    fps = list(fingerprints or []) + [""] * len(new_titles)
    for t, fp in zip(new_titles, fps):
        iid = f"IDEA-{nxt:03d}"
        nxt += 1
        filed.append(iid)
        safe_t = t.replace('"', "'")            # title is controlled, but be defensive
        # SYS-144 — carried onto the ticket by triage on promote; without it the finding
        # refiles the moment the title is sharpened.
        fp_line = f'    fingerprint: "{fp}"\n' if fp else ""
        chunks.append(
            f"\n  - id: {iid}\n"
            f'    title: "{safe_t}"\n'           # QUOTED — titles contain colons (invalid unquoted)
            f"{fp_line}"
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


def open_escalation(backlog: list, label: str):
    """The OPEN 'Persistent diagnostic failure: <label>' ticket, if any. Shared by the
    escalate path (dedupe) and the recovery report (SYS-141)."""
    title = f"Persistent diagnostic failure: {label}".lower()
    for b in backlog:
        if str(b.get("title", "")).lower() == title and b.get("status") in ("todo", "in_progress"):
            return b
    return None


def escalate_to_ticket(label: str, fails: int, backlog: list, today: str):
    """SYS-010 — append a deduped P1 ticket for a PERSISTENT diagnostic failure. Text-append
    + YAML-validation rollback so backlog.yaml can never be left unparseable. Returns the new
    SYS id, or None if one is already open / on error.

    `backlog` is MUTATED on success. It has to be: the next id comes from max(backlog ids),
    so two diagnostics escalating in the same run both computed the SAME id off the same
    stale list and wrote two blocks claiming it — which is exactly what happened on
    2026-08-11 (smoke-test and drift-gate both filed as "SYS-141"; the collision had to be
    repaired by hand into SYS-141 + SYS-142). Appending the new item keeps the second call
    honest, and also lets it dedupe against a ticket this same run just filed."""
    title = f"Persistent diagnostic failure: {label}"
    if open_escalation(backlog, label) is not None:
        return None
    if diag_fingerprint(label) in suppressed_fingerprints(include_ideas=False):
        return None  # SYS-144 — already a ticket under another title, or killed at triage
    nums = [int(str(b.get("id", "")).split("-")[-1]) for b in backlog
            if str(b.get("id", "")).startswith("SYS-") and str(b.get("id", "")).split("-")[-1].isdigit()]
    iid = f"SYS-{((max(nums) + 1) if nums else 11):03d}"
    block = (
        f"\n  - id: {iid}\n"
        f'    title: "{title}"\n'
        f'    fingerprint: "{diag_fingerprint(label)}"\n'   # SYS-144 — survives retitling
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
    backlog.append({"id": iid, "title": title, "status": "todo", "priority": "P1",
                    "fingerprint": diag_fingerprint(label)})
    return iid


def main() -> int:
    # The digest is written UTF-8, but ECHOING it must not crash on a cp1252 console — which is
    # exactly what a scheduled task gets. A digest that was written correctly and then died on
    # its own print reports as a FAILED task (2026-08-22).
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
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
        # SYS-138 — closures that never recorded HOW they were verified. A report, not a
        # blocker: the agreed rule is you may not close without RECORDING what you ran, but you
        # may record a lower level with a stated reason. A must-pass gate is what produced the
        # file-existence "UAT" this framework exists to prevent.
        ("verification", SKILLS / "system-manager" / "verify.py", ["--audit"]),
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
    fp_seen = suppressed_fingerprints()          # SYS-144 — filed-or-killed, by stable key
    new_titles, new_fps, escalated, recovered = [], [], [], []
    for label, ok, _tail in results:
        if ok:
            # SYS-141 — escalation was one-way: a diagnostic could go green and its P1 ticket
            # would sit open forever with nothing saying it had self-healed. That is what
            # happened to the smoke-test ticket (RED 2026-08-11, green again by 2026-08-17,
            # still P1 open on 2026-08-22) — and while a stale P1 sits at the top of the board
            # the operator can't tell a real breakage from a standing one, which is the exact
            # trust loss the ticket was filed about. Surface the recovery; don't auto-close it
            # (this digest SURFACES, the operator triages). Deliberately NOT gated on "was it
            # red last run" — a ticket that went green weeks ago and was never closed is the
            # worse case, and it keeps showing until someone closes it.
            t_open = open_escalation(backlog, label)
            if t_open:
                recovered.append((str(t_open.get("id")), label))
            state[label] = 0
            continue
        state[label] = state.get(label, 0) + 1
        if label in NO_ESCALATE:
            continue          # surfaced in Health above; never becomes a ticket
        if state[label] >= ESCALATE_AFTER:
            tid = escalate_to_ticket(label, state[label], backlog, today)
            if tid:
                escalated.append((tid, label, state[label]))
        else:
            title = f"Diagnostic failing: {label}"
            fp = diag_fingerprint(label)
            if fp not in fp_seen and title.lower() not in seen:
                new_titles.append(title)
                new_fps.append(fp)
                fp_seen.add(fp)
                seen.add(title.lower())
    _save_diag_state(state)
    filed = file_new_ideas(ideas, new_titles, today, new_fps)

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
    if recovered:
        lines += ["", "## Recovered — close these (SYS-141)",
                  "These diagnostics are GREEN again, but their escalated ticket is still open. "
                  "Verify and close, or say why it stays open."]
        lines += [f"- {tid}: {label} is passing again — candidate to close" for tid, label in recovered]
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
