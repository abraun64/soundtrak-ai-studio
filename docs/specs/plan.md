# Plan — Phase 3 Schema (v4)

**Spec version**: v4 · 2026-09-30 — a reader-first rebuild from fourteen operator findings on a
long programme. **Decision first**: "Plan at a glance" opens the document and the column guide,
glossary and attribution key move to a collapsed block at the foot. **One strategy table** replaces
the prose Phasing paragraph. **Waves carry the programme's rollout** — a full-programme Waves table
with date windows, staggered channel starts and test-and-learn in the table, with dependency build
order kept *inside* each wave. **Launch / Ongoing is declared, never guessed.** Channels say where
work lives (Measurement means measurement). A **setup completeness rule** — anything that sends,
collects, publishes, pays or measures needs its enabling rows, each with a `Check:` test. Phase 6
and Search are in the first draft, not bolted on. Plus four new automatic checks, badges from real
status only, and plain language with a mandatory cold read.
· v3 · 2026-07 — Type / Channel / Description columns; one table with a channel ⇄ wave toggle.
· v2 · 2026-06-03 — §N Phase 5 + 6 readiness gate per `docs/specs/rollout-architecture.md` §4.

The **Plan** is the operational map for the campaign. CM authors it after the operator picks a
Concept: the asset list, the agent assignments and the sequencing the operator approves before
Phase 4 fires.

**Length target: 2–3 pages** for a campaign, more for a multi-month programme. Table-led.

**Stored**: `campaigns/<slug>/plan.md` (markdown authoritative) + rendered `plan.html`.

**Locked**: at end-of-Phase-3 operator approval. Material scope changes (asset added or removed,
major sequence change, a change of ownership or platform) need vN+1 and re-approval. Minor tweaks
(a date shift, a dependency reshuffle, filling a TBD) don't.

---

## Reading order is part of the spec (v4 · finding A)

The old spec opened with "How to read this plan" — a column guide, a glossary and an attribution
key, before the reader reached a single decision. That is reference material standing where the
answer should be.

**The order is now fixed:**

1. **Plan at a glance** — the decision surface. What this is, what it promises, what ships, when,
   what it costs, what the operator has to do, and the one decision being asked.
2. **Setting** — Launch, Ongoing, or Launch-then-ongoing.
3. **Strategy** — one table.
4. **Waves** — the rollout.
5. **Asset list** — the work.
6. Roster · Budget · What ships without asking · Open questions.
7. **Getting it live, and keeping it running** (the former "§N").
8. **Change log.**
9. **How to read this plan** — column guide, glossary, attribution key. **Collapsed, at the foot.**

A reader who stops after section 1 should still know what they are approving.

---

## Schema

```markdown
# <Campaign Name> — Plan v<N>

**Concept selected**: <link>  ·  **Approved**: <date>  ·  **Status**: Draft / Approved / Locked
> *(Column guide, glossary and change history are at the foot of this plan.)*

## Plan at a glance

| | |
|---|---|
| **What this is** | One sentence a stranger understands. |
| **What it promises** | The single outcome, and the one number that says it worked. |
| **Setting** | Launch · Ongoing · Launch-then-ongoing *(declared — see below)* |
| **Runs** | <start> → <end>, in <N> waves |
| **What ships** | <N> marketing items across <M> channels, plus <K> setup jobs |
| **What it costs** | $<n> total — $<n> paid media, $<n> production, $<n> held back |
| **What you have to do** | <the operator's own jobs, counted: e.g. "4 approvals, 2 accounts to create, 1 payment to set up"> |
| **Decision now** | Approve this plan so production can start — or tell me what to change. |

## Setting

**Setting: <Launch | Ongoing | Launch-then-ongoing>** — declared, not inferred.

One line on why. *Launch* = a one-time stand-up with an end. *Ongoing* = a recurring engine with no
end date. *Launch-then-ongoing* = a stand-up that becomes an engine, and the handover point is
named here.

## Strategy

One table. Each row is a part of the strategy; the last column points at the work that delivers it.

| Part | What it is | What it promises | When | Rows |
|---|---|---|---|---|
| <name> | <plain description> | <the outcome this part is responsible for> | <wave or window> | <asset-list row numbers> |

## Waves

| Wave | Window | What it is for | Channels starting | Test and learn | Rows |
|---|---|---|---|---|---|
| 1 | <start → end> | <the goal of this wave> | <channels that begin here> | <only if the rollout tests here> | <rows> |

## Asset list

| # | Asset | Description | Type | Channel | Wave | Review format | Form | Ships | Copy file | Owner | Target date | Depends on | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Visual identity kit | The logo, colours and templates every other item is built from | asset | Brand foundation | 1 | `output` | Brand mini-guide (HTML) + logo + templates | Logo (SVG) + social-image template + article template | `none` | Producer | YYYY-MM-DD | — | Everything visual depends on this |
| S1 | Create the publishing account | Stand up the account so every item can link to it | setup | Publishing platform | 1 | — | Operator action (account) | — | `none` | Operator | YYYY-MM-DD | — | Check: the account exists and the address resolves |

## Roster
## Budget
## What ships without asking
## Open questions
## Getting it live, and keeping it running
## Change log (vX → vY)

<details markdown="1">
<summary><strong>How to read this plan</strong> — column guide, glossary, attribution key</summary>
...
</details>
```

