# Insight Brief — schema

**Spec version**: v3 · 2026-06-23 (§2 broadened from "channel routes" to **routes to market** — channels *and* GTM partnerships/intermediaries — with a budget AND time-to-impact filter). The Phase-1 artifact authored by the **Insights Manager** (`.claude/agents/insights-manager/AGENT.md`). It fuels the big idea (feeds the CD's concept §2), recommends the **budget- and time-aware routes to market** for reaching each segment (§2 — media + community + partnership + intermediary + advocacy), and surfaces both on the Phase-1 Brief.

## What it is

The evidence-backed answer to *"what is impacting our target market right now that matters to this campaign?"* — **per target segment**. It turns a disciplined multi-source web sweep (`insight-scan` skill) into the **insight(s) that fuel the big idea**. It is NOT generic demographics, NOT a trend list, NOT a stat dump.

## Where it lives + when

- `campaigns/<slug>/insight-brief.md` (+ `.html`) — full research + all sources.
- Authored **after** the Brief's objective + target segment(s) are set (so the sweep is scoped to them), as part of the Phase-1 output.
- The distilled **"insights that matter"** (per segment) + the **"considered & cut"** register surface on the Phase-1 Brief (`brief.html`) above the fold; the operator's single Brief verdict approves the Brief **including** the insights (SYS-067). CM **derives the Insight Brief's approved-state from that verdict** (approved-*as-part-of*-the-Brief — no separate gate); its dashboard entry may then carry a ✅, and only then — never a standalone or pre-approval tick. A send-back scoped to the insights ("insights on segment X are off") re-dispatches just the Insights Manager, not the whole Brief.

## The insight bar — human insight > market insight (and ≠ wallpaper)

Two layers, and **the human insight is what fuels the big idea**:
- **Human insight (the headline)** — a non-obvious truth about *how the audience thinks, feels, or behaves*: their **identity, motivation, fear, aspiration**, or the tension between who they are and their situation. The *"aha"* that makes someone feel **seen** — what a big idea hooks onto. *(e.g. "a principal carries every unfilled role as private shame" — not "physics ITT is <30% of target".)*
- **Market / category insight (the context)** — what's happening in the market (shifts · data · timing). Earns the why-now and the report's content — but on its own it's category dynamics, **not a human truth**.

**Per segment, lead with the human insight and pair it with its market context** — mark which is which. Test every candidate:
- **Human** — is it about the *person* (feeling/identity/motivation), not just the market? A market fact with no human truth behind it is **context, not the insight**.
- **Non-obvious** · **Tension** (a contradiction/unmet need the campaign can resolve) · **Scoped** (this segment + objective, not generic demographics) · **Evidenced** (named source + date + data point).

Fail → kill register (§3) **with the reason**.

## Schema

### Header
Campaign · target segment(s) · date · objective + primary KPI · **budget + timeframe/KPI deadline** (the two hard filters on §2 routes — budget rules out what you can't afford, the deadline rules out routes that can't pay off in time) · one-line source-sweep summary.

### §1 — Insights that matter (BY SEGMENT — the surfaced set)
For **each** target segment (campaigns may target several), **lead with the human insight, paired with its market context** (1–3 per segment). Each:
- **Human insight (headline)** — one sentence: the audience's identity/motivation/fear/aspiration + the tension. *This is the big-idea fuel.*
- **Market context** — the market shift/data that makes it true + timely (the why-now).
- **Evidence** — named source(s) + date(s) + data point, for both layers (human-behaviour sources — values/behavioural-science/qualitative/social-voice — for the human insight; market sources for the context).
- **Why it matters** — how it serves the objective + KPI.
- **Big-idea hooks** — 1–2 creative directions the *human* insight suggests (for the CD; not finished ideas).
- **Confidence** — High / Medium (Medium ⇒ flag as **HYPOTHESIS**, same discipline as concept §2).

### §2 — Routes to market (channels & GTM partnerships — budget- AND time-aware)
For **each** target segment, where its attention lives + **every route marketing can influence to reach it** — not just media channels but the full GTM surface: **paid/owned/earned media · communities · and partnership/intermediary routes** (co-marketing, co-sell, referral, and the VCs / incubators / associations / advisors who already hold the audience). This is **intelligence that informs the CD + the Plan — NOT a prescribed asset mix** (the CD owns creative + channel selection per `feedback_brief_does_not_ask_asset_mix`; the Plan declares the assets). The operator signs it off on the Brief ("yes, that's how we reach our audience"); it positively shapes the CD's rollout.

**Think beyond "marketing channels."** A route is *anything marketing can influence to put the message in front of the segment*. The **lower the budget, the more the borrowed-audience routes matter** — you borrow someone else's reach + trust instead of buying it. Route types:
- **Media** — mainstream media · trade/industry media · influencer/creator (micro/macro) · owned (CRM/email/own social) · earned (PR).
- **Community** — the Reddit/FB/Slack/Discord/forum where they gather; industry events.
- **Partnership (co-GTM)** — co-market / co-sell / referral / white-label with **complementary, non-competing providers** who serve the same segment (e.g. an agency to partner with on GTM · accountants/lawyers/fractional execs serving the same founders · martech vendors).
- **Intermediary / gatekeeper** — an org that *already holds the audience* and can introduce/endorse: **VCs · startup incubators/accelerators · industry associations · peer networks · co-working hubs · advisor networks**. Reach is borrowed via a relationship, not bought.
- **Advocacy** — existing happy clients (referral/case-study/intro) — the cheapest, highest-trust route.

Each route carries:
- **Route** — named + specific, never a bare category ("LinkedIn — the operator's 1st-degree network" · "Startmate accelerator alumni" · "[named] media agency — co-GTM referral" · "r/Teachers" · "AFL.com.au digital").
- **Type** — one of the above (media / community / partnership / intermediary / advocacy).
- **Why this segment is here / why it works** — evidence (consumption data · where they gather · the relationship that carries it).
- **Access + budget-fit** — owned / earned / partnered / paid, and whether it fits the budget (free-organic / low-cost / needs paid spend). Paid routes on a paid-zero budget → `out-of-scope-this-budget`, noted for later.
- **Time-to-impact** — how long until this route produces a result, judged against the **campaign timeframe + KPI deadline**: **Fast** (works inside the window — owned/earned/warm/existing-relationship) · **Slow-build** (relationship/partnership that takes weeks–months to stand up) · **Existing-relationship-only** (fast *only* if the tie already exists). **A slow-build partnership cannot serve a short-deadline KPI** — flag it "for next campaign / ongoing," don't recommend it as a live route for this run.
- **Reachability confidence** — High / Medium / Hypothesis (access-dependent routes — "is the operator a member / does the relationship exist?" — are Hypothesis until verified).

Mark each route **mainstream** vs **niche**. **Two hard filters: budget AND time.** A $300 paid-zero campaign yields owned + earned + community + existing-relationship routes; a 5-week KPI rules out partnerships that take 3 months to bear fruit (unless the relationship is already in place). Don't pad — one sharp route the audience trusts that pays off in time beats five generic ones.

### §3 — Considered & cut (the kill register — restorable)
The ~top 10 candidates that did **not** make §1, **numbered**. Each: the insight (one line) · which segment · **why cut** (obvious · no tension · thin evidence · off-objective · not compliance-clearable). The operator can restore any from the Brief surface — *"restore insight #N"* → CM promotes it to §1 + re-injects to the CD.

### §4 — Source sweep (provenance)
What was swept + the key sources, by type — **cohort sentiment** (raw verbatim from the campaign **raw-voice store** `campaigns/<slug>/research/raw-voice.md` — CM populates it via Claude-in-Chrome on reachable forums [Lane A] + operator-paste for connector-blocked Reddit/FB [Lane B]; short quotes, `[platform · public thread · date]`, no usernames; if empty → **flag as a gap**) · **B2B trade media** · **authoritative research** (WEF / PwC / IPSOS / Gartner / …) · **tenant research library** (cited first, before re-fetching). Every insight in §1 + every cut in §3 traces to a source listed here. **Mark which insights carry raw verbatim (`raw-voice`) vs those resting on research only.**

### §5 — Durable-layer updates (graduate-then-cite; operator-gated at wrap)
- Proposed additions to the tenant **audience-truths** (`tenant-brand/<tenant>-audience-truths.md`) — enduring tensions validated this campaign.
- Proposed additions to the tenant **research library** (`tenant/research-library/`) — strong papers found this scan.
- Proposed updates to the tenant **segment map** (`tenant-brand/<tenant>-segments.md`) — routes to market (§2 — channels + partnerships) that proved reliable graduate as durable per-segment reachability knowledge.

### §6 — Freshness
Date + cadence: **per-campaign** (re-scanned each campaign; the durable layer refreshes from §5 at wrap).

## Operator surface (on the Phase-1 Brief)
- **"Insights that matter"** grouped by segment — decision-first, above the fold.
- **"How to reach them"** (the §2 routes to market, per segment — channels + partnerships, each budget- and time-noted) — signed off as part of the Brief.
- **"Considered & cut"** as a collapsed `<details markdown="1">` — restorable.
- A link to the full `insight-brief.html`.

## How it feeds downstream
- **CD (Phase 2)**: §1 for the selected segment(s) becomes the **evidenced input to concept §2** — the CD builds the big idea *on* it instead of inferring cold (per `concept.md` §2); **§2 routes to market inform the concept's channel/rollout thinking** — including partnership/co-GTM plays a low-budget concept can be built around (the CD still owns the final asset mix).
- **Plan (Phase 3)**: §2 routes (channels + partnerships, with their time-to-impact) are a reference when the Plan declares the actual assets + sequences the rollout against the deadline.
- **Phase 4 resonance read**: anchors to §1 — *does this asset carry the insight for its segment, or has it drifted generic?*

## Cross-references
`insights-manager/AGENT.md` · `insight-scan` skill · `brief.md` (surface sections) · `concept.md` §2 · `phase-0-tenant-baseline.md` (audience-truths + research library) · `docs/specs/_proposals/insights-manager.md` (the design).
