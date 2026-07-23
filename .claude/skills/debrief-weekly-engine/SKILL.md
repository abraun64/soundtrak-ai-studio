---
name: debrief-weekly-engine
description: |
  Soundtrak - The Debrief weekly production engine.

  Turns ONE editorial-backlog learning into a publish-ready Debrief edition: the ~900-1,100-word
  long-form article (the operator's own voice, Edition 1 exemplar), the 1:1 evidence tile and the 4:5
  Before/After/Learning tile, the two LinkedIn posts (the operator personal + Soundtrak company), and
  three Substack Notes (native promo for the Notes feed).
  One optional input (the target learning, OR "next in the calendar"); the engine drafts, runs the
  content-subedit voice gate + Governance + Brand, and surfaces for review. Outputs land on the
  OneDrive cadence folder, reviewable in the campaign gallery; the operator posts to Substack +
  LinkedIn, and the engine auto-publishes the article to the Soundtrak website (like The Signal).

  TRIGGER when: the operator (or a future Debrief editor) wants to produce the next Debrief
  edition + its trailer. Common phrasings: "run the Debrief weekly engine", "produce
  the next Debrief edition", "draft this week's Debrief on L4", "bank the flagship
  edition through the engine", or the explicit slash command "/debrief-weekly-engine".

  DO NOT TRIGGER when: it's a one-off Brief / Concept / Plan / launch-kit (Phase 1-5)
  task - use /campaign-manager; it's a different Soundtrak content stream (The Signal
  has its own cadence, not this one); or it's the look kit / editorial calendar /
  article hub themselves (those are Phase-4 build assets, not cadence outputs).
---

# The Debrief - Weekly Production Engine

**Version**: v0.2 · 2026-07-08, **format-refreshed 2026-07-20** to the operator's Edition-1 voice + the new stages (long-form article, screenshot mid-article, two-LEARNED evidence beat, the 4:5 Before/After tile, the two LinkedIn posts, and the automatic website publish) · Phase-4 (asset-development) deliverable, built *before* launch so 2-3 editions can be banked *through* it (Plan §sequencing: "the newsletter about building an AI system is itself produced by the AI system, that's the proof").
**Status**: ✅ **INSTALLED 2026-07-23** to `.claude/skills/debrief-weekly-engine/` on `main` (Phase-5 Step 5). This copy in the asset folder (`campaigns/soundtrak-ai-buildlog-2026q3/assets/02-production-engine/`) is the source of truth + reviewable draft; the installed copy under `.claude/skills/` is what `/debrief-weekly-engine` runs. **Path convention**: `scripts/…` is relative to this skill; every `assets/…` data path below is under `campaigns/soundtrak-ai-buildlog-2026q3/` (the scripts resolve it automatically). Re-install = re-copy this file + `scripts/` over the installed copy.
**Owner**: Soundtrak - The Debrief (AI Build-Log newsletter), the sub-brand's Phase-6 weekly cadence.
**Cadence shape**: **ongoing** (weekly) → the per-cadence skill is a Phase-4 deliverable, not a post-deployment retrofit (memory rule `feedback_cadence_skill_is_phase3_deliverable`).
**Replaces**: the conversational "open chat with CM and ask it to write this week's issue" pattern. One command for the editor; same underlying execution (Producer + content-subedit + Governance + Brand).
**Reference standard**: the approved **A1 look kit** (`assets/01-look-kit/`). This skill *fills and gates* that kit's issue-header template; it invents no new visual language. Every component (emblem, masthead lockup, palette, type, the evidence screen card, the hero screen) is the look kit re-run with this edition's content.

> ⚠️ **This is a thin orchestration scaffold (~340 lines + 3 helper scripts).** It carries NO novel design logic and NO new copy engine. The issue format is A1's `issue-header-template.html`; the voice gate is the shared `content-subedit` skill; the review layer is the campaign's own Governance-then-Brand gate. The engine's whole job is orchestration: resolve the learning → draft → clean → gate → populate → surface. If you find yourself adding a component or a renderer here, it belongs in A1, not in the skill.

---

## The design principles this engine dogfoods

The Debrief is a newsletter *about building an AI system*. The engine that produces it is itself built on the system's own learnings - it practises what the editions preach:

