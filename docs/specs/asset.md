# Asset — Phase 4b Schema

The **Asset** is the finished deliverable — copy + visuals + structural elements bundled. Producer authors it from the Per-Step Brief; Brand Manager reviews behind the scenes; CM renders the operator-facing HTML preview; operator approves the finished thing.

**Length target: as long as the asset itself.** Asset bodies aren't compressed; they ARE the deliverable.

**Stored**:
- Markdown (authoritative): `campaigns/<slug>/assets/<asset-slug>/<asset-slug>.md`
- Visual binary (if applicable): `campaigns/<slug>/assets/<asset-slug>/<asset-slug>.png` (or .mp4 / .pdf / etc.)
- HTML preview (operator-facing): `campaigns/<slug>/assets/<asset-slug>/<asset-slug>.html` — rendered by `render-html` skill using the asset-preview template, which mocks up the in-context view (LinkedIn-post mockup, inbox preview, page render, etc.)

---

## Markdown body — required sections

> **Status is single-sourced — MANDATORY (2026-06-19).** The record's status line MUST be the bare `<!-- STATUS_AUTO -->` marker **alone** (no `**Status**:` prefix — render.py replaces the marker with the full `**Status**: X` line) — **never a hand-typed status**. render.py injects the status from `asset.yaml` at render time, so `asset.yaml` is the *one* source of truth and the record cannot drift from it. Change status **only** via the status-propagator (`status-propagator/propagate.py`), which updates `asset.yaml`. Hand-typing a status here creates a second copy that drifts the moment `asset.yaml` changes without it — the recurring status-drift bug class (root-caused on ACME CO 2026-06-19: 22 records hand-authored status, asset 02 went Approved in yaml but the hand-typed record stayed "Awaiting"). `check-state` treats any record containing the marker as yaml-derived and drift-proof. Trailing provenance (Built / Owner / Mode / notes) goes on its own line *below* the marker, not appended to the status.

```markdown
# <Asset name>

**Form**: <e.g. LinkedIn organic post + 16:9 tile>
<!-- STATUS_AUTO -->   <!-- the status line = this bare marker (no "**Status**:" prefix). Single source = asset.yaml (values: Draft / In Production / For Human Review / Approved / Archived); never hand-type a status (drift). Change via status-propagator. -->
<!-- COMPLIANCE_AUTO -->   <!-- Governance verdict (Phase-4); a status-line, stays at the top. Strips to nothing unless asset.yaml has a `compliance:` block. Safe to pre-seed (NO-RETROFIT no-op). -->
**Plan ref**: Asset #<n>
**Target publish**: <date>     **Approved**: <date>     **Published**: <date>
**Asset ID**: AST-<n>

## 0a. Operator-action right-panel (NEW 2026-06-04 — UI architecture)

The asset-preview rendering (asset.md → asset.html via `render-html` skill) AND the gallery lightbox now surface the operator-action sections as a **right-hand sidebar panel**, NOT inline in the asset body.

**Rule**: H2 sections with operator-action keywords (`operator` / `open question` / `next step` / `decision`) get extracted by `render-html/render.py extract_operator_panels()` and rendered into the `{{ operator_panels }}` template slot as a sticky right-column aside (`.asset-preview-layout__aside`). The body content (the deliverable) takes the main column; the operator gates + workflow live in the sidebar.

**Why**: operator caught this 2026-06-04 — *"any questions and next steps go in the right hand panel, not the asset area"*. Inline operator-action sections pad the asset body with metadata that's not part of the deliverable. The reviewer should see the asset content in the main column and the gates/workflow in a peripheral panel that scrolls with them.

**Sections that get extracted** (must follow these exact patterns to be detected):
- `## Open questions for operator (gate)` → orange panel with question count badge
- `## What the operator does next` → green panel with workflow steps
- Producer can vary phrasing slightly as long as the keyword (operator / question / next / decision) appears in the H2

**Sections that stay inline** (excluded by keyword): `## Flags for Brand Manager` / `## Self-QA` / `## Brand verdict` — internal Brand discipline, not operator-facing.

**Mobile**: at ≤1100px the right-panel collapses to stack below the body (single column).

## 0. Deliverable-first asset record (NEW 2026-06-04)

**The asset.md MUST lead with the deliverable, not the rationale.** When the operator opens asset.md (or asset.html via the gallery), they're reviewing the ASSET — the actual emails / slides / page copy / etc. — not the production notes. The structure of every asset.md follows this order:

1. **Top**: header (status, form, cadence, plan ref) + one-line "Reviewing this asset?" pointer
2. **The asset itself** (inline, copy-paste-ready): rendered exactly as it will ship. For multi-piece assets (email sequences, slide decks), each piece in shipping order with subjects / body / signature / personalisation tokens visible.
3. **Open questions for operator (gate)**: numbered list of operator-facing decisions Producer needs at the approval gate (gallery extracts this section per the GALLERY-PARSED comment in §6 below)
4. **What the operator does next**: numbered list of operator actions on approval (gallery extracts this per §7)
5. **Collapsed `<details markdown="1">` block** at bottom containing: rationale, voice + register choices, subject-line strategy, sequence/structural overview, self-QA pass, flags for Brand, relationship to other assets, source files (legacy)

