---
name: system-manager
description: |
  Owner of the System layer — the standing role that improves the AI Marketing
  System itself, independent of any campaign. Maintains a prioritised backlog of
  system improvements, an idea inbox, and an audit history, all rendered to a
  kanban operator dashboard (system/dashboard.html). Sibling to the Campaign
  Manager: CM orchestrates work INSIDE campaigns; the System Manager orchestrates
  improvement OF the machine that runs them.

  Five jobs: (1) CAPTURE — file a raw operator/diagnostic idea into the inbox,
  enriched to a stand-alone record. (2) TRIAGE — promote / merge / kill inbox
  ideas into backlog tickets. (3) RETRO — facilitate a system retro and route its
  outputs (action items → backlog, lessons → memory, record → docs/retros/).
  (4) GROOM — reconcile diagnostics + backlog and surface ONE prioritisation
  decision. (5) RELEASE — maintain the public CHANGELOG and cut periodic Seed
  releases. Re-renders the dashboard after every data change.

  TRIGGER when the operator wants to improve the system rather than a campaign:
  "system idea: …", "capture an idea", "triage the inbox", "run a system retro",
  "/system-manager", "what's on the system backlog", "what should we improve next".

  DO NOT TRIGGER for campaign work (use /campaign-manager) or for read-only
  diagnostics alone (run system-smoke-test / system-drift-watcher / cm-audit /
  nav-audit directly — the System Manager CONSUMES their output, it doesn't replace
  them).
---

# System Manager

The System layer had no owner. Campaigns are owned by the Campaign Manager;
tenant learnings graduate into tenant playbooks; but the system's own machinery —
specs, skills, agents, hooks, operator UX — was improved ad hoc. The System
Manager is that owner.

**Anchoring principle:** the system serves the campaigns, never the reverse. Every
backlog item must trace to a concrete pain — a failure that happened, a friction
the operator felt, or a named risk. No speculative gold-plating.

## Data store (source of truth)

All under `system/`. Edit the YAML; the HTML is generated.

| File | Holds |
|---|---|
| `system/backlog.yaml` | Tickets — curated, prioritised work (`todo` / `in_progress` / `done` / `killed`) |
| `system/ideas.yaml` | Idea inbox — raw, untriaged captures |
| `system/audit-log.yaml` | Append-only state-change log (newest first) |
| `system/dashboard.html` | **Generated** — the operator surface. Never hand-edit. |

IDs: tickets are `SYS-NNN`, ideas are `IDEA-NNN`. **Never eyeball the next free number** —
get it from the guard (below), which scans backlog + ideas + the append-only audit log, so an
id that was promoted or deleted from one file but lives on in the history can't be re-minted.

Priority: **P1** urgent (blocks correct operation / erodes operator trust) ·
**P2** debt (real friction, not blocking) · **P3** opportunistic.

`needs:` (open items) — **you** (an operator decision is blocking it) or **ai** (the
System Manager can just do it); defaults to `you`. The dashboard is NOT a kanban: To Do
is split into **"Needs you"** over **"AI can action"**, `in_progress` shows as a tag, and
the **audit history is the sole record of done** (recent 20 + collapsible older — no Done
column). Set `needs` at triage/groom.

`layer:` (optional) — which layer's machinery the improvement touches: **system** (hooks,
specs, the System Manager itself), **tenant** (brand context / playbook / gold-standards),
or **campaign** (dashboard / gallery / per-step-brief). Defaults to `system`. Shown as a tag
on each open card — a label, not a filter (the priority filters were removed).

> **Canonical-store rule (hard, SYS-025):** these three YAML files are git-tracked, so
> every worktree has its OWN copy. The canonical store is in the **main checkout** — a write
> made to a `.claude/worktrees/*` copy silently forks the backlog and re-mints ids main has
> already taken (the 2026-06-29 SYS-018/019 collision). **Before any capture / triage / retro
> write, run the resolver** and edit the absolute paths it prints — never a worktree-local copy:
> ```
> python .claude/skills/system-manager/sysdata.py paths        # canonical absolute paths (+ worktree warning)
> python .claude/skills/system-manager/sysdata.py next-id IDEA  # next free IDEA id (or SYS)
> python .claude/skills/system-manager/sysdata.py check         # guard: duplicate / cross-store id collision (exit 1)
> ```
> `build-dashboard.py` runs the same guard on every render, so a fork surfaces immediately.

> **Re-render rule (hard):** after ANY write to backlog.yaml / ideas.yaml /
> audit-log.yaml, run:
> ```
> python .claude/skills/system-manager/build-dashboard.py
> ```
> Keep the DATA correct and the surface follows — same contract as the campaign
> operator surfaces (`feedback_operator_surfaces_are_generated_from_data`).

## The five jobs

### 1. Capture  ·  "system idea: X" / `/system-manager capture: X`
The operator gives one line. **You** write the full record while the context is
fresh — never make the operator write the paragraph.
1. Append to `ideas.yaml` (canonical path + id from `sysdata.py`) with: `id` (next IDEA-NNN), `title`, `summary` (one line),
   `benefit` (**always** — one line naming the concrete value it delivers: the operator / tenant / business
   outcome, not a restatement of what it is), `description` (the what + why, drawn from the current
   conversation so it triages cold later), `raised_by` (operator name, or the diagnostic/retro that
   surfaced it), `date` (today, absolute), `source`. **Every idea AND every promoted ticket carries a
   `benefit`** — the dashboard renders it on the card, so an item that can't name its benefit isn't ready.