- **Two inputs, derive the rest (backlog L8).** The editor supplies EITHER a target learning id OR nothing (= "next in the calendar"). The engine derives the draft, the evidence block, the hero pick, and the trailer, and surfaces drafts for review. It is **never a form of questions.**
- **Build the machine that publishes, not the one-off (backlog L16).** This skill IS that machine for The Debrief. It's the on-thesis proof, not a slogan.
- **Match the format to where it lives (backlog L13).** The edition ships as an HTML issue (browse/paste) + the trailer as copy + a tile image; not a meta-preview of either.
- **A rule in the spec is a mechanism, not a hope (backlog L9).** The receipts guardrail and the hero scrub are enforced in code (`populate_issue.py`, `hero_scrub.py`), not left to a memory note.
- **Teaching, not selling.** Every edition hands over a transferable lesson. No product pitch, no offer CTA. The AI Studio is downstream trust, never the ask.
- **Retrospective, always.** Each edition examines a decision *already made*, dated, shown-not-asserted. Never "here's what I built this week." Policed by the "would a debrief say this?" test (look-guide.md).
- **Receipts, not vanity.** The evidence record is elapsed / files / tokens / send-backs. **Never operator hours. Never a client-confidential detail.** (Enforced by the receipts guardrail in `populate_issue.py`.)
- **AU English, zero em-dashes.** The engine runs `content-subedit` as a distinct labelled pass on every issue and every trailer.

---

## Required inputs (minimum viable - often ZERO)

The engine asks for the **least** it can. There is exactly one optional input:

1. *(optional)* **Target learning** - a backlog id (e.g. `L4`) OR a working title. **If omitted, the engine takes the next unwritten row from the editorial calendar** (`assets/14-editorial-calendar/`), top to bottom, skipping rows already Banked/Published. That's the "next in the calendar" default.

That's it. **Everything else is AI-derived and editor-reviewed.** The editor can say "use all defaults" to ship the AI drafts as-is.

> The one truly required *human* input across the whole cycle is the **hero-screenshot scrub verdict** (six locked points) and the final **publish decision** - because a screenshot publishes whatever is in frame, permanently, and because a debrief is the operator-bylined. Neither is derivable; both are gated (see below).

---

## AI-derived (editor reviews drafts)

The engine reads the resolved learning's spine + the look kit + brand context, and drafts the following. It surfaces each for confirm/edit before the final issue populates:

| What | How the engine derives it | Editor's job |
|---|---|---|
| **The learning + its four-field spine** | `next_in_calendar.py` resolves the id (or "next") → pulls STARTED / ENDED / CHANGED / LEARNED from the backlog. For a placeholder slot (7-12), the engine expands it to a full spine from the AI Learnings board and holds it to the **two-test bar** (real AI-Studio learning + reader-implementable) before drafting. | Confirm the pick / spine |
| **Headline (failure-led) + standfirst** | Drafted in the operator's own first-person register (**Edition 1 is the locked exemplar**): lead with the failure, resolve in the standfirst. | Approve or edit |
| **The article body** | **~900-1,100 words, the operator's own voice** (Edition 1 exemplar, NOT a generic register): names AI Studio / Claude.ai, marketing-specific, concise. Structure *Where I started / Where I ended / What it taught me*, one real screenshot **placed mid-article** (no hero at the top), close on the implication. Retrospective throughout. | **Edit in `edition.md`** (final word) |
| **The evidence beat** (two LEARNED lines + dated) | STARTED / ENDED / CHANGED + **two LEARNED lines** + the date. **Receipts only, NO vanity counts**: the operator dropped the elapsed / files / tokens / send-back rows in the 2026-07 rework. Never operator hours, never a client metric, never an outcome/ROI figure. | Confirm the values |
| **The mid-article screenshot** | The engine names a real Soundtrak surface that illustrates *this* lesson + a one-line caption, and places it **mid-article** where the prose reaches the surface. **The operator supplies the actual capture (stage 2); the engine never fabricates it.** | Supply the capture + **run the scrub** |
| **The evidence tile (1:1)** | The evidence beat rendered as the 1:1 LinkedIn scroll-stopper, from the look kit. | Approve or edit |
| **The Before/After/Learning tile (4:5)** | The operator's LinkedIn diagram format: a before/after process diagram + the two learnings, 1080×1350, from the look kit. | Approve or edit |
| **Your LinkedIn post (the operator, personal)** | First-person post that carries the edition into your network: failure hook (first line), the lesson in plain terms, a soft subscribe, the raw Substack URL last. Built to attach the stage-4 visuals. | Approve or edit |
| **The Soundtrak LinkedIn post (company)** | The company-page post in the Soundtrak voice, pointing at the operator's build, same pattern as The Signal's company post. | Approve or edit |
| **Three Substack Notes** | Three native Notes derived from the edition — **core lesson / mechanism / soft-link teaser** — for Substack's Notes feed (the in-platform discovery engine, the biggest on-platform growth lever after Recommendations). Native-first (each stands alone as a lesson), same voice as the edition, **no hashtags**. Meant to be spaced across the week, teaser last. Ship as `notes.md` in the edition folder. | Approve or edit |
| **Subject line / Substack title** | Drafted per BC §2 (no clickbait, no fake urgency). | Approve or override |