**Why**: operator caught this 2026-06-04 reviewing Asset #18 cold outreach. Producer's asset.md led with §1 Sequence overview → §2 Voice + register choices → §3 Subject-line strategy → ... and the actual email content lived in separate `email-N-*.md` files. Result: operator opens asset.html, reads strategy/rationale, can't find the deliverable. Reviewing experience = backwards.

**Producer contract**: every Producer ship-complete return MUST structure asset.md deliverable-first. The rationale section is REQUIRED but BELOW the deliverable, in a collapsed `<details>` block.

**Exceptions**: cookbooks (where the operator IS reading the instructions, not the rendered output) and asset records for assets whose deliverable IS a separate file (like index.html for landing pages where asset.md's job is to wrap + annotate). For those, asset.md naturally leads with the wrapper/annotation; the deliverable is linked + summarised at top, full content lives in the index.html.

## 1. Final asset — ship-complete bundle (post-Retro-001)

An asset is NOT just the copy + visual. It's everything the operator needs to ship it. The complete bundle:

### Copy
<verbatim copy as it will publish — char count noted if platform-relevant>

### Visual(s)
- **File**: `<asset-slug>.png` (or .mp4 / .pdf / etc. — relative path). Downloadable; operator can use directly.
- **Image prompt** (alternative — if visual is AI-generated and operator may want to re-roll): the pastable prompt the operator can drop into Replicate / Canva / Midjourney themselves.
- **Alt text**: <accessibility-compliant description>
- **Production mode**: Mode A (Replicate) / Mode B (Canva MCP) / Mode C (HTML/CSS)
- **Canva design URL** (if Mode B): <link to design in Canva workspace for operator edits>
- **Replicate generation ID** (if Mode A): <prediction ID for audit trail>

### Structural elements (form-dependent)
For presentations: per-slide briefs (storyboard) — copy + visual brief per slide
For long-form: section structure + heading map
For sequences: per-message structure + cadence
For ads: variant set + paired tiles

### HTML web page folder structure standard (v2, 2026-06-05)

Any asset whose deliverable is an HTML web page (landing page, pricing page, article, case study) MUST follow this folder structure so the deployment package is clean and self-contained:

```
assets/<asset-slug>/
├── index.html              ← the page (root-level, deploy this folder)
├── images/                 ← ALL images referenced by the page
│   ├── hero.png
│   ├── screenshot-1.png
│   └── ...
├── cookbooks/
│   ├── deploy.md           ← step-by-step deployment instructions
│   └── verify.md           ← post-deploy checklist
├── copy.md                 ← editable copy companion
├── asset.yaml              ← gallery metadata (NOT deployed)
└── preview.md              ← asset record (NOT deployed)
```

**Rules:**
- `index.html` MUST be at the root of the deliverable folder — not in a subfolder
- All images MUST be in `images/` — not `screenshots-cropped/`, not `assets/`, not inline base64 unless there's a specific reason
- Images MUST be referenced as `images/filename.png` (relative, root-relative) — not absolute paths
- `asset.yaml`, `preview.md`, `copy.md` live alongside `index.html` but are NOT deployed — they are campaign management files
- `view_source:` in asset.yaml MUST point to `index.html` if the gallery tile is a different file
- Gallery "Open folder" resolves to the folder containing `index.html` — that folder IS the deployment package

**Why `images/` not `screenshots-cropped/`:** Standard web server convention. `images/` maps cleanly to CDN, CMS media libraries, and static hosting conventions. Descriptive subfolder names are internal-only.

**For Netlify:** drag-and-drop the entire folder (containing `index.html` + `images/`) → done.
**For CMS:** upload images to the media library first → get absolute URLs → update `index.html` references → paste content into CMS page builder.

Per `feedback_html_web_page_folder_structure.md`.

### Editable copy file — REQUIRED for any web / landing-page / long-form text asset

Bundled file: `copy.md` sibling to `asset.md`. It is the **operator's edit surface** — the bare minimum to read and edit the copy, nothing else. The operator opens it, edits prose directly, saves; the Producer treats it as the authoritative copy source and mirrors edits into `index.html` on the next pass (if `copy.md` and `index.html` diverge, `copy.md` wins).

**The whole file is four things, in this order. Nothing above the copy but a one-line orientation; nothing below but an optional preview link:**

1. **One-line header** — `# Asset #N — <what it is> — Editable copy`, then ONE line: where it goes (channel / live URL) + "Edit below; the Producer mirrors your edits into the asset."
2. **Constraints that bind the copy only** (≤4 bullets) — voice rules in one line; per-field character limits; any hard rule that changes the copy (e.g. keep the UTM string intact). Nothing else.
3. **The copy**, as plainly-labelled editable fields (`**<Field>**: <copy>`), one per editable region. Verbatim external artifacts marked `[VERBATIM — do not edit; <source>]` (edits there revert on the next pass).
4. **(optional) one** `↳ Preview in situ: <link>` line.

**BANNED from copy.md** — this is the operator's edit surface, not the production record. Keep ALL of the following OUT: the strategic thesis / rationale · the "Current state" or version-history changelog · per-section design or production annotations (`[v2.x: the radial auto-cycles…]`) · Brand-verdict commentary · production / deployment notes (timing, tile render specs, ESP setup). **Every one of those lives in `asset.md`** (the asset record + its audit-history section), never here. Structural changes (add/remove a section) go through chat with CM, not in-file.

**Field sets by asset type** — same skeleton; only the fields differ (social vs web is *not materially* different — just shorter fields with character caps):

| Asset type | Editable fields |
|---|---|
| Social tile | Headline · Body · Hashtags · Image alt |
| X / OG share card | Title (≤70 chars) · Description (≤200 chars) · Image alt |
| Email (single / sequence) | Subject · Preheader · Body · CTA (per email) |
| Web / landing / long-form | One labelled block per `§N — <name>` page section (Eyebrow / H1 / Sub-head / Body / Caption / CTA) |

Social / card / email fields carry inline **character limits**; everything else is identical.

**Applies to**: landing pages · long-form articles · whitepaper sections · pricing/About pages · email single + sequences · social tiles · OG/share cards. **Does NOT apply to**: ad headline batches, social-post single bodies <500 chars, microcopy, taglines (operator edits in chat).

**Copy-review contract (v3, 2026-07-03) — MANDATORY.** Every asset that carries ANY copy MUST expose a copy-review surface the gallery can attach as the View + Source edit action. Declare it explicitly via top-level `copy_file:` (the `copy.md`, or the asset's primary prose `.md` — `about.md`, `edition-01.md`, `reveal-post.md`, etc.). **HTML-only assets ship a plain-text extract as `copy.md`** so the reviewer can read + edit the copy without opening the rendered page. The builder auto-falls-back (ship:true `.md` → Plan `Copy file` → largest non-record prose `.md`) and prints a **WARNING** when a copy-bearing asset resolves NO copy surface — that warning is a contract breach, not noise. `copy_file: none` is honoured only for genuinely copy-free visual primitives (a bare logo/stamp); anything with words attaches a copy surface.

### Setup cookbook(s) — REQUIRED for any asset with technical setup
Bundled into the asset, not as a separate Pre-flight item (unless cross-asset). Examples:
- Web page asset → GA event-wiring cookbook + schema.org markup cookbook + OG cards cookbook
- Email asset → ESP setup cookbook (segment, send-time, template-load) + suppression-list cookbook
- Social post asset → posting cookbook (timing rules + tag mechanic + first-2-hours engagement window)
- Lead-magnet asset → gating cookbook (form embed, ESP integration, post-download nurture trigger)

Each cookbook follows the [cookbook spec](cookbook.md) — assumes B2B-marketer baseline, ends with verification step.

### Deploy cookbook — REQUIRED
How the operator gets it live. CMS publish steps; file uploads; link insertion; commit/push if code. Step-by-step.

### Verify cookbook — REQUIRED
How the operator confirms it's working. Names exact places to look and what success looks like (e.g. "Open GA4 Realtime, click the button, see event fire within 30 seconds").

**Ship-complete contract**: the operator opens the asset, reads from top to bottom, and ends with a deployed working thing. No "go figure out the technical setup" handoffs.

### Portable pack — REQUIRED for any NON-WEBSITE asset (SYS-105)

**HTML is the authoring/preview format, not the delivery format.** UNLESS an asset is a genuine website page (deployed AS HTML to Netlify / a CMS-as-HTML), the destination — Substack, Mailchimp, LinkedIn native, most CMS rich-text editors — does **not** accept arbitrary HTML/CSS. Right-click "save image" only works on true `<img>`/SVG; it CANNOT capture an HTML/CSS-composed graphic block (a masthead built from `<div>`s, an evidence card of SVG + `<div>`s) — exactly where the brand design lives. So each such block must be **rendered to a standalone PNG**, or the design is lost on paste.

Every non-website asset therefore ships a **portable pack**: the clean copy (already `copy.md`, pasted as the body) **plus a PNG of every embeddable composed visual block**. Declare it with a top-level `portable:` manifest in `asset.yaml` — the shared exporter `.claude/lib/export_portable_assets.py` (the INVERSE of render-html: HTML → copy + PNGs) reads it, renders `source_html` in headless chromium with brand fonts pinned, and screenshots each block at 2× into a `portable/` subfolder:

```yaml
portable:
  source_html: issue-header.html     # the HTML whose blocks are exported
  copy: copy.md                      # the paste-ready body (pointer)
  fonts: soundtrak                    # optional tenant font set (pins brand fonts)
  images:
    - name: masthead
      selector: "header.masthead"    # CSS selector of the composed block
      where: "Substack post header image"   # WHERE it goes on upload
      platform: Substack
    - name: evidence
      selector: ".art-evidence"
      where: "embed inline after the intro"
      platform: Substack
```

Run: `python .claude/lib/export_portable_assets.py --asset <asset_dir>`. The pack is **production output** (`ship: false` — NOT extra gallery tiles; one tile per asset stays). It surfaces in the asset's gallery **lightbox** as an "📦 Upload pack — what ships & where" section (rendered from the `portable:` manifest), so the operator opens the tile and sees exactly what to upload and where. First cut covers Substack + Mailchimp + the article/email/social forms; extend to CMS as adapters land.

### Single-source render for cadenced newsletter headers (SYS-094, forward-only)

The stale-mirror class (2026-07-09): an edition's body lived verbatim in BOTH `edition.md` AND the hand-authored `issue-header.html`, so a rework of one silently left the other stale. The fix is to stop hand-copying — `issue-header.html` becomes a **build artifact derived from one source**:

- `edition.md` — the article body (THE single source for the prose)
- `header.yaml` — the per-edition data (kicker · headline · standfirst · evidence values · hero)
- a **slotted look-kit template** (`{{SLOT}}` placeholders — the constant chrome)

`python .claude/lib/render_issue_header.py --asset <asset_dir>` renders them into `issue-header.html` (body from `edition.md` markdown, with light conventions: first para after the first `##` → `.lede`, a `> ` blockquote → `.pull`, an `<!-- HERO -->` marker → the hero `<figure>` from `header.yaml`). The output carries a **provenance stamp** — content hashes of its sources — so a content-based staleness check can supersede the mtime heuristic (`_copy_stale_vs_render`). Because the body is rendered, not mirrored, `issue-header.html` can no longer drift from `edition.md`.

**FORWARD-ONLY.** This is the authoring path for **NEW editions (The Debrief #5 onward)**. Editions **#1–#4 are approved + frozen** and are NOT regenerated (their headers are hand-authored, signed off). To adopt at #5: derive the slotted template once from the latest approved edition's `issue-header.html` (replace its per-edition values with `{{SLOT}}`s so it reproduces the approved chrome), then author each new edition as `edition.md` + `header.yaml` and render. Remaining tail: wire `build-gallery`'s staleness check to read the provenance stamp (content-hash) instead of mtime.

## 2. Sub-edit verdicts (Producer self-QA)

- **Copy 3-layer**: Pass / Pass-with-fixes / Fail
  - L1 AI-tells: <pass/fail + 1-line notes>
  - L2 Brand voice: <pass/fail + 1-line notes>
  - L3 Form-native (platform / SEO / deliverability / etc.): <pass/fail + 1-line notes>
- **Visual 3-layer** (where applicable): Pass / Pass-with-fixes / Fail
  - L1 Brand fidelity: <pass/fail>
  - L2 Composition + accessibility: <pass/fail>
  - L3 Visual AI-tells (Mode A) / Brand-kit fidelity (Mode B) / Markup fidelity (Mode C): <pass/fail>

## 3. Brand Manager verdict

- **Verdict**: Pass / Pass-with-Required-Changes / Pass-with-Notes / Fail
- **Findings**: <severity-rated list — H/M/L>
- **Fixes applied by CM**: <list of M-level fixes auto-applied>
- **Conflicts surfaced**: <if any architecture-vs-stretch tension flagged>

## 4. Operator verdict

- **Verdict**: Approved / Sent back / Killed
- **Date**: <when>
- **Notes**: <optional — any operator notes for posterity>

## 5. Production notes

- **Brief drafted against**: link to Per-Step Brief used (saved copy or "ephemeral — see CM session <date>")
- **Iteration count**: <how many Producer cycles to clear self-QA>
- **Brand cycles**: <how many cycles to clear Brand>
- **Lessons captured**: <if any pattern emerged worth feeding back>

## 6. Open questions for operator (gate)

<!-- GALLERY-PARSED. This section is extracted by the asset-gallery skill and rendered as the prominent "🟠 Open questions" panel in the lightbox. Numbered items get counted and surfaced as a "🟠 N questions" badge on the tile. -->

Numbered list of operator-facing decisions Producer needs the operator to make at the approval gate. Be specific. Surface trade-offs. Include Producer's recommended default per question so operator can `approve as-recommended` to accept all defaults.

1. **<Question name>** _(blocks: gate)_: <body of question + Producer's recommended default + tradeoff>
2. ...

**Blocking class + disposition at approval (SYS-106 — "hidden is not resolved").** Every gate question carries a **blocking class** — `gate` (default; must be settled to approve) · `phase-5` · `phase-6` · `publish` (legitimately answered LATER, at that phase). Write it inline as `_(blocks: <class>)_` after the question name. On the Phase-4b **approval**, each open question gets an explicit **disposition** — never left dangling, never silently hidden:

- **resolved** — the approved state or the operator's approval note answers it (CM auto-resolves these; record the answer).
- **waived** — the operator consciously drops it (record why).
- **deferred → Phase-X** — a non-`gate`-class question carried to the phase where it's actually answered. It **graduates** to that phase's `operator_actions` (in `campaign.yaml`) so it re-surfaces on the dashboard To Do — NOT lost. A `gate`-class question **cannot** be deferred (it must be resolved or waived to approve).

Dispositions are recorded in the asset audit (`## 5. Production notes` / the record's audit block). The gallery renders each question's disposition truthfully (resolved / waived / deferred→where) rather than hiding all approved-asset questions under a blanket "resolved" heading.

## 7. What the operator does next

<!-- GALLERY-PARSED. Rendered as the "🎯 What you do next" panel in the lightbox. Step-by-step. Concrete. -->

Numbered list of operator actions on approval. Open files locally, run scripts, click buttons, send to compliance, push to publish surface — name each step.

1. ...
2. ...

## 8. Flags for Brand Manager

<!-- GALLERY-EXCLUDED. This section is internal Brand-vs-Producer discipline. Operator does NOT see this in the gallery. Keep all "needs Brand pressure-test" / "self-QA close-calls" items HERE, not in §6 or §7. -->

Bulleted list of items Producer wants Brand Manager's eye on before clearing — phrase confirmations, edge-case rulings, compliance hairlines, voice pressure-tests.

- ...

## 9. Publish action

Once Approved:
- Publish entry surfaces in `campaigns/tasks.html`
- Destination URL set once Live
- Status → Live once operator confirms publication
```

---

## Peer artifact — `asset.yaml` (REQUIRED per asset folder)

Alongside the asset record markdown, Producer authors `asset.yaml` in the same folder. This is the **declarative metadata** the gallery + future automation read to surface this asset correctly without filename-guessing.

**Enforcement (2026-06-01 update)**: `build-gallery.py` now WARNS LOUDLY (stderr block + per-folder list) when asset.yaml is missing from any asset folder. Operator caught the recurrence on Soundtrak campaign — the rule was on the books but no automated check enforced it. Re-occurrence after this update = P1. Producer must ship asset.yaml on every: landing page · long-form article · whitepaper section · sales-kit asset (pitch deck / battle cards / email templates) · social post · case study · web tool. Exempt: ad headline batches, microcopy single bodies, taglines.

**Companion campaign-level file — `gallery-config.yaml`** lives at the campaign root (`campaigns/<slug>/gallery-config.yaml`) and declares the tenant's channel taxonomy. Two top-level keys: `channels:` (ordered list — drives gallery section order + asset.yaml `default_channel` valid values) and `channel_summaries:` (per-channel human-readable description shown under each channel heading). Missing config → build-gallery.py WARNS LOUDLY and falls back to generic `["Foundation", "Misc"]` skeleton. CM authors this file at Phase 1 (Brief approval) so downstream Producers know what channels exist before they author asset.yaml. See `campaigns/acme-launch-2026q2/gallery-config.yaml` for a working example.

**HTML / MD sibling inheritance (gallery convenience)**: when an asset has `cookbook.md` declared in the asset.yaml `files:` block AND a rendered `cookbook.html` sibling exists on disk, the gallery treats the HTML as the rendered preview of the same artifact — it inherits visibility (ship) AND metadata (title + asset_name) from the MD's declaration, and the type auto-promotes from `Foundation` (right for the source MD) to `Instance` (right for the rendered preview that operator reviews). Producers don't need to dual-declare the source + render pair in asset.yaml; just declare the source.

**Gallery-surface data contract — ALWAYS-POPULATED FIELDS (v3, 2026-07-03)**: the gallery lightbox standardises its naming, its "What this is" lead, its copy-review action, and its Plan trace from `asset.yaml` — so every asset MUST carry the data that populates them. Non-negotiable per asset:

- **`asset_name`** — REQUIRED. The lightbox primary title is `#<asset_id> · <asset_name>` (never a raw filename or a `_`-scaffolding name). Omit it and the title degrades to a filename.
- **`asset_id`** — REQUIRED, matches the Plan `#` (zero-padding is fine: `"01"` matches Plan `1`). Drives the `#id · name` title AND the Plan-row trace.
- **`rationale`** — REQUIRED. The "What this is" block ALWAYS renders; it resolves per-file `review:` → asset `rationale:`/`summary:` → the Plan row's `Notes`/`Form` → a type-based default — but a written `rationale:` is the intended source. Do not rely on the fallback.
- **per-file `title:`** — REQUIRED on every `ship: true` file. It's the lightbox subtitle (the specific file under the `#id · name` heading) and the clean tile subtitle. Absent → a humanised filename is used as a last resort.
- **A copy-review surface** — REQUIRED for every asset that carries any copy. Declare a top-level `copy_file:` (a `copy.md`, or the primary prose `.md` — e.g. `about.md`, `edition-01.md`). HTML-only assets ship a short **text extract** as `copy.md` so a View + Source copy surface always exists. If you declare nothing, the builder falls back (ship:true `.md` → Plan `Copy file` name → largest non-record prose `.md`) and WARNS to stdout if it still finds none — a build WARNING here means the copy-review contract is unmet; fix it.

**Gallery modal rule — three blocks only (v2, 2026-06-04)**: the approval lightbox shows exactly three things and nothing else:

1. **Rationale** — from `asset.yaml` `rationale:` field. Combined description + why-it-exists. What this asset is and what problem it solves. Operator-facing, decision-useful, one paragraph.
2. **Gate questions** — from `## Open questions for operator (gate)` in asset record MD. Numbered list of operator decisions needed at the approval gate. Specific. Surface trade-offs. Producer's recommended default per question.
3. **Next steps** — from `## What the operator does next` in asset record MD. Numbered list of operator actions on approval: open files locally, run scripts, click buttons, send to compliance, push to publish surface.

Everything else (plan metadata, related docs, type labels, path, last-touched timestamp, internal Producer reasoning sections) is excluded from the modal. The modal is a decision surface, not documentation.

**`## Flags for Brand Manager`** is the internal-only sibling — explicitly excluded from gallery extraction. Internal Brand-vs-Producer discipline stays out of the operator review surface.

Section extraction uses H2 keyword match (operator / open question / next step / decision); only `kind === questions` and `kind === next-steps` sections render. Any other H2 section whose header happens to match "operator" or "decision" but isn't a gate-questions or next-steps block will be excluded by the kind filter.

```yaml
asset_id: "0a"                              # matches Plan asset list ID + folder prefix
asset_name: "Welcome page + first email"    # = the Plan row's name, verbatim (do not invent)
default_channel: Substack                   # = the Plan row's Channel, verbatim — one of THIS campaign's valid channels (the CM injects them; never a generic list)
status: "For Human Review"                  # REQUIRED — gallery badge + filter. Values: "For Human Review" / "Approved" / "In Production"
rationale: >
  One paragraph: what this asset is + why it exists / what problem it solves.
  This is Block 1 of the gallery modal — the only context shown alongside gate questions
  and next steps. Operator-facing, decision-useful. Not a production summary.
  Example: "Unified email design system replacing Acme Co's dated justified-body layout.
  Solves stock-photo overuse across Acme Co Talks Weekly + Acme Co News Monthly. Every future
  Friday Note inherits from this template."
  Note: legacy `summary:` field is accepted as a fallback — new assets should use `rationale:`.
copy_file: "copy.md"                        # Optional — path to editable companion (md/csv/pptx/docx). Shown as ✏️ Edit copy button in modal header.

files:
  # ship: true | false  — THE GALLERY-TILE CONTRACT (load-bearing, added 2026-06-15)
  #   — Set `ship: true` on EXACTLY the files named in the Plan's `Ships` column for
  #     this asset, and nothing else. Each ship:true file = one gallery tile, 1:1.
  #   — Set `ship: false` (or declare as type: Foundation / a non-ship role) on every
  #     supporting file: render-pipeline sources (slide.html, build-pptx.py), embedded
  #     component images (images/*), deployment wrappers (modal-embed.html), copy
  #     mirrors (copy.md), and the asset record itself (asset.html). These are NEVER tiles.
  #   — GOTCHA the Producer MUST avoid: a file DECLARED in this block with NO ship flag
  #     and type: Instance DEFAULTS TO SHOWN. So a captioned-but-not-shipped component
  #     image will wrongly tile unless you mark it ship: false. When in doubt, be explicit.
  #   — Non-web-renderable ships (.pptx/.pdf/.docx/.xlsx) DO tile: the gallery renders a
  #     format-card poster + a download action. Mark them ship: true like any other ship.
  #   — A deck or document with two delivery formats (e.g. HTML + PPTX) = two ship:true
  #     files = two tiles. This is the canonical "two outputs, not just the HTML" case.
  #
  # For each file entry, two further optional fields control gallery behaviour:
  #
  # production_file: "path/to/file.pdf"
  #   — When the tile is a PNG/HTML preview but the deliverable is a binary (PDF, PPTX, DOCX),
  #     declare the binary path here. Gallery shows a 📄 Download PDF/PPTX button in the modal.
  #     Use when: bookmarks (PDF to send to printer), decks (PPTX to send to prospect), etc.
  #     (Note: a ship:true binary now also auto-tiles directly — production_file is for
  #     attaching a binary download to a SEPARATE visual tile.)
  #
  # view_source: "path/to/full-version.html"
  #   — When the thumbnail file differs from the actual production deliverable
  #     (e.g. preview.html thumbnails but full-html-preview/index.html is what ships),
  #     declare the real deliverable path here. "View in full" opens this file instead.
  #     Use when: complex interactive HTML pages that Playwright can't thumbnail cleanly.
  #
  # copy_file: "trailer-copy.md"   (or  copy_file: true)   — PER-TILE edit-copy source (SYS-099)
  #   — By DEFAULT every tile's ✏️ Edit-copy button opens the ASSET-level `copy_file` (above).
  #     That is correct for a single-deliverable folder, and for a folder built around ONE
  #     unified copy source that mirrors into every surface (e.g. an edition whose `copy.md`
  #     mirrors into the article + the trailer). But when a folder ships DELIVERABLES WITH
  #     GENUINELY SEPARATE COPY — an article tile and a paired social tile whose words differ
  #     — declare each tile's own source here so its button opens THAT deliverable's copy, not
  #     a folder-level default. String = a path (relative to the asset folder). `true` = THIS
  #     file IS its own copy surface (an inherited HTML tile resolves to its `.md` sibling).
  #   — Precedence: per-tile `copy_file` → asset-level `copy_file` → fallback chain. Without a
  #     per-tile value the old per-folder behaviour is unchanged, so this is purely additive.

files:
  master-template.html:
    type: Template                          # Template (parametric form) · Instance (concrete output) · Foundation (source/rationale)
    title: "Master template — the parametric design system"
    review: >
      What is the operator REVIEWING when they look at this file? Specific.
      Template = "review chrome / slot placement / structural integrity".
      Instance = "review brand discipline + sample content when populated".

  sb-talks-weekly.html:
    type: Instance
    title: "Output 1 — Acme Co Talks weekly newsletter"
    review: "..."

  design-system.md:
    type: Foundation
    role: rationale                         # primary_doc · rationale · how_to_use · doc_index · design_doc · render_pipeline · catalog · asset_record
```

**Per-file channel override** (when a single asset bundle spans multiple channels — e.g. visual templates that each serve different platforms):

```yaml
files:
  templates-preview/T1-sb-talks-episode-card.png:
    channel: "LinkedIn + social"            # overrides default_channel for this file — still a valid campaign Plan channel
    type: Instance
    template_source: "templates-html/T1-sb-talks-episode-card.html"
    title: "T1 — Acme Co Talks episode card (sample render)"
    review: "..."
```

See `.claude/agents/producer/AGENT.md` Step 4.5 for the full schema + type/role definitions + gallery-publish discipline.

### Multi-deliverable folders — file-naming convention (SYS-099)

When one asset folder ships **several deliverables** (the gallery sub-numbers them `N.1 / N.2 / N.3`
per SYS-097), the files inside must stay **legible** so the operator — and the edit-copy mirror
pipeline — can tell which file belongs to which deliverable. Two rules:

1. **Number the deliverable's files with its sub-number.** A deliverable that surfaces as tile `5.2`
   carries its sub-number on its own files: `05.2-trailer-tile.html`, `05.2-trailer-copy.md`,
   `05.2-trailer-tile.png`. Shared/foundation files (the asset record, a folder-wide moodboard)
   keep the plain asset prefix. This makes the folder self-documenting: a stray file's number tells
   you which tile it feeds. (A single-deliverable folder needs no sub-numbers — keep the plain names.)
2. **One canonical, declared edit-copy per deliverable — never an ad-hoc fork.** Each deliverable's
   editable copy is a single file, declared as that tile's `copy_file` (above). Do **not** hand-create
   parallel working copies like `Linkedin-copy-AB edits.md` — a file nothing points to strands the
   operator's edits (the button opens the stale canonical) and the mirror pipeline can't find them.
   If copy must be edited, edit the **declared** file; the render + the button both follow it.

> **Why (SYS-099):** the lightbox edit-copy button used to resolve once per FOLDER, so every tile in a
> multi-deliverable folder opened the same file. Combined with ad-hoc fork filenames, an operator's live
> edits could sit in a file the button never opened. Per-tile `copy_file` + numbered files close both gaps —
> the button follows explicit data, and the folder reads at a glance. See `feedback_edit_copy_syncs_with_render`.

---

## `deployment:` block — REQUIRED for every shipping asset *(v2 — Rollout Architecture §7)*

Every `asset.yaml` MUST include a `deployment:` block capturing per-asset specifics. The block is **mostly auto-inherited** from Brief `tech_stack` + `tenant/<name>/integrations.yaml` `channel_defaults` — Producer manually fills only `format_requirements`, `verification`, and `deployment_notes`. See Rollout Architecture v2 §7.1 for the full inheritance flow.

**Producer's Step 4.6** (added to Producer AGENT.md): fill `deployment:` block before final approval. Inheritance saves ~80% of fields; per-asset specifics are authored.

**Schema:**

```yaml
deployment:
  # ↓ Inherited from Brief tech_stack via integrations.yaml channel_defaults.
  # Producer reads asset.default_channel (= the Plan channel) → looks up channel_defaults[<channel>] → gets platform.
  # Producer SHOULD NOT manually override unless asset diverges from campaign default.
  destination_type: email                   # email | intranet | social | static-site | print | drive | api | none
  platform: "Mailchimp"                     # inherited; explicit here for asset-level audit trail
  publish_method: api                       # api | cookbook | hybrid  (from integrations.yaml has_adapter flag)
  location: "Mailchimp Content Studio"      # platform default location pattern; can be more specific per-asset

  # ↓ AUTHORED by Producer at build time — per-asset specifics that DON'T inherit.

  format_requirements:
    # What does THIS asset need from its destination that's specific to this asset?
    # NOT generic platform requirements (those live in integrations.yaml platform defaults).
    - "HTML email importable to Mailchimp Content Studio"
    - "Inline styles only (no <style> blocks — Mailchimp strips them)"
    - "Hosted PNG for hero lockup (Content Studio image upload before HTML import)"

  verification:
    # How do we know THIS asset landed correctly? Each entry has `check` (human-readable)
    # + optional `automated` (bool). Automated checks run as part of CM deploy step;
    # manual checks surface in operations.html as operator action.
    - check: "Mailchimp preview renders without broken images"
      automated: false
    - check: "Test send to the operator's inbox renders clean in Gmail + Outlook"
      automated: false
    - check: "Public URL returns 200 with expected page title"
      automated: true                       # only set true if CM has the verification logic

  deployment_notes: >
    Free-form notes Producer wants the deployer to see. Surfaces in operations.html
    alongside the asset. Use for: first-time installs, gotchas, prerequisites,
    "must do X before Y", etc.
    Example: "First-time Acme Co Mailchimp install — upload sb-wordmark-lockup-white.png
    to Content Studio first, replace src in HTML before importing."

compliance:
  # Written by CM from the governance-manager return at the Phase-4 governance gate (W1).
  # OPTIONAL + NO-RETROFIT: absent on assets with no Compliance Profile / no governance
  # review. The verdict surfaces on the asset preview via the <!-- COMPLIANCE_AUTO -->
  # marker — place it in preview.md right after <!-- STATUS_AUTO -->; rendered by
  # operator_actions.inject_compliance_line (emoji-coded ✅/⏸️/⛔ + disclaimers + counsel +
  # not-legal-advice note). Absent block = marker strips to nothing = existing behaviour.
  verdict: clear                # clear | clear-with-disclaimers | hold | blocked
  reviewer: governance-manager
  risk_tier: standard           # high | standard | low (from Compliance Profile §9)
  disclaimers_applied: []       # ids from Compliance Profile §1, inserted verbatim by CM
  claims_checked: []
  counsel_confirmed: "no"       # yes | partial | no (advisory until counsel confirms)
  reviewed: ""                  # ISO date
  notes: ""

resonance:
  # Written by CM from the insights-manager return at the Phase-4 advisory resonance read.
  # OPTIONAL + NO-RETROFIT: present ONLY on external-touchpoint assets in campaigns with an
  # Insight Brief — absent on internal/Foundation assets and on campaigns predating the
  # Insights Manager. Surfaces TWO ways from this one block: (1) the asset preview, via the
  # <!-- RESONANCE_AUTO --> marker placed at the BOTTOM of the asset record (render.py →
  # operator_actions.inject_resonance_line renders a titled "### 🧭 On Strategy — resonance
  # read" closing section — verdict pill + why + Fix); (2) the gallery lightbox, where
  # build-gallery.py reads this block directly and renders an "On Strategy" panel (kind-strategy)
  # at the bottom of the per-asset meta. NOTE: unlike STATUS/COMPLIANCE (top status-lines), the
  # RESONANCE marker belongs at the BOTTOM — it's a closing section, not a status line.
  # ADVISORY ONLY — a read, not a verdict; never blocks an asset. Absent block = no-op.
  read: on-insight              # on-insight | mixed | off-key | n/a-by-design
  reviewer: insights-manager
  segment: ""                   # which target segment this asset speaks to
  insight_ref: ""               # the Insight Brief §1 insight it anchors to (e.g. "1.2"); "-" if n/a
  why: ""                       # the read — anchored to that §1 insight + its evidence
  fix: ""                       # the single highest-value change to raise resonance ("" if on-insight)
  reviewed: ""                  # ISO date
```

**Inheritance flow** (per Rollout Architecture §7.1):

1. Brief `tech_stack` authored in Phase 1; locked end-of-Phase-3.
2. `tenant/<name>/integrations.yaml` authored from the Brief at tenant onboarding (Phase 0) — env-var refs + `channel_defaults`; available by Phase 4 for the Producer lookup below. Live credentials are filled later, at Phase 5 execution.
3. Producer at asset-build time reads `default_channel` → looks up `integrations.yaml#channel_defaults[<channel>]` → auto-populates `destination_type`, `platform`, `publish_method`, `location`.
4. Producer manually fills `format_requirements` + `verification` + `deployment_notes`.
5. Producer escalates Brief OQ ONLY if `default_channel` has NO mapping in `integrations.yaml` (genuinely new destination not anticipated in Brief).

**Enforcement** (build-gallery.py WARNS LOUDLY when missing):

```
⚠️  WARNING: campaigns/<slug>/assets/<asset-folder>/asset.yaml
   missing deployment: block.

   Producer Step 4.6 not completed. Inheritance from
   tenant/<name>/integrations.yaml channel_defaults[<channel>] would
   auto-populate ~80% of fields. Per-asset specifics
   (format_requirements + verification + deployment_notes) require
   manual authoring.

   Fix: edit asset.yaml; add deployment block per docs/specs/asset.md §deployment.
```

**When `destination_type: none` is valid:**
- Reference / library assets (e.g. Brand Context, design system docs, template-only files with no deployment)
- Internal-only artifacts (`asset_id` Foundation that lives in tenant library and isn't published anywhere)

Use sparingly. If unsure, declare a destination — even `drive` (deposit to OneDrive folder) is valid.

---

## HTML preview (operator-facing)

CM invokes `render-html` skill after Producer returns, with template `asset-preview`. The template:

- Shows the asset rendered as it would appear in-context:
  - **LinkedIn organic post**: LinkedIn-post mockup with profile picture, name, copy, tile embedded
  - **LinkedIn paid**: LinkedIn ad mockup with CTA button
  - **Email**: Inbox-preview frame with subject + preview text + body + sender info
  - **Landing page**: Rendered page at desktop + mobile breakpoints (responsive iframe)
  - **Substack issue**: Rendered Substack-style article view
  - **Twitter thread / IG carousel / TikTok**: Platform-specific mockup
- Embeds the visual file inline (not just a path)
- Shows the operator: copy + visual + Brand verdict + Operator action buttons (or instructions to reply in chat)
- Sidebar: KPI targets for this asset + key message + mandatories check

**Operator opens this HTML, sees what the asset looks like, replies in chat with approve / send back / kill.**

---

## Status flow

```
Draft (Producer authoring)
   ↓
In Brand Review (Brand Manager pass)
   ↓
Brand Pass (CM has applied fixes if any)
   ↓
Awaiting Your Approval (asset.html opens in operator's browser; surfaces in tasks.html)
   ↓
Approved
   ↓
Awaiting Publish (publish entry created in tasks.html)
   ↓
Live (operator confirmed publication; URL set)
```

Skip-paths:
- Producer self-QA Fail → back to Draft (3-strike rule applies)
- Brand Fail → back to Draft with findings
- Operator Sends Back → back to Draft with operator notes
- Operator Kills → Archived
- Fast-lane assets (per Plan §Fast-lane) skip Awaiting-Your-Approval and go straight to Awaiting Publish on Brand Pass

## Drafting discipline

- The markdown IS the asset record. No separate "draft" doc + "approved" doc.
- All review evidence inline. No separate Review records.
- HTML preview is regenerated from markdown on every status change.
- Visual binary lives in the asset's folder alongside the markdown — relative path linkage means folder is portable.

## Status tracking

The asset's `Status` field in the markdown body drives `tasks.html` and `dashboard.html`. CM updates the field and re-renders HTML on every status change. No external DB.

For cross-campaign queries ("all assets awaiting approval"), CM scans `campaigns/*/assets/*/<asset>.md` for the Status field and renders `campaigns/tasks.html`. Cheap and deterministic.
