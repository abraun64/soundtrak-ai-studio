---
name: library-add
description: Add a creative reference (URL, image+description, or internal asset path) to the operator's Best-Practice Library (creative exemplars) at tenant/library/entries/. Operator pastes URL in chat ("add this to my Best-Practice Library", "add to my marketing library", "add this to the library", "save this as a benchmark", "log this Cannes winner"). Skill fetches source, drafts entry with full facetable frontmatter (audience / vertical / shape / idea-or-tactic / source / etc.), proposes cross-links to existing entries, surfaces draft for operator edit, writes on approval, updates INDEX. Supports archive-sweep mode for sources like System1 Ad of the Week. Triggers include "add this to my best-practice library", "add to my marketing library", "add this to the library", "save this as gold-standard", "log this", "save this benchmark". (For a RESEARCH source — market data / behavioural science — the operator says "add this to my Insights Library" instead; that goes to tenant/research-library/ per docs/specs/research-library.md, a different schema — not this skill.)
---

# Library Add

You take a creative reference — URL, image+description, or internal asset path — and add it as a structured entry to the unified library at `tenant/library/entries/`.

## The single library

There is **one library** for all references — operator-curated exemplars, canonical work, Netwealth-research-sourced craft tactics, award-database sourced campaigns, all in one place. See `tenant/library/SCHEMA.md` for full schema; `tenant/library/INDEX.md` for the faceted table.

Provenance is captured via the **`source` frontmatter field** (Operator-curated · Inspiration-canon · Netwealth-research · System1 · Cannes / Effie / WARC / etc.) — not via folder location.

## What you do

### Step 1 — Identify the input

Operator's message contains one of:
- A **URL** (most common): Cannes Lions Archive, The Drum, System1, LinkedIn post, brand newsroom, YouTube case study, etc.
- An **image** they've attached or referenced + some context
- A **local path** to an internal asset (saving an approved tenant asset as a library entry)

If ambiguous, ask one clarifying question, then proceed.

### Step 2 — Gather source material