**Edit-loop**: any draft the editor rejects is re-drafted with the feedback baked in, up to 3 redrafts per item (Producer 3-strike rule). On the 3rd failure the engine refuses-to-surface that item and flags it.

### Format rules pinned by the 2026-07 A/B test (two independent engine runs each flagged these)

- **Word count = the prose BODY only.** "~900-1,100 words" is the opening intro line + the standfirst + the three sections. It does NOT count the header block, the evidence beat, or the footer (a full edition file runs ~1,200-1,250). Do not pad or trim to hit the target on the wrong text.
- **Headline = one clean two-sentence line** ("I did X. Then I realised Y."), and **this rule WINS if it conflicts with the exemplar or the backlog title.** Do NOT cram the full thesis or the learning into the headline; that belongs in the body + the evidence beat. (The L5 run overloaded its headline; the L2 run correctly kept the clean turn even though the backlog L2 title crams three clauses. Keep it to the turn.)
- **Screenshot: show the lesson's OWN surface where one exists; otherwise a representative AI Studio surface + a caption that connects it.** Some lessons name a specific screen (the review gallery); some do not (L5's self-ticketing lives in the backlog, not a hero screen). When the mechanism has no clean screen, use a representative surface and let the caption earn the link. The operator always supplies the real capture (stage 2).
- **"Lesson NN" = the EDITION number, not the backlog L-id.** The subheading reads "Lesson 02" for Edition 2 even when the source learning is L1. Track edition order, not the L-id.

---

## The three helper scripts (in `scripts/`)

| Script | Job | Enforces |
|---|---|---|
| `next_in_calendar.py` | Resolve the target learning: `--learning L4`, or default = next unwritten calendar row. Returns the working title + the four-field spine as JSON. | Two-inputs-derive-the-rest (L8); the running order |
| `populate_issue.py` | Fill the look kit's `issue-header-template.html` `data-slot` fields from a `cycle-inputs.yaml`; delete the slot legend. **Touches nothing else** - the red rule, emblem, masthead lockup, screen-card chrome, and which field carries red stay locked. | The receipts guardrail (blocks operator hours / ROI / proven / guaranteed / results in any record value); every slot filled |
| `hero_scrub.py` | The **LOCKED 6-point hero-screenshot scrub**. Prints the six checks, records the reviewer verdict, **BLOCKS (exit 2 = Governance Hold)** unless all six are an explicit pass. Any unsure/unanswered point = Hold (point-6 policy). | The look-guide's locked scrub; multi-tenant screenshot safety |

All three are pure orchestration/validation. They read the approved A1 files + the calendar/backlog; they do not author copy and do not invent design.

---

## Per-cycle output folder structure

All outputs land on the **Soundtrak OneDrive**, in the campaign's cadence area (separate from the Phase-1-4 asset folders so launch/build assets and cadence editions don't intermingle):

