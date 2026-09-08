# Data Architecture — Single Source of Truth

**Status**: Canonical · adopted 2026-06-10 after a session that uncovered ~5 distinct status-drift bugs.

## The rule

**`asset.yaml` is the single source of truth for everything about an asset.**

Status. File metadata. Operator actions. Channel. Asset name. All of it.

Every operator-facing surface that displays asset state — preview pages, asset records, the campaign dashboard, the gallery, cross-campaign tasks — **derives** from `asset.yaml` at render time. No surface hand-authors state.

If a surface needs to show asset state, it gets it via:
- An auto-inject marker in the markdown (`<!-- STATUS_AUTO -->`, `<!-- OPERATOR_ACTIONS_AUTO -->`, `<!-- ASSET_LIST_AUTO -->`)
- A render-time scan of `assets/*/asset.yaml` (gallery does this directly; render-html does this via `operator_actions.py`)

## Why

Before this rule, asset state was hand-authored in 5+ places per asset:
- `asset.yaml` `status:` field
- `<NN>-<slug>.md` `**Status**:` line
- `preview.md` `**Status**:` line
- Campaign dashboard's "🚨 To Do" table (rows like "Gate Asset #X")
- Campaign dashboard's "📋 Full asset list" table

Each layer drifted independently. The gallery once said "For Human Review" for assets that had been Approved twice over, because the operator updated `preview.md` but never touched `asset.yaml`. The dashboard once said "Wave 2 Producer in flight" three weeks after Wave 2 closed. We caught all of this only when a third-party (a future-the operator, a stakeholder, a client) tried to read the surfaces and pointed at the contradictions.

The bug class is structural. Hand-authoring derived data **always** drifts. The only fix is to stop hand-authoring derived data.

## Approved surfaces and what they derive from

| Surface | What it shows | Sourced from | Mechanism |
|---|---|---|---|
| `gallery.html` | Tile status badges | `asset.yaml` `status:` (primary) + MD scan (fallback) | `build-gallery.py` reads yaml first |
| `preview.html` `**Status**:` line | Asset's current status | `asset.yaml` `status:` | `<!-- STATUS_AUTO -->` marker, injected by `operator_actions.py:inject_asset_status_line()` at render time |
| `<NN>-<slug>.html` `**Status**:` line | Asset's current status | `asset.yaml` `status:` | same as above |
| Dashboard "🚨 To Do" | Pending operator actions across the campaign | every `assets/*/asset.yaml` `operator_actions:` with `status: pending` | `<!-- OPERATOR_ACTIONS_AUTO -->` marker, injected via `operator_actions.py:render_actions_table_md()` |
| Dashboard "📋 Full asset list" | Asset roster with current statuses | every `assets/*/asset.yaml` (name + status) | `<!-- ASSET_LIST_AUTO -->` marker, injected via `operator_actions.py:render_asset_list_table_md()` |

## What's NOT derived (yet) — Phase 4 backlog

These surfaces still hand-author derivable data and will be migrated in a future pass:

- `campaigns/tasks.md` cross-campaign queue — should auto-derive from all campaigns' yaml operator_actions
- `campaigns/index.md` campaign roster — should auto-derive from a folder scan
- Dashboard "Agents currently active" section (in some dashboards) — could auto-derive from asset statuses (in-production = Producer in flight, for-human-review = Brand queued, etc.)
- `campaigns/<slug>/<slug>.md` stage line + phase descriptions — could auto-derive from `assets/*/asset.yaml` status aggregation

Until then, these are noted as **known drift surfaces**. `check-state.py` flags drift in them where detectable.

## Tools that enforce + maintain the rule

### Authoring side

- **`status-propagator/propagate.py`** — single command to update status across all the asset-local layers (yaml + numeric-prefix .md + preview.md if any still hand-author it + HTMLs + gallery). Also handles `--task <id> --done` for `operator_actions`. **Use this every time you change asset state.** Never edit yaml's `status:` field by hand if propagator can do it.

- **`render-html/render.py`** — render markdown to HTML. When the markdown is recognized as a dashboard (filename matches `<slug>/<slug>.md`), auto-injects `OPERATOR_ACTIONS_AUTO` + `ASSET_LIST_AUTO` markers. When the markdown is a per-asset MD with a `STATUS_AUTO` marker, auto-injects the current yaml status. **The render-html script is the choke point** — no surface ships HTML without going through here.

- **`operator_actions.py`** — sibling of render.py; the scanner that reads yaml fields and builds the derived markdown blocks.

### Validation side

- **`check-state/check.py`** — read-only drift detector. Walks every asset folder in a campaign (or all campaigns) and reports any disagreement between yaml + asset record + preview + dashboard. **Run before any review session**, and **at session end via the Stop hook** (added 2026-06-10).

