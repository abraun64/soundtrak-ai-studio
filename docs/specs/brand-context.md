# Brand Context — Durable per-tenant record

The **Brand Context** is the durable per-tenant record of voice + visual identity + positioning + Canva brand kit reference. Established in **Phase 0 (tenant baseline)** — extracted from the operator's existing brand assets (brand-voice skills), or authored by CD as a Phase 0 task if absent. Reused across every campaign for the same tenant.

**Length target: 1–3 pages.** Big enough to be useful for slicing; small enough to skim.

**Stored**:
- Markdown (authoritative): `tenant-brand/<tenant-slug>.md`
- HTML (operator-facing view): `tenant-brand/<tenant-slug>.html`, rendered by `render-html` skill

**Stewarded by**: Brand Manager (across campaigns; flags drift and proposes updates as a separate "Brand maintenance" surface, not in-campaign).

---

## Schema

```markdown
# Brand Context — <Tenant name>

**Last updated**: <date>     **Last reviewed by Brand Manager**: <date>     **Source**: <operator's brand guide URL / authored by CD <date> / extracted from prior campaigns>
**Canva brand kit ID**: <id from Canva workspace> | NOT YET SET UP

## 1. Positioning

- **What we do (one sentence)**: <plain-language description>
- **Who we do it for**: <primary audience type — not campaign-specific persona, the always-true audience>
- **Why we exist / what we believe**: <the POV that differentiates>
- **What we're NOT**: <2–3 explicit anti-positioning statements>

## 2. Voice

### Tonal calibration
Where this brand sits on each axis (0–100):
- Direct ←→ Diplomatic: <position>
- Provocative ←→ Restrained: <position>
- Concise ←→ Expansive: <position>
- Casual ←→ Formal: <position>
- Expert ←→ Approachable: <position>

### Writing principles
5–7 principles. Each one line, plus a 1-line do-this / not-that example pair.

### Words we use (preferred)
List of preferred terminology — 10–20 words/phrases the brand owns or favors.

### Words we avoid
List of banned / discouraged terms — 10–20 words/phrases including AI-slop terms ("synergy", "leverage", "innovative", "best-in-class", etc.) and brand-specific vetoes.

### Spelling + grammar conventions
AU / US / UK English. Oxford comma yes/no. Title-case conventions. Date format.

## 3. Visual identity

### Palette
| Role | Color | Hex | Notes |
|---|---|---|---|
| Primary | <name> | #xxxxxx | <usage rule> |
| Accent | <name> | #xxxxxx | <usage rule — e.g. "ONE element per composition"> |
| Background | <name> | #xxxxxx | <usage rule> |

### Typography
| Role | Family | Weights | Notes |
|---|---|---|---|
| Display / title | <font> | <weights> | <usage rule> |
| Body | <font> | <weights> | <usage rule> |
| Annotation / signature | <font> | <weights> | <usage rule> |

### Visual register
- **Movement**: <named aesthetic — e.g. "Behavior Gap minimalism" / "Editorial photography" / "Maximalist motion graphics">
- **Composition rules**: <2–5 hard rules — e.g. "ONE accent element per sketch", "Signature bottom-right", "Hand-drawn imperfection over vector-smooth">
- **What we never do**: <2–4 explicit visual no-gos>

### Standard aspect ratios + canvas sizes
LinkedIn 16:9 / 1:1, Substack hero, email header, etc. — whatever this brand actively uses.

## 4. Canva brand kit

- **Canva brand kit ID**: <id from list-brand-kits>
- **Status**: Active / Pending setup / N/A (tenant doesn't use Canva)
- **Templates created**: <list of named brand templates if any have been built — e.g. "LinkedIn 16:9 anchor tile", "Substack hero 1200×675", "Email header 600×200">
- **Logo assets uploaded**: <yes/no — list if yes>

If absent for this tenant: the brand kit is created in **Phase 0** after voice + visual identity are locked. Palette + fonts uploaded to Canva via `upload-asset-from-url` or operator-supplied files. Brand kit ID captured here.

## 5. Gold-standard examples
3–7 named pieces of the brand's own published work that exemplify the voice + visual register. Each entry: name + link + 1-line "what to take from this".

## 6. Architecture state
- **Source of truth (operator's authoritative brand guide if one exists)**: <link / file:/// path>
- **Last brand audit**: <date if Brand Mgr has run a full review>
- **Open recommendations**: <queue of Brand Mgr suggestions awaiting operator decision>
```

