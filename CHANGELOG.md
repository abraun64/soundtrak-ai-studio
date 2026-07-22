# Changelog — Soundtrak AI Studio

All notable changes to the **system** (the product) are recorded here — the public release log.
Each version is a clean Seed cut published to GitHub. Format follows
[Keep a Changelog](https://keepachangelog.com); versioning follows [SemVer](https://semver.org).

Only **system-layer** changes appear here. Tenant- and campaign-layer work is never recorded —
the `build_seed` allowlist defines what counts as "system" (i.e. what ships). Maintained by the
System Manager; see "Cutting a release" at the foot of this file.

## [Unreleased]

### Added
- **Newsletter editions can now be built from one source, so the published page can't fall out of sync with the copy.** For new editions going forward, the issue's web page is *generated* from the article text plus a small data file, instead of being a hand-kept second copy that has to be updated in lockstep — removing the class of bug where the page and the copy silently disagree after an edit. Existing signed-off editions are left exactly as they were.
- **Assets that publish outside the web are now uploadable everywhere.** A newsletter, email or social asset is authored in HTML for preview, but Substack, Mailchimp, LinkedIn and most CMS editors need image files and pasteable text — and you can't right-click-save a graphic that's built from HTML/CSS. The system now exports each such asset into a "portable pack": the clean copy plus a crisp PNG of every composed graphic block, and the asset's review card tells you exactly which file goes where. No more hand-screenshotting.
- **Approving an asset now settles its open questions instead of hiding them.** When you approve, every open question is explicitly resolved, waived, or carried forward to the phase where it'll actually be answered (and it re-appears on your to-do there) — so a question you never actually answered can't silently vanish under a "resolved" label. (First half shipped; the matching review-card display is next.)

### Fixed
- **A phase's "human time" is now calculated instead of showing a blank.** The per-phase Human Time on a campaign dashboard used to be a value someone had to type in by hand — so a phase like Asset Production kept surfacing an empty "—". It's now *computed* by adding up the review-time estimates of that phase's own operator tasks (the same way AI cost is already pulled live from the ledger), so it can't read blank while the phase still has work to approve, and the campaign's total human-time figure folds it in automatically. A hand-set estimate still wins where one is given; the pre-review check now also flags an unresolved human-time cell the same way it already flagged a blank cost cell.
- **Approving an asset now updates everything downstream on its own.** When you approve the assets in a wave, that wave's approval task disappears from your to-do list by itself, and the campaign's phase advances on its own — both are now *computed* from the assets' actual states instead of being separate switches someone had to remember to flip. So the gallery, the to-do list, and the phase indicator can't disagree about where things stand.
- **Your operator surfaces can no longer be silently out of date.** Every page — each campaign's dashboard and gallery, the cross-campaign task list and index, and the tenant home pages — is now automatically checked against the underlying data at the end of every turn, and any page that's fallen behind is rebuilt on the spot, whether or not anything "remembered" to re-render it. (It immediately caught real cases in the wild — two campaign dashboards that were days behind their data — and brought them current.) This is the first half of a deliberate push to make out-of-sync surfaces structurally impossible rather than something we fix one instance at a time.
- **A stale draft can no longer slip through in the other direction either.** The pre-review check already caught the case where a published version moved ahead of its editable copy; it now also catches the reverse — where someone edited the copy after your feedback but the published page was never re-generated — so what you review always matches the latest edit, in either direction.
- **Half-finished automated work can't quietly reach you.** If a production step stops partway (or an edit silently doesn't apply), the system now re-checks the actual files on disk — did the edit land, did the page rebuild — before an asset is put in front of you, rather than trusting a "done" that wasn't.
- **Approving an asset now shows what actually happened to each open question** — resolved, waived, or carried forward — instead of labelling them all "resolved"; a carried-forward question reappears on your to-do at the right stage.
- **Release builds no longer clutter your workspace.** Cutting a public release now writes to a scratch folder outside your synced drive by default (and warns if pointed back inside), so regenerable build output stops piling up and syncing to the cloud.
- **The system's own safety checks got two quiet-but-important hardenings.** The backlog's integrity check now catches a whole class of file corruption it used to miss — where two tickets accidentally merge into one and silently overwrite each other — and it flagged (and we fixed) a real latent instance the moment it went in. And the automatic session backup no longer sweeps regenerated pages into an isolated workspace's branch, closing the path by which a bad page-rebuild could have been carried into the main workspace.

### Added
- **A stale draft is now caught before it reaches you.** After the gallery rebuilds, the system automatically checks each asset for a common drift — where the editable copy was left behind after the published version was reworked — and flags it by name, so a review page can't quietly show you an out-of-date draft. Previously this check only ran if someone remembered to run it by hand.