- **`check-state/gate.py`** — the **drift ratchet** (added 2026-06-15). Wraps `check.py`'s detection (imports it; does not modify it) but compares against an accepted baseline (`.claude/state/drift-baseline.json`), so it reports only drift introduced *since the baseline* — turning check.py's full backlog dump into one signal: "did this change add drift?" Exits 1 on NEW drift, 0 otherwise (known backlog grandfathered). **LOUD + NON-BLOCKING.** Accept the current state as the new baseline with `gate.py --all-campaigns --write-baseline` after deliberately resolving or accepting items. The baseline can only ratchet **down** — new drift can never silently join the backlog. This is the systemic answer to the drift class: detection existed before, but was advisory and accumulated; the gate makes new drift impossible to *miss*.

### Hook integrations

- **PostToolUse hook** (`.claude/hooks/post_tool_use.py`) — classifies every write into a campaign reason; `asset.yaml` writes classify as `asset_artifact` which triggers a dashboard re-render at session end.

- **Stop hook** (`.claude/hooks/stop.py`) — drains the dirty-campaigns ledger; runs render-html for each dirty campaign's dashboard; runs the drift **gate** (`gate.py`) after the rebuild and surfaces any **NEW** drift (beyond the baseline) as a one-line advisory in the session-end breadcrumb — non-blocking. The known backlog is silent; only regressions surface.

## Schema reference

### `asset.yaml` — canonical asset state

```yaml
asset_id: "05"                              # numeric prefix matches folder name
asset_name: "Bookmark designs"              # human-readable
default_channel: "Retail"                   # which channel the gallery groups under
status: "Approved"                          # canonical state — propagator-managed

# Optional — used by gallery deploy buttons:
deployment:
  destination_type: file
  format_requirements: ...

# Optional — surfaces in dashboard To Do:
operator_actions:
  - id: pick-printer                        # stable slug for --task
    title: "Pick print partner"
    why: "Inkness Carlton recommended"      # optional
    time: "~10 min"                         # optional
    blocks_launch: true                     # optional; surfaces 🚀
    priority: P1                            # optional; default P1
    phase: 4                                # optional; default 4
    where: "preview.md"                     # optional; renders as [open] link
    status: pending                         # pending | done
    completed: "2026-06-12"                 # auto-set when status → done

# Per-file declarative metadata (read by gallery for tile titles, review prompts):
files:
  preview.md:
    type: Foundation
    title: "Operator review surface"
    role: primary_doc
  <visual-file>:
    type: Instance
    title: "Tile-displayed name"
    review: "What to look for"
```

### `<NN>-<slug>.md` and `preview.md` — operator-readable surfaces

These files SHOULD include a `<!-- STATUS_AUTO -->` marker where the Status line goes. Render-html replaces the marker with the current yaml status at render time.

They MUST NOT hand-author the `**Status**:` line. If the marker is missing and a `**Status**:` line exists, that's hand-authored drift waiting to happen — use status-propagator's migration logic, or replace the line manually with the marker.

### Campaign dashboard `<slug>.md`

The dashboard MUST include:
- `<!-- OPERATOR_ACTIONS_AUTO -->` where the To Do table goes
- `<!-- ASSET_LIST_AUTO -->` where the asset list goes

Everything else (campaign description, Big Idea, stage notes, KPIs, budget) is operator-authored prose. Those are not asset-state — they're campaign metadata. Hand-author freely.

## Migration playbook

When you find a surface with hand-authored asset state:

1. Identify what's being hand-authored (status? operator actions? asset list?).
2. Replace the hand-authored content with the appropriate marker (`<!-- STATUS_AUTO -->` / `<!-- OPERATOR_ACTIONS_AUTO -->` / `<!-- ASSET_LIST_AUTO -->`).
3. If the relevant data isn't in yaml yet, propagate it: `python .claude/skills/status-propagator/propagate.py --campaign <slug> --asset <NN> --status <state>` (or edit asset.yaml directly to add `operator_actions:`).
4. Re-render the surface. Verify the auto-injected content matches reality.
5. Run `python .claude/skills/check-state/check.py --campaign <slug>` to confirm no drift.

## The discipline

The rule isn't "use the tools." The rule is **"asset state is yaml; everything else is a view."**

If you find yourself typing `**Status**: Approved` into a `.md`, stop. That's a derived value. The yaml is the source. Add the marker, edit yaml, re-render. The propagator does both in one command.

If you find yourself adding a row to a dashboard table that mentions "#15 awaiting approval", stop. That's a derived view. The view exists; you're hand-authoring it. Add the action to `15-banner-ads/asset.yaml` as an `operator_action`, or just let the auto-derived asset list show #15's current status.

Drift cannot happen if state has only one author. That's the architecture.

---

**Related**:
- `.claude/skills/status-propagator/SKILL.md` — propagator usage
- `.claude/skills/check-state/SKILL.md` — drift checker usage
- `.claude/skills/render-html/operator_actions.py` — marker injection logic
- `~/.claude/projects/.../memory/feedback_status_update_both_md_files.md` — captured the 2026-06-10 incident that led to this spec
