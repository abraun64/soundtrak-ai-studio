---
name: system-smoke-test
description: |
  Run a system-level health check on the AI Marketing System.

  Validates that the operator-quartet renders cleanly for all active campaigns,
  the gallery builds without errors, hooks are wired correctly, and the render
  pipeline is operational. Returns a traffic-light report: green (all pass),
  amber (warnings), red (failures requiring action).

  TRIGGER when: after any significant system change (spec update, hook edit,
  new skill, Python version change, new machine setup); before onboarding a new
  tenant; when something feels "off" and you can't pinpoint it.
  Common phrasings: "run system smoke test", "check the system is working",
  "validate everything still works", "system health check".

  DO NOT TRIGGER for: campaign-specific issues (use campaign dashboard instead);
  routine session work; gallery rebuilds (those happen automatically via hooks).
---

# System Smoke Test

**Version**: v1.0 · 2026-06-15 (implemented)
**Status**: Implemented — `smoke_test.py`. The scaffold was promoted to a working runner when the tenant-layer + governance + Phase-1–6 system changes landed.
**Owner**: CM (operator-triggered on demand)

## How to run

```
python .claude/skills/system-smoke-test/smoke_test.py
```

Read-only, < 30s, stdlib + PyYAML. Prints the traffic-light report below and exits 0 (all green) or 1 (any failure, with the reason inline). When this skill is invoked, **run that command and relay the report** — don't just describe the checks.

This skill runs a structured validation of the AI Marketing System's core machinery. It does NOT test campaign content quality — it tests that the system infrastructure is operational. The check tables below document what `smoke_test.py` verifies.

---

## What it checks

### Layer 1 — Render pipeline

| Check | Pass criteria | Command |
|---|---|---|
| render.py is callable | Exits 0 with `--help` | `python .claude/skills/render-html/render.py --help` |
| Sample MD renders to HTML | Output file exists + non-empty | Render `docs/workflow.md` → temp HTML |
| build-gallery.py is callable | Exits 0 with `--help` | `python .claude/skills/asset-gallery/build-gallery.py --help` |

### Layer 2 — Operator-quartet per active campaign

For each campaign in `campaigns/`:
| Check | Pass criteria |
|---|---|
| `<slug>.html` exists + mtime recent | File present; mtime within 7 days of newest MD in campaign |
| `gallery.html` exists | File present |
| `tasks.html` exists | File present |
| `campaigns/index.html` exists | File present |

### Layer 3 — Hook wiring

| Check | Pass criteria |
|---|---|
| `settings.json` has PostToolUse hook | `settings.json` contains `post_tool_use.py` reference |
| `settings.json` has Stop hook | `settings.json` contains `stop.py` reference |
| Hook scripts are executable Python | `python .claude/hooks/post_tool_use.py` exits without syntax error |
| Hook scripts are executable Python | `python .claude/hooks/stop.py` exits without syntax error |

### Layer 4 — Git repos (if applicable)

| Check | Pass criteria |
|---|---|
| System repo is clean or has committed changes | `git status` exits 0 |
| Campaigns repo is clean or has committed changes | `git -C campaigns status` exits 0 |

### Layer 5 — Drift gate (added 2026-06-15)

The gate (`gate.py`) is the hard pass/fail for the drift class — RED if anything introduced drift beyond the accepted baseline.

| Check | Pass criteria | Command |
|---|---|---|
| No NEW drift vs baseline | `gate.py --all-campaigns` exits 0 (RED on exit 1 = new drift) | `python .claude/skills/check-state/gate.py --all-campaigns` |
| Baseline file present | `.claude/state/drift-baseline.json` exists | — |
| `gate.py` callable | imports `check.py` + runs | `python .claude/skills/check-state/gate.py --all-campaigns` |

To accept current drift as the new known baseline (after deliberately resolving or accepting items): `gate.py --all-campaigns --write-baseline`.

---

## Output format

```
=== SYSTEM SMOKE TEST ===
Date: YYYY-MM-DD HH:MM

LAYER 1 — Render pipeline
  render.py callable ............. PASS
  MD → HTML render ............... PASS
  build-gallery.py callable ...... PASS

LAYER 2 — Operator-quartet (4 campaigns)
  beta-corp ................. PASS
  gamma ........................... PASS
  the-signal ..................... PASS
  soundtrak-overview ............. PASS

LAYER 3 — Hook wiring
  PostToolUse hook wired ......... PASS
  Stop hook wired ................ PASS
  post_tool_use.py syntax ........ PASS
  stop.py syntax ................. PASS

LAYER 4 — Git repos
  system repo status ............. PASS
  campaigns repo status .......... PASS

LAYER 5 — Drift gate
  no new drift (vs baseline) ..... PASS
  baseline present ............... PASS

RESULT: ALL GREEN
```

If any check fails, emit the failure reason and the fix command.

---

## Implementation notes (for when this is built)

- Keep it fast: target total runtime < 30 seconds. Use `subprocess.run` with short timeouts.
- Keep it non-destructive: read-only checks only. No writes, no state changes.
- Keep it self-contained: no external dependencies beyond Python stdlib + what's already in the system.
- The campaign quartet checks just verify file existence + recency — they don't validate HTML content.

---

## Deferred until first regression

The implementation is deliberately not built yet. Build it when:
- A system change silently breaks something that this test would have caught
- A second deployer is onboarded and needs a reliable "does this work?" check before using it
- The render pipeline is consolidated (E5) and a single entry-point exists to test

Per `docs/specs/retro.md` queued-cleanup-decay rule: this scaffold captures the design so it doesn't have to be rethought from scratch when the moment comes.
