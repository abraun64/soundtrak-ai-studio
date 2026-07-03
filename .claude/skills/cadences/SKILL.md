---
name: cadences
description: |
  SYS-020 — the proactive scheduled-cadence pack. Four read-only timers built on
  the proven SYS-005 weekly-digest pattern, so the system runs sweeps "whether or
  not the operator remembers". Each cadence SURFACES only: it writes a dated
  markdown digest (rendered to HTML) and/or files a DEDUPED inbox idea for
  genuinely-new findings. NONE auto-triages, auto-edits campaigns/tenants, or
  auto-ships — there are no destructive actions anywhere in this pack.

  The four cadences:
  (1) competitor-library-scan (weekly) — surfaces a prompt/checklist to pull new
      exemplars + the System1 Ad-of-the-Week into tenant/library/ as DRAFT
      entries; reports the library's size + freshness; files an idea if the
      library has gone stale. Does NOT fetch or commit.
  (2) tenant-brand-drift (monthly) — flags tenants whose playbook is stale
      relative to the newest shipped asset (read-only mtime comparison).
  (3) stale-sweep — flags assets parked in 'For Human Review' too long and any
      rendered HTML older than its source data.
  (4) tenant-shipped-blocked-rollup (weekly) — per tenant, what shipped
      (Approved this period) vs what's blocked (open operator_actions).

  TRIGGER when the operator wants to run a cadence by hand, inspect a cadence
  digest, or (re)register the scheduled tasks: "run the library scan", "check
  tenant brand drift", "run the stale sweep", "what shipped / what's blocked",
  "register the cadence scheduled tasks".

  DO NOT TRIGGER for campaign work (use /campaign-manager) or for the system
  weekly-health digest (that is SYS-005, in the system-manager skill).
---

# Scheduled cadences (SYS-020)

Both Claude-setup references treat scheduled automations — "Claude on a timer,
runs whether you remember or not" — as a core pillar. Before this pack the system
had exactly one timer: the SYS-005 weekly system-health digest. This pack adds
the four cadences SYS-020 named, each modelled on that proven digest.

**Anchoring guardrail (non-negotiable, identical to the weekly digest).** Every
cadence is READ-ONLY and SURFACES only. A cadence writes a dated markdown digest
and/or files a DEDUPED inbox idea. It NEVER auto-triages, auto-edits a campaign or
tenant, auto-ships, re-renders an operator surface, or takes any destructive
action. Re-rendering is CM's job on a state change; triage is the operator's job
on the inbox. A timer only surfaces.

## Shared machinery — `_cadence_common.py`

One copy of the load-bearing safety logic, factored out of `weekly-digest.py`:

- **Worktree-aware DATA resolution** via `repo_paths.data_root()` — `campaigns/`,
  `tenant-brand/`, `tenant/library/`, and `system/` always resolve to the MAIN
  checkout, even when a cadence runs from a worktree.
- **`file_new_ideas()`** — appends deduped idea entries to `system/ideas.yaml` as
  TEXT (preserves the header + comments; never `safe_dump`), with the YAML-safe
  **quoted title** (idea titles contain colons → invalid unquoted) and the
  **parse-then-rollback** safety net so `ideas.yaml` can never be left
  unparseable. Dedupe is by case-folded title against existing ideas AND backlog
  tickets, so a finding already filed or promoted is not re-raised.
- **`write_digest()`** — writes `system/digests/<subfolder>/<date>-<slug>.md` and
  renders an HTML sibling via the render-html skill. Each cadence owns its own
  `digests/` subfolder so it never collides with the SYS-005 top-level
  `digests/<date>.md`.

## The four scripts

| # | Script | Cadence | Surfaces | Files an idea when |
|---|--------|---------|----------|--------------------|
| 1 | `competitor-library-scan.py` | weekly | library size + freshness + an add checklist (System1 Ad-of-the-Week + competitor/award/operator-spotted) | the library hasn't grown in 14 days |
| 2 | `tenant-brand-drift.py` | monthly | per-tenant playbook mtime vs newest shipped asset | a playbook lags its newest shipped asset by >30 days |
| 3 | `stale-sweep.py` | weekly | assets parked in review >10d + HTML older than its source | either category is non-empty |
| 4 | `tenant-shipped-blocked-rollup.py` | weekly | per tenant: Approved-this-week vs open operator_actions | any tenant has open blocking operator actions |