```
campaigns/soundtrak-ai-buildlog-2026q3/cadence/ed-<NN>-<slug>/
├── issue/
│   ├── issue-header.html          # the populated look-kit header (slots filled, legend removed)
│   ├── edition.md                 # the full edition body (Substack paste-ready) + subject line
│   └── images/
│       └── hero-<slug>.png        # the hero screen - a real Soundtrak surface (scrub-passed)
├── trailer/
│   ├── post-copy.md               # LinkedIn trailer copy + hashtags + alt text
│   └── evidence-block.png         # the evidence block rendered as the LinkedIn post image (16:9 / 1:1)
├── notes.md                       # 3 Substack Notes (native promo for the Notes feed; teaser last)
├── cycle-inputs.yaml              # the finalised draft picks (audit) - populate_issue.py reads this
├── scrub-verdicts.yaml            # the recorded hero-scrub verdict (p1..p5 + reviewer) - audit
├── asset.yaml                     # gallery metadata for this edition
└── ed-<NN>-<slug>.md              # short cadence-edition asset record (gate questions + next steps)
```

**Naming**: `ed-<NN>-<slug>` - `NN` is the calendar row number, `slug` from the working title. The evidence path chip on the issue is `debrief/ed-<NN>/evidence`; the hero path chip names the real surface (e.g. `soundtrak/ai-studio/history`).

**Output root**: `<OneDrive root>/Marketing AI System/campaigns/soundtrak-ai-buildlog-2026q3/cadence/ed-<NN>-<slug>/` - whichever OneDrive Claude Code is rooted at.

### The stable Phase-6 publishing surface (REQUIRED - refreshed every cycle)

