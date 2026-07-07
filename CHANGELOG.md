# Changelog — Soundtrak AI Studio

All notable changes to the **system** (the product) are recorded here — the public release log.
Each version is a clean Seed cut published to GitHub. Format follows
[Keep a Changelog](https://keepachangelog.com); versioning follows [SemVer](https://semver.org).

Only **system-layer** changes appear here. Tenant- and campaign-layer work is never recorded —
the `build_seed` allowlist defines what counts as "system" (i.e. what ships). Maintained by the
System Manager; see "Cutting a release" at the foot of this file.

## [Unreleased]

### Fixed
- **Auto-captured system ideas can never be handed a reused id.** The scheduled cadences that file
  new ideas now record each one in the append-only audit log and draw the next free id from the full
  history (ideas + backlog + log) rather than the idea inbox alone — so an id that was later promoted
  to a ticket or removed can't be silently minted a second time and collide.

## [1.1.0] — 2026-07-06

### Fixed
- **Assets can no longer silently vanish from the gallery.** The root cause was two channel
  vocabularies drifting apart with nothing to catch it: the Producer picked a channel from a
  hard-coded generic list that didn't match the campaign's actual channels, so the gallery's render
  loop skipped it — the asset was built but never drawn, with no warning. Fixed by collapsing to **one
  vocabulary — the Plan's channels**: the fossil list is deleted; the CM injects each asset's channel +
  name from its Plan row and the Producer derives `asset.yaml` from it (never invents); the gallery
  groups by the Plan's channels; and `check-state` now **hard-fails** if any `asset.yaml`
  `default_channel`/`asset_name` doesn't match its Plan row. The Plan is the single source of truth for
  the asset catalog.
- **Gallery "Open folder" / "Edit copy" buttons work on any machine.** The one-time setup for the
  gallery's native-open protocol now auto-detects the install path (a small `setup-protocol.ps1`)
  instead of a `.reg` file hardcoded to the original author's folder — so it works wherever a
  downloader unzips the system, not just on the machine it was built on. (The buttons already fall
  back to plain browser behaviour if the setup isn't run, so nothing breaks either way.)
- **Scheduled-cadence setup works on any machine.** The `Register-ScheduledTask` commands for the
  weekly cadences no longer hardcode the author's Python interpreter + install folder — they
  auto-detect both (`python -c sys.executable` + the current folder), so a downloader's paste just
  works. (Found in a full public-codebase sweep for hardcoded paths.)
- **Early-phase campaigns work fully before they have assets.** A campaign now appears on the
  All-Campaigns index and its tenant home as soon as it has a `campaign.yaml` (previously it stayed
  hidden until asset production began), the stage pill correctly skips the inherited Phase-0
  foundation row, and its campaign-level to-dos (e.g. the next gate action like "pick a concept")
  now surface on the dashboard To Do and the tasks queue — a second spot where the assets-first
  assumption had silently hidden them.
- **Campaign To Do shows only current-stage tasks.** The dashboard To Do and the
  cross-campaign tasks queue no longer surface tasks for phases the campaign hasn't
  reached yet (e.g. launch or cadence steps while still in asset production) — only the
  current stage's tasks, plus any still-open earlier work.
- **A malformed campaign no longer blanks the campaigns index.** A bad `campaign.yaml`
  used to crash the Active-campaign list so the index rendered empty; the index now
  tolerates the bad entry, and any unexpected render failure degrades to a basic roster
  with a warning instead of silently showing nothing.
- **System Manager backlog/ideas/audit resolve to one canonical store.** Edits and id
  allocation always target the main checkout (never a per-worktree copy), with a
  duplicate-id guard — preventing ticket-id collisions when work spans git worktrees.
- **The licensor's name is kept in the legal files when cutting a Seed.** The clean-cut's
  privacy scrub no longer rewrites the operator's name inside `LICENSE` / `NOTICE` — a
  liability disclaimer must name who it protects — while still scrubbing real client names
  everywhere, so a release can't be blocked by its own license text.
- **Stale-surface sweep stops crying wolf.** The scheduled stale check now flags only
  genuinely auto-rendered operator surfaces (those the render pipeline rebuilds), not the
  hand-built one-off artifacts in an asset folder — so the report shows real, actionable
  drift instead of dozens of false positives from a sibling file's timestamp.

### Changed
- **Plan (Phase 3) — one asset list, grouped by channel or wave.** The plan's asset list
  is now a single table you can flip between grouping **by channel** (what / where) and **by
  wave** (what's parallel), split into **Launch** vs **Ongoing** work. Every row is typed as a
  **marketing asset** or a **setup / deploy task** (create the account, deploy the page, drop the
  tracking tags), carries a plain-English description of what it is, and shows its dependency.
  **Waves are derived from the dependency column** — Wave 1 is everything with nothing to wait on —
  so the Campaign Manager produces a whole wave in parallel instead of one asset at a time. Existing
  plans keep their card view until migrated (the new format switches on when a plan declares a Type
  column).
- **The asset gallery mirrors the plan.** The Phase-4 gallery now derives its channels, names,
  descriptions, dependency waves, and Launch/Ongoing split from the plan — via one shared parser both
  surfaces read, so the plan and gallery can't drift — with the same channel⇄wave toggle. A produced
  asset that has no plan row shows in a visible "not in the plan yet" bucket instead of hiding, so the
  plan stays the single source of truth. Legacy campaigns are untouched until their plan adopts the
  new format.
- **Campaign dashboard — one authoritative link per phase.** The Phases & Artifacts
  table now shows a single primary link per phase (the gate document to review), with
  earlier/supporting/superseded docs moved to a collapsed "Earlier & supporting
  documents" block below — so it's unambiguous what each gate is asking you to review.

- **Copy-review files are just the copy now.** A `copy.md` (the operator's edit surface)
  is held to a strict minimum — a one-line orientation, the copy as labelled fields, and the
  few constraints that bind it. Strategic rationale, version-history, and design/production
  notes no longer clutter the edit surface (they live in the asset record).
- **Copy-surface guard.** The state checker now flags any copy file that regrows a
  banned section (a thesis, a version-history log, or design annotations), so the edit
  surface stays clean over time.
- **Board-currency guard.** The state checker + the turn-boundary gate now flag any
  to-do item that's still pending in a phase the campaign has already moved past — so the
  board reflects reality during long working sessions instead of silently lagging.

### Added
- **The practitioner playbook ships with the product.** The 53-principle strategic playbook — the
  discipline the system is "configured on" — is now embedded at `craft/frameworks/` and read by the
  Campaign Manager and Creative Director as fixed strategic input, so every campaign is shaped by the
  same frameworks. Your *own* voice, positioning, and proof still come from your tenant baseline
  (Phase 0); these are the transferable *frameworks*, not one operator's specifics. (The old external,
  author-specific knowledge-base pointer is retired.)
- **Fresh-install validation.** A new `validate_seed` step cold-clones a cut Seed into a
  throwaway dir (exactly as a downloader receives it) and gates the release on three checks
  passing — install doctor reports READY, the Phase-0 gate correctly blocks with no tenant,
  and one render produces HTML — so a release can't be cut that fails for a real downloader.
- **Archive / unarchive a campaign in one step.** A finished or parked campaign can be moved
  out of the Active grid into a collapsed "Archived" block (and out of the tasks queue) and
  back again with a single command — a pure surface move that never deletes the campaign.
- **No-silent-blank render guard.** If a generated surface ever fails to fill a section, the
  renderer now shows a visible "this section failed to render" placeholder and logs a warning
  (and the smoke test catches it) instead of shipping a silently empty page.
- **Archive-migration utility.** A reusable tool buckets a flat folder of prefixed files into
  per-edition folders with a manifest — dry-run by default, never deletes — for tidying a
  tenant's legacy content archive.
- **Memory-origins cross-reference.** A tool that answers "why does this rule exist?" — it maps
  each remembered rule back to the work that spawned it (the retro, ticket, or session) and lists,
  per piece of work, the rules it produced. Read-only, with an opt-in backfill for the unambiguous
  cases only.
- **First-run license acceptance.** On first run the install doctor now shows the disclaimer and
  won't proceed until you accept it (type "I AGREE", or `--accept-license` when scripting) — an
  affirmative act of assent recorded locally, so downloading is no longer silent acceptance.
- **Phase-0 baseline dashboard.** A per-tenant operator surface that shows every foundation item as
  done (with the date it was established), drafted-but-not-yet-ratified, or still to do — plus the
  best-practice library with a one-click "add an entry" prompt and an audit-history footer. Linked
  from each tenant home and refreshed alongside it, and reachable from the All-Campaigns index (a
  **Brand** link on every campaign card) and every campaign dashboard (a **Phase 0 · Foundation** row).
- **Docs-currency check.** A new `docs-audit` diagnostic (run in the smoke test + the
  weekly digest) catches stale agent counts, dropped navigation-index columns, and public
  docs that fell behind the agent/spec set — so the reference docs stay honest automatically.

- **Proactive scheduled cadences.** Four optional weekly/monthly sweeps (competitor &
  library scan · tenant brand-drift · stale-asset/surface · per-tenant shipped/blocked
  rollup) that surface findings to the inbox on a timer — read-only, never auto-act.
- **Disqualifiers / hard-nos card.** Each tenant playbook gains an always-loaded section
  for who you don't target and what you won't say (the inverse of audience truths), sliced
  into every brief — referencing the compliance profile rather than duplicating it.

- **Categorised spec index.** `docs/specs/README.md` groups the specs into artifact
  schemas / asset-type specs / architecture & process, so the folder is navigable at a
  glance without moving any files.

- **Machine-checkable agent handoffs.** CM and the specialist agents now exchange a
  structured envelope alongside their prose, and CM validates each return (status,
  required fields, and that every claimed deliverable actually exists on disk) before
  acting — so a silently-incomplete handoff fails loudly instead of breaking downstream.

## [1.0.0] — 2026-06-29

Initial public release — the standalone, single-tenant "Seed".

### Added
- **Seven-role marketing system**: Campaign Manager (orchestrator) + Creative Director,
  Insights Manager, Governance Manager, Brand Manager, Producer, and Marketing Forensic Analyst.
- **Full campaign pipeline**: Phase-0 tenant baseline (with a hard gate) → Brief → Concept →
  Plan → Asset, with compliance and brand gates before the operator sees any asset.
- **Data-driven operator surfaces** — index, campaign dashboards, asset gallery, and tasks,
  auto-rendered from YAML so the data is the single source of truth.
- **System Manager** — a backlog / idea-inbox / audit dashboard for evolving the system itself,
  independent of any campaign.
- **Tooling** — install doctor, Phase-0 gate, and the `build_seed` clean-cut + secret-leak scanner.
- **Self-service docs** — Help & Guides hub, deployment guide, getting-started, FAQ, and an
  illustrated training guide.
- **Legal** — PolyForm Internal Use license plus trademark, notice, and data-handling notes.

---

## Cutting a release

_For the maintainer (the System Manager owns this):_

1. Make sure **[Unreleased]** lists every system-layer change since the last cut.
2. Rename **[Unreleased]** to the new version with today's date, and add a fresh empty
   **[Unreleased]** above it. Bump per SemVer — MAJOR (breaking) · MINOR (feature) · PATCH (fix).
3. Tag the commit: `git tag -a vX.Y.Z -m "Soundtrak AI Studio vX.Y.Z"`.
4. Cut + scan the Seed: `python .claude/lib/build_seed.py --out <dir> --git`.
5. Validate the cut: `python .claude/lib/validate_seed.py --seed <dir>` (cold-clone → doctor + Phase-0 gate + render; must pass).
6. Eyeball it, then push the Seed to the public repo — the human-gated step.