---

## Setting — declared, never guessed (v4 · finding D)

The renderer used to classify each row Launch or Ongoing by reading words in a Phase column. On a
long programme that misfiled work: builds scheduled for January, part of the ongoing engine, sat by
themselves in a group of their own because nothing in their wording said "ongoing".

- **The Plan declares `Setting:` once**, at the top, from the list above.
- **The renderer reads the declaration.** It may only fall back to the keyword heuristic for a
  legacy plan that has no `Setting:` line, and when it does it says so on the surface.
- **A row may override** with an explicit `ongoing` or `launch` value in `Notes` — spelled out, not
  implied by vocabulary.

`plan_lint` fails a v4 plan with no `Setting:` line.

---

## Strategy — one table (v4 · finding B)

The strategy used to be a prose paragraph plus a scattering of per-part sections, which meant the
same information in several shapes and no way to see it at once. **One table**: part · what it is ·
what it promises · when · rows.

- **"What it promises" is an outcome, not an activity.** "Builds a list of candidates we can email"
  — not "runs social posts".
- **"Rows" is the join to the work.** Every strategy part names the asset-list rows that deliver it,
  and every asset-list row belongs to at least one strategy part. A part with no rows is a wish; a
  row belonging to no part is unexplained work. Both are findings.
- Keep it to the parts a reader must hold in their head. If the table runs past about eight rows,
  the strategy is a list of tactics.

---

## Waves — the programme's rollout (v4 · finding C)

On a ten-wave programme the old model broke down. Waves were derived purely from the dependency
graph, so they described *build order* while the operator needed *rollout* — when each channel
starts, what each stage is for, and what is being tested before the next stage commits.

**Both exist, and they are different axes. Say which you mean.**

- **A wave is a stage of the rollout**, with a **date window**, a purpose, the channels that start
  in it, and its test-and-learn. This is **authored** from the strategy, because only the strategy
  knows when a channel should open.
- **Build order lives inside a wave**, and is still **derived** from `Depends on`. Within one wave,
  a row whose dependencies are all met can be produced immediately and in parallel with its
  siblings. Never hand-author a build-order column — it drifts from the dependencies.

So: the Waves table replaces the old Phasing paragraph, the asset list carries a `Wave` column, and
the dependency graph orders work *within* each wave.

**Rules:**

- **Channel starts are staggered on purpose.** Two channels starting in the same wave should be
  there because the strategy wants them together, not because everything defaulted to wave 1. If
  every channel starts at once, say why.
- **The waves come from the Concept's rollout, not from here.** The Concept owns the phasing and
  its logic (concept spec §6); the Plan dates it, puts rows against it and checks it. If the Plan
  finds itself inventing the sequence, the Concept is underspecified — go back rather than guess.