Run any by hand anytime (safe, read-only):

```
python .claude/skills/cadences/competitor-library-scan.py
python .claude/skills/cadences/tenant-brand-drift.py
python .claude/skills/cadences/stale-sweep.py
python .claude/skills/cadences/tenant-shipped-blocked-rollup.py
```

Thresholds are constants at the top of each script (`STALE_AFTER_DAYS`,
`DRIFT_GAP_DAYS`, `REVIEW_STALE_DAYS` / `SURFACE_SKEW_DAYS`, `PERIOD_DAYS`).

## Schedule (local Windows tasks) — register these by hand

Mirror the SYS-005 task: run by the **REAL pythoncore interpreter**, not the
WindowsApps `python` alias (that stub fails in non-interactive scheduled tasks).
Find the real interpreter on your machine via `python -c "import sys;print(sys.executable)"`
(NOT the WindowsApps `python` alias). The setup block below captures it automatically.

These are a LOCAL step — run each block in an elevated PowerShell. They are not
auto-registered by this skill.

```powershell
$py   = (python -c "import sys; print(sys.executable)")   # the REAL interpreter (verify it's not a WindowsApps stub)
$root = (Get-Location).Path                                # run this block from your Marketing AI System folder

# (1) Competitor / library scan — weekly, Mondays 08:15
Register-ScheduledTask -TaskName "AI Marketing System - Competitor Library Scan" `
  -Action  (New-ScheduledTaskAction  -Execute $py `
              -Argument "`"$root\.claude\skills\cadences\competitor-library-scan.py`"" `
              -WorkingDirectory $root) `
  -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8:15am) `
  -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) `
  -Description "SYS-020 (a): weekly read-only library scan — surfaces exemplars to add as drafts."

# (2) Tenant brand-drift — monthly, 1st of the month 08:30
Register-ScheduledTask -TaskName "AI Marketing System - Tenant Brand Drift" `
  -Action  (New-ScheduledTaskAction  -Execute $py `
              -Argument "`"$root\.claude\skills\cadences\tenant-brand-drift.py`"" `
              -WorkingDirectory $root) `
  -Trigger (New-ScheduledTaskTrigger -Weekly -WeeksInterval 4 -DaysOfWeek Monday -At 8:30am) `
  -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) `
  -Description "SYS-020 (b): monthly read-only brand-drift check — flags playbooks lagging shipped work."

# (3) Stale-asset / stale-surface sweep — weekly, Mondays 08:45
Register-ScheduledTask -TaskName "AI Marketing System - Stale Sweep" `
  -Action  (New-ScheduledTaskAction  -Execute $py `
              -Argument "`"$root\.claude\skills\cadences\stale-sweep.py`"" `
              -WorkingDirectory $root) `
  -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8:45am) `
  -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) `
  -Description "SYS-020 (c): weekly read-only stale sweep — parked reviews + surfaces behind their data."

# (4) Per-tenant shipped/blocked rollup — weekly, Fridays 16:00
Register-ScheduledTask -TaskName "AI Marketing System - Shipped Blocked Rollup" `
  -Action  (New-ScheduledTaskAction  -Execute $py `
              -Argument "`"$root\.claude\skills\cadences\tenant-shipped-blocked-rollup.py`"" `
              -WorkingDirectory $root) `
  -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At 4:00pm) `
  -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) `
  -Description "SYS-020 (d): weekly read-only rollup — per tenant what shipped vs what's blocked."
```

`-WeeksInterval 4` approximates "monthly" within the weekly-trigger API (the
SYS-005 task uses the same `-Weekly` shape). Remove any task with
`Unregister-ScheduledTask -TaskName "<name>"`.

## Boundaries

- **Independent of campaigns.** A cadence never touches a live campaign artifact,
  tenant playbook, asset, or operator surface — it only reads them and writes its
  own digest under `system/digests/<cadence>/`.
- **Surfaces, never acts.** The only writes are (a) a digest file and (b) a
  deduped append to `system/ideas.yaml`. Triage stays the operator's; re-render
  stays CM's.
- **Consumes, doesn't duplicate.** Where a diagnostic already exists (check-state,
  cm-audit) the cadence layer complements it with time-based sweeps, it does not
  re-implement it.
```