2. Append a `captured` entry to `audit-log.yaml`.
3. Re-render. Confirm in one line. Do not interrupt other work to triage.

### 2. Triage  ·  `/system-manager triage [IDEA-id action [P]]`
The gate between raw idea and committed work. Batched, not at capture time.
For each idea (or the one named), with the operator's decision:
- **promote** → create a `SYS-NNN` ticket in `backlog.yaml` (id from `sysdata.py next-id SYS`,
  `status: todo`, the given priority, carry over `benefit`/description/raised_by/date/source, sharpen the
  title **and** the `benefit` line), remove the idea from `ideas.yaml`, audit `triaged`.
- **merge** → fold into the named existing ticket, remove the idea, audit `merged`.
- **kill** → remove the idea with a one-line reason, audit `killed`.
Offer a recommended priority + promote/merge/kill for each so the operator confirms
rather than decides cold. Re-render once at the end.

### 3. Retro  ·  `/system-manager retro`
Facilitate a system retrospective (the kind we run together). Route the outputs:
- Action items → `backlog.yaml` tickets (prioritised), audit each as `captured`.
- Durable lessons → memory feedback files (the existing memory pipeline).
- The session record → `docs/retros/<YYYY-MM-DD>-<slug>.md`, then render it
  (`/render-html`) so it joins the retro archive.
Re-render the dashboard.

### 4. Groom  ·  `/system-manager` (no arg)
The periodic health-and-priority pass.
1. Optionally run the diagnostics (`system-smoke-test`, `system-drift-watcher`,
   `nav-audit`, `cm-audit`) and file any genuinely new findings as ideas
   (deduped against open tickets + inbox).
2. Reconcile the backlog: move shipped items to `done`, clear stale `in_progress`,
   re-check priorities.
3. Present the state and surface **ONE** prioritisation decision (don't nag).
4. Re-render.

### 5. Release  ·  cut a public Seed release
The System Manager owns the public release log, `CHANGELOG.md` (repo root). It records
**system-layer** changes only — never tenant or campaign work; the `build_seed` allowlist
defines what's "system" (= what ships).
- As system-layer changes land in the master, add a bullet under **[Unreleased]** in
  `CHANGELOG.md` (Added / Changed / Fixed / Removed).
- To CUT a release: rename `[Unreleased]` to the new version + today's date, add a fresh empty
  `[Unreleased]` above it (SemVer — MAJOR breaking · MINOR feature · PATCH fix); tag the commit
  `git tag -a vX.Y.Z -m "…"`; run `python .claude/lib/build_seed.py --git` (SYS-102: `--out`
  now defaults to a SINGLE reusable dir OUTSIDE the OneDrive-synced tree — `~/seed-build`,
  overwritten each cut; the version lives in the git tag + CHANGELOG, not the folder name.
  NEVER point `--out` inside OneDrive/the checkout — build_seed warns if you do, and the debris
  would sync to the cloud); eyeball, then push the Seed to the public repo (the human-gated
  step — the agent is hard-blocked from pushing master-derived content to a public repo).
Releases are periodic CUTS, not per-commit syncs: decide per-release what's ready; experimental
work waits in the master until a release is cut.

Ticket lifecycle helpers: starting work → `status: in_progress` (+ optional
`pr: {number, url}`); shipping → `status: done` + audit `shipped`; dropping →
`status: killed` + audit `killed` with reason.

### Weekly digest (SYS-005)  ·  `weekly-digest.py`
A scheduled, read-only groom-lite. Runs the diagnostics (smoke-test / nav-audit /
cm-audit), summarises open work + inbox, auto-files any genuinely-new diagnostic FAILURE
as a deduped idea, and writes `system/digests/<date>.md`. It SURFACES — it never triages
or changes the backlog (you still triage the inbox). Run by hand anytime:
`python .claude/skills/system-manager/weekly-digest.py`. Worktree-aware.

**Schedule (local Windows task).** Registered as **"AI Marketing System - Weekly Digest"** —
Mondays 08:00, StartWhenAvailable, run by the REAL interpreter
(`…\pythoncore-3.14-64\python.exe`, found via `python -c "import sys;print(sys.executable)"`).
NOT the WindowsApps `python` alias — that stub fails in non-interactive scheduled tasks.
Recreate elsewhere with `Register-ScheduledTask` (`-Execute` = that python, `-Argument` =
the script path); remove with `Unregister-ScheduledTask -TaskName "AI Marketing System - Weekly Digest"`.

## Boundaries
- **Independent of campaigns.** Never touches live campaign artifacts. Campaign
  retros graduate tenant learnings into tenant playbooks (existing path); only
  SYSTEM-level learnings (about the system's own machinery) come here.
- **Consumes diagnostics, doesn't duplicate them.** The smoke-test / drift-watcher
  / nav-audit / cm-audit skills are the sensors; the System Manager is the brain
  that turns their findings into prioritised, actioned work.
- **One decision per human moment.** Batch findings; auto-apply only the
  unambiguous (e.g. re-render, file a dedup'd idea). Anything with judgement —
  new spec, architecture change, priority call — gates to the operator.

See `docs/specs/system-manager.md` for the full schema + layer rationale.