- **Test-and-learn is a column, not a quota.** Where the rollout has a test phase, the entry names
  what is being learned and what result would change the next wave. Where it doesn't, the cell is
  blank — **a plan that commits from the start is a legitimate plan**, and manufacturing a test to
  fill every row is worse than an empty cell (operator correction 2026-10-01).
- **Every wave has at least one row that starts it** (see the setup rule below). A wave with no
  opening row cannot begin.
- **Windows must not overlap incoherently.** Wave N's window starts on or after wave N−1's starts;
  a deliberate overlap is fine and is stated. `plan_lint` checks the ordering.

---

## Channels say where the work lives (v4 · finding E)

A channel is **the surface the work lives on**. It is not a category of effort, and it is not a
bucket for things that don't fit.

The failure: setup rows for lists, forms and publishing were filed under **Measurement** because
they were "plumbing". Measurement then read as a large workstream when almost none of it measured
anything.

- **`Measurement` is only for true measurement** — analytics, tracking, reporting, the numbers that
  tell you whether it worked. Standing up a mailing list is not measurement; it is the mailing
  channel's setup.
- **Standard channels**: `Brand foundation` · `Website` · `Email — <list name>` · `LinkedIn + social`
  · `Video` · `Ads & paid` · `Publishing platform` · **`Candidate database`** *(new in v4)* ·
  **`Search: Google and AI answers`** *(new in v4)* · `Measurement` · `Partnerships` · `Events`.
- **Extend the list when a real new surface appears**, and add it here in the same turn. Don't
  overload an existing channel because the list is short.
- **The Plan's channels and the gallery's channels must match.** The gallery derives its channels
  from the Plan through the shared `plan_model`, and `gallery-config.yaml` declares the taxonomy. A
  channel in one and not the other is drift, and `plan_lint` fails on it.

---

## Setup completeness (v4 · finding F)

The programme shipped with no mailing lists created, no form routing, no publishing path for
leadership content and no way to pay a referral. Each was invisible because the *marketing* item
existed and looked complete.

**The rule — anything that sends, collects, publishes, pays or measures needs its enabling setup
rows.** Walk those five verbs against every channel before the Plan is done:

| If the plan… | it needs setup rows for |
|---|---|
| **sends** | the list or audience, the sending account, the from-address, consent and unsubscribe |
| **collects** | the form, where submissions go, who is notified, where the data lands |
| **publishes** | the account, the access for whoever posts, the approval route, the publish action itself |
| **pays** | the payment method, who authorises it, the terms whoever is paid has agreed |
| **measures** | the tracking, the tagged links, the report and who reads it |

**Every setup row carries a `Check:` line in `Notes`** — a test a person can run to see it is done.
Not "configured correctly" but *"Check: send a test to yourself and it arrives with the right
from-name"*. A setup row with no check cannot be verified and will be marked done on hope.

**Every wave has a row that starts it.** For each wave, at least one row must be producible on day
one of its window — otherwise the wave opens blocked.

`plan_lint` flags a setup row with no `Check:`, and a wave with no opening row.

---

## The asset list

One table — every marketing item AND every setup job, as rows. Keep `# | Asset` as the first two
columns: the gallery and `check-state` contract keys on them.

**Type values**
- `asset` — a **marketing deliverable** (page, post, image, video, email). Gets an asset folder, a
  per-item gate and a gallery tile.
- `setup` — a **setup, deploy or configuration job**. Plan-only: `Ships` is `—`, no asset folder, no
  gallery tile. It sits beside the work it enables so a channel reads as a complete unit. Give it an
  `S<n>` id so other rows can depend on it.

**Row numbers never change** (v4 · finding J). A row's `#` is its permanent identity: dependencies,
the gallery, `check-state` and the operator's own notes all point at it. When a row is removed, its
number is **retired, not reused** — leave the gap. When a row is added, take the next free number
even if it sorts oddly. Renumbering a plan silently repoints every dependency and every reference
made outside the document. `plan_lint` fails on a duplicate `#`, and on an `S<n>` clashing with an
existing id.

