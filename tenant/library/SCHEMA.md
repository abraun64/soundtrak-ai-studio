# Library — Schema

The single reference library that **Creative Director** + **Producer** read for inspiration, exemplars, tactics, and visual references. Replaces the prior 3-library structure (inspiration / gold-standard / best-practices) with one faceted library that filters by content shape, not provenance.

## Why one library

A CD doesn't ask "is this an inspiration entry or a gold-standard entry?" — they ask "is this B2B? Is it a campaign or a playbook? Is it big-idea or tactic? Pro-services-relevant?" Filtering on **content facets** is what the CD actually does. Provenance becomes one column among many.

## Folder layout

```
tenant/library/
  SCHEMA.md                     ← this file
  INDEX.md                      ← unified faceted table (read first)
  entries/                      ← 74 entries (case studies + craft references)
    <publisher-or-brand>-<slug>-<year>.md
  playbooks/                    ← Netwealth-authored synthesis docs (different shape)
    winning-new-clients-playbook.md
    creating-loyalty-playbook.md
  archetypes/                   ← 9 journey-mode docs (the creative "job" an entry does — a classifier)
    aperture-setting.md
    attention-fame.md
    educational-pipeline.md
    trust-proof.md
    utility-service.md
    participatory.md
    direct-response.md
    community-advocacy.md
    identity-reinforcement.md
  visual-movements/             ← 8 aesthetic-register docs (an OPEN starter palette, not a closed set)
    clean-authoritative.md
    editorial-documentary.md
    editorial-cartoon-handdrawn.md
    maximalist-chaotic.md
    premium-luxury.md
    retro-nostalgic.md
    techno-futurist.md
    playful-vibrant.md
  WEB-SOURCES.md                ← Tier 2 allowlist for live WebFetch (when canon insufficient)
```

## Entry frontmatter — full field set

```yaml
---
name: <Campaign or asset name>
brand: <Brand or author>
year: <YYYY or YYYY-ongoing>
industry: <free-text description of category>
audience_type: B2C | B2B | Multi | Internal | N/A
vertical: <see controlled list below>
shape: <see controlled list below>
idea_or_tactic: Big-idea | Tactic | Hybrid | Style-ref
journey_mode_primary: Aperture-setting | Attention/fame | Educational pipeline | Trust/proof | Utility/service | Participatory | Direct-response | Community/advocacy | Identity reinforcement | Other/N-A
journey_mode_secondary: <same enum, or null>
posture_taken: Safe | Smart | Wild | N/A
brand_stretch: Low | Standard | High | N/A
formats: [hero film, OOH, social, AR, PR stunt, ...]
kpi_outcome: <one-line measured impact, or "not publicly disclosed">
big_idea: "<one sentence — the concept compressed>" (optional for tactic-shaped entries)
source: Operator-curated | Netwealth-research | System1 | Cannes | Effie | WARC | Inspiration-canon | Soundtrak-own
date_added: <YYYY-MM-DD> (for new entries — older inspiration-canon entries may omit)
added_by: <operator name> (for new entries)
tags: [free-form list]
source_links:
  - <url>
---
```

## Controlled lists

### Audience
- **B2C** — consumer-facing
- **B2B** — business-facing
- **Multi** — cross-audience campaigns
- **Internal** — employee comms
- **N/A** — style references where audience is irrelevant

### Vertical
- **Tech-SaaS** (B2B software, dev tools, AI platforms)
- **Tech-Consumer** (consumer tech, music, search)
- **Retail-DTC** (direct-to-consumer brands)
- **Retail** (mass retail, big-box)
- **CPG** (food, drinks, packaged goods)
- **QSR-Food** (quick-service restaurants, food delivery)
- **Travel-Hospitality**
- **Fintech-Banking** (consumer + B2B banking, fintech)
- **Wealth-Investment** (wealth management, asset mgmt, investment platforms)
- **Health-Wellness**
- **Apparel-Footwear**
- **Beauty**
- **Auto**
- **Entertainment-Media**
- **Industrial-B2B**
- **Insurance**
- **Telco**
- **Pro-services** (legal, accounting, consulting, agency)
- **Education-EdTech**
- **Toys-Kids**
- **Gambling-Sports**
- **Multi** (genuinely cross-vertical)

### Shape
- **Single-asset** — one ad, one post, one piece
- **Multi-step-campaign** — coordinated effort over time, finite duration
- **Always-on** — ongoing program, no start/end
- **Launch** — new product, brand, or category launch
- **Brand-refresh** — repositioning or major brand-level reset
- **Visual-style-ref** — pure aesthetic reference, no campaign context

### Idea-or-tactic
- **Big-idea** — a transferable creative concept worth stealing the move from
- **Tactic** — a portable mechanic / format / structural device
- **Hybrid** — both a big idea AND a transferable mechanic
- **Style-ref** — visual or copy style reference, not idea-led