- **URL** → `WebFetch` the page. Pull title, publisher, date, byline, body content, hero image URL (record but don't download). For YouTube case-study videos, fetch description + comments where possible.
- **Image** → ask operator for source URL if any, plus the fields image alone can't give: brand, year, audience, big idea, why it's the bar.
- **Internal asset** → read the asset markdown + per-step brief + Brand verdict. Pull the strategic + creative + visual spine from the existing artifacts.

If `WebFetch` fails or returns thin content, ask operator for missing fields rather than guessing.

### Step 3 — Draft the entry

Build a full draft in memory with the complete frontmatter from `tenant/library/SCHEMA.md`. Fields to populate:

**Auto-extractable** (fill from fetched content):
- `name`, `brand`, `year`, `source_links`, `formats`, `industry`, `date_added`, `added_by`

**Infer with `[inferred]` tag** (auto-guess, flag for operator):
- `audience_type`, `vertical`, `shape`, `idea_or_tactic`, `journey_mode_primary`/`_secondary`, `posture_taken`, `brand_stretch`, `source`, `tags`

**Operator-judgment** (load-bearing fields — write best attempt + flag `TBD` if unsure):
- Strategic spine (audience insight, big idea, key message, product, channel)
- Creative move (the move, why-it-worked, when-to-steal, anti-patterns)
- Visual direction (hero description, palette, typography, photo/illustration style, composition, mood) — describe in prose using source content; mark `TBD — operator describe` if you can't see the visuals

### Step 4 — Set `source` correctly

The `source` field captures provenance. Use the controlled list from SCHEMA.md:

- **`Operator-curated`** — default for hand-picked URLs/screenshots the operator passes you
- **`Inspiration-canon`** — only for Wave 1.5 seed entries (rarely added new)
- **`Netwealth-research`** — only when source is one of the operator's Netwealth IQ Reports
- **`System1`** — when URL is from System1 Ad of the Week
- **`Cannes`** / **`Effie`** / **`WARC`** / **`Spikes-Asia`** / **`Dubai-Lynx`** / **`Webby`** — when URL is from an award-database

Per-publisher credibility extraction:
- **System1**: extract Star Rating + Spike Rating + Brand Fluency scores → `kpi_outcome` field
- **Cannes / Spikes / Dubai-Lynx / Effie**: extract award category + level (Grand Prix / Gold / Silver / Bronze / Finalist) → `award` field
- **WARC**: extract effectiveness rating + dataset insights → body's "Why it worked"
- **Contagious**: extract their strategic angle → body teach
- **Trade press** (Adweek / Ad Age / The Drum / Campaign): primary use is editorial context + agency credits

### Step 5 — Propose cross-links

Read `tenant/library/INDEX.md`. Identify 1-3 existing entries that share archetype, audience type, primary journey mode, vertical, or core move with the draft. List them in the draft's `## Related` section as `- [[<entry-slug>]] — <one-line rationale>`.

### Step 6 — Surface the draft for operator review

Show the full draft to the operator IN CHAT (don't write to disk yet). Markdown so they see exactly what'll get written. Flag every `[inferred]` and `TBD` explicitly so their eye lands on fields needing confirmation.

Ask: "Edit anything, then say `approve` to write — or send back with changes."

### Step 7 — Write on approval

When operator approves:

1. Determine filename: `<publisher-or-brand>-<slug>-<year>.md` (e.g. `cannes-heinz-draw-ketchup-2022.md`). Lowercase, hyphenated. Use operator's suggestion if they give one.
2. Write entry file to `tenant/library/entries/<filename>.md`.
3. Update `tenant/library/INDEX.md` — insert new row at the TOP of the table (sorted: operator-curated first, then by year DESC). Preserve the page header — the `# Best-Practice Library` title, the "How to add to the library" block, and the Insights-Library cross-link; only the Entries table changes. (If `INDEX.md` is ever missing — a fresh deployment ships a scaffold, so this is rare — recreate it with that same header + the Entries table columns before inserting.)
4. If reciprocal cross-links were approved: edit matched entries to add `## Related` lines pointing to the new entry.
5. Return short confirmation: `Added: <filename>. INDEX updated. <N> cross-links written.`

### Step 8 — Suggest next moves (optional, light)

After write, if the operator seems engaged:
- "Want to add another?"
- "Notice this is the 3rd <vertical> entry this month — anything in our pipeline that should pull this archetype?"

Light touch. Don't badger.

## Archive-sweep mode

When the operator pastes an archive URL (e.g. `https://system1group.com/ad-of-the-week`) instead of single-asset URL, AND optionally specifies a date range / count ("sweep the last 4 weeks" / "add the 10 most recent"):

1. Fetch the archive index. Extract list of featured items (brand / campaign / date / detail URL).
2. **Surface the queue to operator before ANY drafts.** Show: count, date range, list of brand + campaign names. Ask: "Process which of these? (all / pick by number / first N / skip)"
3. For each operator-confirmed item: fetch detail page → draft full entry → surface draft → operator approves/edits → write.
4. NEVER bulk-write entries without per-item approval — operator's edit pass is the curation step.
5. If operator wants to defer some items: write them to `tenant/library/queue/<source>-<date>.md` as a TODO list, NOT as draft entries.

## Failure modes to avoid

- **Don't invent facts**. If WebFetch returns thin content and you can't infer with confidence, mark `TBD` and ask operator.
- **Don't bypass the human gate**. Always surface draft for operator review before writing.
- **Don't download images**. Operator decision 2026-05-26 — text metadata + URL only. If image-cache value emerges later, this skill grows an opt-in `--cache-image` flag.
- **Don't auto-approve cross-links** to entries — operator confirms each one.

## Return envelope (after successful add)

Brief, in chat. No JSON wrapper needed.

```
Added: cannes-heinz-draw-ketchup-2022.md
INDEX: tenant/library/INDEX.md (row inserted at top)
Cross-links: 2 written
```

## Edge cases

- **URL behind paywall** → ask operator for paste of body content, or public mirror URL.
- **YouTube case study video** → fetch page description + transcripts where possible; else ask operator to summarise key narrative beats.
- **Image with no source URL** → operator-described entry. Skip `source_links` if truly none.
- **Operator pastes multiple URLs** → process one at a time, confirm each, prompt "next one?"
- **Duplicate** — entry already exists (same `name` + `year` in INDEX) → show operator the existing entry and ask whether to overwrite, append notes, or skip.
- **Style-only reference** (Kneebone-style image, no campaign) → set `shape: Visual-style-ref`, `idea_or_tactic: Style-ref`. Strategic spine fields become minimal — entry is visual-direction-focused.