### Name and description — written for a stranger

Both are the operator's decision surface: someone who has never seen this campaign must read them
and know exactly what the thing is and what it is for, with **no interpretation**.

- **No internal jargon.** Say the plain thing — *social share-image*, not *tile*; *the weekly-issue
  tool*, not *the cadence engine*; *auto-approved*, not *fast-lane*.
- **Spell out every acronym on first use** — *business number (ABN)*, *tagged links (UTM)*, *the
  goal (KPI)*. Never a bare acronym.
- **No cross-references** — no `§3`, no `A2`, no raw file path, no "the X unit".
- **No cryptic codes.** An issue's description says what it is *about*, never "learning A2".
- **The test**: could someone outside marketing read it and act with zero interpretation?
- The description is the *purpose* — the format lives in `Form` and `Ships`.

### Review format
- `output` — the specific deliverable; the operator approves it as-is.
- `template [+N exemplars]` — the template is the approval target; populated examples inherit it.
- `variant-comp [N × M]` — one representative comp is the approval target; resizes inherit it.

### Copy file
`md` (editable Markdown companion) · `csv` (multi-variant copy) · `pptx` / `docx` (the document *is*
the deliverable) · `none`.

### Ships — the output manifest

The **authoritative contract for exactly what each row produces** — one entry per *distinct output*,
intermediate or final. `Form` describes the item in prose; `Ships` enumerates the concrete outputs.

- A deck whose `Form` is "slide deck + presenter notes" ships **two formats**: `HTML deck + PowerPoint`.
- A video whose `Form` is "silent social videos" ships **two gated outputs**: `4 storyboards (HTML)
  + 8 × MP4` — the storyboard has its own approval gate before expensive rendering, so it is named.

This column is load-bearing, not documentation:

- **Gallery tiles = Ships, 1:1.** Every entry becomes exactly one tile; nothing else does. A
  non-web-renderable output still ships and tiles as a format-card with a download.
- **asset.yaml `ship: true` = Ships, 1:1.** Render sources, embedded component images, deployment
  wrappers and the asset record are never ships. A prose file that is merely the `copy_file` behind
  a visual tile stays `ship: false` — it is an input to a shown deliverable, not a second one.
- **`check-state` validates the chain** Plan `Ships` ↔ `ship: true` ↔ tiles. A mismatch is drift.
- **The gallery reconciliation is the closing guard on the count.** `build-gallery` counts the
  `ship: true` files in `asset.yaml` and flags a deviation from the `Ships` count, so a mix change
  that reached `asset.yaml` but not the Plan is caught even when it renders no visual tile.

**If you can't fill `Ships` cleanly, the row isn't specified yet** — tighten the scope before
production rather than letting the Producer improvise.

### Search is in the first draft (v4 · finding L)

Search arrived late on the programme, as rows added after the plan was approved — which meant the
pages it needed to influence were already written.

**Every plan with a website or a publishing channel carries search in its first draft**, as rows,
in the wave where the pages are actually built:

- the questions real buyers type, and the answers the site owes them;
- which existing or planned pages answer them, and what is missing;
- how the pages are found by both a search engine and an AI answer engine — the channel is
  `Search: Google and AI answers`, because a page that only satisfies one of them is half-built;
- the measurement rows that tell you whether any of it worked.

If the campaign genuinely has no search surface, say so in one line under Open questions. Silence
reads as an omission.

### Phase 6 is in the plan from the start (v4 · finding K)

For a long programme, the running rhythm is not an appendix. The old spec appended the Phase-5/6
readiness section at the *end of Phase 4*, which is far too late for a programme whose later waves
*are* the ongoing engine: the rows that keep it running were being discovered after the plan was
approved.

- **Setting `Ongoing` or `Launch-then-ongoing` → the plan carries its recurring work as rows from
  the first draft**, in the waves where it begins: the repeating items, who runs each cycle, how
  long a cycle takes, and the per-tenant cadence skill that is the operator's entry point.
- The readiness section ("Getting it live, and keeping it running") still gets its own operator gate
  at the end of Phase 4 — but it is *confirming* work already planned, not inventing it.
