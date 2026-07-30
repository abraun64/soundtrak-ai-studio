# Visual craft — shared universal reference

**Read by**: Creative Director (Concept §4 visual architecture, §6 channel rollout visual treatment per channel), Static Designer, Motion Designer.

Universal principles that apply across static AND motion design. Static-specific principles live in [static-design.md](static-design.md); motion-specific principles live in [motion-design.md](motion-design.md). This file holds the shared layer.

## Contents

- [Brand fidelity](#brand-fidelity)
- [Visual hierarchy](#visual-hierarchy)
- [Contrast](#contrast)
- [Color theory basics](#color-theory-basics)
- [Typography fundamentals](#typography-fundamentals)
- [Accessibility (WCAG AA)](#accessibility-wcag-aa)
- [Asset specs reference](#asset-specs-reference)
- [Brand-token discipline](#brand-token-discipline)
- [Cross-format consistency](#cross-format-consistency)
- [Generation-prompt craft](#generation-prompt-craft)
- [Common visual AI tells](#common-visual-ai-tells)

---

## Brand fidelity

Every visual must read as the brand. Brand fidelity is the floor; creative expression sits on top.

**The fidelity stack** — load in priority order from `tenant/brand/`:

1. **Logo system** — primary lockup, monogram, app icon, clear-space rules, minimum size
2. **Color palette** — primary, secondary, accent; with HEX / RGB / CMYK / Pantone references; with usage rules (when to use which)
3. **Type system** — display font, body font, weights and sizes; with usage rules (display for headlines, body for paragraphs, never reversed)
4. **Photography / illustration direction** — style references, do's and don'ts, named photographers / illustrators if the brand has a visual lineage
5. **Iconography** — line weight, corner radius, fill vs outline conventions
6. **Pattern / texture system** — repeating elements that signal the brand at glance
7. **Layout principles** — grid choices, white space discipline, margin/gutter rules

If any of these are missing in `tenant/brand/`, flag in §10 Production notes and ask before proceeding.

**Fidelity violations** that automatically flag:

- Logo distorted, recoloured outside brand rules, or used at sub-minimum size
- Colors outside the palette without reasoning
- Fonts outside the type system without reasoning
- Photography / illustration style that contradicts brand direction (e.g. stock photo on a brand that uses commissioned illustration only)
- Mixed iconography styles within one composition

---

## Visual hierarchy

Every composition must answer: where does the eye go first, second, third?

### Hierarchy techniques (any combination)

| Technique | How it creates priority |
|---|---|
| **Scale** | Bigger elements read first |
| **Contrast** | High-contrast elements stand out |
| **Color** | Saturated / accent colors pull attention; muted recedes |
| **Position** | Top-left / center-top read first (in left-to-right reading cultures); golden-ratio / rule-of-thirds focal points |
| **Whitespace** | Isolated elements draw eye; crowded elements recede |
| **Motion / animation** | (Motion design) moving elements pull attention |
| **Typography weight** | Heavier weights read first within the same scale |
| **Direction / sight-lines** | A face in the composition pointing at the headline directs the eye there |

### Hierarchy rule

**One primary focal point per composition.** If you have two competing focal points, the viewer's eye ricochets and lands nowhere. If the brief demands two equal elements, treat them as a paired-system (left/right balance) not two separate focal points.

---

## Contrast

Visual separation between elements — without contrast, hierarchy collapses.

### Contrast dimensions

- **Tonal contrast**: light vs dark
- **Color contrast**: hue separation (red vs green; warm vs cool)
- **Scale contrast**: large vs small
- **Weight contrast**: heavy vs light (typography especially)
- **Form contrast**: organic vs geometric; rough vs smooth
- **Density contrast**: crowded vs sparse regions

### Contrast rule of thumb

A composition with strong contrast in 1–2 dimensions reads cleanly. A composition with weak contrast across all dimensions reads as mush — the eye finds no entry point.

### Accessibility floor

Text-on-image and text-on-color combinations must meet WCAG AA:
- **Normal text**: 4.5:1 contrast ratio
- **Large text** (18pt+ regular or 14pt+ bold): 3:1
- **UI components and graphical objects**: 3:1

See [Accessibility](#accessibility-wcag-aa) for the full checklist.

---

## Color theory basics

### Color systems

- **HEX** (#RRGGBB): web/digital primary
- **RGB**: digital (255-255-255 scale)
- **CMYK**: print
- **Pantone (PMS)**: print spot colors; brand-critical for consistency across substrates
- **HSL / HSB**: useful for color generation and harmony (Hue / Saturation / Lightness or Brightness)

### Harmony patterns

- **Monochromatic**: one hue, varied saturation/lightness — calm, refined
- **Analogous**: hues adjacent on the wheel — harmonious, low-tension
- **Complementary**: hues opposite on the wheel — high-tension, attention-grabbing
- **Triadic**: three hues equidistant on the wheel — vibrant, balanced
- **Split-complementary**: one hue + two adjacent to its complement — strong but softer than complementary
- **Tetradic / square**: four hues equidistant — complex, hard to balance

### Color and meaning (culturally Western default; check tenant context)

- **Red**: urgency, passion, warning, energy
- **Orange**: warmth, friendliness, creativity
- **Yellow**: optimism, attention, caution
- **Green**: growth, calm, ecological, financial-positive
- **Blue**: trust, calm, professionalism, corporate
- **Purple**: luxury, creativity, royalty
- **Pink**: warmth, femininity (cliché — use with care), youth, playfulness
- **Brown**: earthiness, warmth, vintage
- **Black**: premium, sophistication, edge
- **White**: clean, minimal, premium
- **Grey**: neutral, technical, premium-secondary

**Cross-cultural caveat**: white = mourning in some East Asian contexts; red = wedding/celebration in China; check tenant audience context if cross-cultural.

---

## Typography fundamentals

### Type pairing principles

- **One display + one body** is the default pair — display for headlines and emphasis, body for paragraphs
- **Pair by contrast** — pair a high-contrast display with a more neutral body (serif display + sans body; geometric sans display + humanist sans body)
- **Avoid pairing similar fonts** — two near-identical sans serifs look like an error
- **Three fonts max** in most systems — display + body + a tertiary (often monospace for technical contexts)

### Type scale

- Use a modular scale (1.25, 1.333, 1.5, 1.618 multipliers) for predictable size progression: 12 / 15 / 19 / 24 / 30 / 38 / 47 / 59 etc.
- **6–8 sizes** typical for a complete design system
- **Each size has a clear role** — body, body-small, caption, H1, H2, H3, display

### Line length

- **Body copy**: 45–75 characters per line (66 is the classic optimal). Wider = hard to track. Narrower = choppy.
- **Headlines**: shorter is better; the eye absorbs in single fixation
- **Microcopy / captions**: 40–60 characters

### Line height (leading)

- Body copy: 1.4–1.6× the font size
- Headlines: 1.0–1.2× the font size (tighter)
- Increase line height for longer line lengths

### Weight contrast

- Pair heavy display weight with light/regular body for high contrast
- Italics for emphasis (sparingly); bold for emphasis within body
- Never both italic + bold for the same element

### Common typography failures

- All-caps body text (illegible at length)
- Tracking too tight (letters touch)
- Tracking too loose (letters detach from words)
- Justified text with poor hyphenation (river-streaks of white space)
- Headlines wider than body's reading column (eye breaks)
- Hierarchy too shallow (all sizes within 2px of each other = no hierarchy)

---

## Accessibility (WCAG AA)

The minimum accessibility floor for production work. Higher (AAA) for accessibility-sensitive contexts (government, education, healthcare).

### Contrast ratios

- **Normal text (under 18pt regular / under 14pt bold)**: 4.5:1 minimum
- **Large text (18pt+ regular / 14pt+ bold)**: 3:1 minimum
- **UI components, focus indicators, graphical objects conveying info**: 3:1 minimum
- **Decorative elements / inactive UI**: no requirement, but consider AAA at 7:1 for premium accessibility

Use a contrast checker (WebAIM, Stark, Figma plugins) to verify every color-on-color combination in the design.

### Alt text discipline (static)

- **Decorative-only images**: alt="" (intentional empty); flag the choice in §10
- **Informational images**: describe the content + function in 1–2 sentences
- **Functional images** (icons that link, buttons with image): describe the action ("Search" not "magnifying glass icon")
- **Complex images** (charts, infographics): brief alt + longer description in surrounding text or `aria-describedby`

### Captions and transcripts (motion)

- **Captions**: synchronised text track for spoken content; mandatory for video
- **Transcripts**: full text version of audio for podcasts and long videos
- **Audio descriptions**: narration of visual content for blind/low-vision viewers (rare in marketing, but flag for high-accessibility brands)
- **Burnt-in captions**: hardcoded in video (better for sound-off scroll); track-based captions (better for control + multilingual)

### Motion accessibility

- **Respect prefers-reduced-motion** in web contexts (CSS media query)
- **Avoid flashing** more than 3 times per second (epilepsy risk; WCAG 2.3.1)
- **Parallax effects**: provide a way to disable
- **Auto-playing video**: muted only; with controls visible

### Color-independence

- Never convey critical information by color alone (red/green callouts also use shape, label, or pattern)
- Test designs in greyscale and with color-blindness simulators (Deuteranopia, Protanopia, Tritanopia)

### Text alternatives in design

- Avoid putting critical information ONLY in images (a screenshot of text is not text)
- If text is in an image (poster, ad), provide the text in the alt or in surrounding copy
- Live text > rasterised text for accessibility and SEO

---

## Asset specs reference

Common asset specs across major channels. Always check the latest platform docs — these change.

### Web

- **Web hero image**: 1920×1080 (full HD landscape); 2x retina (3840×2160) optional
- **Web product image**: 1200×1200 (square) or 1200×800 (landscape)
- **Blog featured image**: 1200×630 (matches OG image ratio for social-share preview)
- **Logos**: SVG for web (scalable, small); PNG fallback
- **Favicons**: 32×32, 192×192, 512×512 (multiple sizes for browser + PWA)
- **OG image / Twitter card**: 1200×630 (1.91:1)
- **File formats**: WebP (best compression, broad support), AVIF (better compression, newer), JPEG (universal), PNG (transparency), SVG (vector)
- **Page weight target**: hero image <200KB, body images <100KB each

### Email

- **Email width**: 600–640px max (most clients respect)
- **Email header image**: 600×200 typical
- **Email body image**: 600×400 or smaller
- **Image format**: JPEG or PNG (GIF for animation); WebP unsupported in Outlook
- **File size**: <100KB per image to keep email under 1MB total
- **Image:text ratio**: 60:40 text:image to avoid spam filters

### Social — Instagram

- **Feed post (square)**: 1080×1080 (1:1)
- **Feed post (portrait)**: 1080×1350 (4:5) — maximum portrait
- **Feed post (landscape)**: 1080×566 (1.91:1) — rarely used; portrait/square better
- **Reels / Stories**: 1080×1920 (9:16)
- **Profile picture**: 320×320 minimum
- **Carousel**: each slide 1080×1080 (square) or 1080×1350 (portrait); 10 slides max

### Social — LinkedIn

- **Single image post**: 1200×627 (landscape) or 1200×1200 (square)
- **Document carousel (PDF upload)**: 1080×1080 or 1080×1350 per page
- **Video**: 1080×1920 (vertical) preferred for mobile; 1920×1080 (landscape) for desktop
- **Profile cover**: 1584×396
- **Company page cover**: 1128×191

### Social — X / Twitter

- **Single image**: 1200×675 (16:9) or 1200×1200 (square)
- **Profile picture**: 400×400
- **Header**: 1500×500
- **Card image (link preview)**: 1200×630

### Social — TikTok

- **Video**: 1080×1920 (9:16)
- **Profile picture**: 200×200

### Social — Facebook

- **Single image**: 1200×630
- **Cover photo (Page)**: 820×312
- **Profile picture**: 170×170 (desktop)

### Social — YouTube

- **Thumbnail**: 1280×720 (16:9)
- **Channel art**: 2560×1440
- **Video upload (long-form)**: 1920×1080 (16:9) at 30/60fps
- **Shorts**: 1080×1920 (9:16)

### Display ads (IAB standard sizes)

- **Medium rectangle**: 300×250
- **Leaderboard**: 728×90
- **Skyscraper**: 160×600
- **Half-page**: 300×600
- **Mobile banner**: 320×50
- **Mobile interstitial**: 320×480
- **Large rectangle**: 336×280
- **Billboard**: 970×250

### Out-of-home (OOH)

- **US billboard (bulletin)**: 14×48 ft (aspect ~3.4:1) — typical resolution 9600×3360 px at 100dpi
- **US poster billboard**: 12×24 ft (aspect 2:1)
- **UK 48-sheet**: 6.1m × 3.05m (aspect 2:1)
- **UK 6-sheet**: 1.2m × 1.8m (aspect 2:3 portrait)
- **Transit (bus side)**: varies — typically 240×60 in (4:1) or similar long-narrow
- **Digital OOH**: native resolutions vary per network — check specs per buy

### Print

- **Magazine full-page bleed**: A4 + 3mm bleed (216×303mm at 300dpi = 2551×3579px); US Letter + bleed similar
- **Newspaper**: tabloid (11×17 in), broadsheet (15×22 in)
- **Color space**: CMYK for print, sRGB for screen; convert at output stage

### Video

- **HD**: 1920×1080 (16:9)
- **4K UHD**: 3840×2160 (16:9)
- **Vertical 4K**: 2160×3840 (9:16)
- **Frame rates**: 24fps (cinema), 25fps (PAL/Europe broadcast), 29.97/30fps (NTSC/US broadcast), 60fps (high-motion / web)
- **Codec**: H.264 (universal), H.265/HEVC (better compression, newer), VP9 (web), AV1 (newest, best compression)
- **Bitrate**: varies — Vimeo / YouTube recommend 10–50 Mbps for HD

---

## Brand-token discipline

The brand's design tokens (colors, type, spacing, radius, shadow, etc.) live in `tenant/brand/` and are referenced by name in production work — NEVER hardcoded with magic numbers in a comp.

### Token categories

| Category | Examples |
|---|---|
| **Color tokens** | `--color-primary`, `--color-accent-1`, `--color-text-body`, `--color-bg-elevated` |
| **Type tokens** | `--font-display`, `--font-body`, `--size-h1`, `--size-body`, `--weight-bold` |
| **Spacing tokens** | `--space-xs` through `--space-3xl`; consistent scale (4px / 8px / 16px / 24px / etc.) |
| **Radius tokens** | `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-full` |
| **Shadow tokens** | `--shadow-sm` through `--shadow-xl`; named by depth/elevation |
| **Motion tokens** | `--duration-fast`, `--duration-base`, `--ease-out`, `--ease-in-out` |

### Token discipline

- **No magic numbers** — every color, size, spacing value should reference a token
- **Tokens are sourced from `tenant/brand/`** — Designer reads, doesn't author
- **Variations are tokens too** — `--color-primary-hover`, `--color-primary-active`, `--color-primary-disabled`
- **Token names are semantic** — `--color-error` not `--color-red` (the color may change but the meaning shouldn't)

---

## Cross-format consistency

When the same campaign concept ships across multiple formats (landing page + email + social tiles + OOH + video), the visual system must be **recognisable across all formats** without being identical.

### Consistency anchors (must persist)

- Color palette (with format-appropriate selection — accent on social, brand-primary on OOH)
- Type system (with format-appropriate selection — display for headlines across; body for long copy where applicable)
- Logo placement convention (top-left default; deviation flagged)
- Brand voice in copy (via Copywriters)
- Photography / illustration style

### Variation permissions (can flex)

- **Composition**: a square IG tile is composed differently than a vertical TikTok thumbnail than a 14:48 billboard
- **Density**: OOH is sparse; web hero is medium; landing page body is dense
- **Motion**: present in video, absent in static, light on web
- **Voice intensity**: same brand voice, but a TikTok script is more conversational than a webpage hero

### Anti-pattern

- **Same image resized for every format** — 1:1 IG tile stretched into 16:9 landing hero or cropped from 16:9 into 9:16 — composition breaks
- **Different visual systems per format** that don't read as one brand — looks like multiple agencies' work

---

## Generation-prompt craft

When using AI generation tools (Midjourney / DALL-E / Stable Diffusion / Firefly for static; Runway / Sora / Pika for motion), the prompt is the brief. Prompts must be:

### Self-contained

- Stand alone — readable without conversation history
- Include style direction (photographic / illustrated / 3D / specific aesthetic)
- Include composition direction (subject placement, framing, perspective)
- Include lighting direction (where applicable)
- Include color palette direction (named or hex-referenced)
- Include aspect ratio
- Include any "no-go" exclusions

### Specific, not generic

- ❌ "A modern, sleek office space"
- ✅ "Photograph of an early-morning meeting in a glass-walled conference room, six diverse adults seated around a marble table, low-angle shot, cool grey/blue palette, soft natural light from floor-to-ceiling windows, in the style of editorial photography by Annie Leibovitz"

### Named style references

Every prompt should name a specific reference — named photographer, art movement, brand precedent. Generic ("modern aesthetic" / "clean and minimal") is the AI-output tell.

### Negative prompts (where supported)

- List what to avoid: "no text overlay, no watermarks, no stock-photo lighting, no overly saturated colors"

### Iteration discipline

- Generate 4 variations
- Identify which 1 has the best foundation
- Iterate with refinement prompts ("same as v3 but with [adjustment]")
- Don't randomly re-roll — drift loses progress

### Tool-specific prompt grammars

- **Midjourney**: `--ar 16:9` for aspect ratio; `--style raw` for less stylised output; weighted prompts with `::`
- **DALL-E**: more natural-language prompts; less parameter syntax
- **Stable Diffusion**: more technical prompts; checkpoint models affect output dramatically
- **Firefly**: brand-safe outputs; commercial-use guarantees; integrates with Creative Cloud
- **Runway / Sora**: motion-specific — describe motion verbs, camera moves, duration

---

## Common visual AI tells

Patterns that signal AI-generated visuals and should be caught in QA.

### Static AI tells

- **Plastic skin** in portrait generation (smoothness in places real skin has texture)
- **Hand mistakes** — 6 fingers, fused fingers, wrong proportions
- **Text mistakes** — gibberish text on signs, products, or labels in the image
- **Background-foreground mismatch** — perspective or lighting that doesn't reconcile
- **Symmetry where there shouldn't be** — overly mirrored faces, identical eyes
- **Stock-photo lighting** — flat, even, lifeless illumination
- **Generic "modern minimal aesthetic"** — sterile, no specificity, looks like every other AI image
- **Pattern artifacts** — repeating textures, identical clones, glitchy edges

### Motion AI tells

- **Janky physics** — objects that don't move with weight or momentum
- **Inconsistent identity** — face changes shape between frames
- **Limb confusion** — arms / legs that bend wrong or appear/disappear
- **Background drift** — environment morphing during motion
- **Smooth-but-wrong motion** — too-perfect interpolation that looks "floaty"

### Repair patterns

- **Reroll selectively** — keep the foundation, fix the broken part
- **Compositing** — use the AI generation as a base, fix the broken element in Photoshop / After Effects manually
- **Crop out the failure** — if the broken element isn't critical, crop the frame
- **Reference photography** — for high-stakes work, AI augments not replaces photography

---

## Cross-references

- **Static-specific principles**: [static-design.md](static-design.md)
- **Motion-specific principles**: [motion-design.md](motion-design.md)
- **Channel grammar (aspect ratios, glance times)**: [channel-grammar.md](channel-grammar.md)
- **Platform-native social rules (visual aspects)**: [platform-native-social.md](platform-native-social.md)
- **Brand fidelity source**: `tenant/brand/` (logo, color, type, photography, iconography)
