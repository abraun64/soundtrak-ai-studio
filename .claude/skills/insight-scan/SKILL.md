---
name: insight-scan
description: |
  The disciplined multi-source web sweep that feeds the Insight Brief. Invoked by the
  Insights Manager (or CM) in Phase 1, scoped to a target segment + objective, it sweeps
  cohort sentiment (Reddit / public social), forums + business groups, B2B trade media,
  and authoritative research (WEF / PwC / IPSOS / Gartner / …) — citing the tenant research
  library first before re-fetching — and returns numbered, source-tagged insight candidates
  ready to triage (insight vs wallpaper) into the Insight Brief.

  TRIGGER when: the Insights Manager needs to gather audience/market signals for a campaign
  (Phase 1), or to refresh the tenant audience-truths / research library.

  DO NOT TRIGGER for: competitor/market structure (use company-intelligence), audience
  segmentation (use segmentation-strategy), or post-campaign performance (forensic analyst).
---

# Insight Scan

A **scoped, evidence-first** sweep — you are not surveying the internet, you are hunting the **tension** that serves *this objective* for *this segment*. Run it per target segment.

## Inputs
- The **target segment** (+ its segment-map slice) and the **objective + primary KPI** (the anchor).
- The **shared research library** (`tenant/research-library/INDEX.md`) — read FIRST, filtered to this tenant's **vertical + `universal`** entries (it's shared across all tenants; see `research-library.md`).
- The **tenant audience-truths** (`tenant-brand/<tenant>-audience-truths.md`) — the enduring tensions to refresh against.

## The sweep — source types (tag every finding with its type + named source + date)