- Setting `Launch` keeps the old behaviour: the readiness section is appended at end of Phase 4.

### Cadence skill scaffold

For `Ongoing` or `Launch-then-ongoing`, the asset list must include a per-tenant cadence skill as a
Phase-4 deliverable — `.claude/skills/<tenant-slug>-<cadence-name>-assets/`. Intentionally thin at
this stage (orchestration prose only, no novel logic); versioned after two or three real cycles.
Without it, the running-rhythm document points at a skill that doesn't exist.

### Foundation-shaped campaigns

Where the Brief's objective is strategy development, the asset list is **strategy artifacts** rather
than market-facing items: segment map · competitive claim map · value-proposition one-pager · brand
platform · fit evidence base. Each is a normal row with a gate and a tile. At wrap they graduate to
the tenant layer, and that graduation gate *is* the foundation approval.

---

## Waves are executable — CM dispatch

The wave structure drives production. In Phase 4, CM dispatches a wave's `asset` rows whose
dependencies are met as **one parallel Producer batch** — one Producer role, many concurrent jobs.
The operator gate is at the **wave boundary**: approve wave 1 and wave 2 fires together, except
where a specific row is flagged as needing its own approval. `setup` rows the operator owns are the
roots that gate the first asset wave — surface them up front.

---

## The plan is the living source of truth

The Phase-4 gallery **derives** its channels, names, descriptions, waves and Launch/Ongoing split
from this plan through the shared `plan_model`. The gallery is a *view*, never a second list.

- **Any change to the asset set, in any phase, updates this plan first — in the same turn.** A row
  added during Phase-4 review, dropped, or re-scoped: edit it here, then re-render `plan.html` and
  rebuild the gallery. Material change → version bump and re-approval; a like-for-like swap doesn't.
- **`check-state` enforces the floor**: an asset folder on disk with no plan row is flagged as
  drift, and the gallery shows an unmatched tile in a visible "not in the plan yet" group rather
  than hiding it.

### Badges come from real status only (v4 · finding I)

Rows showed a green **Live** badge that nothing had earned — the badge was inferred from wording.

**A status badge may only render from an explicit machine-readable status field**, never from prose.
This is the rule SYS-127 established for the gallery (`review_status`, trusted first, with prose
inference as a fragile fallback); it applies to every Plan surface too. If no status field is set,
render no badge. **An absent badge is correct; a wrong one is a lie the operator acts on.**

---

## Roster

Specialists in scope. Producer for production; Brand Manager on every gate; CM orchestrating;
Creative Director on call for creative-integrity callbacks; the operator for bylines, sign-offs and
publish actions. Additional agents only where the Producer escalates beyond the AI-tooling ceiling.

## Budget

| Line | Amount | Purpose |
|---|---|---|
| <paid line> | $<n> | <what> |
| Production tooling | $<n> | AI generation costs |
| Held back | $<n> | 5–15% reserve |
| **Total** | $<n> | matches the Brief's total |

## What ships without asking (v4 · finding G)

Formerly "Fast-lane rules". Two changes, both from the same finding: **give people information and
short rules rather than locking in a process.**

- **State the rule, not the workflow.** "Weekly companion posts go out without approval once the
  first three have set the pattern" is a rule. A six-step routing diagram is a process that will be
  wrong by the second week.
- **Say what the rule is for**, so someone can apply judgement at an edge the rule didn't
  anticipate. A rule whose purpose is unstated gets followed off a cliff or ignored entirely.
- Keep the list short and specific. "All social posts" is too broad.
- Name what is **not** included: anchor posts, paid creative, anything with a new format.

## Open questions

Genuine pending items only, each with who resolves it and by when. Includes dependencies outside
the campaign's control — legal review windows, someone's availability, a decision not yet made.

---

## Getting it live, and keeping it running

*(Formerly "§N — Phase 5 + 6 readiness". Renamed per finding H: internal section numbers are not
names. For `Ongoing` settings this is populated from the first draft per finding K; for `Launch` it
is appended at the end of Phase 4.)*

