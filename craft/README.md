# `craft/` — Universal craft context layers

**Purpose**: tenant-agnostic, universal craft knowledge that every specialist agent reads as reference material. Mirrors the `tenant/` pattern but holds craft principles that don't change by tenant.

## What lives here vs `tenant/`

| `craft/` (this directory) | `tenant/` |
|---|---|
| Universal craft principles (hook discipline, composition rules, motion principles, accessibility specs) | Tenant-specific voice, positioning, brand architecture, gold-standard work |
| Format-tagged rules (LinkedIn post norms, email deliverability, video timing) | Tenant overrides where the brand intentionally diverges from universal rules |
| Universal AI-tells (Layer 1 of the sub-edit pipeline) | Tenant voice rules (Layer 2 of the sub-edit pipeline) |
| Reference tables, taxonomies, patterns | Brand-specific examples, archetypes, exemplars |
| Read-only reference; agents pull sections on demand | Read-only reference; agents pull on demand; can be overridden by tenant |

## Tenant override pattern

Agents read `craft/<file>.md` first for universal craft. If `tenant/brand/craft-overrides.md` exists, agents layer the tenant's overrides on top. Tenant overrides are **opinionated divergences from universal craft**, not replacements — they should be narrow, specific, and reasoned (e.g. "our brand uses 'unlock' deliberately as a positioning term; allow it despite the universal banned-phrase rule").

## File index

| File | Holds | Read by |
|---|---|---|
| [copywriting.md](copywriting.md) | Universal AI-tells (Layer 1), hook discipline, sentence rhythm rules, restatement detection, banned phrases, strictness-by-form table, prose principles | All 5 Copywriters + Social/Community Manager + Creative Director (where it touches copy) |
| [sub-edit-pipeline.md](sub-edit-pipeline.md) | The three-layer sub-edit procedure (scan → fix → re-scan → refuse-after-3), Layer 3 overlay catalogue, §7 Sub-edit report structure | Every agent that produces written or scripted output |
| [platform-native-social.md](platform-native-social.md) | Per-platform rules (LinkedIn / X / Instagram / TikTok / Facebook / Threads / Reddit / Hacker News / YouTube Shorts), hashtag taxonomy, accessibility, disclosure mandatories, community-response classification | Social/Community Manager + Copywriter–Short-form (paid social) |
| [channel-grammar.md](channel-grammar.md) | Per-channel reference (aspect ratios, glance times, sound defaults, motion defaults, dwell time) — billboard / transit / TV / IG / TikTok / YouTube / LinkedIn / web / email / podcast / packaging | Creative Director + all Copywriters + Social Mgr + Static Designer + Motion Designer |
| [asset-architecture-patterns.md](asset-architecture-patterns.md) | Email sequence defaults, thread shapes, carousel shapes, content calendar ratios, repurposing matrices, landing page anatomy, long-form structures, presentation arcs | Copywriter–Email + Copywriter–Web + Copywriter–Long-form + Copywriter–Presentation + Social/Community Manager |
| [visual-craft-shared.md](visual-craft-shared.md) | Universal visual principles — brand fidelity, hierarchy, contrast, accessibility (WCAG AA), asset specs reference, brand-token discipline | Creative Director + Static Designer + Motion Designer |
| [static-design.md](static-design.md) | Composition, typography-as-visual, grid systems, color in static design, format-tagged sections (tile / carousel / display / billboard / web hero / email / slide / poster / infographic), variant generation across formats | Static Designer + Creative Director (visual concept) |
| [motion-design.md](motion-design.md) | Storyboarding, beat timing, motion principles, transitions, sound design, format-tagged sections (short-form video / long-form video / GIF / motion graphics / animated banner / animated logo) | Motion Designer + Creative Director (brand-film concept) + Copywriter–Presentation (slide transitions only — light) |

## How agents reference `craft/`

Agents do NOT load the entire `craft/` directory on every invocation. They pull **named sections** of specific files when they hit a relevant craft decision. Example flows:

- Copywriter–Email starting a sequence draft → reads `craft/copywriting.md#hook-discipline` + `craft/copywriting.md#strictness-by-form` (email row) + `craft/asset-architecture-patterns.md#email-sequences` + `craft/sub-edit-pipeline.md#layer-3-email`
- Social Mgr drafting a LinkedIn carousel → reads `craft/platform-native-social.md#linkedin` + `craft/platform-native-social.md#carousel-architecture` + `craft/asset-architecture-patterns.md#carousels` + `craft/static-design.md#carousel` (visual brief section)
- Motion Designer producing a TikTok cut-down from a Presentation script → reads `craft/motion-design.md#short-form-video` + `craft/channel-grammar.md#tiktok` + `craft/visual-craft-shared.md#brand-fidelity`

Each file has a ToC at the top with anchor-style section names. Agents reference by section name in their workflows.

## Maintenance discipline

- **Source of truth**: this is the canonical home for universal craft rules. If a rule lives both in `craft/` and in an AGENT.md, `craft/` wins; the AGENT.md should be updated to read from `craft/` instead of duplicating.
- **Updates propagate**: improving a rule in `craft/` improves every agent that pulls from it on next invocation. No multi-agent sync sweep needed.
- **Tenant-agnostic**: never name a specific brand, operator, or vertical in a `craft/` file. Examples should be generic ("a B2B SaaS launch" not "Soundtrak's launch"). Tenant-specific guidance belongs in `tenant/`.
- **Reference-shaped, not narrative**: tables, bullet lists, taxonomies. If a `craft/` file reads like an essay, restructure it for lookup.
