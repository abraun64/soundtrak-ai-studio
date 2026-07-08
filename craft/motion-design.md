# Motion design craft — universal reference

**Read by**: Motion Designer (primary), Creative Director (Concept §4 visual architecture when authoring brand-film concept, §6 channel rollout for video channels), Copywriter–Presentation (light — slide transitions only), Social/Community Manager (Workflow 5 short-form video script authoring).

For shared visual fundamentals (brand fidelity, accessibility, color theory, typography, asset specs) see [visual-craft-shared.md](visual-craft-shared.md). This file holds motion-specific principles + format-tagged sections.

## Contents

- [Storyboarding](#storyboarding)
- [Beat timing](#beat-timing)
- [Motion principles](#motion-principles)
- [Transitions](#transitions)
- [Pacing](#pacing)
- [Sound design fundamentals](#sound-design-fundamentals)
- [Sound-off design](#sound-off-design)
- [Format-tagged sections](#format-tagged-sections)
  - [Short-form video (TikTok / Reels / Shorts)](#short-form-video)
  - [Long-form video (YouTube / brand film / explainer)](#long-form-video)
  - [GIF / animated header](#gif--animated-header)
  - [Motion graphics (kinetic typography / infographic animation)](#motion-graphics)
  - [Animated banner (HTML5 display ad)](#animated-banner)
  - [Animated logo / ident / lockup](#animated-logo--ident)
  - [Cinemagraph](#cinemagraph)
  - [Web hero motion / scroll-triggered animation](#web-hero-motion)
  - [Presentation slide transitions](#presentation-slide-transitions)
- [Common motion-design AI tells](#common-motion-design-ai-tells)

---

## Storyboarding

Motion design starts with storyboarding — frame-by-frame or beat-by-beat plan before any animation work begins.

### Frame-by-frame storyboard

- Each scene drawn / sketched as a single frame
- Includes: visual composition + camera angle + on-screen text + spoken / audio cue + duration
- Used for: longer-form video, talking-head explainers, narrative spots

### Beat-by-beat storyboard

- Each beat (a unit of meaning, typically 2–5 seconds) summarised in 1–2 frames
- Lighter than frame-by-frame; faster to iterate
- Used for: short-form social video, GIF loops, simple motion graphics

### Storyboard fields per beat / frame

| Field | What goes here |
|---|---|
| **Frame # / Beat #** | Sequential identifier |
| **Time** | Start time + duration (e.g. 0:00–0:03) |
| **Visual** | What the camera shows; subject, framing, action |
| **Camera move** | Static / pan / zoom / track / handheld / drone |
| **On-screen text** | Text overlay; verbatim |
| **Spoken / VO** | Spoken content; verbatim |
| **Sound / SFX** | Music cue, sound effect, ambient |
| **Transition out** | Cut / dissolve / wipe / match-cut |
| **Delivery / pacing note** | Speaker energy, pace, pause |

### Storyboard discipline

- **Storyboard is a REQUIRED FIRST GATE for any video** *(operator rule, 2026-07-08)* — the storyboard is produced and **signed off by the operator BEFORE any motion is produced**. Do not animate or generate the video until the storyboard is approved. This is a named exception to "no intermediate gates on sub-deliverables": for video, iterating on a storyboard is ~10× cheaper than iterating on the produced motion, so the checkpoint pays for itself.
- **Storyboard BEFORE animating** — iterating in After Effects (or any motion build) is 10× more expensive than iterating on a storyboard.
- **Surface the storyboard as its own reviewable artifact** (a gallery tile / gate surface), not buried in the asset record — kill bad concepts cheaply.
- **Storyboard is the brief** that the motion designer (or AI generation tool) executes against.

---

## Beat timing

Every motion piece is composed of beats — units of meaning paced over time.

### Three-act structure for short-form

| Act | Duration (in 30s video) | Role |
|---|---|---|
| **Hook** | 0:00–0:03 | Pattern-interrupt + the question / claim / surprise |
| **Payload** | 0:03–0:27 | The substance — story / framework / demo / proof |
| **Close** | 0:27–0:30 | CTA + final visual beat |

For longer formats, the ratio shifts but the structure persists: hook (10–20% of runtime), payload (60–75%), close (10–20%).

### Hook timing (critical for social)

- **First 1.5 sec**: pattern-interrupt visual (movement, contrast, face) — this is "is this worth watching"
- **0–3 sec**: spoken hook + on-screen text + visual cue — three signals firing at once
- **3 sec mark**: the viewer has decided to keep watching or scroll; the hook has worked or failed

### Pacing variation

- **Fast cuts** (every 1–2 sec): high-energy, social-trend, urgent
- **Medium cuts** (every 3–6 sec): conversational, educational, explainer
- **Long takes** (10s+): contemplative, cinematic, emotional
- **Vary the pacing within a video** — uniform pacing is exhausting; the eye needs rhythm

### Pause as design

- **Beats of stillness** between fast cuts let the eye rest
- **Held final frame** lands the message — fast-cut sequences ending in 2 sec of stillness on a logo / CTA work
- **Pre-cut pause** (a beat of silence before a punchline / reveal) is a comedic motion technique

---

## Motion principles

The 12 principles of animation (Disney, ported to motion design):

| # | Principle | Application in motion design |
|---|---|---|
| 1 | **Squash and stretch** | Objects deform to convey weight + speed; subtle in UI / motion graphics |
| 2 | **Anticipation** | Pre-motion that signals the main motion is coming (a button "winds up" before launching) |
| 3 | **Staging** | Composition that makes the intended action clear |
| 4 | **Straight-ahead vs pose-to-pose** | Frame-by-frame (fluid, intuitive) vs key-framed (planned, controlled). Modern motion design is mostly pose-to-pose. |
| 5 | **Follow-through and overlapping action** | Parts of an object continue moving after the main object stops; secondary motion adds realism |
| 6 | **Slow in, slow out (easing)** | Motion accelerates and decelerates; never uniform speed (linear motion looks robotic) |
| 7 | **Arcs** | Most natural motion follows curved paths, not straight lines |
| 8 | **Secondary action** | Supporting motion that complements primary (a character's hair moving as they walk) |
| 9 | **Timing** | The speed of motion conveys meaning — fast = light/energetic, slow = heavy/important |
| 10 | **Exaggeration** | Push motion beyond literal realism for emphasis |
| 11 | **Solid drawing** | Objects feel three-dimensional and consistent across frames |
| 12 | **Appeal** | Motion has charisma — interesting to watch |

### Easing curves (most-used in motion graphics)

- **Linear**: constant speed — feels robotic; avoid for most use cases
- **Ease-in**: starts slow, ends fast — entering motion
- **Ease-out**: starts fast, ends slow — settling motion
- **Ease-in-out**: slow at both ends, fast in middle — natural acceleration + deceleration; default for most
- **Custom cubic Bézier**: brand-specific curves; named in `tenant/brand/motion-tokens.md` if present

### Anticipation in marketing motion

- A small reverse-motion before a launch (a button pulling back before springing forward) signals impending action
- Pre-roll movement at the start of a transition primes the eye for what's coming

### Follow-through in marketing motion

- Elements that continue moving slightly after the camera stops (a slight settle on text reveals)
- Adds polish and natural feel

---

## Transitions

How one shot / scene / frame moves to the next.

### Cut

- Hardest transition — instant change from one frame to the next
- Standard for most narrative video
- Used for: dialogue, action, fast pacing, scene changes
- Workhorse — most transitions in most videos are cuts

### Dissolve / cross-fade

- Gradual blend from frame A to frame B
- Conveys: time passing, change of perspective, dream / memory
- Use sparingly — overused dissolves signal "amateur edit" or "stock-footage montage"

### Wipe

- One frame is replaced by another via a moving edge (linear wipe, clock wipe, iris wipe)
- Conveys: scene change, deliberate cinematic style
- Use cautiously — wipes are stylised and date the work

### Match cut

- Two visually-related shots cut together (e.g. a circle in shot A matches a circle in shot B)
- Powerful for narrative — implies connection between scenes
- Hard to design; rewards craft

### Whip pan / whip transition

- A fast motion blur connects two shots
- Conveys: energy, immediacy, action
- Modern social trend (TikTok, Reels) leans heavy on whip transitions

### J-cut / L-cut (audio overlap)

- Audio from next scene starts before video (J-cut); audio from previous scene continues into next video (L-cut)
- Smooths transitions; classic editorial technique
- Adds polish to talking-head and narrative video

### Match-on-action

- Cutting on the moment of action (a hand reaching for a door, then cut to the door opening from inside)
- Invisible; the eye doesn't perceive the cut
- Hallmark of polished narrative editing

### Transition discipline

- **Default to cuts** — most transitions in most videos
- **One stylised transition per video maximum** — overusing wipes / dissolves / whips makes the work look amateur
- **Transition style matches brand register** — corporate brands often cut-only; entertainment brands can wipe / whip more freely
- **Audio carries transitions** — sound design as much as visuals; a hard cut with audio bridge feels different than the same cut with silence

---

## Pacing

How the video's energy varies over time.

### Pacing curves

- **Flat fast**: constant high energy; effective for short-form social
- **Flat slow**: constant slow pacing; cinematic, brand-film
- **Build**: starts slow, escalates; common for product reveals
- **Hook-and-settle**: fast hook, then slows for substance; standard for explainer
- **Wave**: alternating fast and slow sections; longer-form variety

### Cut frequency by format

| Format | Average cut frequency |
|---|---|
| TikTok / Reels (15–30s) | Every 1–2 sec |
| TikTok / Reels (30–60s) | Every 2–3 sec |
| YouTube Shorts (educational) | Every 2–3 sec |
| LinkedIn video (1–2 min) | Every 3–5 sec |
| YouTube long-form (5–15 min) | Every 4–8 sec for vlog-style, longer takes for cinematic |
| Brand film (1–3 min) | Every 3–8 sec, often longer takes |
| Cinema commercial (30s) | Every 1–3 sec |
| Explainer / product demo (1–2 min) | Every 3–5 sec |

### Watch-through metric

- Completion rate (% of viewers who watch to the end) is the dominant social algorithm signal
- Drop-off analysis: identify where viewers leave; tighten or restructure that section

---

## Sound design fundamentals

Motion design without sound is half-finished. Sound design choices shape the viewer's emotional response as much as visuals do.

### Music as scaffolding

- **Track selection sets the mood** — choose deliberately; not "any music"
- **Tempo matches cut pacing** — fast cuts to fast music; slow cuts to slow music
- **Music drops at hook moments** — silence pre-drop, then music in on the reveal
- **Music ducks for VO** — if there's voice-over, music sits lower in mix (ducked) when VO speaks
- **Licensing**: brand-safe library music (Artlist / Musicbed / Epidemic Sound), royalty-free (commercial use cleared), or original composition for premium brands

### Sound effects (SFX) as emphasis

- **Transitions get SFX** — whoosh on a whip-pan, click on a UI element, thump on a hard cut
- **Reveals get SFX** — a "ding" on a CTA appearance; a "bass drop" on a product reveal
- **Use sparingly** — every cut doesn't need an SFX; overuse signals amateur

### Voice-over (VO)

- **VO casting matters** — voice matches brand register; warm/cool, masculine/feminine, accent, age
- **VO pacing**: ~150 wpm conversational; ~120 wpm for manifesto / brand-anthem
- **VO and music must mix** — VO sits on top; music ducks below
- **VO sub-edit pass**: read aloud, flag tongue-twisters, acronyms, hard-to-pronounce words (see [sub-edit-pipeline.md#layer-3-presentation](sub-edit-pipeline.md#layer-3-presentation))

### Silence

- **Beats of silence** are design — used deliberately, silence draws attention
- **Pre-CTA silence** lands the call-to-action
- **Pre-reveal silence** builds anticipation

### Brand sonic identity

- **Brand sonic logos** — short audio mark (Intel chime, Netflix "ta-dum", McDonald's "I'm lovin' it" jingle)
- **Brand voice cast** — same VO talent across multiple campaigns builds recognition
- **Brand music palette** — recurring track or composer / style for the brand

---

## Sound-off design

Critical for social — ~50% of feed video views are muted (public transit, open offices, headphone-less scroll).

### Sound-off design rules

- **Critical info also in on-screen text** — captions, supers, key takeaway text
- **Visual narrative carries the story** — even without sound, the video should make sense
- **Captions burnt in** for social short-form (TikTok native auto-captions can be inaccurate; manual captions safer)
- **On-screen text style consistent with brand** — same typography as the rest of brand
- **Captions readable on mobile** — sans-serif, bold, high contrast against background

### Sound-on layered experience

- **Sound adds, doesn't replace** — sound design should enhance the silent narrative, not be required for comprehension
- **VO + music + SFX layered** for engaged viewers; visual + text for muted viewers

---

## Format-tagged sections

### Short-form video

**TikTok, Instagram Reels, YouTube Shorts, LinkedIn vertical video.**

| Constraint | Value |
|---|---|
| Aspect ratio | 9:16 vertical always |
| Duration | 15–90 sec; 30–45 sec sweet spot |
| Sound default | OFF (~50% muted) |
| Frame rate | 30fps (standard); 60fps for action |

**Production rules**:

- **Three signals firing in 0–3 sec**: pattern-interrupt visual + spoken hook + on-screen text
- **Sound-off friendly**: on-screen text carries the hook; captions throughout
- **Cover frame designed**: high-contrast moment with text from hook
- **Verbal CTA in last 2 sec**: caption echoes
- **Cut frequency**: every 1–3 sec for high-energy; every 3–5 sec for educational
- **Trending sound** (TikTok): if used, used early in trend cycle; forced trends backfire
- **Caption style**: word-by-word reveal native to TikTok; sentence-block on Reels / Shorts

**Visual style choices**:

- Face-led (founder, talent, customer) — humans outperform abstract on social
- Demo-led (product in use)
- Screen-recorded (UI walkthroughs, design process)
- B-roll heavy (cinematic establishing shots)
- Typography-led (kinetic text without faces)
- Mixed (talking head + B-roll + on-screen text)

### Long-form video

**YouTube long-form, LinkedIn native video >3 min, brand films, explainer videos.**

| Constraint | Value |
|---|---|
| Aspect ratio | 16:9 (YouTube); 1:1 or 4:5 for in-feed autoplay |
| Duration | 3–15 min (YouTube sweet spot); 1–3 min (LinkedIn); 60–120 sec (brand film); 30s–3 min (explainer) |
| Sound default | ON (YouTube — user clicks to play); OFF (LinkedIn autoplay) |
| Frame rate | 30 / 60fps |

**Production rules**:

- **First 30 sec hooks** — YouTube intro must earn the watch-through; LinkedIn autoplay needs visual hook in first 3 sec
- **Title + thumbnail = the hook** for YouTube (search-driven discovery)
- **Captions provided** (track-based for YouTube; burnt-in for LinkedIn autoplay)
- **Production polish**: viewers expect higher production value than short-form social
- **Pacing varies**: hook fast, payload medium, narrative beats can hold long takes

**Brand film specifics**:

- 60–120 sec typical; longer for premium / cinematic
- Music-led (often), sometimes pure VO
- Cinematic aesthetics (shallow depth, color-graded, sound-designed)
- Single emotional arc — start, shift, land
- Brand reveal often delayed until the close (last 5–10 sec)

**Explainer specifics**:

- 60–180 sec typical
- Often kinetic typography + simple motion graphics (lower production cost; faster turnaround)
- Clear narrative: problem → solution → how it works → CTA
- VO + on-screen reinforcement; sometimes VO-only with text supers

### GIF / animated header

**Email animated header, social GIF post, web micro-animation.**

| Constraint | Value |
|---|---|
| Format | GIF or animated WebP / APNG |
| Duration | 2–5 sec loop |
| File size | <500KB for email header; <2MB for social |
| Frame rate | 12–24fps (GIFs scale with FPS) |
| Sound | None (GIFs are silent) |

**Production rules**:

- **Subtle motion** outperforms aggressive motion (parallax, light text reveal, gentle camera move)
- **Loop seamlessly** — start and end frames match (or fade-in / fade-out built in)
- **File size discipline** — GIFs balloon fast; optimise frame count and color palette
- **Designed for muted viewing** — GIFs have no audio; all communication is visual
- **Web alternatives**: APNG (better quality), WebP (smaller files), Lottie (vector, smallest)

### Motion graphics

**Kinetic typography, animated infographics, explainer animation, UI mock-up motion.**

| Constraint | Value |
|---|---|
| Format | MP4 / MOV (rendered), Lottie (vector for web), GIF (web) |
| Duration | Varies — micro-animations (1–3s), explainers (30s–2 min), title sequences (5–15s) |
| Aspect ratio | Format-dependent |

**Production rules**:

- **Easing on everything** — linear motion looks robotic
- **Text reveals**: typewriter / fade-in / slide-in — match brand register
- **Anticipation + follow-through** — every motion has a setup and a settle
- **Consistent timing system** — use timing tokens (durations + easing curves from `tenant/brand/motion-tokens.md`)
- **Performance** (web): Lottie for vector motion is 10× smaller than MP4; use where format supports

### Animated banner

**HTML5 display ads with light motion.**

| Constraint | Value |
|---|---|
| Format | HTML5 (preferred) or animated GIF |
| Duration | 15 sec total animation max (most ad networks enforce) |
| Loop | 3 loops max, then static end-frame |
| File size | <150KB for HTML5; varies for GIF |
| Sound | None |

**Production rules**:

- **End frame is the CTA** — animation ends on a clear call-to-action visible without further motion
- **First 3 sec is the hook** — banner blindness is real; pattern-interrupt early
- **Subtle motion** — aggressive motion in display ads gets blocked and annoys
- **CTA button prominent** — color + position + animation cue (a subtle pulse or arrow)

### Animated logo / ident

**Brand intro at start of video, lockup animation, sonic logo paired with motion.**

| Constraint | Value |
|---|---|
| Duration | 1–3 sec; sometimes up to 5 sec for cinematic brand idents |
| Format | MP4 / MOV; alpha channel preferred for compositing |
| Sound | Often paired with sonic logo |

**Production rules**:

- **Brand-defining** — this is the audience's first impression of the brand in motion
- **Once produced, used consistently** — every video starts (or ends) with the same ident
- **Sonic logo paired** — audio mark synchronised with visual mark
- **Variable durations** — 1 sec for fast-paced content, 3 sec for cinematic
- **Alpha channel** — for compositing over varied backgrounds

### Cinemagraph

**Mostly-static image with one small element in motion (a steaming coffee, a flag waving, hair moving in wind).**

| Constraint | Value |
|---|---|
| Format | Animated GIF / WebP / MP4 |
| Duration | 3–8 sec seamless loop |
| Motion area | <20% of frame typically |

**Production rules**:

- **Loop seamless** — start and end identical
- **Subtle moving element** — too much motion turns it into a video; too little turns it static
- **Foreground stable** — main subject often static; one element moves
- **Premium-coded** — cinemagraphs read as crafted, intentional, high-end

### Web hero motion

**Scroll-triggered animations, parallax, hero video, motion in landing-page heroes.**

| Constraint | Value |
|---|---|
| Format | CSS animation (lightest), Lottie (vector), MP4 background video (heavier) |
| Duration | Often looping (background video) or scroll-progress-driven |
| File size | <2MB for MP4 hero video; <100KB for Lottie |

**Production rules**:

- **Respect prefers-reduced-motion** — provide static fallback
- **Performance critical** — heavy hero motion kills page-speed scores
- **Subtle outperforms aggressive** — too much motion distracts from the headline and CTA
- **Sound off** — never autoplay sound on web
- **Mobile-friendly** — hero video that's beautiful on desktop may be heavy on mobile; consider static mobile fallback

### Presentation slide transitions

Light motion — handled by Static Designer (slides are static; transitions are a thin overlay).

**Transition discipline for slides**:

- **Default**: no transition (instant cut between slides)
- **Acceptable**: subtle fade / push for section breaks
- **Avoid**: 3D rotations, dramatic wipes, distracting transition effects
- **Builds within a slide**: progressive reveal of bullet points or chart elements — purposeful, subtle, eased

---

## Common motion-design AI tells

Patterns that signal AI-generated motion design (Runway / Sora / Pika / Stable Video).

| Tell | What to look for | Repair |
|---|---|---|
| **Janky physics** | Objects don't move with weight or momentum; floaty motion | Reroll with explicit physics direction; or composite hand-keyed motion |
| **Inconsistent identity** | Subject's face / clothing shifts between frames | Reroll; or composite a single hero shot with motion graphics |
| **Limb confusion** | Arms / legs that bend wrong, appear / disappear | Reroll with simpler motion; or use stock footage |
| **Background drift** | Environment morphs during motion | Anchor with a single locked-off shot; reroll with stronger spatial prompts |
| **Smooth-but-wrong motion** | Too-perfect interpolation that looks "floaty" / dream-like | Add motion blur in post; or composite with real footage |
| **Cuts that don't match** | AI generation series doesn't cut together cleanly | Hand-edit transitions; or generate as one continuous take if tool supports |
| **Lip-sync failure** | If using AI lip-sync, mouth shapes don't match audio precisely | Use a different AI lip-sync tool (HeyGen, Synthesia) or accept slight mismatch |
| **Detail drop in motion** | Subject loses detail as it moves; resolution / sharpness drops | Reroll with higher quality settings; or upscale with VFX |
| **Generic "cinematic" aesthetic** | Looks like every AI-generated brand film — slow drift, anamorphic lens, vague mood | Re-prompt with specific style reference (named cinematographer, named film, specific camera) |

### AI-motion production discipline

- **AI generates raw footage**; human edits and polishes
- **Composite AI motion with brand-asset motion graphics** — pure AI rarely ships unedited
- **Generate multiple takes** — pick the best, never settle for the first
- **Hand-key the critical moments** — hero shots and CTA frames often benefit from non-AI motion design

---

## Cross-references

- **Shared visual fundamentals**: [visual-craft-shared.md](visual-craft-shared.md)
- **Static-specific principles**: [static-design.md](static-design.md)
- **Channel grammar (per-format aspect ratios, duration, sound defaults)**: [channel-grammar.md](channel-grammar.md)
- **Platform-native social rules (TikTok / Reels / Shorts)**: [platform-native-social.md](platform-native-social.md)
- **Asset architecture (short-form video architecture)**: [asset-architecture-patterns.md](asset-architecture-patterns.md#short-form-video-architecture)
- **Sub-edit Layer 3 presentation (spoken-friendliness for VO scripts)**: [sub-edit-pipeline.md#layer-3-presentation](sub-edit-pipeline.md#layer-3-presentation)
- **Motion tokens source**: `tenant/brand/motion-tokens.md` (if present)