### Fixed
- **Your review queue and dashboards stay current, and show what's actually waiting on you.** Two fixes to how the operator surfaces keep up. First, when work is done in an isolated workspace (a git worktree), the dashboards, task list and gallery now re-render just as they do from the main workspace — previously they could silently freeze, so a page you were looking at might lag behind the work you'd just done. Second, the cross-campaign task list now always shows a clear "N assets awaiting your review → open the gallery" line for every campaign that has assets sitting with you, even when the campaign is also tracked by broader wave-level approvals — so per-asset progress is never hidden behind a coarse gate.
- **Every declared deliverable now shows in the gallery, and the Plan is kept honest about the count.** When you add or drop a deliverable during production, the gallery closes the loop two ways. First, a text-only deliverable (a prose write-up, a set of social notes, an outreach list) now gets its own review card instead of silently disappearing because it isn't an image — so nothing you marked as shipping can vanish from view. Second, the gallery cross-checks what each asset *declares* it ships against what the Plan says it ships, and flags any mismatch loudly at the top of the page — so a change that reached the asset but never made it back to the Plan can't hide. (The reverse discipline holds too: a text file that is merely the editable source behind a picture tile stays marked as source, not a second deliverable.)
- **Gallery lightbox numbering + resolved-question handling.** The lightbox header and its Plan reference now show the same number as the tile (e.g. `#6.3` for the deliverable, `#6` for the Plan asset — not the raw zero-padded folder id). And once an asset is **approved**, its gate questions move to the collapsed "Audit history — resolved questions" section instead of still appearing as open — so an approved asset no longer looks like it has questions outstanding.

## [1.5.0] — 2026-07-21

### Changed
- **Hardened the license for public release.** The PolyForm Internal Use License now carries a complete set of Soundtrak Additional Terms: the **licensor is identified** (Andrew Braun trading as Soundtrak Consulting, ABN 76 312 469 616); a **binding governing-law + exclusive-jurisdiction clause** (Victoria, Australia) with a global carve-out for non-excludable mandatory laws; **survival**, **no-professional-advice**, **compliance**, **third-party-software**, **export/sanctions**, **individual-claims**, and **one-year limitation** clauses; a **broadened indemnity** (AI outputs, infringing prompts/content, privacy, regulatory investigations); and an explicit **third-party-beneficiary** right for Andrew Braun. A second review pass then added an **indemnity carve-out** for the Protected Parties' own gross negligence or wilful misconduct (the Australian Unfair-Contract-Terms fix), an **output-ownership** clause (you retain the rights in what you generate, subject to the AI providers' terms), an explicit **order of precedence** (the Soundtrak Additional Terms prevail over the PolyForm base on any conflict), and a condition that your use complies with your **AI provider's Acceptable Use Policy**. Internal drafting notes were removed.

### Added
- A prominent **commercial-use notice** at the top of the README, a **`CONTRIBUTING.md`** (no unsolicited contributions; CLA required if invited), and a **`COMMERCIAL-LICENSE.md`** pointer for agency/SaaS/OEM/resale enquiries.

