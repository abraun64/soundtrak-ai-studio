# Render Pipeline — Consolidation Spec

**Spec version**: v0.1 scaffold · 2026-06-08
**Status**: Inventory + consolidation proposal. Implementation deferred — build when fragility bites.
**Owner**: CM + the operator

---

## Current state — five separate scripts

| Script | Location | Job | Called by |
|---|---|---|---|
| `render.py` | `.claude/skills/render-html/` | Markdown → HTML (all templates: base, dashboard, tasks, index, asset-preview) | CM SKILL.md operator-quartet rule · hooks · manual |
| `build-gallery.py` | `.claude/skills/asset-gallery/` | asset.yaml + MD files + Playwright → gallery.html (thumbnails + lightbox) | CM SKILL.md quartet rule · hooks · manual |
| `render-template.py` | `campaigns/acme-co-podcast-engine-2026q2/assets/0e-canva-brand-kit/` | Jinja2 YAML data → HTML visual templates (T1-T8) | Manual / skill dispatch |
| `sync-tenant.ps1` | `docs/playbooks/` | Master OneDrive → Tenant OneDrive (PowerShell, Windows-only) | Manual per Phase 6 setup |
| `stop.py` / `post_tool_use.py` | `.claude/hooks/` | State tracking + auto-render on file changes | Claude Code hooks engine |

---

## Operator-surface rendering contract (auto-generated — added 2026-06-12)

The cross-campaign surfaces are **generated**, not hand-authored. `operator_actions.py` (imported by `render.py`) replaces marker comments in the markdown with derived HTML. Authoring the markdown by hand for these blocks is wrong — edit the data sources instead.

| Surface | Marker | Source of truth | What it emits |
|---|---|---|---|
| **index.html** | `<!-- CAMPAIGN_INDEX_AUTO -->` | each `campaigns/<slug>/campaign.yaml` (+ `assets/*/asset.yaml` status) | One **card per active campaign**: nickname-or-name title (formal name as subtitle when a nickname is set) · top-right **phase pill** (current = first non-approved phase) · **Brand context** link under the pill · gate links **Dashboard · Brief · Concept · Plan · Gallery** (Brief/Concept/Plan only from *approved* phases; Playbook is never a card link) · muted stats line. Archived campaigns drop into a collapsed **🗄 Archived** list. |
| **tasks.html** | `<!-- CROSS_CAMPAIGN_ACTIONS_AUTO -->` | each `assets/*/asset.yaml` `operator_actions:` (+ `campaign.yaml` phases) | To Do **grouped per campaign** (header = name + phase pill + Dashboard link). Itemised table where `operator_actions` exist: **priority pill** (🔴 Blocker = `blocks_launch` · 🟡 Action = P0/P1 · ⚪ Nice-to-have) · task · why · time · descriptive link. A **pointer row** to the dashboard To Do where a campaign has pending assets but no itemised actions. Archived + nothing-pending campaigns omitted. |
| index + tasks | `**Last updated**:` line | render time | Auto-stamped `YYYY-MM-DD HH:MM` (local) on every render — never hand-typed (it drifted stale twice before this). |

**Per-campaign data contract** (what makes a campaign render richly vs. degrade):
- **`campaign.yaml` with `phases:`** → phase pill + approved-gate links on the index card. Without it the card falls back to a file-probe for `brief.html` / `concepts/concept-trio.html` / `plan.html` and a "Setup / In progress" pill. **Every campaign should have a `campaign.yaml`.**
- **`asset.yaml operator_actions:`** on review-stage assets → itemised rows in tasks.html. Without it the campaign shows only a pointer row. **Review-stage assets should declare `operator_actions`.**
- **`nickname:`** (optional, in `campaign.yaml`) → card/tasks title shows the nickname, formal name as subtitle.
- **`archived: true`** (in `campaign.yaml`) → campaign moves to the collapsed Archived section and out of the tasks queue.

`operator_actions` entry schema: `id · title · why · time · where` (file relative to asset folder) `· priority` (P0/P1/P2) `· phase · blocks_launch` (bool).