---

## Slice extraction discipline (CM authoring Per-Step Briefs)

When CM injects a "voice slice" into a Per-Step Brief, it pulls:
- Tonal calibration (always)
- The 3–5 writing principles most relevant to the form (not all 5–7)
- The avoid-list items most likely to trip on this form
- 1 gold-standard reference closest to the asset's form

When CM injects a "visual identity slice":
- Palette hexes (always — full)
- Typography for the surfaces this asset uses
- Composition rules applicable to this asset's aspect ratio + form
- The "what we never do" list (always — full, it's short)
- **Canva brand kit ID** (if Producer will dispatch Mode B)

**Slicing is not summarising.** Slices are verbatim pulls of the relevant rules. CM never paraphrases brand rules.

### Per-asset-form slicing guide

The table below specifies which BC sections are load-bearing for each common asset form. CM uses this to avoid over-including (context bloat, Producer attention diluted) and under-including (quality gap, voice drift).

| Asset form | Always include | Include if relevant | Usually skip |
|---|---|---|---|
| Social post (LinkedIn/X/IG) | §2 Tonal calibration · §3 Writing principles (3 most relevant) · §3 Avoid-list · §5 Channel-specific voice for this platform | §4 Visual identity (if post has a tile) · §5 Hashtag conventions | Compliance posture (unless client-facing regulated) |
| Email single / newsletter | §2 Tonal calibration · §3 Writing principles · §3 Avoid-list · §4 Full visual palette · §4 Typography | §1 Compliance posture (if regulated tenant) · §5 Email-specific conventions | Channel guidance for non-email platforms |
| Landing page / web copy | §2 Tonal calibration · §3 Writing principles (all) · §3 Avoid-list · §4 Full visual identity · §7 Positioning | §1 Compliance posture · §5 CTA conventions | Adviser-specific channels |
| Display ad variants | §2 Tonal calibration · §3 Avoid-list · §4 Full visual identity + Canva kit ID | §3 Writing principles (headline rules specifically) | Long-form voice rules (irrelevant at ad scale) |
| Long-form article / whitepaper | §2 Tonal calibration · §3 Writing principles (all) · §3 Avoid-list · §7 Positioning + strategic arguments | §1 Compliance posture (if regulated) | Visual identity (unless article has designed header) |
| Sales deck / pitch | §2 Tonal calibration · §3 Writing principles · §7 Positioning · §8 BC recommendations (any open posture questions) | §4 Visual identity (full — deck is visual) | Adviser channels, podcast conventions |
| Outreach email (cold/warm) | §2 Tonal calibration · §3 Writing principles · §3 Avoid-list | §7 Positioning (if pitch-heavy) | Visual identity · compliance posture (unless required) |
| Print collateral (bookmark, poster) | §4 Full visual identity + print-specific rules · §3 Brand-adjacent copy constraints | §1 Compliance posture (if visible) | Channel voice rules (irrelevant for print) |

**When in doubt**: include §2 (tonal calibration) and §3 (avoid-list) for every asset — they're always relevant. Everything else is form-dependent.

---

## Lifecycle

- **Created** in **Phase 0 (tenant baseline)**, before the tenant's first campaign (extracted from the operator's existing assets OR authored by CD as a Phase 0 task; Canva brand kit set up if missing).
- **Reused** by every subsequent campaign for the same tenant — CM checks first, then asks operator "is this still current?" before Phase 2 (Concept Design).
- **Updated** when (a) operator signals a brand evolution, or (b) Brand Mgr's recommendations queue surfaces an update worth applying, or (c) a campaign's Stretch Tolerance: Loose produces brand-additive learnings worth absorbing.
- **Updates require operator approval.** Not auto-applied. Brand evolution is a deliberate act.