> **Authored**: <date> · **Status**: Draft / ✅ Approved / 🟥 Blocked · **Approves**: operator

### Going live

**Read these to populate it**: the Brief's technology setup (destination per channel), its roles
(who runs what), its cadence shape, the asset list above, and the tenant's integration file.

| # | Item | Where it goes | How | Owner | How we know it landed |
|---|---|---|---|---|---|

**Setup to complete first** — accounts, keys, the integration file, the operator's machine, the
folder structure. Each with its `Check:`.

**Training** *(only where the tenant runs it themselves)* — materials to read beforehand, a live
session on day one, and how long support runs afterwards.

### Keeping it running *(any setting except Launch)*

**Who owns each cycle** and **how long a cycle takes**, then the cycle steps: what triggers it, what
the operator does, what fires automatically, what they must do by hand. **Escalation**: one line per
category naming what to do and who to contact.

### Retro milestones

Per `docs/specs/retro.md`: a light retro at each phase boundary (~10 min, skippable if the operator
confirms there was no friction), and a mandatory heavier one at each wave close, at campaign end or
quarterly, and at the fourth cycle of a running rhythm.

### Before this section is approved

- [ ] The Brief's technology setup, roles and cadence shape are resolved — no TBDs.
- [ ] Every row has its destination recorded, or an explicit TBD with a reason.
- [ ] No outstanding Brand verdicts.
- [ ] The operator has confirmed anything they must provide: access, keys, availability.

Any unmet criterion keeps the status 🟥 Blocked, and the next phase does not fire.

---

## Numbers must agree with each other (v4 · finding M)

A plan is read by someone checking whether it adds up. Three specific consistency rules, each from a
real inconsistency:

- **The budget split matches its total**, and the total matches the Brief. If a line changes, the
  total and the Brief reference change in the same edit.
- **A test's length is stated once and used everywhere.** A paid test described as "about seven
  weeks" in one place and "a month" in another is two different plans. State the window with dates
  in the Waves table and refer to it, never restate it.
- **Cited evidence keeps its source.** A number carried in from research names who published it and
  when, and the figure must be present in that source. A statistic whose source doesn't contain it
  is worse than no statistic — flag it for verification rather than passing it through.

---

## Plain language, and the cold read (v4 · finding H)

- **Plain language everywhere** — the name, the description, the notes, the change log. Notes may
  carry finer production detail but stay interpretable. The bar relaxes on *depth*, never *clarity*.
- **Internal headings get real names.** "§N" is a cross-reference, not a title. Name the section
  after what the reader gets from it.
- **A cold read is mandatory before the plan is surfaced.** Run the `review-ready` gate: the jargon
  lint plus a read as someone who did not write it. Fix what it finds; surface the judgement calls.
- **Every defined term is checked against its source.** A term borrowed from a framework, a
  platform or a client's own language must mean here what it means there. The failure this comes
  from: "paid read" was used for something that was not a paid read, and the error propagated
  because nobody checked the definition against the source. **Where a term is load-bearing, quote
  the source line.**
- **A shared glossary lives in the collapsed block at the foot** — one definition per term, used
  consistently, so the same thing is not called three things across a long document.
- **Use the plan-safe edit path.** Editing a plan by hand risks renumbering rows, breaking the
  `# | Asset` contract, or reordering sections the renderer classifies. Make structural edits
  through the tooling that preserves row identity and section order, and run `plan_lint` afterwards.
  If you must hand-edit, re-run `plan_lint` before surfacing — **an edit after a check re-opens that
  check** for the surface it touched.

---

## Automatic checks — `plan_lint.py` (v4 · finding J)

Four things were being checked by eye on the long programme, and two were caught only by accident:
dates out of order, waves whose windows didn't line up, gallery channels that had diverged from the
Plan's, and a duplicate row id (`S17` used twice). A guard only covers what it enumerates, so these
are enumerated:

