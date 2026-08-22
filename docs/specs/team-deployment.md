# Team Deployment — Multi-Operator Architecture (Microsoft 365 shop)

**Status**: v3 — ALL 12 PHASES BUILT 2026-08-22 (pilot + fresh-person UAT outstanding). Originally v2 draft · 2026-08-22 · authored with the operator. Re-scoped mid-build as a **product for multiple organisations**, not a one-off deployment (see §0.1). Phases 0.5 + 1 built; the rest designed.
**Owner**: the operator. **Implements**: SYS-028 — the Retro-5 §1.7 `profile: small-business | enterprise` toggle, which this spec makes concrete.
**Related**: [`standalone-deployment.md`](standalone-deployment.md) (single-tenant fork — the sibling model) · [`data-architecture.md`](data-architecture.md) (asset.yaml as single source of truth) · [`surface-freshness.md`](surface-freshness.md) · [`rollout-architecture.md`](rollout-architecture.md) (campaign lifecycle, not code rollout).

---

## §0 Purpose

Run the Marketing AI System with **several operators at one organisation**, each on their own
Claude Code instance under a Claude Enterprise account, sharing one set of brands, one central
library, and one campaign estate — in a Microsoft 365 environment (Entra ID · OneDrive · SharePoint).

This is a **third deployment shape**, distinct from the two that exist:

| | the operator's master (today) | The Seed | **Team deployment (this spec)** |
|---|---|---|---|
| Operators | 1 | 1 | **N** |
| Tenancy | Multi-tenant agency hub | Single-tenant fork | Multi-brand, one org |
| Data store | Local OneDrive | Local disk | **Shared git, Claude-driven** |
| Code updates | Edit in place | Client pulls upstream when they choose | **Versioned release, pulled by all** |
| Surfaces | Local HTML | Local HTML | **Local HTML + published to SharePoint** |

**Scope**: topology, path resolution, identity, concurrency, sync, code rollout, media, secrets,
state, publishing, provisioning. **Out of scope**: the campaign lifecycle itself (unchanged — see
`rollout-architecture.md`), and any per-brand content decisions.

### 0.1 This is a PRODUCT, not a migration (operator direction, 2026-08-22)

> *"We are designing it ahead of demand, so we can deploy it at multiple organisations."*

That reframes the whole build, and three things follow that were **not** true when this spec was
first written against a single hypothetical deployment:

**(a) the operator's master is not the thing we carve.** It stays exactly what row 1 of the table above
says: a single-operator, multi-tenant agency hub. The team shape is a *variant the Seed cutter
emits*, not surgery on a live 16 GB working repo. Phase 2 is therefore a `build_seed.py` feature,
not a restructure — and the risk drops accordingly.

**(b) A fresh deployment starts EMPTY.** `build_seed.py` already ships `campaigns/` and
`tenant-brand/` as `EMPTY_DIRS`. There is no history to rewrite, no 6.4 GB to partial-clone, and no
PNG-outside-LFS debt — provided the seed ships a correct `.gitattributes` on day one. See §8.

**(c) The §14 assumptions become install-time CHECKS, not questions.** "Does this organisation
permit local hooks?" cannot be answered once for N organisations. It has to be verified per
install, by the doctor, at the moment it matters. See §14.

It also means the **profile toggle (§12) is structural, not final** — it is how one codebase serves
both the single-operator and team shapes, so it moves early in the build order rather than last.

Each organisation gets its **own** CODE and DATA repos. Cross-organisation isolation is therefore
guaranteed by construction — a stronger boundary than any in-repo permission model, and the reason
decision #5 ("everyone sees everything") is safe: the blast radius is one organisation's own team.

---

## §1 Locked decisions

Confirmed by the operator on 2026-08-22. These are the load-bearing choices; everything below derives.