### Fixed
- **Gallery "Edit copy" buttons open the right deliverable.** In an asset that ships several deliverables, a ship-complete markdown deliverable (for example an article's `edition.md`) now opens its own source from the gallery, instead of falling back to a shared folder-level copy file.

## [1.4.0] — 2026-07-21

### Added
- **A readability check before anything reaches you.** Every operator surface is now checked to read clearly for a marketer who didn't write it — no internal codes, file names, or jargon — before it is put in front of you for review, so what you are asked to approve is always plain and self-explanatory.
- **One consistent "Campaign DNA" panel at the top of every artifact.** The Brief, Insight Brief, Concept, Plan and dashboard now all open with the same compact summary — objective, big idea, primary KPI — the one you already know from the dashboard, instead of a different crammed header on each page.
- **A "For review" status on campaign boards.** The dashboard now distinguishes work the AI is still producing from work waiting on your review, so you can see at a glance whose court the ball is in.
- **Consistent asset numbering across the plan and the gallery.** Every asset carries one number, with sub-numbers for the several deliverables under it, so you can map any gallery tile straight to its plan row and back — and each deliverable is uniquely referenceable.
- **A subtle product footer with a one-click licence link on every rendered page** — clear attribution, and the licence is always one click away.
- **Total human time on every campaign dashboard**, shown next to total AI cost — the two halves of "what has this campaign cost me".

### Changed
- **A whole-of-product plain-language and usability pass.** Every operator surface was reviewed and reworked for a non-author to act on: plain English throughout, one consistent name for your action-items, a coherent breadcrumb on every page, tables that stay legible on a laptop, friendlier empty states, and accessibility-grade (WCAG AA) contrast — done at the shared template layer, so every surface improved at once.
- **Briefs now follow one canonical template.** Every Brief reads the same way, in the same order, in plain section names — understandable by someone who did not write it — with a structure check that keeps it consistent across campaigns.
- **The Insight Brief opens with what matters** — a lean "what the campaign is + who it is for" block — and now uses the full screen width like the other surfaces.
- **The campaign dashboard leads with the numbers that matter.** KPIs and Budget are open by default, redundant and internal blocks were dropped, and the metadata header paragraph was removed from every artifact so each page opens on its useful content.
- **The gallery leads with your assets, not a QA audit.** A plan-vs-produced mismatch still catches the eye, but only when there is a genuine deviation.
- **Fewer ways for surfaces to quietly disagree.** The tenant hub, baseline page and campaign dashboard now single-source a tenant's status and summary, and the operator guides are single-sourced too, so one edit reaches the page you actually open.
- **The Plan's asset table uses a self-evident column name** instead of internal "review shape" wording.

### Fixed
- **Every "Edit copy" button opens the right file.** In an asset with several deliverables, each one's button now resolves to its own current source instead of a shared folder default — so you never open the wrong or a stale copy.
- **AI-cost figures stay trustworthy as caching varies** — per-phase and per-campaign costs are now caching-aware, rather than one blended rate that drifts as cache-heavy and cache-light work mix.
- **Documented examples render faithfully** — the render step no longer consumes marker text shown inside code examples in the reference docs, making a full re-render of every surface safe.

## [1.3.0] — 2026-07-14

### Added
- **The studio checks its own rendered work before you see it.** A new render → inspect → fix pass reads the actual rendered page and catches layout defects — overflowing tables, orphaned headings, missing image descriptions — auto-fixing the safe ones, so assets reach you visually correct the first time.
- **An automatic guard against false "approved" ticks.** The system now flags any green ✅ that has landed on something you didn't actually approve, protecting the trust of every approval mark on your boards.
- **Behavioural self-tests.** A lightweight test suite checks that the studio's core machinery actually does the right thing on known inputs (not just that pages exist), run as part of the health check — so regressions are caught before they reach you.
- **A guided way to add new publishing channels.** A new integration scaffolder stamps out a tested deploy connector to a standard contract (with a working reference connector included), making it a guided step to extend the studio to a new channel or environment.
- **A weekly "a release is ready" nudge.** The studio notices when improvements have piled up unreleased, prepares a validated release, and tells you it's ready to publish — you always do the final publish.
- **Faster brand setup and updates.** Onboarding is now re-runnable: it detects what you already have and only asks about what's missing, and you can update just one part (your voice, segments, channels) without redoing the whole baseline — and it never overwrites something you've approved without showing you the change first.
- **New craft references.** A catalogue of ~60 marketing mental models, a conversion-optimisation audit framework, and a voice-of-customer research method the studio's creative direction now draws on.
- **Engineer-facing architecture docs.** A new illustrated explainer (two diagrams) of how the studio is built and how it extends to new environments — for developers and partners.
- **Live per-phase cost on every campaign dashboard.** Each phase shows its real AI cost, rendered live from the metered ledger so the totals can't go stale.

### Changed
- **The insights behind a campaign are now genuinely approved with the Brief.** Approving a campaign Brief formally covers the audience insights that inform it — shown at the approval point — so the sign-off is real, not assumed.
- **Stricter approval honesty.** The studio never treats a passing chat comment as a formal approval, and a reworked artifact always comes back for a fresh, explicit sign-off.

### Fixed
- Per-phase cost cells no longer read blank where real work happened.
- Removed false "approved" ticks that had appeared on inputs you hadn't approved.
- Hardened the gallery's output-count reading so image dimensions (e.g. 256×256, @2x) are never mistaken for quantities.

## [1.2.0] — 2026-07-08

### Added
- **Two clearly-named libraries, shipped populated, reachable from the top of every screen.** A fresh
  deployment now ships with a starter **Best-Practice Library** (a curated set of standout-campaign
  exemplars the studio learns from) and an **Insights Library** (a starter research corpus), each
  titled, explained, and cross-linked, with a top-right menu pill on every operator surface. The
  Best-Practice Library opens with plain instructions on how to grow it (in chat, say "add this to my Best-Practice
  library"), and every release automatically carries the latest curated entries. (Real third-party
  client names in the shipped entries are automatically genericised to an example tenant.)
- **A richer creative toolkit for the Creative Director.** The strategic "journey modes" a campaign can
  build toward expanded from 5 to 9 (adding Attention/fame, Trust/proof, Utility/service, and
  Community/advocacy, plus an explicit escape hatch), and the visual-register palette grew from 4 to 8
  (adding Premium/luxury, Retro/nostalgic, Techno-futurist, and Playful/vibrant) — a deeper strategic and
  aesthetic range, each with worked exemplars behind it.

### Changed
- **Key legal docs now sit at the repository root.** LICENSE, NOTICE, and TRADEMARK are at the top level
  where they're expected and easy to find; the operational data-handling notice stays under docs/legal.
- **The Help-hub FAQ now covers both libraries** — how to add to your Best-Practice Library and your
  Insights Library, each in one plain step.
- **The system-improvement board states the benefit of every item.** Each idea and backlog ticket now
  leads with the concrete value it delivers, rendered on the card — so the board reads prioritisable at a glance.

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