| Check | Fails when |
|---|---|
| **Dates in order** | a row's target date falls outside its wave's window, or a wave's window starts before the previous wave's |
| **Wave windows** | a wave has no window, windows are incoherent, or a wave has no row that can start it |
| **Gallery channels match** | a channel appears in the Plan but not `gallery-config.yaml`, or the reverse |
| **Row numbers stable** | a duplicate `#`, or an `S<n>` clashing with an existing id |

Plus the structural floor: a v4 plan must declare `Setting:`, and every `setup` row must carry a
`Check:`.

```bash
python .claude/skills/plan-lint/plan_lint.py campaigns/<slug>/plan.md
```

Run it before surfacing a Plan, alongside `review-ready`. It is wired into the system smoke test, so
a regression in the checks themselves goes red before it reaches a campaign.

---

## Drafting discipline

- The asset list is the headline — table-led and scannable.
- The Brief's effort tier sets the expected count: XS 1–3 · S 3–6 · M 6–12 · L 12–25 · XL 25+. Above
  the range, justify per row; below it, justify the restraint.
- Owner must match the agent roster.
- **Change history goes to the foot, never the header.** A revised plan re-reads as a clean whole
  from the top. Put a one-line pointer under the header and a single `## Change log (vX → vY)`
  section at the bottom. The renderer auto-moves history-classified sections to the tail but cannot
  move header prose — so never author change history as header prose.
- **The channel summary is never truncated** — it shows every row name at full length.
- **Check the rendered plan at phone width** before surfacing (v4 · finding N). Tables are the whole
  document here; a table that scrolls off a phone is unreadable to an operator approving on one. The
  wide tables fold to stacked rows at narrow widths — confirm it on the rendered HTML, not the
  markdown.

---

## What this Plan does NOT contain

- Per-row detail — lives in each Per-Step Brief, written at dispatch time.
- Brand context — lives in the Brand Context record; CM injects slices.
- Concept narrative — lives in the chosen Concept.
- The full going-live runbook — `campaigns/<slug>/phase-5-rollout.md`.
- The full cycle runbook — `campaigns/<slug>/phase-6-cadence.md`.
- Tenant credentials — `tenant/<tenant>/integrations.yaml`, never here.

---

## How to read this plan *(authoring note: this block renders collapsed, at the foot)*

The Plan's own reference material — the column guide, the glossary and the attribution key — is
authored inside a `<details markdown="1">` block as the **last** section before the change log.

- **Column guide**: one line per column of the asset list.
- **Glossary**: every load-bearing term, one definition each, matching its source.
- **Attribution key**: how each line was sourced — `[operator]` stated, `[interview]` captured,
  `[AI synthesis]` composed from inputs.

The `markdown="1"` attribute is required for tables and lists inside `<details>`.

---

## Migrating a v3 plan

A v3 plan keeps rendering. To bring one to v4:

1. Add `Setting:` and the "Plan at a glance" table at the top.
2. Replace the Phasing paragraph with the Strategy table, then the Waves table with windows.
3. Re-file any setup row sitting under `Measurement` to the channel it actually enables.
4. Walk the five verbs — sends, collects, publishes, pays, measures — and add the missing setup
   rows, each with a `Check:`.
5. Add search rows if there is a website or publishing channel.
6. Move the column guide and glossary into the collapsed block at the foot.
7. Rename `§N` to "Getting it live, and keeping it running".
8. Run `plan_lint` and `review-ready`; check it at phone width.
9. Bump the version and re-approve — this is a material change.

---

## Cross-references

- **Rollout Architecture**: `docs/specs/rollout-architecture.md` — defines the readiness gate and
  the phase-5 / phase-6 artifacts this section seeds.
- **Brief spec**: `docs/specs/brief.md` — technology setup, roles and cadence shape are the upstream
  source for going live. The Brief's exhaustive intake is where the strategy's evidence comes from.
- **Asset spec**: `asset.yaml`'s `deployment:` block feeds the going-live matrix.
- **Gallery QA**: `docs/specs/gallery-qa.md` — the `Ships` ↔ `ship: true` ↔ tile reconciliation.
- **Review-ready**: the mandatory cold read before any surface reaches the operator.
