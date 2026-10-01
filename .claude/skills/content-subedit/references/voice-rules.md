# Soundtrak Voice — Sub-Edit Rules

These are the rules applied on every sub-edit pass. Run them in order.
Flag every violation. Fix every violation before saving the file.

---

## RULE 1 — EM-DASHES (near-zero)

Default: **no em-dashes (—).** Replace every one with a comma where the sentence breathes.
*Calibration (the operator's lived edits, 2026-06):* keep an em-dash **only** where a comma would
create genuine ambiguity, or where the structural pause is genuinely load-bearing. In practice
almost all body em-dashes become commas — a kept em-dash should be rare and defensible.

**Fix:** Replace with a comma as the default. Use a regular hyphen only for a true compound word.
Flag any em-dash you keep, with the one-line reason it's load-bearing (in the Step 5 report).

---

## RULE 2 — BANNED WORDS AND PHRASES

Flag any occurrence of the following. Delete or rephrase — never keep.

**Run this as a literal, deterministic find-check, not a vibe check (reinforced 2026-07-15).** Search the copy for each banned word below in turn — an explicit find over the exact string, one word at a time. Do not skim and trust that it "reads clean." "genuinely" slipped through into the Ed 19 draft twice and Ed 20 once despite this rule existing, because the pass was done by feel. Scan every pass, every word, including short common words like "genuinely" and "quietly" that a vibe read glides straight over.

### AI vocabulary
delve, delving, tapestry, intricate, intricacies, interplay, foster, fostering,
garner, garnering, underscore, underscores, pivotal, showcase, enduring, realm,
multifaceted, robust, seamless, seamlessly, holistic, leverage (as a verb),
unlock, unlocking, transformative, transformation (used loosely), game-changer,
game-changing, synergy, synergies, ecosystem (unless a literal biological or
technical ecosystem), curate, curated (unless actual curation is being described),
navigate (as a metaphor — "navigating challenges", "navigate the landscape")

### Banned words added by the operator
genuinely, honestly (when used as a filler — "honestly, this is..."), quietly (as an empty intensifier — "quietly building", "quietly changed everything")

### Padding phrases
"It's worth noting that", "It's important to remember that",
"Highlighting the importance of", "Plays a crucial role in",
"This further underscores", "In today's rapidly evolving landscape",
"In an ever-changing world", "At the end of the day",
"It goes without saying", "Needless to say", "First and foremost",
"I wanted to reach out", "Hope this finds you well",
"Look forward to connecting", "Hope to hear from you"

### Structural AI tells
- "Not only... but also..." — delete the whole construction
- "From X to Y" used vaguely ("from ancient wisdom to modern innovation")
- The automatic rule of three ("speed, efficiency, and innovation") — only when there are genuinely three distinct things
- "In conclusion...", "To summarize...", "Overall..." — if the point has been made, stop writing
- "Let's walk through...", "Below is a detailed overview...", "In this section we will explore..." — meta-commentary; just say the thing
- "It is important to note that..." — if it's important, it doesn't need to announce itself

---

## RULE 3 — PUNCHY FRAGMENT PATTERN

Two distinct AI rhythm tells. Both must be flagged.

**3a — The reframe pair:**
- "Not X. Not Y."
- "That's not X. That's Y."
- "Most X are Y. Yours is Z."
- Any pair where the second sentence exists solely to reframe the first as a dramatic standalone conclusion.

**3b — The staccato parallel series:**
Three or more consecutive short sentences (under ~50 characters each) built on the
same grammatical pattern. Classic form: "Same X. Same Y. Same Z. Different outcome."
Also flagged: "No X. No Y. No Z." / "More X. Less Y." repeated three or more times.
This pattern creates fake drama through repetition rather than through an actual idea.

**Limit (calibrated to the operator's lived edits, 2026-06 — the short sentence is a deliberate Soundtrak device, not a banned tell):**
- The short-sentence / reframe technique (3a) is **permitted but rare: one per piece, two absolute max**, and only if the two serve **different argumentative moments**. It lands precisely *because* it's rare — at 3+ it becomes a mannerism and loses all force. This applies across forms (LinkedIn and Substack alike).
- The **3b mechanical staccato series** (3+ identical-pattern fragments in a row, "Same X. Same Y. Same Z.") is still **never permitted** — a single such series already counts as the overuse the rule guards against.
- Named §2 voice devices (e.g. the four-word declarative "That's the Trailer. This is the Playbook.") count toward the 1-2 budget but are not auto-stripped — they're the device working as intended.

**Fix:** Absorb the contrast into a single longer sentence, then let a short sentence
land the point. Pattern: longer setup → short landing.

Examples:
- Before (3a): "Structure and flexibility aren't opposites. Agile makes them the same system."
- After: "Running at two speeds means structure and flexibility stop being opposites, with the sprint handling adaptation and the strategy holding direction."

- Before (3b): "Same broadcasting window. Same advertising inventory. Same viewers. Different outcome."
- After: "It ran in the same advertising break as a dozen other spots, to the same audience, with the same reach."

---

## RULE 4 — RESTATEMENT

Flag any sentence that restates or summarises the sentence immediately before it
without adding new information.

**Test:** Could you delete the second sentence without losing any meaning not already
present in the first? If yes, delete it.

**Common forms:**
- "X is important. Without X, Y suffers." (if "Y suffers" was already implied)
- "We built four newsletters. These newsletters grew our subscriber base." (when the
  implication was obvious)

**Fix:** Delete the restating sentence. If both halves carry distinct information,
merge them into one sentence.

---

## RULE 5 — RECAP CLOSING

Flag any final paragraph (last paragraph of the piece) that summarises or recaps
the argument rather than ending on the point itself.

**Test:** Does the closing paragraph restate the key ideas from earlier in the piece?
If yes, it is a recap and must be cut or rewritten.

**What the closing should do instead:**
- Land on the sharpest version of the point
- End on an image or implication that makes the reader sit with it
- Or end on a question worth sitting with (LinkedIn only — Substack earns a statement)
- If the case has been made, stop writing

**What it should never do:**
- Restate the article's argument in summary form
- Use "In conclusion...", "To summarise...", or any variant
- Repeat the article's structure as a final beat ("strategy for direction, sprints for momentum")

**5a — The lyrical-image closer (added 2026-10-02, calibrated from eds 20/22/26).** A poetic image standing in for the point rather than the point itself: *"a busy quarter with good lighting"*, *"die halfway up the hill"*, *"Attention has become cheap. Belief has become the scarce thing."* It feels like a strong ending; it is decoration. Flag it. The author prefers a plain closing statement, or a single explicitly-quoted aphorism in his own voice (wrapped in quotation marks).

**5b — The "two-versions-of-me" callback close (added 2026-10-02, from ed 24).** The ending loops back to the opening scene via a before/after of the narrator: *"The version of me that walked into the room saw… the version that walked out saw…"*, *"the version of me that started… the version that finished…"*. A dramatised recap. Flag and cut to the plain point. (See also Rule 10.)

---

## RULE 6 — THE HOLLOW CONTRAST (added 2026-06-30)

AI borrows the *rhythm* of an insight to stand in for the insight. Classic form, usually three sentences:

> "A lot of leaders talk about accountability. Fewer build the structures that make it real. The difference shows up fast."

Two linked moves, flag either, flag both:

**6a — The "many say, few do" antithesis.** A balanced contrast between what "a lot of / most" people SAY and what "fewer / the few" actually DO. It reads as insight but is empty:
- **Portable** — swap the topic noun (accountability → culture → focus → strategy → customer-centric) and it still works unchanged. A real observation is welded to its subject; a template floats free.
- **Fake data** — "a lot of" / "fewer" assert a distribution with nothing measured behind it.
- **Flattery** — it sorts the reader into "the few" for free.
- **Truism** — "talking is easier than doing" is true of everything.

**6b — The vague significance kicker.** A short declarative that claims the contrast matters without saying how: "The difference shows up fast." / "That gap is everything." / "It changes everything." / "That's where it counts." A consequence with the consequence removed.

**Two tests:**
- *Portability (6a):* can you swap the topic noun and keep the sentence? If yes, it is a template, not a thought.
- *Specificity (6b):* does the kicker name an actual consequence — what shows up, where, how much? If not, it is empty.

**Fix:** name the real thing and the real difference, with a concrete example or number. *"A lot of leaders talk about accountability. Fewer build the structures that make it real. The difference shows up fast."* → *"Most leadership teams have 'accountability' on a slide and nothing behind it: no owner per outcome, no date, no consequence when it slips. The teams that add those three close issues in days; the rest relitigate them next meeting."* If you cannot make it specific, the sentence was carrying nothing — cut it.

**Limit: zero.** This pattern is never the strongest version of the point. (The setup half is allowed *only* when the very next sentences cash it out into concrete specifics and there is no vague kicker.)

---

## RULE 7 — UNVERIFIED / MIS-ATTRIBUTED STATISTIC (added 2026-07-15)

A factual-accuracy safeguard, not a taste rule. Flag any statistic, percentage, or hard number that:
- **lacks a named, verifiable source** — no report, no author, no year ("studies show 70% of buyers..."), or
- **is attributed to a source that may not contain it** — a real-sounding number hung on a real-sounding report the writer never actually checked.

AI drafts fabricate plausible figures and attach credible attributions to them. On Ed 20, the draft carried a fabricated "44%" and "9% from websites" attributed to *McKinsey State of the Consumer 2026* — neither number was in that report. It read as authoritative and was caught only by manual verification against the primary source.

**Test:** For every number in the copy, ask — is there a named source (who, what report, what year)? Has that number been confirmed present in the actual primary source, not a summary of it? If either answer is no, flag it.

**Fix:** Do not silently keep or reword the number. Flag it back to the writer for verification against the primary source. If it cannot be verified, it must be cut or replaced with a figure that can. Never let an unverifiable statistic ship.

**Limit: zero unverifiable statistics.** A sub-edit cannot itself verify a claim against the web, so its job is to **catch and flag** every number that lacks a checkable source — never to pass it through on the assumption someone else checked.

---

## RULE 8 — REGISTER SLANG / OFF-VOICE IDIOM (added 2026-09-14)

the operator's register is **dry Australian plain-speak**: if you'd say it out loud to a CEO across a table, use it; if you wouldn't, cut it. Two off-register habits slip past Rules 1–7 because they are neither a banned AI word nor a statistical pattern, so only a register read catches them. Run this as a literal read, like Rule 2.

**8a — Casual Americanisms / film / startup slang.** Flag and replace with plain English. Starter list (scan each; extend as new ones surface):
took a beat, a beat (meaning "a moment"), dialled in / dialed in, no-brainer, crushing it / crush it, nail it, move the needle, circle back, double down, deep dive, level up, unpack (as a metaphor), lean in, table stakes, secret sauce, drink the Kool-Aid, game-changer, low-key, for sure, gonna, wanna.
US terms and spelling — use the Australian word: soccer → footy (ed 20, "soccer field" → "footy field"), sidewalk → footpath, vacation → holiday, "math" → "maths", -ize → -ise, color → colour. The author writes to an Australian ear; a US term is off-register even when it is not slang.

**8b — Metaphor-dressing where instruction belongs.** A plain statement dressed as a metaphor the reader has to decode first: "a content problem wearing a volume problem's clothes", "wearing the costume of a strategy problem", "a wolf in X's clothing". If a sentence's job is to say what is true or what to do, say it plainly. (This extends the §2 / Rule-2 example "a measurement problem wearing the costume of a strategy problem".)

**Test:** read the sentence aloud in the operator's voice. If it sounds like a US podcast host or a movie voiceover, it is off-register. For 8b: does the metaphor have to be decoded before it can be used? If yes, replace it with the plain statement.

**Fix:** replace with the plain, in-voice phrasing. ("It took a beat" → "It took me a moment / longer than it should have"; "wearing a volume problem's clothes" → "a content problem, and cutting the frequency will not touch it".)

**Limit: zero.** Ed 24 shipped *"It took a beat to see it the other way around"* (film slang) and *"a content problem wearing a volume problem's clothes"* (metaphor-dressing, already banned by the §2 example) past both the linter and the banned-word scan; the operator caught them on read. This rule names them so the pass does — the linter counts, the banned list enumerates known words, and register slang falls in the gap between the two. **Since 2026-10-02 `slop_lint.py` checks the 8a and 8b phrases
automatically (SYS-156).** The US spellings above are still a manual read, and the list there grows when this one does.

---

## RULE 9 — SELF-AWARE EDITORIAL TICS & STAGED PUSHBACK (added 2026-09-22)

A cluster of essayistic tics that make copy sound like an AI performing "smart writing" rather than the operator making a point. None is a banned AI word or a statistic, so they slip past Rules 1–8. Run this as a literal read, like Rules 2 and 8. All four sub-types share one fault: they add editorial *texture* in place of a thought.

**9a — Staged pushback / imagined interlocutor.** A sentence that invents a reader or a "smart" objector so the writer can look even-handed, then flatters them. the operator's flag: *"A sharp operator will push back here."* Also: "You might be thinking…", "Here's where a sceptic pushes back", "The obvious objection is…", "A good marketer will already be asking…". (Distinct from a genuine **§ 'the fair objection'** section, which states the real counter-argument plainly and answers it — this tic is the *glib gesture* at one, usually flattering "the sharp / smart" reader.)

**9b — Told emotion / editorial aside.** Tacking on how the reader is supposed to feel, or how hard/uncomfortable the point is, instead of letting the point do it. the operator's flag: *"and it is uncomfortable."* Also: "and that's the hard part", "which is harder than it sounds", "and that stings". Say the thing; do not narrate its emotional weight.

**9c — Tired approval idioms.** Stock phrases that gesture at value without naming it. the operator's flag: *"that earns its keep."* Also: "punches above its weight", "does the heavy lifting", "pulls its weight", "worth its salt".

**9d — Vague self-congratulatory verbs / comparatives.** A verb or comparative that claims an effect without a concrete one. the operator's flags: *"has sharpened it"*, *"a louder"* (as in "a louder version of the same problem"). Also: "has only sharpened", "throws it into sharp relief", "a quieter / bigger / louder version of". Name what actually changed, or cut it.

**9e — Evaluative-adjective inflation (added 2026-10-02).** Praise-adjectives and intensifiers bolted onto a plain noun to make it feel bigger: *"the update was beautiful"*, *"the slides were sharp"*, *"genuinely credible"* → *"credible"*, *"a comfortable habit"*. The author strips the modifier and lets the noun stand. Flag an evaluative adjective/adverb that adds colour, not information. (Overlaps Rule 2's "genuinely", which still slips in — scan for it literally.)

**Test:** does the sentence add an idea, or only editorial colour (a staged objector, a told feeling, a stock idiom, a vague comparative, a praise-adjective)? If only colour, cut it or replace it with the plain point.

**Fix:** delete the tic and state the point directly. *"A sharp operator will push back here, and it is uncomfortable"* → the actual objection, stated plainly, then answered. *"content that earns its keep"* → "content a competitor could not rebuild in a week". *"AI has sharpened it"* → what specifically changed.

**Limit: zero.** These read as polish and are pure texture; the strongest version of the point never needs them.
`slop_lint.py` checks the 9a-9d phrases automatically (SYS-156). 9e is a judgement call and stays a manual read.

---

## RULE 10 — FABRICATED SCENE, INTERIORITY & ROLE (added 2026-10-02)

The single most frequent thing the operator strips when he edits a draft (eds 20, 21, 22, 24, 26). AI manufactures a *story* around the point — a scene, a feeling, an inflated role — that the source material never supplied. It is not a word tic; it is invented fact and invented drama. Flag any of three sub-types and cut to the plain account.

**10a — Dramatised scene / staging.** A scene the author never described, complete with setting and reaction shots: *"I have sat in a lot of quarterly reviews where the marketing update was beautiful. The slides were sharp… The room nodded along. Then I asked the question that tends to change the temperature in a meeting"* (ed 22); *"I sat in a marketing review looking at a chart I did not like"* (ed 24). Fix: state what actually happened, plainly, with only the facts the author gave.

**10b — False interiority / realisation arc.** The draft narrates the author's inner journey — a first reaction, a turn, a confession: *"My first reaction was that we had a problem… it took a beat to see it the other way around"* (ed 24); *"For a long time I read that as a volume problem… I was wrong"* (ed 26). The author does not perform his own epiphany. Fix: cut the arc; keep the conclusion.

**10c — Overstated role / invented case study.** The draft inflates the author's seniority, scope or ownership, or invents a case study starring him: *"…all reported into one P&L. **Mine.** I owned the whole arc"* → *"I influenced a big chunk of the journey"* (ed 21); a fabricated Netwealth "familiarity went 12% → 56%" chasm story dropped into ed 26 and cut wholesale. Downgrade claims of authority to what the author actually says ("I ran…", "I influenced…", "I had visibility over…"), and never invent an anecdote, a result or a number on his behalf. (Where the invention is a *statistic*, Rule 7 also applies.)

**Test:** for every scene, feeling, or claim of the author's role — did the source material actually supply it? If the draft added the staging, the epiphany, or the seniority, it is fabrication. Would the author recognise this as something he told you, or something you wrote for him?

**Fix:** replace with the plain factual account in the author's own frame. Keep the point; delete the theatre.

**Limit: zero invented scene, interiority or role.** This is a truth rule, not a taste rule — like Rule 7, the cost of a miss is the author's credibility, not just his voice.

**Why this one can't be linted (read this before trusting a green run).** Rule 10 is **semantic, not lexical.** A new draft never reuses the old wording — it invents a *fresh* scene ("I remember standing at the whiteboard when the CFO leaned over…"), a fresh epiphany, a fresh inflated title. So a regex catches only the exact phrases we have already seen, and a counting check sees nothing (it isn't a statistical property). `slop_lint.py` carries a few known-phrase tripwires ("my first reaction was", "the version of me that", "nodded along") as cheap belt-and-braces, but **they are a sliver of the rule, not the rule.** Do not read a clean `slop_lint` run as Rule 10 being clear.

**Verification protocol — PRODUCE this, don't just assert it (the forcing function).** Because the read-pass is exactly the step that let these through before, Rule 10 is not satisfied by "I read it and it's fine." The pass must output a **source-trace**: enumerate every one of these in the draft and, for each, cite where it came from or cut it —
1. each **scene** (a meeting, a room, a place, a moment with any setting or reaction);
2. each **stated feeling or realisation** ("my first reaction…", "I was wrong", "it felt…");
3. each **claim about the author's role, seniority, scope or ownership**;
4. each **result, number or named anecdote attributed to the author**.
For each: *source = the operator's brief / an operator-supplied doc / a quote the operator gave* → keep. *source = the model wrote it* → **UNTRACED, cut or rewrite to the plain fact.** If the trace table is empty of untraced items, the rule is clear; if you did not build the table, the rule was not run. The table format is in `SKILL.md` Step 5, and `source_trace_check.py` fails a report that lacks it or keeps an untraced row (SYS-173). The other half of the fix is upstream: drafters follow `references/author-facts.md` so the fabrication is not written in the first place.

---

## HOW TO RUN THE SUB-EDIT

1. Read the full content of the file.
2. Work through Rules 1–10 in order. For each rule, list every violation found.
3. If violations exist, fix them in the content.
4. Check that fixes haven't introduced new violations.
5. Report: number of violations found per rule, what was changed, and the corrected text.
6. If the content was generated via a Python script, update the script with the corrected text
   and re-run it to overwrite both _Original and _Edit files.

---

## CHANNEL-SPECIFIC SUMMARY

| Rule | Substack (long) | LinkedIn (medium) |
|------|----------------|-------------------|
| Em-dashes | Near-zero (keep rare load-bearing) | Near-zero (keep rare load-bearing) |
| Banned words | Zero | Zero |
| Punchy / short-sentence technique | 1 per piece (2 max) | 1 per piece (2 max) |
| Mechanical staccato series (3b) | Never | Never |
| Restatements | Zero | Zero |
| Recap closing | Not permitted | Not permitted |
| Hollow contrast (many-say-few-do + kicker) | Zero | Zero |
| Unverified / mis-attributed statistic | Zero (flag every one) | Zero (flag every one) |
| Register slang / off-voice idiom (Rule 8) | Zero | Zero |
| Editorial tics / staged pushback (Rule 9) | Zero | Zero |
| Fabricated scene / interiority / role (Rule 10) | Zero (truth rule) | Zero (truth rule) |