| # | Decision | Choice | Consequence |
|---|---|---|---|
| 1 | Authoritative data store | **Git, driven by Claude Code** | Real merge model, history, attribution, rollback. Humans never type a git command. SharePoint becomes a *publishing* surface, not the filesystem. |
| 2 | Code rollout | **Versioned git pull** | Operators run a pinned release; updating is a pull Claude performs. Requires a code/data split (§2). |
| 3 | Concurrency | **Explicit claim / ownership lock** | One active operator per campaign; collisions prevented, not repaired. |
| 4 | Brand model | **Flat sibling tenants** | Parent and sister brands are independent tenants sharing only the central libraries. No inheritance machinery. |
| 5 | Access model | **One repo, everyone sees everything** | No per-brand permission boundary. Simplest to administer. |
| 6 | Git host | **Must support BOTH Azure DevOps Repos and GitHub Enterprise** | Host-neutrality is a hard design constraint — no `gh`-CLI dependency on any load-bearing path. |
| 7 | Heavy media | **Keep in git; expand LFS + partial clone** | Media stays versioned. **Re-scoped by §0.1**: for the PRODUCT this reduces to shipping a correct `.gitattributes` (a fresh org starts empty). The LFS budget + history decision apply only to migrating the operator's own master (§8). |

### 1.1 Accepted costs

Two of these carry a known cost the operator accepted with eyes open. Recorded so a future reader
does not mistake them for oversights:

- **Flat sibling tenants (#4)** means values shared between the parent brand and its sisters —
  tone-of-voice floor, compliance boilerplate, group-level audience truths — are **duplicated per
  brand and will drift apart**. Cheap mitigation, no new machinery: keep genuinely shared material
  as *library* entries (one copy, central) and cite it from each brand's playbook, rather than
  copying prose between `tenant-brand/*.md`. This is the existing "graduate-then-cite" rule
  applied sideways.
- **One repo, everyone sees everything (#5)** means a brand cannot be hidden from an operator, and
  every clone carries the full history of every brand. This is fine for one in-house team. It
  becomes the blocking constraint the moment a *client* operator needs a seat, or a sister brand
  is divested — at which point §5 must be revisited before that person is onboarded, not after.

---

## §2 Topology — the code/data split

**The single biggest prerequisite.** Decision #2 (versioned code pull) is impossible while
operator-written data lives in the code repo. Today it does: `system/`, `tenant/`, and
`tenant-brand/` all sit in the `ai-marketing-system` repo, so pulling a code release would collide
with data writes on the same branch.

### 2.1 The classification rule

**The Seed allowlist in [`build_seed.py`](../../.claude/lib/build_seed.py) already defines this
boundary and is reused verbatim: what ships in the Seed is CODE; everything else is DATA.**

The System Manager's release job (`/system-manager` job 5) already uses this boundary, so no new
concept is introduced.

### 2.2 The three stores

**CODE repo** — versioned, tagged, operators only ever pull:

```
.claude/lib · .claude/hooks · .claude/agents · .claude/skills · .claude/settings.json
docs/ (specs · playbooks · guide · legal · workflow · NAVIGATION_INDEX)
craft/
index.html
seed content for tenant/library + tenant/tactics   (see 2.3)
```

**DATA repo** — operators read and write:

```
campaigns/                 every campaign, every brand
tenant-brand/              per-brand context · playbook · compliance · segments · audience truths
tenant/<brand>/            brand assets · discovery
tenant/library/            Best-Practice Library  — central, operators add via /library-add
tenant/research-library/   Insights Library       — central, operators add
tenant/tactics/            named plays            — central, operators graduate into
system/                    backlog · ideas · audit-log
retros/ + docs/retros/     session records
.claude/state/             shared subset only — see §9
```

**SharePoint site** — published, read-only rendered HTML for stakeholders without a Claude Code seat (§11).

### 2.3 The library conflict, resolved

`tenant/library/` and `tenant/tactics/` **ship in the Seed** (they are deliberately populated so a
fresh deployment starts useful) yet **operators write to them** — the operator's stated requirement
is that the best-practice and insights repos are central.

They cannot be both read-only code and writable data. The resolution:

> The code repo carries a **seed copy**, used only to populate a *fresh* install.
> The data repo carries the **live copy**, which is the one every operator reads and writes.
> After first install, the code repo's copy is never read again.

`tenant/research-library/` is already excluded from the Seed (it is real client research) and is
straightforwardly DATA.

### 2.4 Two repos or three?

The `campaigns/` estate is 6.4 GB tracked; `tenant-brand/` + `system/` + `tenant/` together are
under 25 MB. Keeping them in one DATA repo is simpler to reason about and makes cross-brand
surfaces (the index, cross-campaign tasks) a plain filesystem walk. **Recommendation: one DATA
repo**, with partial clone (§8) doing the size work. Splitting campaigns out again buys little once
`--filter=blob:none` is in place, and costs every cross-campaign surface a second checkout to resolve.

---

## §3 Path resolution

Each operator clones to their own location; nothing can be hardcoded, and the two clones need not
be siblings.

[`repo_paths.py`](../../.claude/lib/repo_paths.py) currently resolves DATA by walking *up* from the
running checkout (worktree → main). Under the split, DATA is a **different repo entirely**, so
that resolution no longer terminates anywhere useful.

**Change**: `data_root()` gains a resolution order, first hit wins:

1. `MAS_DATA_ROOT` environment variable
2. `.claude/local/config.json` → `{"data_root": "<abs path>"}` (per-machine, gitignored)
3. the existing worktree→main walk (preserves single-operator behaviour unchanged)

> ✅ **Built 2026-08-22** (commit `88ee0c6`). `repo_paths.data_root()` implements the order above
> and raises `DataRootError` on a configured-but-broken root. A worktree also reads the *main*
> checkout's config, so it inherits the machine's configuration rather than falling back silently.
> 10 tests in `.claude/lib/test_repo_paths.py`, wired into the smoke test; four of them prove the
> guard can fail. Verified unchanged from both the main checkout and a live worktree.
> ✅ **Sweep completed 2026-08-22** (commit `dc8b9fe`) — 21 files, two distinct defects.
> **(a)** The guard was defeated in **14 of 19 call sites**, which wrapped `data_root()` in
> `except Exception: DATA = ROOT` — swallowing `DataRootError` and performing exactly the silent
> fallback it exists to prevent. Narrowed to `except ImportError`, keeping the SYS-126 degradation
> path. (`post_tool_use.py`, `stop.py` and `smoke_test.py` were left alone: they SURFACE the failure
> via a degrade flag or a smoke FAIL rather than swallowing it.)
> **(b)** Seven tools never used `repo_paths` at all — `check.py`, `gate.py`, `ledger.py`,
> `propagate.py`, `build-phase0-surface.py`, and `phase0_gate.py` + `phase0_detect.py`, whose
> `--root` **defaulted to the running checkout** (a worktree run reads an absent `tenant-brand/`
> and reports a false BLOCKED). All 58 data-dir joins in `.claude/` were enumerated and classified;
> `operator_actions.py`, `render.py`'s `find_project_root`, `build_seed.py`'s output dir and the test
> fixtures were confirmed correct and left alone. Verified against a synthetic `MAS_DATA_ROOT`,
> including that a broken root now raises through `gate.py` instead of falling back.
>
> **Phase 1 is complete.** Phase 2 (the repo split) is unblocked.

**A missing or unresolvable data root must fail loudly, never fall back to the code checkout.** A
silent fallback is exactly the worktree blind spot that SYS-103 fixed, re-introduced in a worse
form: writes would land in the code repo and ride a release.

> ⚠️ **Resolver sweep required.** SYS-103's lesson (`feedback_resolver_sweep_on_blind_spot_fix`) is
> that a data-resolution change lives in several tools. Every caller of `repo_paths` — plus
> `stop.py`, `build-tenant-home`, `surface_freshness.py`, `sysdata.py`, `build-gallery.py`,
> `weekly-digest.py` — must be swept together. Last time the missed third caller nearly corrupted main.

---

## §4 Identity and attribution

Every surface today says "the operator", singular. With N operators that is a defect.

- **Operator identity** resolves from `git config user.email` (which, on Entra-backed hosts, is the
  person's work identity), exposed as `MAS_OPERATOR`.
- **Stamped into**: `system/audit-log.yaml` entries · `asset.yaml` `operator_actions[].completed_by`
  · asset approval records · campaign claim locks (§5) · retro records.
- **Surfaced on**: the campaign dashboard's To Do rows, the gallery's approval badges, the System
  Manager audit history.
- **Not** a permission system. It is an audit trail. Decision #5 puts no access boundary anywhere.

---

## §5 Concurrency — campaign claim locks

**Rule: a campaign has at most one active operator at a time.**

> 📌 **This already happens at N=1.** On 2026-08-22, two Claude Code sessions on the operator's single
> machine worked the same tickets within the hour, unaware of each other. One diagnosed the
> freshness-gate coverage hole and filed SYS-143; the other fixed it and landed it on `main`
> minutes later. One repaired a duplicate `SYS-141` id **by hand** while the other was committing
> the fix for the code that minted it. Both wrote to the same working tree, where `stop.py`'s
> blanket `git add -A` would have swept one session's uncommitted work into the other's commit.
> The collision cost was low here only because both sessions happened to touch different files.
> Parallel *sessions* are the same hazard as parallel *operators* — so claim locks (and §6.1's
> scoped commit) earn their place before headcount ever rises.

`campaigns/<slug>/claim.yaml` (DATA repo):

```yaml
operator: jane.smith@example.com
claimed:  2026-08-22T09:14:00+10:00
expires:  2026-08-22T17:14:00+10:00     # TTL, default 8h
session:  <claude-session-id>
```

**Behaviour**

| Situation | What happens |
|---|---|
| Operator starts campaign work | Pull; if unclaimed or expired → write claim, push. |
| Claim held by someone else, unexpired | **Warn before any write**, naming holder and expiry. Operator may proceed only by explicit override, which is recorded in the audit log. |
| Claim expired | Treated as free; the stale claim is overwritten. |
| Session ends | Claim released by the Stop hook. |

**Surfaces display the holder** — the campaign dashboard and the cross-campaign index show who
holds each campaign, so "who's on this?" never requires asking.

**Deliberately not locked**: the central libraries (`tenant/library`, `tenant/research-library`,
`tenant/tactics`) and `system/`. These are append-mostly, one-file-per-entry stores where
concurrent adds do not collide. `system/backlog.yaml` *is* a single shared file — it relies on the
existing `sysdata.py check` id guard plus rebase (§6) rather than a lock.

---

## §6 Sync model

Claude Code performs all git operations. **No operator ever types a git command.**

| Moment | Action |
|---|---|
| Session start | `git pull --rebase` on DATA. Check CODE for a newer pinned release (§7) and report. |
| Before claiming a campaign | `git pull --rebase` on DATA (so the claim decision is current). |
| Session end (Stop hook) | Commit DATA changes **attributed to the operator**, rebase, push. Release held claims. |

### 6.1 Changes to the existing Stop hook

[`stop.py`](../../.claude/hooks/stop.py) today runs a blanket `git add -A` + commit + push on both
repos. Three changes are required:

1. **Never commit to the CODE repo.** Under decision #2 it is pull-only for operators. The System
   Manager publishes releases from a separate authoring checkout.
2. **Scope the commit.** `git add -A` currently sweeps whatever is in the tree. With shared data it
   must stage only paths this session actually touched — the PostToolUse dirty-ledger already
   tracks this and would become load-bearing rather than an optimisation.
3. **Rebase before push**, and on conflict **stop and surface** rather than auto-resolve.

### 6.2 Conflict policy

- **Prose markdown** (briefs, concepts, asset copy): standard git merge; Claude resolves and reports.
- **Structured YAML** (`asset.yaml`, `campaign.yaml`, `backlog.yaml`): **never auto-resolve.**
  Surface the conflict to the operator. Silent data loss in structured state is precisely the bug
  class `data-architecture.md` exists to prevent.
- **Generated HTML**: cannot conflict — it is no longer committed (§10).

---

## §7 Code rollout

**Requirement: a system update reaches every operator.** Host-neutral per decision #6.

- The CODE repo is **tagged** on every release, using the existing System Manager release job and
  `CHANGELOG.md` (SemVer, already in place).
- Operators sit on a **pinned tag**, not a moving branch — so an operator's system cannot change
  underneath them mid-campaign.
- **Session start reports** when a newer release exists: *"System update v1.4.0 available — 3 fixes.
  Update now?"* Applying it is `git fetch --tags && git checkout <tag>` performed by Claude.
- **Rollback** is checking out the previous tag. This is the property the "shared code folder"
  alternative could not offer.
- **Host neutrality**: the remote URL is configuration. No load-bearing path may shell out to `gh`
  (GitHub-only) or `az` (Azure-only). Release *authoring* tools may be host-specific; the operator
  *update* path may not.

> 🔍 **Verify before building**: LFS storage and bandwidth terms differ between Azure DevOps Repos
> and GitHub, and both change over time. Confirm current limits and pricing on the chosen host(s)
> before committing to the media plan in §8 — the numbers there are the constraint, not the design.

---

## §8 Media, LFS, and clone size

**Measured 2026-08-22** (the reason this section exists):

| | |
|---|---|
| Tracked in `campaigns/` | 6.4 GB across 2,159 files |
| Video, in LFS (`.mp4`/`.mov`) | ~1.4 GB |
| PNG, **not** in LFS | 779 MB, in plain git objects |
| Largest single file | 1.25 GB `.mp4` |

[`.gitattributes`](../../campaigns/.gitattributes) still says *"Free tier: 1GB storage / 1GB
bandwidth — plenty for current usage"*. That has been false for some time, and **LFS bandwidth
scales with headcount**: every operator's first clone pulls the full media payload.

> 🔄 **Re-scoped 2026-08-22 (§0.1).** Every number above is **the operator's master**, and none of it is
> a *product* problem. A fresh organisation's deployment starts with `campaigns/` and
> `tenant-brand/` empty, so there is no history to rewrite and nothing to partial-clone. What the
> product must do is **ship a correct `.gitattributes` in the seed** so a new org never accumulates
> this debt: LFS for `.png` from commit one, not retrofitted at 779 MB. That is a one-file change
> with no migration risk, and it is the whole of the product-side media work.
>
> The rest of this section is a **migration plan for the operator's master specifically**, to run only if
> and when that master moves to the team shape. It is not on the product's critical path, and
> §13.1's destructive history-rewrite decision can stay open indefinitely without blocking anything.

**Plan**

1. **Partial clone by default** — `git clone --filter=blob:none`. Blobs download on demand, so
   day-one checkout is metadata plus what the operator actually opens. This is the single
   highest-leverage change.
2. **Sparse-checkout as an option** — an operator working one brand materialises one brand. A
   convenience, not a boundary (decision #5).
3. **Extend LFS to `.png`** — 779 MB of images in plain git objects is paid for by every clone,
   forever. Going forward this is a one-line `.gitattributes` change; retroactively it needs
   `git lfs migrate`, which **rewrites history and invalidates every existing clone**. → decision needed (§13).
4. **Budget for an LFS data pack** on whichever host is chosen, sized to headcount × payload.
5. **Guard the tree** — a pre-commit size check rejecting new non-LFS files over a threshold. The
   169 MB `chrome-headless-shell.exe` sitting under `node_modules` shows how easily build detritus
   reaches a shared repo; it is ignored today by luck of a pattern, not by policy.

---

## §9 State, secrets, and per-machine files

### 9.1 Splitting `.claude/state/`

Today `.claude/state/` mixes shared truth with per-session scratch. Shared, the ledger races;
split naively, the baseline forks.

| File | Classification | Where |
|---|---|---|
| `drift-baseline.json` | **Shared** — the ratchet is a team-wide agreement | DATA repo |
| `cost-ledger.jsonl` | **Shared** — append-only, per-line, merges cleanly | DATA repo |
| `dirty-campaigns.json` | **Per-machine** — this session's ledger | Local, gitignored |
| `hook-latency.json` | **Per-machine** — debug artifact | Local, gitignored |
| `license-accepted.json` | **Per-machine** — per-install acceptance | Local, gitignored |

### 9.2 Secrets

`tenant/credentials.md` is gitignored but **sits on disk in the shared tree**. Under decision #5
every operator can already read every brand's data, so this is not a new exposure — but it must not
enter the DATA repo, where it would be permanent in history.

- Per-operator `.env` outside both clones; never committed.
- API keys (Replicate, etc.): per-operator keys are simplest and give per-person cost attribution
  via the existing cost ledger. A shared key in Azure Key Vault is the alternative if per-seat
  billing is unacceptable. → decision needed (§13).
- A pre-commit secret scan on the DATA repo, reusing the leak-scan machinery already in `build_seed.py`.

---

## §10 Surface freshness under N writers

This is where the shared-folder alternative failed, and the git model must not reproduce it.

**The problem**: [`surface_freshness.py`](../../.claude/lib/surface_freshness.py) compares mtimes
and *heals* by re-rendering. With N operators each running that hook against shared data, operators
race to rebuild the same surfaces and overwrite each other's renders.

**The fix: stop committing generated HTML.**

- Rendered HTML in the DATA repo becomes **gitignored and locally derived**. It is a pure function
  of markdown + YAML, so it is not information — it is a cache.
- Each operator renders locally; the freshness gate heals *their own* working tree only. No race,
  because no shared write target.
- Stakeholder-facing HTML is produced once by a nominated publisher (§11), not by every operator.
- Bonus: this removes the largest source of merge conflicts *and* meaningfully shrinks the repo.

**Guard on the keystone.** `surfaces-fail-loud` (SYS-126) requires that a reader never sees a stale
surface without a signal. A fresh clone has *no* HTML at all, which is a new state that rule never
contemplated. Mitigation: the session-start hook renders any missing surface before the operator
can open one, and absent HTML — being absent rather than stale — cannot mislead. **This must be
explicitly tested before rollout**, as it touches the system's keystone guarantee.

---

## §11 Publishing to SharePoint

Stakeholders without a Claude Code seat still need to read dashboards, galleries, and asset previews.

- A **nominated publisher** — one machine or a CI job — renders the full surface set from the
  current DATA `main` and writes it into a SharePoint document library.
- **Simplest viable mechanism**: the publisher writes into a locally synced SharePoint library
  folder; the sync client does the upload. No Graph API app registration, no tenant admin consent.
  Because only one machine writes, none of the multi-writer sync problems apply.
- **Upgrade path** if that proves fragile: Microsoft Graph with an app registration, publishing to
  a SharePoint site — better auth and audit, at the cost of tenant admin involvement.
- Published output is **strictly read-only and one-way**. Nothing in SharePoint is ever read back
  as authoritative; that is what decision #1 rejected.

---

## §12 The SYS-028 profile toggle, made concrete

SYS-028 asked for a `profile:` toggle changing **defaults, not code**. This spec supplies the axes.

```yaml
# config.yaml (repo root)
profile: enterprise      # small-business | enterprise
```

| Axis | `small-business` (today's default) | `enterprise` |
|---|---|---|
| Operators | 1 | N |
| Campaign claim locks (§5) | off | **on** |
| Attribution (§4) | "the operator" | **required, per person** |
| Data store | local | **shared git remote** |
| Code updates | edit in place | **pinned release + pull** |
| Generated HTML | committed | **gitignored, locally derived** |
| Publishing | local files | **SharePoint publish step** |
| Approval depth | single gate | **multi-approver where the brief defines one** |
| Compliance weight | light | **Governance Manager gating on by default** |

`small-business` must remain the behaviour a fresh Seed gets with no config file present, so
nothing about the existing single-operator install changes.

---

## §13 Open decisions

Not blocking the design; each needs an answer before the phase that depends on it.

1. **PNG history rewrite** (§8.3) — accept a `git lfs migrate` that invalidates existing clones, or
   apply LFS to new PNGs only and leave 779 MB in history?
2. **API keys** (§9.2) — per-operator keys (simple, per-person cost attribution) or one shared key
   in Key Vault (central billing, weaker attribution)?
3. **Nominated publisher** (§11) — a person's machine, or a CI runner on the chosen host?
4. **Claim TTL** (§5) — 8h default proposed. Too short strands overnight work; too long blocks a colleague.
5. **Both hosts at once, or one?** Decision #6 requires both be *supported*. Confirm whether both
   run simultaneously (e.g. GitHub for code, Azure DevOps for data) or whether this is portability
   against a future migration.

---

## §14 Environment assumptions → install-time checks

Originally written as questions to answer once. Under §0.1 that is wrong: these cannot be settled
for N organisations in advance, and a product that *assumes* them will fail silently at the third
customer. **Each becomes a check the doctor runs at install**, with a written remediation.

`.claude/skills/system-smoke-test/doctor.py` is the right home — it already asks "is THIS MACHINE
set up to run it?" and already checks this exact class of thing (it fails when only `python3` is on
PATH, precisely because the hooks would otherwise "silently never fire").

| # | Assumption | Check to build | If it fails |
|---|---|---|---|
| 1 | **Claude Enterprise permits local hooks + Python** | Doctor writes a temp file, confirms the PostToolUse hook actually fired, and reports whether a managed-settings policy overrode `.claude/settings.json` | **FAIL, blocking.** The sync (§6) and freshness (§10) architecture both run on hooks. Fallback: an explicit `/sync` command the operator invokes. Must be known before install, not after. |
| 2 | **Headcount + literacy** | Not a machine check — an onboarding question in the deployment guide, captured into `config.yaml` | >~10 operators pushes §5 from claim locks toward brand partitioning |
| 3 | **A writable SharePoint target** | Doctor confirms the configured publish path exists and is writable | WARN — publishing (§11) is optional; the system runs locally without it |
| 4 | **Private repos on a permitted host** | Doctor confirms both remotes resolve and authenticate | FAIL — nothing works without the DATA remote |
| 5 | **`git` and `git-lfs` present** | Doctor already checks `git`; add `git lfs` | FAIL if media is in scope (§8) |

Assumption 1 remains the largest blast radius, but it is no longer a *blocker on this design* — it
is a check we build, and a documented fallback. That is the difference between designing for one
deployment and designing a product.

---

## §15 Build phases

Ordered by dependency. Each is a separate ticket with its own gate; **no phase starts before the
§14.1 hook-policy check passes.**

> ⚠️ **Phase order corrected 2026-08-22.** The split and path resolution were originally listed
> the other way round. That ordering cannot work: **path resolution must come first**, because the
> carved-out DATA repo has nowhere to live until `data_root()` can point outside the checkout.
> Carving first leaves every tool broken until resolution lands. They are now 1 and 2 respectively.

> ⚠️ **New prerequisite (phase 0.5), found 2026-08-22.** A repo restructure cannot happen over
> outstanding branches. There were **9 unlanded branches / 443 commits**.
>
> **These branches were not merely stale — they were actively poisoned.** Every abandoned worktree
> branch carried regenerated `tenant-brand/*-home.{md,html}` surfaces in which each tenant's campaign
> card had been replaced by *"No active campaigns yet."* Cause: `build-tenant-home.py` ran inside a
> worktree, where `campaigns/` does not exist (it is a separate gitignored repo), found zero
> campaigns, and rendered the empty state — which `stop.py`'s blanket `git add -A` then committed.
> **A full merge of any one of them would have wiped every tenant's campaign listing on `main`.**
> This is the SYS-103 blind spot fossilised: the fix landed on `main` 2026-07-22 (`62170ad`), but a
> worktree runs its own FROZEN copy of the resolver, so branches kept producing corrupt surfaces
> after `main` was correct. Verified 2026-08-22 that `main`'s resolver now resolves correctly from a
> live worktree, so this is historical damage, not an open hole.
>
> **Cleared:** `festive-noyce` (143 commits), `zealous-gauss` (105), `bold-curie` (38),
> `peaceful-northcutt` (17) — all four contained *only* corrupted tenant surfaces plus
> `hook-latency.json`, a per-machine debug artifact. `three-guides-campaign-launch` deleted as fully
> landed (zero diff). `romantic-joliot` is superseded — its code additions are already on `main`.
>
> **Still to triage (real, unlanded content):** `ai-studio-onboarding-simplify` (8 files —
> `build_seed.py`, `settings.json`, `setup/SKILL.md`, deployment guide),
> `insights-manager-language` (21 files, ~1,700 insertions across the render pipeline + specs),
> `operator-surface-phase-5-updates` (the `phase-5-rollout` spec only). Each also carries the same
> corrupted tenant surfaces, so **cherry-pick the code — never merge the branch.**
>
> Two lessons this hands to the spec: it is the strongest possible case for §6.1's **scoped commit**
> (a blanket `git add -A` is what committed the corruption), and for §10's **stop committing
> generated HTML** (had those surfaces been derived rather than tracked, there would have been
> nothing to corrupt).

> 🔄 **Re-ordered 2026-08-22 for the product framing (§0.1).** Phase 0 is deleted — its four
> questions became §14 install-time checks. Phase 2 is no longer surgery on the operator's master but a
> `build_seed.py` feature. The profile toggle moves from last to **third**, because it is the
> mechanism by which one codebase serves both shapes — everything after it is written *against* it
> rather than retrofitted into it. Media drops off the critical path entirely (§8).

| Phase | Work | Gate |
|---|---|---|
| ~~0~~ | ~~Verify §14 assumptions~~ — **deleted**, became install-time checks (§14) | — |
| **0.5** ✅ | Branch hygiene — clear debris branches, prune stale worktree dirs | **Done 2026-08-22** — 6 branches cleared |
| **1** ✅ | Path resolution (§3) + full resolver sweep | **Done 2026-08-22** — single-operator behaviour provably unchanged |
| **2** ✅ | **Profile toggle (§12)** — `config.yaml` `profile:` selecting single-operator vs team defaults | A fresh Seed with no config behaves byte-identically to today |
| **3** ✅ | **Seed cutter emits the team shape (§2)** — `build_seed.py --profile team` produces TWO repos (CODE + DATA) using the existing allowlist; seed-vs-live libraries per §2.3 | Both repos clone clean into a working install; single-repo Seed unchanged |
| **4** ✅ | **Provisioning + doctor (§14, §16)** — installer writes `.claude/local/config.json`, registers operator identity, and the doctor gains the 5 environment checks | A second machine reaches READY unaided |
| **5** ✅ | State split + secrets (§9) | No shared file races; secret scan green |
| **6** ✅ | Identity + attribution (§4) | Every audit entry names a person |
| **7** ✅ | Sync model + Stop-hook rework (§6) | Two operators, concurrent sessions, no data loss |
| **8** ✅ | Claim locks (§5) | Second operator correctly warned |
| **9** ✅ | Derived-HTML change + freshness under N writers (§10) | **Keystone test**: no stale surface, no render race |
| **10** ✅ | Code rollout + pinned releases (§7) | An update reaches a second machine and rolls back |
| **11** ✅ | SharePoint publishing (§11) | Stakeholder reads a current dashboard with no seat |
| **12** ✅ | **Team deployment guide (§16)** — sibling to the single-operator guide | A non-technical operator installs unaided from the guide alone |
| — | Seed `.gitattributes` ships LFS for `.png` (§8) — one file, fold into phase 3 | New org never accumulates the media debt |
| — | *(off critical path)* the operator's-master media migration (§8, §13.1) | Only if that master ever moves to the team shape |

**SYS-028 closes at phase 2**, not last — the toggle is now the structural mechanism, not the
final bow on top.

**Dogfood before selling.** The product cannot ship on a design nobody has run. Once phases 2–9
land, stand up a **two-operator pilot on a real deployment** — an internal one or a friendly first
client — for one full campaign cycle before the guide (phase 12) is written as fact rather than
intention. Every claim in that guide should be one somebody has actually performed.

---

## §16 Provisioning and the deployment guide

A product is the install experience, not just the code. Today's
[`docs/guide/deployment-guide.html`](../guide/deployment-guide.html) walks ONE person through ONE
machine. The team shape needs two things it does not have.

### 16.1 Two roles, not one

The single-operator guide has one reader. The team guide has two, and conflating them is why most
multi-user install docs fail:

| Role | Does it once, for the organisation | Frequency |
|---|---|---|
| **Administrator** | Creates the CODE + DATA repos on the chosen host · grants the team access · sets up the SharePoint publish target · cuts the first release | Once per organisation |
| **Operator** | Clones both repos · runs the doctor to READY · gets their identity registered · starts working | Once per person |

Write them as **separate documents**. An operator who reads repo-creation steps concludes the
product is for engineers, and stops.

### 16.2 Provisioning must be a command, not a checklist

Every manual step is a step someone gets wrong at the fifth organisation. The operator path should
be one command that:

1. clones CODE (at the pinned release tag) and DATA
2. writes `.claude/local/config.json` with the resolved `data_root` (§3)
3. registers operator identity from `git config user.email` (§4)
4. runs the doctor and prints READY or the exact remediation (§14)

Everything above already exists in pieces — `data_root()` reads the config, the doctor reports
prerequisites. What is missing is the thing that *writes* the config and drives the sequence.

### 16.3 The guide must be tested by someone who has not read this spec

The existing guide's known gaps are instructive and both are already on the backlog: **SYS-139**
(no screenshot of Claude Code's "Open folder" control — the step most likely to strand a
first-timer) and **SYS-140** (whether Git for Windows is actually required, which the guide
currently calls optional). Both were found by watching a real person, not by review. The team guide
needs the same treatment before it ships: a fresh-machine, fresh-person UAT, in the manner of the
existing `docs/guide/uat-*.html` run sheets.

**Acceptance for phase 12**: a non-technical operator, given only the guide and repo access,
reaches a working install and ships one asset — without asking the operator a question.