**The Debrief archive** (cumulative; newest at top) - the public home + running order of every edition.
- **Lives at**: `campaigns/soundtrak-ai-buildlog-2026q3/the-debrief-archive.html` (the campaign-root archive; the live public version is the A12 article hub on soundtrakconsulting.com, which this feeds).
- **First cycle**: the engine *creates* it with the new edition as the only entry.
- **Subsequent cycles**: the engine *prepends* the new edition above the marker `<!-- INSERT NEW EDITION ABOVE THIS COMMENT ON EACH CYCLE. -->`.
- **What this is NOT**: the Substack email (that's the edition itself) or the A12 site hub (operator deploys that to Netlify). The archive is the campaign-side running record that keeps the two in sync.

---

## Reference materials (what the engine reads - does NOT modify)

- **A1 look kit** - the format this engine fills:
  - `assets/01-look-kit/issue-header-template.html` (the LOCKED per-edition layout - `populate_issue.py` fills its `data-slot` fields)
  - `assets/01-look-kit/look-guide.md` (the one-page rulebook - the LOCKED 6-point hero scrub, the palette/type locks, the do/don't, the retrospective test)
  - `assets/01-look-kit/look-kit.html` (the full component reference - the emblem, screen card, evidence device)
  - `assets/01-look-kit/emblem-debrief.svg` + `app-icon-debrief.svg` (the fixed masthead signature + favicon)
- **A0 editorial backlog** - `assets/00-editorial-backlog/editorial-backlog.md` (the input queue; the two-test bar every candidate must pass; the four-field spine per learning)
- **A14 editorial calendar** - `assets/14-editorial-calendar/14-editorial-calendar.md` (the running order; `next_in_calendar.py` pulls the next unwritten row)
- **Concept** - `concepts/selected.md` (§4 key message, §4a the 15s radio that forces the frame clear, §7 narrative architecture incl. the trailer beat, §11 force-multiplier + mandatories)
- **Brand Context** - `tenant-brand/soundtrak.md` (§2 voice - AU English, near-zero em-dashes, words-we-use / words-we-avoid, the Substack + LinkedIn channel defaults; §3 visual identity - the shared palette/type the look kit inherits; §4 receipts discipline - elapsed/files/tokens, never operator hours)
- **Compliance Profile** - `tenant-brand/soundtrak-compliance.md` (§2 prohibited claims; §3 mandatories - the **au-sender-id footer** forward-rule; risk tiers)
- **integrations.yaml** - `tenant/soundtrak/integrations.yaml` (channel→platform: Substack cookbook-publish `example.substack.com`; LinkedIn cookbook, hashtags; the ABN-pending park that blocks the bulk-email footer)
- **content-subedit skill** - `.claude/skills/content-subedit/SKILL.md` (the authoritative voice gate; loads Soundtrak §2 as the tenant source of truth)

---

## Non-negotiable rules (carried from the concept + brand + look kit - injected into every Producer dispatch)

1. **Retrospective only.** Every edition examines a decision *already made*, dated. Never "here's what I built this week." Run the "would a debrief say this?" test (look-guide) on every surface before it ships.
2. **Teaching, not selling.** A transferable lesson, no product pitch, no offer CTA. The AI Studio is downstream trust, never the ask.
3. **Receipts, not vanity.** The record is elapsed / files / tokens / send-backs, **never operator hours, never a client-confidential detail.** `populate_issue.py` blocks any operator-hour / outcome token in a record value.
4. **Send-backs left in** as a line item of the record. That is the uncopyable part; never quietly drop it.
5. **SHOWN, not proven/guaranteed/results.** The stamp word is fixed. Those claim-words are banned near it and anywhere in the edition (Compliance §2). The record shows what the build *cost*, never a result it produced.
6. **AU English, zero em-dashes.** Run `content-subedit` (Soundtrak §2 tenant precedence) as a distinct labelled pass on **every** copy deliverable - the edition body AND the trailer. Report the per-rule result into the edition asset record §7.
7. **Force-multiplier framing.** A named practitioner (the operator) debriefing his own build. Never "AI replaces the operator," never "the AI wrote this" (§0a moral-disgust research).
8. **One red argument.** Signal Red stays in its five sanctioned homes only (top rule · emblem stamp-tick · screen-card leftmost dot · SHOWN stamp · LEARNED line). No decorative red. `populate_issue.py` never adds colour; the trailer's evidence-block image inherits the same rule.
9. **Hero scrub is mandatory + blocking.** No edition publishes until `hero_scrub.py` returns CLEAR (all six points pass). In doubt → Governance Hold, not a judgment call.
10. **Clean-room.** Nothing from the archived vinyl / liner-notes newsletter; no Behavior-Gap illustration (that is The Signal's register, not The Debrief's).

---

## Governance + Brand gate (per the campaign - every edition + trailer)

Per the campaign's per-asset model, **Governance (the legal floor) signs off BEFORE Brand (the taste ceiling)** on every public surface (backlog L20 - the two gates, in order):

- **Governance** checks: retrospective frame (no live-build over-claim) · SHOWN not proven/guaranteed/results · no prohibited claim · receipts not outcomes, no operator hours, no client-confidential · **the hero scrub passed** · **the au-sender-id footer forward-rule** (see below).
- **Brand** checks: voice (BC §2, AU English, em-dash discipline, teaching-not-selling) · the "would a debrief say this?" retrospective test · one-red discipline · the issue reads unmistakably The Debrief, a distinct sibling to The Signal · craft (the header reads at a glance; the trailer stops the scroll).
- **Fast-lane** (Plan §Fast-lane): **Edition #1 (the flagship) is NOT fast-lane** - approving it pattern-locks the template + tone. Once #1 locks, Editions #2, #3 and every Phase-6 edition ship on **Governance + Brand sign-off without a fresh per-asset operator approval** - EXCEPT the two things that always reset to a human gate: (a) the **hero-scrub verdict** (a fresh screenshot every week), and (b) the **final publish decision** (the operator-bylined).

### Governance forward-rule - the au-sender-id footer (ABN pending)

An actual *published* edition (a bulk/commercial email via Substack) needs the **AU bulk-email footer**: an unsubscribe mechanism + the sender's legal entity name + ABN (Spam Act 2003; Compliance §3). **The ABN is currently PARKED** (integrations.yaml checklist - operator to provide; blocks the au-sender-id disclaimer). So:

- The engine **flags this at publish time on every edition**: "au-sender-id footer required before this goes out as bulk email - legal name + ABN + unsubscribe. ABN pending (operator to provide)."
- Substack supplies the unsubscribe mechanism natively; the **legal name + ABN** line is the missing piece. The engine drafts the footer with an `[ABN pending]` placeholder and holds the bulk send at a Governance flag until the real ABN lands.
- This does not block *drafting/banking* editions (the flagged buffer editions can be produced and reviewed now); it blocks the **bulk send**. The archive/site publication (free-to-read web page) is not a bulk email and is not gated on the ABN.

---

## Execution flow (what the engine orchestrates)

```
[1] Trigger: editor runs /debrief-weekly-engine  (optionally: "... on L4" / "... next")

[2] Load context - the engine reads:
       · tenant-brand/soundtrak.md              (voice §2 · visual §3 · receipts §4)
       · tenant-brand/soundtrak-compliance.md   (§2 prohibited claims · §3 au-sender-id mandatory · tiers)
       · tenant/soundtrak/integrations.yaml      (Substack + LinkedIn publish=cookbook · ABN park)
       · campaigns/soundtrak-ai-buildlog-2026q3/
            · concepts/selected.md   (§4 key message · §4a radio · §7 trailer beat · §11 mandatories)
            · assets/01-look-kit/    (the LOCKED format + look-guide + the 6-point scrub)
            · assets/00-editorial-backlog/editorial-backlog.md   (the spine per learning · two-test bar)
            · assets/14-editorial-calendar/14-editorial-calendar.md  (the running order)

[3] Resolve the learning:
       python scripts/next_in_calendar.py [--learning L4]
       → JSON: row number, working title, the four-field spine, source, status.
       If a placeholder slot (7-12): expand to a full spine from the AI Learnings board,
       hold it to the two-test bar (real AI-Studio learning + reader-implementable). If it
       fails either test, do NOT produce it - surface the fail and pick the next row.

[4] AI DRAFTS the article (retrospective, teaching-framed, the operator's OWN voice - Edition 1 is the
       locked exemplar; NOT a generic Seth-Godin register):
       · headline (failure-led) + standfirst
       · the ~900-1,100-word long-form body: Where I started / Where I ended / What it taught me;
         names AI Studio / Claude.ai; one real screenshot placed MID-ARTICLE (no hero at the top);
         close on the implication
       · the evidence beat: STARTED / ENDED / CHANGED + TWO LEARNED lines + dated. RECEIPTS ONLY,
         NO vanity counts (the elapsed/files/tokens/send-back rows were dropped in the 2026-07
         rework). Never operator hours, a client metric, or an outcome/ROI figure.
       · the mid-article screenshot: name a real Soundtrak surface that shows THIS lesson + a
         caption. The OPERATOR supplies the actual capture (stage 2); the engine NEVER fabricates it.
       · the subject line / Substack title

[5] AI PRODUCES the visuals (from the A1 look kit - invents no new visual language):
       · the article page (issue-header.html) - populated look kit, screenshot mid-article
       · the evidence tile (1:1) - the evidence beat as the LinkedIn scroll-stopper
       · the Before/After/Learning tile (4:5, 1080x1350) - the operator's LinkedIn diagram format

[6] AI DRAFTS the two LinkedIn posts (both gated + reviewed):
       · YOUR post (the operator, personal): failure hook (first line) → the lesson in plain terms →
         soft subscribe → raw Substack URL last; built to carry the stage-5 visuals
       · the SOUNDTRAK post (company page): company voice, points at the operator's build - same pattern
         as The Signal's company LinkedIn post
       · THREE Substack Notes (notes.md): native promo for the Notes feed - core lesson / mechanism /
         soft-link teaser, same voice, NO hashtags; meant to be spaced across the week, teaser last

[7] content-subedit gate - DISTINCT labelled pass on the article body, both LinkedIn posts, AND the
       three Substack Notes
       (Soundtrak §2: AU English, ZERO em-dashes, banned words, punchy-pair / restatement /
       recap-closing). Fix + re-scan ≤3 cycles; refuse to surface if still un-clean. Report into §7.

[8] HERO SCRUB (mandatory, blocking):
       python scripts/hero_scrub.py --image cadence/ed-<NN>-<slug>/issue/images/<screenshot>.png
       Reviewer answers the six locked points (or provide scrub-verdicts.yaml).
       Exit 0 = CLEAR → continue.  Exit 2 = HOLD → crop/scope/replace, or escalate. Do NOT publish.

[9] Populate + gate:
       python scripts/populate_issue.py --inputs .../cycle-inputs.yaml
           --template assets/01-look-kit/issue-header-template.html --out .../issue-header.html
       (Fills only the data-slot fields; removes the legend; runs the receipts guardrail; leaves
        the red rule / emblem / masthead / screen-card chrome / which-field-is-red LOCKED.)
       Then GOVERNANCE (retrospective · SHOWN-not-asserted · receipts · hero-scrub-passed ·
       au-sender-id footer forward-flag) → BRAND (voice · debrief-test · one-red · sibling-not-clone),
       on the article AND both LinkedIn posts. Auto-apply surgical fixes; only Pass-with-Required-
       Changes / Fail surface. Fast-lane: pattern-locked editions skip the per-asset operator gate
       (hero-scrub + publish decision never skip).

[10] SURFACE the batch review to the editor:
       article (EDIT IN edition.md - the operator's voice is the final word) · the 3 visuals ·
       both LinkedIn posts · the three Substack Notes (notes.md) · subject line. Edit-loop per item
       (≤3 redrafts). "Use all defaults" ships.
       Write cadence/ed-<NN>-<slug>/asset.yaml + record; PREPEND to the-debrief-archive.html; rebuild gallery.

[11] PUBLISH flag - Substack + LinkedIn have no coded adapter → cookbook (MANUAL):
       · "Substack: paste edition.md into a new post; set the header image; subject from edition.md.
          BEFORE bulk send: add the au-sender-id footer (legal name + ABN + unsubscribe). ABN PENDING
          - hold the bulk send until it lands. Free web/archive publication is not gated on the ABN."
       · "LinkedIn: post the personal + company posts with the visuals; raw Substack URL, not anchor text."
       · "Substack Notes: post the three Notes across the week (roughly one every 2-3 days), native-first;
          the teaser Note last, restacking the edition into the Notes feed."

[12] PUBLISH TO THE WEBSITE (AUTOMATIC) - same as The Signal:
       Call the publish-soundtrak-article-website skill → generate the edition's article page, add it
       to the Soundtrak website (the free article hub + a per-edition page), cross-link the hub.
       The site deploys via Netlify (operator push, as with The Signal).
       ⛔ BLOCKED until the Debrief website URL(s) are finalised + configured in
          tenant/soundtrak/integrations.yaml (a forward-flag, exactly like the ABN holds the bulk
          send). Until the URL lands: the engine still DRAFTS the page but HOLDS the publish, and
          the workflow is not signed off as the standing routine. The URL is NOT derivable.

[13] Return summary to the editor:
       · edition id · link to cadence/ed-<NN>-<slug>/ + the gallery
       · the hero-scrub verdict + the au-sender-id footer status (ABN pending vs cleared)
       · which surfaces auto-shipped (fast-lane) vs needed a fresh gate
       · the manual steps left: Substack paste-and-send · the two LinkedIn posts · Netlify deploy

[14] CLOSE THE CYCLE — record + re-render (the martech-stack loop, SYS-119). In the SAME session:
       (a) RECORD it — append (or update) the cadence entry in campaign.yaml under a top-level `cadence:`
           list (create the list on the first cycle):
             - cycle: <N>                      # 1, 2, 3 … the cadence cycle number
               edition: "Ed <NN> — <slug>"     # the edition shipped this cycle
               ship_date: "<YYYY-MM-DD>"
               status: done                    # `done` once published; `drafted` if HELD on a forward-flag
                                               #   (ABN for the bulk send / the Debrief website URL)
           This `cadence:` list is the SINGLE source the dashboard Phase-6 row reads
           (`status_mode: derive_cadence` → counts status:done vs total). No hand-kept page table.
       (b) RE-RENDER — run the turn-end operator-surface rebuild (dashboard + phase-6-cadence.html) so the
           cadence position updates on the spot (feedback_render_html_on_every_state_change +
           feedback_operator_surfaces_are_generated_from_data). A cold fresh session then reads the recorded
           `cadence:` state and reports the correct position — with NO hand-edit. This closes the loop:
           the system records its own cadence, so every fortnightly session starts from an accurate state.
```

---

## What this engine DOESN'T do

- **Click Send in Substack / post to LinkedIn**: that's the editor. The engine produces the paste-ready issue + the trailer + the cookbook steps; the human publishes.
- **Publish a bulk email without the au-sender-id footer**: hard block. Legal name + ABN + unsubscribe are mandatory for a bulk/commercial AU send (Compliance §3). ABN is pending; the engine holds the bulk send and flags it every cycle.
- **Publish a hero that fails the scrub**: hard block. `hero_scrub.py` must return CLEAR. In doubt → Governance Hold.
- **Invent new visual components or a new renderer**: it fills A1's look kit. New components belong in A1, not here.
- **Put operator hours or a client-confidential detail in the record**: hard block (the receipts guardrail in `populate_issue.py`).
- **Redraw or mock a hero surface that never existed**: the hero is a REAL captured surface. Reconstruct only if a live capture is truly impossible, and say so (look-guide).
- **Produce a placeholder edition (slots 7-12) that fails the two-test bar**: it expands the stub from the AI Learnings board and screens it; a fail is surfaced, not shipped.
- **Run The Signal's cadence**: different sub-brand, different register (Register B Behavior-Gap). This engine is The Debrief only.
- **Run a different tenant's cadence**: Soundtrak-Debrief-specific. Other tenants get their own per-cadence skills (or a generic `/cadence --tenant <slug>` once enough tenants share a shape).

---

## Versioning + evolution

- **v0.1 (2026-07-08, this scaffold)**: orchestration-only draft; not installed. One edition + trailer per run; two-inputs-derive-the-rest; three helper scripts (resolve / populate / scrub). Built pre-launch so Editions #1-#3 can be banked *through* it.
- **v0.2 (post first banked edition)**: revise after Edition #1 (the flagship) is produced through the engine and reveals UX gaps; firm up the receipts-from-ledger pull; confirm the archive prepend shape against the real A12 article hub.
- **v1.0 (launch / ABN landed)**: drop the au-sender-id `[ABN pending]` placeholder once the operator supplies the legal name + ABN; the bulk-send hold lifts; wire the `deploy-cookbook` (or a Substack adapter if one exists by then).
- **v2 (multi-tenant)**: if a second tenant lands with the same "one-learning-per-week debrief" shape, extract a generic `/debrief-cadence --tenant <slug>` config-driven skill; this skill becomes a thin wrapper or is retired.

---

## Process learning captured (dogfood note)

> The engine *is* backlog L16 ("build the machine that publishes, not the one-off") applied to The Debrief itself. Producing the first three editions **through** this engine, before launch, is the proof the concept rests on: the newsletter about building an AI system is produced by the AI system. If we hand-wrote the buffer editions and only built the engine later, we would have skipped exactly the deliverable the campaign's sequencing (Plan §Wave 2) puts first.

---

## Cross-references

- **Producer agent**: `.claude/agents/producer/AGENT.md` - what this engine dispatches per surface.
- **Campaign Manager skill**: `.claude/skills/campaign-manager/SKILL.md` - orchestrator this engine uses.
- **content-subedit skill**: `.claude/skills/content-subedit/SKILL.md` - the voice gate (Soundtrak §2 precedence; near-zero em-dashes; run on every copy deliverable).
- **deploy-cookbook fallback**: `.claude/skills/deploy-cookbook/SKILL.md` - Substack + LinkedIn manual-publish steps (no coded adapter).
- **Sibling structural templates**: `.claude/skills/sb-podcast-weekly-assets/SKILL.md` (v1.2) + `campaigns/acme-workforce-report-2026/assets/21-cadence-skill/SKILL.md` (v0.1) - the cadence-skill pattern this scaffold follows.
- **A1 look kit**: `campaigns/soundtrak-ai-buildlog-2026q3/assets/01-look-kit/` (the LOCKED format this engine fills).
- **A14 editorial calendar**: `campaigns/soundtrak-ai-buildlog-2026q3/assets/14-editorial-calendar/` (the running order).
- **A0 editorial backlog**: `campaigns/soundtrak-ai-buildlog-2026q3/assets/00-editorial-backlog/` (the input queue + two-test bar).
- **Phase 6 cadence** (the runbook this engine operationalises): `campaigns/soundtrak-ai-buildlog-2026q3/phase-6-cadence.md` (authored at Phase-4; this skill is its entry point).
```
