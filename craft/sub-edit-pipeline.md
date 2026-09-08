# Sub-edit pipeline — universal procedure reference

**Read by**: every agent that produces written or scripted output (5 Copywriters, Social/Community Manager, Creative Director where it touches copy, future Designer agents for their visual-QA equivalents).

The sub-edit pipeline is the agent-internal QA step that runs after drafting and before the agent returns to Campaign Manager. **Refuse-to-surface** is its end state: if the pipeline can't reach clean after 3 cycles, the agent returns `ok: false` rather than handing un-clean work to CM.

## Contents

- [The three-layer model](#the-three-layer-model)
- [Procedure (scan → fix → re-scan → report)](#procedure)
- [Refuse-to-surface rule](#refuse-to-surface-rule)
- [§7 Sub-edit report structure](#7-sub-edit-report-structure)
- [Layer 3 overlay catalogue](#layer-3-overlay-catalogue)
- [Layer 3 — Email (deliverability)](#layer-3-email)
- [Layer 3 — Presentation (spoken-friendliness)](#layer-3-presentation)
- [Layer 3 — Social (platform-native)](#layer-3-social)
- [Layer 3 — Web (AEO/SEO discipline)](#layer-3-web)
- [When no tenant voice signal exists](#when-no-tenant-voice-signal-exists)

---

## The three-layer model

| Layer | What it checks | Source | Tenant-swappable |
|---|---|---|---|
| **Layer 1 — Universal AI-tells** | Hardcoded craft rules that signal AI-generated prose regardless of brand | [copywriting.md](copywriting.md) | No (universal craft) |
| **Layer 2 — Tenant voice rules** | The brand's specific voice — its banned words, its sentence patterns, its register, its sign-off conventions | `tenant/brand/voice.md` (+ supplemental: `positioning.md`, `CLAUDE.md`, `campaigns/<slug>/brand-note.md`) | Yes (tenant overrides universal where intentional) |
| **Layer 3 — Form-specific overlay** | Form-native rules that don't fit the prose-quality model — deliverability for email, spoken-friendliness for presentation, platform-native scan for social, AEO discipline for web | This file's [Layer 3 overlay catalogue](#layer-3-overlay-catalogue) + format-specific craft files | No (universal craft, tagged by form) |

**Layering precedence**: Layer 1 is the floor. Layer 2 can *narrow* Layer 1 (a brand can ban additional words) but cannot *broaden* it (a brand cannot un-ban Tier 1 corporate platitudes unless one is used deliberately as positioning and named explicitly in `tenant/brand/voice.md`). Layer 3 runs alongside; its rules are non-overlapping with Layers 1 and 2.

---

## Procedure

Every sub-edit pass runs the same shape regardless of form. The form determines which Layer 3 overlay applies; the procedure itself is universal.

### Step 1 — Scan

Read the draft through all three layers and list every violation. For each violation capture:

- **Layer** (1, 2, or 3)
- **Rule** (specific rule name from the relevant craft file)
- **Location** (sentence / line / slide number)
- **Offending text** (quote verbatim)
- **Severity** (auto-fix / discretionary / hard-block)

### Step 2 — Fix

Apply fixes in this order:

1. **Hard-block violations first** (Tier 1 banned phrases, deliverability mandatories, accessibility gaps, char-limit breaks)
2. **Layer 1 universal AI-tells**
3. **Layer 2 tenant voice violations**
4. **Layer 3 form-specific violations**
5. **Discretionary improvements** (sentence rhythm tweaks, slight word swaps) — only if Steps 1–4 are clean

Fixes are minimal: change exactly what flagged, don't rewrite the surrounding prose unless the fix itself demands it.

### Step 3 — Re-scan

Run Step 1 again on the fixed draft. If violations remain, return to Step 2.

### Step 4 — Cycle limit

Maximum **3 fix-and-rerun cycles**. After 3 cycles:

- If clean → write the §7 Sub-edit report and proceed to Asset write
- If still un-clean → **refuse to surface** (see below)

### Step 5 — Report

Write the §7 Sub-edit report (structure below) into the Asset. The report is part of the Asset's reviewable surface — Brand Manager reads it on every gate review.

---

## Refuse-to-surface rule

If after 3 fix-and-rerun cycles the draft still has un-cleared violations, the agent:

1. Returns `ok: false`, `code: self_qa_unreachable` to CM
2. Includes the final violation list in the return envelope
3. Includes the version of the draft from cycle 3 (the least-bad version)
4. Names the specific rules that won't clear and the agent's hypothesis on why (e.g. "Layer 2 ban on 'unlock' conflicts with Concept §2 messaging which uses 'unlock the playbook' as the campaign positioning — needs human call")

CM then decides: escalate to user (the rule conflicts with the campaign's needs), revise the brief / concept (the upstream artifact is asking for un-clean work), or accept the violation with explicit user sign-off (override the rule for this Asset only, logged in §10 Production notes).

**Never silently ship un-clean work.** Refuse is the cheaper failure mode than shipping AI-coded prose.

---

## §7 Sub-edit report structure

Every Asset has a §7 section the sub-edit pass writes into. The structure is uniform across forms:

```markdown
## §7 Sub-edit report

**Pipeline state**: Pass (N violations fixed in M cycles) | Pass — first scan clean | Fail — N violations unreachable after 3 cycles

**Layers run**:
- Layer 1 (universal AI-tells): <Pass / Fail with count>
- Layer 2 (tenant voice — source: `tenant/brand/voice.md` + <supplemental list>): <Pass / Fail with count / N/A — no voice signal available>
- Layer 3 (<form-specific overlay name>): <Pass / Fail with count>

**Violations fixed**:
| # | Layer | Rule | Cycle fixed | Original (verbatim) | Fixed |
|---|---|---|---|---|---|
| 1 | 1 | Restated-conclusion close | 1 | "..." | "..." |
| 2 | 1 | Throat-clearing opener | 1 | "..." | "..." |
| 3 | 2 | Brand-banned word "leverage" | 2 | "..." | "..." |

**Unreachable violations** (only if Fail):
| # | Layer | Rule | Why it won't clear |
|---|---|---|---|

**Tenant voice signal sources loaded**: `tenant/brand/voice.md` (last modified <date>); supplemental: <list>; gold-standard reference: <Asset slug>

**Notes for reviewer**:
- <One line per discretionary call the agent made, e.g. "Kept one punchy pair in §3 — deliberate rhythm break per long-form strictness allowance">
```

The report is **visible to Brand Manager** at gate review and **visible to the user** at the Final asset gate via the Review Request §9 block.

---

## Layer 3 overlay catalogue

Layer 3 is the form-specific scan that runs alongside Layers 1 and 2. It's not voice — it's the deliverability / accessibility / platform-grammar discipline that's specific to the form's surface.

### Layer 3 — Email

Email-specific deliverability + format scan. Read by Copywriter–Email.

**Spam triggers** — flag in subject line, preview text, or body:

- ALL CAPS in subject line
- Excessive punctuation: "!!!" / "???" / mixed "!?"
- Trigger phrases: "FREE!!" / "ACT NOW" / "100% guaranteed" / "you've been selected" / "earn $$$" / "miracle" / "no risk" / "limited time only!!!" / "this isn't spam" / "you have been chosen"
- Currency symbols in subject ($$$, €€€)
- All-caps brand name (most brands use mixed case)

**Image:text ratio** (HTML emails):

- Image bytes:text bytes > 60:40 → flag
- Image-only emails (no text body) → flag as deliverability risk and accessibility fail

**Mobile preview cutoff**:

- Subject line >50 chars → flag (will truncate)
- Most-important word not in first 30 chars of subject → flag (mobile cutoff is ~33–41 on iPhone, ~30 on Android)
- Preview text >90 chars → flag (will truncate)
- Preview text repeats subject verbatim → flag (waste of the slot)
- Preview text empty → flag (mail client will pull body line 1, often bad)

**Mandatories** (per Brief §9):

- Unsubscribe link present in footer → required for marketing email
- Sender postal address present → required (CAN-SPAM US, similar regional)
- List-unsubscribe header where applicable (technical, often dev-implemented but worth flagging)
- Region-specific footer present (GDPR EU, CASL Canada, PECR UK, etc.)

**Format**:

- Single CTA per email → flag if multiple primary CTAs (exception: newsletter digest format)
- CTA repeated >2 times → flag
- Paragraphs >3 sentences → flag (mobile readability)
- Body >300 words for non-newsletter → flag for review

### Layer 3 — Presentation

Spoken-friendliness scan. Read by Copywriter–Presentation.

**Tongue-twisters**:

- Adjacent words starting with same consonant cluster (>3 in a row) → flag for read-aloud test
- Sibilance runs (>4 "s" sounds in a sentence) → flag
- Hard consonant clusters that trip the speaker → flag

**Acronyms-spoken-aloud**:

- Any acronym used in script → flag, ask "speaker says letters or word?"
- Acronyms that don't pronounce cleanly → flag (e.g. "TPS" said aloud, vs "NASA" said as word)
- Industry acronyms unfamiliar to expected audience → flag

**Spoken numbers**:

- Large numbers (>1,000) → flag, prefer "thousand" / "million" / "billion" or round ("about three thousand")
- Decimal numbers → flag, simplify or convert ("3.7" → "almost four")
- Percentages → fine spoken; flag if >2 in a sentence
- Years spoken as digits → confirm pronunciation ("twenty twenty-six" vs "two thousand twenty-six")

**Conversational register**:

- Contractions (don't / won't / can't / it's) → encourage in scripted speech; flag if absent
- Sentence length: speakable sentences are ~12–18 words. Anything over 25 words → flag as "needs breath break"
- Subordinate clauses stacked > 2 deep → flag (loses listener)

**Slide-script coherence** (for Storyboard format):

- Slide visual contradicts script line → flag
- Script names a number / chart not on slide → flag
- Memorable line (the audience-tweet candidate) not on a slide → flag

### Layer 3 — Social

Platform-native scan. Read by Social/Community Manager + Copywriter–Short-form (for paid social). Full per-platform rules live in [platform-native-social.md](platform-native-social.md); this overlay summarises the scan checks.

**Character / length limits** (flag if exceeded):

| Platform | Limit |
|---|---|
| X / Twitter post | 280 chars |
| LinkedIn post | 3,000 chars (1,200–1,800 ideal) |
| Instagram caption | 2,200 chars (hook in first 125) |
| TikTok caption | 150 chars typical (2,200 max) |
| Threads | 500 chars |
| Facebook | no hard limit; 40–80 words optimal |

**Hook truncation**:

- LinkedIn post hook clips before landing at "...more" cutoff (~210 chars on mobile) → flag
- X first post of thread doesn't stand alone if quote-tweeted → flag
- IG caption first 125 chars don't include hook → flag
- TikTok caption hook competes with on-screen text hook → flag for coherence

**Hashtag count** (per platform):

| Platform | Min | Max | Placement |
|---|---|---|---|
| LinkedIn | 3 | 5 | End of post |
| X | 0 | 2 | Inline |
| Instagram | 5 | 15 | First comment OR end of caption |
| TikTok | 3 | 5 | Caption |
| Threads | 0 | 2 | Inline |
| Facebook | 0 | 2 | Inline (rarely move engagement) |

**Hashtag formatting**:

- Lowercase multi-word hashtag → flag (CamelCase is screen-reader accessible: #ReadableHashtag not #readablehashtag)
- Spaces or punctuation inside the tag → flag (breaks the tag)
- Campaign hashtag missing → flag (must be present per Plan)
- Banned hashtag from taxonomy used → flag

**Platform-banned hooks**:

- LinkedIn: "I'm excited to announce..." / "I'm thrilled to share..." / "It is with great pleasure..." → flag
- Facebook: "[Name] is feeling [emoji] at [location]" boilerplate → flag
- X: ratio-bait engagement-only first tweet → flag

**Accessibility**:

- No alt text written for image-attached post → flag (write it; Designer / operator inputs)
- No caption track planned for video post → flag
- All-caps body text > 1 word → flag (screen readers struggle)
- Emoji-only sentence → flag (screen reader reads "smiley face")
- Critical info conveyed only by color or visual → flag

**Disclosure mandatories**:

- Paid partnership without #ad / #spon / "Paid partnership with X" → flag (FTC)
- Regulated industry (finance / healthcare / crypto / gambling) missing required disclosure → flag
- Brand-mandated tags per Brief §9 missing → flag

**CTA shape**:

- LinkedIn post with hard "Buy now" CTA in body → flag (kills reach; use soft CTA, comment-prompt, or link in first comment)
- X thread with link in middle post → flag (kills thread completion; links go in final post)
- IG post with link inline → flag (links don't activate; needs "link in bio" reference)
- TikTok with link in caption → flag (doesn't activate; needs link in bio)

### Layer 3 — Web

AEO/SEO discipline scan. Read by Copywriter–Web; light overlay for Copywriter–Long-form when destination is HTML / owned blog. Full rules will live in `craft/web-aeo.md` (future build). Summary:

**AEO (Answer Engine Optimisation) — for content surfaces that LLMs read**:

- H1 frames the page's primary question or topic → required
- H2/H3 subheadings are answerable questions or noun-phrase topics (not creative titles) → required
- Direct answer to the H1 question in the first 1–3 sentences → required
- Entity-clarity: people, products, places, dates named with full proper names, not pronouns → required
- Schema-readable structure: FAQ blocks marked clearly, lists structured as lists, tables as tables → required

**SEO — for surfaces that rank in search**:

- Primary keyword in H1 → required
- Primary keyword in first paragraph → required
- Meta title ≤60 chars including brand → required
- Meta description ≤155 chars, action-led → required
- Heading hierarchy well-formed (no H3 before H2) → required
- Internal links present where contextually relevant → flag if absent
- Image alt text descriptive (not "image" or "graphic") → required

---

## When no tenant voice signal exists

If `tenant/brand/voice.md` is missing AND no supplemental signal exists (`positioning.md`, `CLAUDE.md`, gold-standard work, campaign brand-note), the pipeline degrades gracefully:

1. **Layer 1 runs normally** — universal craft is universal
2. **Layer 2 is skipped** — log "no tenant voice signal available" in §7 report
3. **Layer 3 runs normally** — form-specific overlays are universal craft

The agent flags the missing voice signal as a §9 Open question in the Review Request. CM can escalate to the user to either provide voice signal or accept Layer-1-only review for this Asset.

**Never invent tenant voice rules.** If the signal isn't there, the pass runs on universal craft only and flags the gap.

---

## Cross-references

- **Universal AI-tells (Layer 1 source)**: [copywriting.md](copywriting.md)
- **Strictness-by-form table**: [copywriting.md#strictness-by-form-the-scaling-table](copywriting.md#strictness-by-form-the-scaling-table)
- **Social platform rules (Layer 3 social source)**: [platform-native-social.md](platform-native-social.md)
- **Asset spec (where §7 lives)**: [docs/specs/asset.md](../docs/specs/asset.md)
- **Review Request §9 format**: [docs/specs/review-request.md](../docs/specs/review-request.md)
