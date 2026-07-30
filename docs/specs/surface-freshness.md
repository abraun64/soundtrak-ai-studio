# Surface freshness — the "impossible to show stale" guarantee (SYS-112)

**Status:** prong A shipped 2026-07-22 · prong B (derive-more-store-less) sequenced.

## The problem this solves

Every operator surface — the per-campaign **dashboard** and **gallery**, the cross-campaign
**tasks** and **index**, the **tenant homes** — is a **pre-rendered static HTML file** opened
via `file://`. There is **no running server**: nothing computes a page when you open it. So
each surface is a *snapshot* that must be re-generated after every data change. When a
regeneration is skipped — a no-op hook, a worktree blind spot, a subagent that dies mid-task,
a hand edit, a forgotten render — the snapshot silently falls behind the data, and the
operator reviews stale content without knowing. This produced a long run of individual bugs
(SYS-013/016/094/101/103/104/109/110). They share one root; this is the fix for the *class*.

## The guarantee: verify, don't remember

`\.claude/lib/surface_freshness.py` treats freshness as something to **verify**, not remember:

- **Check.** For every surface, compare its `mtime` to the **newest of its data inputs**. Any
  surface older than its data is **stale**. The rule is *coarse but sound*: a surface must be
  at least as new as the newest non-generated file it could depend on — over-inclusion only
  costs an occasional rebuild, and it can **never** let a stale surface through.
- **Heal.** Rebuild every stale surface via its canonical render tool (`render.py`,
  `build-gallery.py`, `build-tenant-home.py`), then **re-verify**. A surface still behind its
  data after a rebuild is a **loud hard-blocker** (something is genuinely broken).

Surface → data inputs:

| Surface | Stale when older than… |
|---|---|
| `<slug>/dashboard.html` | newest `.md`/`.yaml` in the campaign (operator_actions, plan, brief, the dashboard md) |
| `<slug>/gallery.html` | newest file under `assets/` (asset.yaml + ship files) |
| `tasks.html` · `index.html` | their `.md` source + every active campaign's `campaign.yaml`/`asset.yaml` |
| `tenant-brand/<tenant>-home.html` | the active campaigns' `campaign.yaml` + the tenant's own `.yaml`/home md |

It resolves DATA to the **main checkout** via `repo_paths` (SYS-103), so it works from a
worktree session too.

## Where it runs

- **Every turn, in the Stop hook** (`freshness_guarantee()` in `stop.py`) — after the
  dirty-ledger drain, and on no-dirty turns too. So the **dirty ledger is an optimisation, not
  the guarantee**: even a change that was never flagged dirty is caught and healed before the
  turn ends. The cheap mtime check gates the rebuild, so quiet turns cost almost nothing.
- **On demand / pre-surface** — `python .claude/lib/surface_freshness.py --check` (exit 1 if
  any surface is behind its data) or `--heal` (rebuild + re-verify). The CM runs `--check`
  before putting a surface in front of the operator.

## Two prongs

- **Prong A — the freshness guarantee (this doc, shipped).** Removes the "a render was
  skipped" failure mode entirely: a surface can no longer end a turn behind its data.
- **Prong B — derive more, store less (in progress).** The *other* root of drift is a few facts
  stored in two hand-kept places. Compute these *from* asset states instead of storing them in
  parallel, so each fact has one home and there is nothing to keep in sync. Done per fact:
  - **Wave-gate completion — SHIPPED.** A campaign-level `operator_action` that declares
    `gates: [asset_ids]` is done (dropped from the To Do) when all its gated assets are
    `Approved`, computed from `asset.yaml` — no hand-set status. (`operator_actions.py`.)
  - **Phase status — SHIPPED.** The production phase uses `status_mode: derive_assets`, so both
    the phase pill (`_phase_done`) and the display string (`_derive_phase_status`) derive from
    asset states. Net: approving an asset flows to the To Do and the phase without a hand-edit.
  - **Remaining:** the Plan `Ships` column vs `asset.yaml ship:true` (SYS-101 added a
    reconciliation *guard*, but the fact is still authored in both places); and the article body
    in `edition.md` vs `issue-header.html` (SYS-094 shipped the single-source render for new
    editions). Both are lower-priority now that each has a guard/derivation path.

Rejected: a **live local server** that renders on view would eliminate prong-A staleness
entirely, but it contradicts the deliberate "static files on OneDrive, no backend, just a
folder you can open" architecture — not worth abandoning the file model for.
