# Per-Step Brief — Phase 4a Schema

The **Per-Step Brief** is the self-contained context package CM writes to a specialist (almost always Producer) at the moment of dispatch for each asset in the Plan.

**No operator approval** at this layer. CM owns it. CM is the librarian: it curates exactly the context this asset needs and nothing more.

**Length target: 1 page.** Self-contained — the Producer should not need to load other tenant files. Everything the Producer needs to do the work is in this brief.

**Stored**: ephemeral by default — written inline as Producer's invocation prompt. Optionally mirrored to `campaigns/<slug>/assets/<asset-slug>/brief.md` if the asset is high-stakes / multi-cycle / worth keeping as audit trail.

---

## Schema

```markdown
# Per-Step Brief — <Asset name>

**Plan ref**: Asset #<n> from `plan.md`     **Form**: <e.g. HTML/CSS landing page (Mode C)>     **Target publish**: <date>     **Producer fast-lane**: yes / no
**Review shape**: `output` / `template [+N exemplars]` / `variant-comp [N variants × M sizes]`
**Copy file**: `md` / `csv` / `pptx` / `docx` / `none`

## 1. The task
One paragraph: what to produce, what form, what destination, what success looks like for THIS asset specifically.

## 2. Strategy slice (from Brief + Concept)
Pull only what this asset needs. Typically:
- Audience for this asset (may be a subset of the campaign audience)
- Key message for this asset (the one specific thing this asset should land)
- Why this asset exists in the sequence (what came before, what comes after)
- **Tenant playbook slice** (tenants with prior campaigns): 1–3 most-relevant tactical learnings from `tenant-brand/<tenant>-playbook.md`, quoted verbatim with evidence tag (FINDING / HYPOTHESIS) + `Playbook §N` citation. Omit entirely for first-campaign tenants. See [`tenant-playbook.md`](tenant-playbook.md).

## 3. Voice slice (from the tenant Brand Context)
The voice rules that apply to THIS asset. CM is the librarian — pulls the relevant slices from the tenant Brand Context and cites inline:
- Tonal calibration (Direct/Provocative/Concise/Casual/Expert positions) — from tenant Brand Context §2
- 5–8 most-relevant voice principles — from tenant Brand Context §2 (voice) and, where the tenant's positioning bears on tone, tenant playbook §0. Producer reads only the slice; does not load source files.
- Avoid-list applicable to this form — banned words from tenant Brand Context §2 + any tenant-specific additions
- 1 gold-standard reference link (closest published sibling) — from tenant Brand Context §5

Voice is tenant-specific: every tenant's voice/visual/positioning comes from its own Brand Context (built at Phase 0), not from any cross-tenant source.

## 4. Visual identity slice (from Brand Context)
Only if the asset has a visual component:
- Palette hex codes
- Typography (display + body)
- Aspect ratio + canvas
- Composition rules applicable to this form (signature placement, accent rules, etc.)
- Visual register reference link (closest published sibling)
- **Canva brand kit ID**: <id> — if Mode B is the recommended production path
- **Suggested production mode**: A (Replicate) / B (Canva MCP) / C (HTML/CSS) — CM's recommendation; Producer can override with reasoning

## 5. Mandatories
HARD rules for this asset — what must be present, what must be absent. Pulled from Brief §Mandatories + Concept §risks + Plan §Fast-lane.

## 5b. Knowledge-gap classification (post-Retro-001 — required field)

For each operator-action embedded in this asset, classify:
- **Marketing decision the operator owns** → frame the choice; trust the call; no cookbook needed
- **Technical execution the operator may not know** → cookbook required; name the cookbook path Producer must bundle into the asset

Default audience for cookbooks: B2B-marketer baseline (knows UTM / pixel / event listener; doesn't know click-by-click of GA/GTM/Posthog/etc.). See [`docs/specs/cookbook.md`](cookbook.md) for the cookbook artifact schema.

## 5c. Ship-complete checklist (post-Retro-001 — required field)

List what Producer MUST bundle into this asset for it to be operator-shippable without handoffs:
- Copy (verbatim, ready to publish)
- **Gallery-surface data (MANDATORY — populates the lightbox)**: `asset.yaml` carries `asset_id` + `asset_name` (= the Plan row's name, VERBATIM) + `default_channel` (= the Plan row's `Channel`, VERBATIM — one of THIS campaign's valid channels; never invented, since an off-list channel silently drops the asset) + `rationale` (the "What this is"), a per-file `title:` on every `ship: true` file, and a **copy-review surface** — a top-level `copy_file:` (a `copy.md` or the primary prose `.md`; HTML-only assets ship a text extract as `copy.md`). Every asset must trace to its Plan `#` row — **the Plan is the source of truth for the asset catalog** (`#` · name · type · channel · ships · copy-file); `asset.yaml` derives from it and `check-state` enforces the match. See [`asset.md`](asset.md) §Gallery-surface data contract.
- Visual(s) (downloadable file OR pastable image prompt the operator can run themselves)
- Setup cookbook(s) (e.g. GA event wiring, schema markup, form embeds, OG cards — one cookbook per technical-execution step)
- Deploy cookbook (how the operator gets it live — CMS publish steps, file uploads, link insertion)
- Verify cookbook (how the operator confirms it's working — what to look at, what success looks like)

No technical handoffs as separate Pre-flight items unless they're cross-asset. If a setup step is cross-asset (e.g. one GA event-spec covers 5 different assets), the cookbook lives at the Plan's Pre-flight level and gets cross-linked from each asset that depends on it.

## 6. KPIs for this asset
What this specific asset is trying to move:
- Primary metric + target (e.g. "engagement ≥6%")
- Secondary metric + target if any
- Note which Brief KPI it ladders up to

## 7. Open questions / dependencies
Anything Producer should flag if it changes the work:
- Dependencies on prior assets (sequence-based)
- Pending operator decisions (e.g. founder sign-off on a framing)
- Open creative questions (e.g. Mode A/B choice for Producer to call)

## 8. Output expected
Concrete:
- File paths for finished asset(s) — markdown + visual file + HTML preview (CM renders preview from markdown after Producer returns)
- Self-QA verdict required (3-layer copy + 3-layer visual where applicable)
- **In-situ operator preview** — REQUIRED for social media + email + any feed/inbox asset (see §9 below)
- Status to return: ready-for-Brand / blocked / needs-rescope

## 9. In-situ operator preview (REQUIRED for social + email + feed/inbox forms)

For any asset that will live inside a feed, inbox, or scroll-state context, the operator-review surface MUST show the asset **as the reader will encounter it**, not as a bare file. This means two states for any post-style asset:

1. **Collapsed view** — feed-truncated state. For LinkedIn: ~140 char preview + "see more" cutoff + tile thumbnail at feed scale. For Twitter: 280-char card. For Instagram: caption truncated + image carousel preview. For email: subject line + preview text + sender + inbox-preview snippet.
2. **Expanded view** — clicked / opened state. Full post copy + tile at native scale + comment/reaction affordances rendered as visual context (don't have to be functional). For email: full open state.

**Why required**: a LinkedIn post reviewed as "copy + separate tile file" is reviewed in isolation from how the reader actually experiences it. The collapsed view tells the operator whether the first 140 characters earn the click. The expanded view tells them whether the full read delivers. Without both, the operator approves a thing that may render badly in-feed.

**Per form, default in-situ contexts**:

| Form | Collapsed mockup | Expanded mockup |
|---|---|---|
| LinkedIn organic post | Feed card with author + ~140 char teaser + "see more" + 1:1 or 1.91:1 tile thumbnail | Full post copy + native-scale tile + reaction bar + 3 dummy comments |
| LinkedIn paid (sponsored) | Sponsored feed card with "Promoted" tag + headline + tile + CTA button | Full ad card + landing-page-link preview card |
| Twitter / X | Card with author + 280-char + tile thumbnail | Thread expanded if applicable |
| Instagram feed post | Square crop preview in 3-col grid context | Expanded post with caption fully visible |
| Instagram carousel | First-slide preview + dot indicators | Each slide rendered + caption |
| TikTok / Reels short | Vertical card + caption truncated + audio icon | Full vertical with caption expanded |
| Email | Inbox row: sender + subject + preview text + date | Full opened email with header + body + footer |
| Substack issue (web) | Discover-card / share-preview state | Full article with hero |

**Rendering responsibility**: CM's `render-html` skill produces both mockup states from the asset markdown + asset visual file via the `asset-preview` template with `extra_context` form param. Producer returns the asset markdown + visual; CM renders the in-situ. If `render-html` doesn't yet support a given form's mockup, CM falls back to side-by-side raw display + a flag in the surface message so the operator knows to imagine in-context, but logs the gap to the render-html backlog.

**Exceptions** (no in-situ required): visual primitives (stamps, logos, brand kit pieces — Asset #1 in this campaign was an example); internal-only docs (retros, scope-and-plan notes); landing pages (the page IS the in-situ — full-page render is the preview).
```

---

## CM authoring discipline

- **Self-contained.** Producer reads ONLY this brief + its own craft lenses. Producer does not load tenant brand files.
- **Slice, don't paste.** Voice slice = the 5–8 rules that apply; not the whole brand guide. Same for visual identity.
- **Graduate-then-cite (three-layer rule).** Slices come ONLY from the tenant layer (Brand Context, tenant playbook, `tenant/library/`), the system layer (specs, craft), and THIS campaign's own artifacts. NEVER from a sibling campaign's folder. If a previous campaign's element is wanted, it graduates to the tenant layer first, then gets cited. See [`docs/workflow.md`](../workflow.md) §The three layers.
- **Pull, don't repeat.** Reference Brief §X / Concept §Y / Plan #Z where the source is — don't duplicate the full content.
- **Form-fit.** A LinkedIn post brief and a whitepaper brief have different shapes. §3 (voice) for a LinkedIn post calls out the platform-native rhythm; for a whitepaper it calls out long-form discipline. CM tailors.
- **Mode dispatch is CM's recommendation, Producer's call.** CM suggests Mode A/B/C based on what the asset needs (text-led → Mode B Canva; photo-led → Mode A Replicate; markup → Mode C). Producer can override with reasoning in its return envelope.
- **Avoid the "include everything just in case" trap.** If Producer needs more, it asks. The brief is a contract for THIS asset; more context = more noise.

## When to write a saved mirror

Most briefs are ephemeral (live in the Producer invocation prompt). Save to disk when:
- Asset is high-stakes / paid budget / hero piece
- Asset is multi-cycle (likely to iterate via Brand verdicts)
- Audit trail matters (e.g. retrospective analysis post-campaign)

For routine recurring assets (weekly Tuesday companion post #4), save the FIRST one as a template, then briefs 2–N reference it.