- **Phase 5/6 plan-gate collapse** (`collapse_phase_plan_actions`, applied to both tasks.html and the dashboard To Do): when a campaign has a `phase-5-rollout.md` / `phase-6-cadence.md`, that doc is the execution checklist, so its phase's `blocks_launch` **step** actions are removed from the task lists and replaced by **one** *"Approve the Phase N plan"* gate row **while the doc's `**Plan status**` line says Draft**. Approval = trim that line to `✅ Approved` → the gate clears on next render. Non-step actions tagged to the phase stay visible. The dashboard's blocker COUNT (`derive_blocks_launch`) re-scans `asset.yaml` independently and is unaffected. Index-card surface links for these docs read **🚀 Execute & Launch** / **🔄 Manage & Report**.
- **Brand-recs queue footer** (`_split_rec_pointers` + `_rec_pointer_footer`): an `operator_action` whose `where` targets `tenant-brand/_recommendations-queue.md` is an asset-verdict recommendation (durable, no time pressure), so it is **not** a task row — it renders as one muted footer line at the **bottom** of that campaign's group ("📋 Items queued from asset verdicts — no time pressure. See the recommendations queue ↗"), linking to the rendered `_recommendations-queue.html`. Applies to both tasks.html and the dashboard To Do.

### One asset-number convention across every surface (SYS-097 / SYS-099)

Each asset carries **one number** — its Plan id with the `A`-prefix and leading zeros stripped, but a lone zero kept (`A8` → **#8**, `A0` → **#0**, folder `08-…` → **#8**). That same `#N` is rendered everywhere the asset is named, so an operator can trace any item back to the Plan at a glance:

| Phase | Surface | Where the number is produced |
|---|---|---|
| 3 | **plan.html** | `render.py transform_plan` — `#N` badge before the name (accent, bold) |
| 4 | **gallery.html** | `build-gallery.py display_num` — `#N`, or `#N.1 / #N.2` sub-numbers when one asset ships several deliverable tiles |
| 5 | **dashboard To Do + tasks.html** | `operator_actions.display_num(asset_id)` — `#N · name` on each action row |
| 6 | **cadence rollup** | `tenant-shipped-blocked-rollup.py` — `#N · camp/NN-folder` on shipped lines |

The rule of thumb: **never surface the raw zero-padded folder prefix (`#08`)** — always normalise through the shared logic so the Plan (#8), the gallery (#8 / #8.1) and the task rows (#8) read as the same asset. The gallery's deep-link anchor (`gallery.html#<asset_id>`) is the one exception — it matches the raw tile id and is functional, not displayed.

## Current fragility points

1. **No Python version floor.** Any of the five scripts could break silently on Python 3.10 vs 3.14 behavioral differences. Playwright in particular has version-specific behavior.
2. **No single entry point.** To do a full rebuild, you need to know which script to call with which arguments. Documented in SKILL.md but not enforced.
3. **Windows-only sync.** `sync-tenant.ps1` uses PowerShell-specific syntax. macOS operators would need an equivalent rsync script.
4. **No dependency manifest.** `pip install playwright pyyaml jinja2` is implicit. A new machine setup can fail silently if these aren't installed.

---

## Proposed consolidation — `python -m marketing_ai <command>`

When load justifies it (second deployer, or first script failure from version drift):

```
python -m marketing_ai render --markdown <path> --template <name>
python -m marketing_ai build-gallery --campaign <slug>
python -m marketing_ai render-template --template <name> --data <yaml>
python -m marketing_ai sync-tenant --target <slug>
python -m marketing_ai smoke-test
```

### Requirements

- Single `pyproject.toml` at `Marketing AI System/` root
- Python version floor: `requires-python = ">=3.11"`
- Dependencies: `playwright`, `pyyaml`, `jinja2`, `markdown` (all already in use)
- Entry point: `marketing_ai/__main__.py` dispatches to existing scripts unchanged
- `sync-tenant` wraps `rsync` on macOS + `Robocopy`/PowerShell on Windows

### What does NOT change

- The individual scripts themselves — they stay as-is
- The hook wiring in `settings.json` — hooks call scripts directly, not via CLI
- The CM SKILL.md operator-quartet commands — update to use CLI once it exists

---

## Interim mitigation (before consolidation)

1. Add `python --version` check at the top of `render.py` and `build-gallery.py`:
   ```python
   import sys
   if sys.version_info < (3, 11):
       print("WARNING: Python 3.11+ required. Current:", sys.version, file=sys.stderr)
   ```
2. Add a `requirements.txt` at the project root listing explicit versions.
3. Document `pip install -r requirements.txt` as step 1 of any new machine setup.

---

## Build trigger

Implement the full consolidation when:
- A Python version shift on the operator's or a tenant's machine breaks a script
- A second deployer (non-the operator) needs to set up the system independently
- The script count grows beyond 7-8 (current: 5)

Per `docs/specs/retro.md` queued-cleanup-decay: don't implement prematurely. The spec exists so the design doesn't need to be re-thought from scratch when the moment comes.