Two jobs: find the **human insight** (what makes them tick) *and* the **market context** (what's happening). **Lead with the human** — the human truth fuels the big idea; the market facts earn the why-now.

**For the HUMAN insight (the tick — identity · motivation · fear · aspiration):**
1. **Shared research library (cite-first, filtered).** Read the INDEX filtered to `vertical = <this tenant's vertical>` OR `vertical = universal`; **prioritise `layer = human-behaviour`** entries. Cite lodged papers — don't re-fetch.
2. **Human-behaviour research** — **psychographic / values** studies (what this audience wants from work + life; generational values — IPSOS, Pew, Gallup, Edelman) · **behavioural science** (identity, status, loss-aversion, belonging, applied to the segment) · **qualitative / ethnographic** academic studies on the segment's *motivation + identity* (the reasons behind the reasons). The richest human-insight source, and mostly `WebFetch`-accessible.
3. **Cohort sentiment — raw voice (READ the store: `campaigns/<slug>/research/raw-voice.md`)** — where the cohort actually talks: frustration, aspiration, identity, the *exact words* they use. **You (the scan) READ the raw-voice store; you do NOT drive the browser** — the **main session (CM) populates the store** via Claude-in-Chrome on reachable forums + the operator-paste lane (see the discipline block + `research/raw-voice.md`). ⚠️ **Connector boundary**: the Claude-in-Chrome connector **hard-blocks Reddit + Facebook** ("site not allowed"), so the biggest pools come via **operator-paste**; **niche public forums ARE reachable** (e.g. **Indie Hackers** for founders — confirmed, thread-level). If the store is empty/thin, **fall back to #2** (a stronger base than scraped anecdote) and **flag the gap** in §3 — never invent voice.

**For the MARKET context (the why-now):**
4. **B2B trade media** — the trade publications specific to the audience's industry; the category's current preoccupations. Named publication + article + date.
5. **Authoritative research** — demographics + trend + macro papers: **WEF**, consultancies (**PwC**, McKinsey, Deloitte, Bain), research firms (**Gartner**, Forrester, Nielsen), government data.

**For ROUTES TO MARKET (every GTM route marketing can influence — feeds Insight Brief §2; budget- AND time-aware):**
6. **Reachability + GTM-route signals** — not just *where the segment consumes media* but *every route marketing can influence to reach it*, scoped to budget + deadline:
   - **Media** — trade/industry media it reads · influencers/creators it follows (named, micro+macro) · mainstream media (only if budget allows paid) · owned (CRM/email/own social).
   - **Community** — the forum/Slack/Discord it gathers in (the same one the raw-voice sweep found) · industry events.
   - **Partnership / co-GTM** — **complementary, non-competing providers serving the same segment** you could co-market / co-sell / refer with (e.g. an agency to partner with on GTM · accountants/lawyers/fractional execs · martech vendors).
   - **Intermediary / gatekeeper** — orgs that *already hold the audience* and can introduce/endorse: **VCs · startup incubators/accelerators · industry associations · peer networks · co-working hubs · advisor networks**.
   - **Advocacy** — existing happy clients (referral/intro).
   For each: named + specific · type · why-it-works (evidence / the relationship) · **mainstream vs niche** · **time-to-stand-up** (fast / slow-build / existing-relationship-only). **Two hard filters: budget AND deadline** — a paid-zero campaign surfaces owned/earned/community/partnership routes (not a media buy); a short-deadline campaign rules out slow-build partnerships unless the relationship already exists. **The lower the budget, the harder you hunt partnership + intermediary + advocacy routes** — borrowed reach + trust beats bought reach.

Tooling: `WebSearch` + `WebFetch` (+ **Claude-in-Chrome** for raw social voice). Search with the segment's real language, not generic terms. (Paid/proprietary feeds can be wired via the integrations layer later.)

## Raw-voice capture (Claude-in-Chrome) — discipline

**Who runs it**: the **main session (CM)** — it holds the connected browser + the Claude-in-Chrome MCP. The capture writes verbatim into the campaign **raw-voice store** (`campaigns/<slug>/research/raw-voice.md`); the Insights Manager subagent then **reads the store** (subagents don't reliably have the browser, so they never drive it). Two lanes, both write the store: **Lane A — Chrome** (reachable forums), **Lane B — operator-paste** (connector-blocked: Reddit/FB). Capture the cohort's *register* — the actual words — never build a dossier on people.

**How (Lane A — Chrome, run from the main session)**: confirm a browser is connected (`list_connected_browsers`) → `WebSearch` to find a **reachable** public community → `navigate` to the FORUM, then **`navigate` to a specific thread URL** (the SPA often won't follow an in-page click — grab the thread's `/post/...` href via `javascript_tool` and navigate to it directly) → `get_page_text` → lift short verbatim into the store with provenance. e.g. **Soundtrak founders → Indie Hackers** (`/post/...` threads on *can't-tell-what-marketing-works / ChatGPT-slop / build-it-myself*); **Acme Co teachers → r/Teachers is BLOCKED** → Lane B. **Lane B — operator-paste**: emit a precise request (named source + what to grab + the store path) → operator pastes public excerpts into `research/raw-voice.md`.

**Hard rules (privacy + copyright + safety)**:
- **Public sources only.** Public subreddits / open forums. **Do NOT** log in, accept terms, or join groups to reach gated content; **skip** anything behind a login (most Facebook groups). If a page needs auth, it's out of scope — note it, move on.
- **Capture voice, not identities.** No usernames, no handles, no profile details, no names — strip them. Never compile or cross-reference personal information about any individual. You're after the *phrasing and the feeling*, not who said it.
- **Short verbatim only**, quotation-marked, tagged `[platform · public thread · date]` (link the thread, not the person). A handful of short representative phrases — never reproduce whole posts/threads. This is **internal research, never published** (paraphrase for the Brief if a quote is too identifying or too long).
- **Never fabricate.** No browser / nothing found → say so and fall back to source #2. A made-up "quote" is a fireable error.

If the browser is connected, raw voice **promotes** a human insight from "research-backed" to "research-backed + in their own words" — the version that makes copy sing. Tag these candidates `raw-voice` so the Insights Manager can mark which insights now carry verbatim.

## Evidence rule (non-negotiable)
**No source, no candidate.** Every candidate carries: source type · named source · date · the specific data point or quote. A candidate you can't source is killed.

## Output — numbered candidates, ready to triage
Return a numbered list. Each candidate:
- **#N** — the candidate insight (one sentence: audience truth + tension).
- **segment** it serves.
- **evidence** — type · named source · date · data point/quote.
- a one-line **so-what** toward the objective.

The Insights Manager then applies the bar (**human truth, not just a market fact** · non-obvious · tension · scoped · evidenced) and triages keep / reshape / **kill (with reason)** into the Insight Brief §1 (human insight + market context, per segment) + §3 (cut).

**Also return, per segment, the routes to market** (from source #6) — every GTM route marketing can influence (media + community + partnership + intermediary + advocacy), mainstream + niche, each with type · why-it-works · budget-fit · **time-to-impact** · confidence. These become Insight Brief **§2** and inform the CD's rollout (intelligence, not the asset mix). Apply both filters — budget AND deadline.

## The bar (human insight > market insight; ≠ wallpaper) — surfaced here so the scan aims right
Aim above all for the **human truth** — how the audience *thinks/feels/behaves* (identity · motivation · fear · aspiration). A market fact (trend headline, demographic platitude, bare stat) is **context, not the insight** — surface it only paired with the human truth it implies, else expect it killed. Every candidate must be **non-obvious · create a resolvable tension · tied to this segment + objective · evidenced**.

## Cross-references
`insights-manager/AGENT.md` · `insight-brief.md` (the artifact this feeds) · `company-intelligence` (competitor/market — complementary) · `segmentation-strategy` (who the audience is — complementary).