### Journey-mode (the creative job the work does — a CLASSIFIER)
Every entry gets a **primary** mode (+ optional **secondary**). This is a real classifier the CD filters on (KPI → mode), so it aims to be **near-complete across the funnel**; use **Other/N-A** rather than force a bad tag. Each mode has a deep-dive in `archetypes/<mode>.md`.
- **Aperture-setting** — reset / reframe what the brand stands for (reposition)
- **Attention/fame** — earn broad, disproportionate attention (reach, earned media)
- **Educational pipeline** — teach / nurture toward consideration
- **Trust/proof** — make claims believable with evidence (data, case studies, demos)
- **Utility/service** — be genuinely useful (tools, calculators, data, service content)
- **Participatory** — invite the audience to act / co-create / engage
- **Direct-response** — drive an immediate specific action (convert)
- **Community/advocacy** — turn customers into a community + referral engine
- **Identity reinforcement** — deepen belonging / loyalty among the existing audience
- **Other/N-A** — nothing fits (escape hatch — prefer a real mode where honest)

### Visual movements (an OPEN reference palette — NOT a classifier)
Unlike journey-mode, visual movements are **not** a frontmatter facet and **not** a closed set. They're `visual-movements/*.md` reference registers the CD *pulls* when shaping §4 — a starter palette (currently 8), deliberately non-exhaustive because the space of aesthetics is effectively infinite. The CD names a new register when a concept needs one and adds it back via `/library-add`. Don't force a concept's visual direction to be one of the listed registers.

### Source
- **Operator-curated** — operator-spotted (URLs, screenshots, hand-picked)
- **Netwealth-research** — extracted from Netwealth IQ Reports (2024 wealth-management research)
- **System1** — System1 Ad of the Week archive
- **Cannes** / **Effie** / **WARC** / **Spikes-Asia** / **Dubai-Lynx** / **Effie** / **Webby** — award-database sourced
- **Inspiration-canon** — Wave 1.5 generalist seed (Apple, Nike, Slack, etc.)
- **Soundtrak-own** — the tenant's own published marketing, gold-standard exemplars

## Entry body structure

Tight. ~150-400 words. Frontmatter carries structured signal; body explains the *why* + *the move* + *when-to-steal*.

```markdown
## Strategic spine
(For campaign entries) audience insight / big idea / key message / product / channel mix

## Creative move
**What it did**: 1-2 sentences
**The move**: bullets — the portable structural elements
**Why it worked**: bullets — strategic + behavioural-science reasons
**When to steal**: bullets — brief signals that say "this applies here"
**Anti-patterns / risks**: bullets — what goes wrong when cloned badly

## Visual direction
(For entries with distinctive visual signature) hero description / palette / typography / photography-or-illustration style / composition / mood / source URL

## Related
- [[other-entry-slug]] — one-line rationale
```

## How agents use this library

### Creative Director (Workflow 1 — Concepts)

In Step 1 (Brief deconstruction) + Step 3 (Reference scan):

1. **Read `INDEX.md`** as the entry point.
2. **Filter mentally** by the columns relevant to the brief at hand:
   - **Tenant industry** → Vertical filter (single value or `vertical ∈ {wealth, pro-services}` for portable references)
   - **Brief KPI** → Journey-mode filter (Direct-response brief? Filter on that mode.)
   - **Brief shape** → Shape filter (launching? Filter on Launch + Brand-refresh)
   - **Stretch tolerance** → Posture filter (Wild brief? Don't surface only Safe references)
   - **Idea-vs-tactic need** → If brief calls for a Big Idea, filter `idea_or_tactic = Big-idea OR Hybrid`. If brief needs tactical scaffolding for a known idea, filter `Tactic`.
3. **Deep-read 3-7 most relevant entries.** Cite specific entries in concept §11 (References) as `[Library: <name>]`.
4. **Read the relevant `archetypes/<mode>.md`** for journey modes you're considering.
5. **Pull `visual-movements/<movement>.md`** when shaping §4 Visual architecture — these are an **open starter palette, not a closed set**; name a new register (and `/library-add` it) when a concept needs one.
6. **For prof-services tenants**: ALSO read the relevant `playbooks/*.md` section for tactical playbook content.

### Producer (per-asset craft)

When CM's Per-Step Brief names a gold-standard reference, Producer reads that entry directly. Producer may filter the library for adjacent entries when struggling — same column logic.

### `/library-add` (skill)

Writes new entries to `entries/` with full frontmatter populated (asks operator for any inferable values it can't auto-extract). Adds to INDEX.

## Anti-clone discipline

Same as before. **Steal the move, not the surface.** A concept that's a recognisable clone of a library entry fails the smell test — re-roll.

## Provenance preservation

The old three-library structure is preserved as a `source` value on every entry:
- `Inspiration-canon` = the 46 generalist seed entries from Wave 1.5
- `Operator-curated` = URLs/screenshots the operator has personally added
- `Netwealth-research` = extracted from the operator's Netwealth IQ Reports
- `System1` = System1 Ad of the Week archive
- `Soundtrak-own` = the tenant's own published marketing, gold-standard exemplars (The Signal + soundtrakconsulting.com/thinking)
- etc.

Filter on `source` if you need to surface a specific provenance subset (rarely needed — content-shape filters do the real work).

## Version

v1.0 — 2026-05-26 unified refactor. Replaced prior 3-library structure (`tenant/inspiration/` + `tenant-brand/gold-standard/` + `tenant-brand/best-practices-professional-services/`). All content preserved.
