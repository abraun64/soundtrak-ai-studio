# Compliance Profile — Durable per-tenant regulatory record

**Spec version**: v1 · 2026-06-15 · Foundation of the three-evolutions build (governance agent + Phase 0).

The **Compliance Profile** is the durable per-tenant record of the legal / regulatory constraints a tenant's marketing must satisfy — the regulatory analog to Brand Context. It holds the two things the Governance Manager needs to do anything: **(a) the industry + jurisdiction(s) operating in**, and **(b) the company-specific rules** (approved disclaimers, prohibited claims, mandatory inclusions). Without it, the Governance Manager is an inert shell and the Stage-2b gate is a no-op.

> **⚖️ NOT LEGAL — OR COMPLIANCE — ADVICE.** The Governance Manager and this profile **raise red flags for a human to review**. They do not give legal advice, and they do not give compliance advice either. They surface *"here's a thing you should check"*, cite the rule, and suggest a fix; the operator (and their counsel) **decide**. Rules inferred by AI research are tagged `HYPOTHESIS` until confirmed by the tenant's compliance officer or counsel.

> **🔒 FUTURE-ONLY / NO-RETROFIT.** A tenant has a Compliance Profile only if one has been authored (Phase 0, or on request). **Absent a profile, every consumer below no-ops** — existing campaigns are unaffected. This artifact never retrofits onto a live campaign.

**Not to be confused with:**

| Artifact | Holds | This profile's relation |
|---|---|---|
| **Brand Context** (`tenant-brand/<tenant>.md`) | voice / visual / positioning | Profile holds *law/reg*, not taste |
| **Tenant Playbook §0** | value prop / claim map / segments | Profile holds *regulatory constraint*, not strategy |
| **Brand Manager** | brand-fit verdict | Governance Manager does the *legal/compliance* verdict — the **mandatories check migrates here** (BM keeps a fallback only where no profile exists) |
| **Substantiation register** (§4 here) | evidence backing each claim | lives inside this profile |

**Stored:**
- **Current (flat) structure**: `tenant-brand/<tenant>-compliance.md` (+ rendered `.html`)
- **Business-rooted (post-W4)**: `<business>/baseline/compliance.md`
- Markdown authoritative; HTML via `render-html`.

**Authored**: in **Phase 0** by the Governance Manager (industry research + operator/counsel input), or at a tenant's first campaign if Phase 0 hasn't run. **Stewarded by**: Governance Manager — proposes updates; **operator approves** (like Brand Context; never auto-applied). **Cited as FIXED INPUT** by: every campaign Brief (Compliance subsection) · CD trio dispatch (the `compliance-clearable` convergence filter) · Producer per-step brief (compliance slice, shift-left) · the Stage-2b governance gate (enforcement).

---

## Schema

```markdown
# Compliance Profile — <Tenant name>

**Last updated**: <date>     **Last reviewed by**: <compliance officer / counsel / Governance Manager>     **Counsel-confirmed**: <yes / partial / no — AI-drafted, pending review>
**Status**: Active / Draft / N/A (unregulated, general-commercial only)

## §0 Regulatory scope
- **Industry / category**: <e.g. financial advice, health/wellness, food retail, SaaS>
- **Jurisdiction(s)**: <countries/states the marketing reaches>
- **Applicable regimes**: <named — e.g. AFSL/ASIC (AU), FINRA/SEC (US), FCA (UK), GDPR / Privacy Act, FTC endorsement guides, ASA/advertising codes, health-claim codes>. Each: regime · what it governs · FINDING/HYPOTHESIS.
- **Regulator bodies + reference URLs**: <where the rules are published>
- **Effective dates / known upcoming changes**: <if any>

## §1 Approved disclaimers (the disclaimer library)
**One or more** operator/counsel-approved disclaimers, stored **verbatim** and reusable. CM auto-inserts the right one at the gate — **never paraphrased**. Each carries an explicit **when-to-use trigger** so the same library serves every asset type and Governance knows *when* to demand each.

| ID | Verbatim text | When to use (trigger) | Where it goes (channel / placement) | Notes |
|---|---|---|---|---|
| `gen-advice` | "<exact text>" | any asset giving general financial information | email + landing-page footer · ad fine-print | always (this tenant) |
| `past-performance` | "Past performance is not indicative of future results." | whenever a return / performance figure appears | adjacent to the figure | conditional — only if a number is shown |
| `afsl` | "<Licensee>, AFSL <number>" | all client-facing financial content | footer / sign-off | always |

Rules: (1) **list every disclaimer the tenant uses** — one or more; (2) each needs a **trigger** (the condition that requires it) so Governance demands it at the right moment and CM inserts it automatically; (3) **verbatim only** — exact legal wording, never paraphrased; (4) a disclaimer whose trigger is "always" is also a §3 mandatory.

## §2 Prohibited & restricted claims
- **Banned claims**: <claims that must never appear>
- **Restricted claims (need substantiation)**: <claim → what evidence is required → see §4>
- **Comparative-claim rules**: <when competitor comparisons are allowed + conditions>
- **Performance / guarantee language**: <e.g. "past performance is not indicative…"; no "guaranteed returns">

## §3 Mandatory inclusions (per channel / asset type)
What MUST be present for an asset to be publishable.
| Asset type / channel | Mandatory elements |
|---|---|
| Email | unsubscribe · physical address (CAN-SPAM/Spam Act) · <licence no.> |
| Landing page | privacy-policy link · <risk warning> · <licence no.> |
| Paid ad | <disclaimer> · advertiser identity |

## §4 Substantiation register
Claims the tenant makes + the evidence backing each, so Governance can verify a claim is *backed*, not just *present*.
| Claim | Evidence / source | Status (held / needed) |

## §5 IP / copyright / third-party
- **Image / font / music licensing rules**
- **Trademark usage** (own + third-party)
- **Endorsement / testimonial rules** (FTC-style disclosure; consent on file)
- **Named-works / named-person rules** (e.g. Gamma Foods tenant: no named gamma or cookbook titles in public copy — generic category language only; private 1:1 outreach + retailer names + editorial coverage are exceptions)

## §6 Privacy & data
- **PII handling** · **consent model** · **cookie / tracking disclosure** · **data-collection claims** (what you may/can't say about data use)

## §7 Accessibility-as-legal
WCAG / ADA / DDA obligations where legally required (distinct from Brand Manager's craft-level accessibility).

## §8 Review & escalation
- **Compliance officer / counsel**: <role/title — or "tenant-managed internally" / "none — operator self-certifies">
- **When human/counsel sign-off is MANDATORY**: <asset types / claim types that cannot ship on AI verdict alone>
- **Audit-retention requirement**: <how long compliance records must be kept, if any>

## §9 Risk-tier rubric (for THIS tenant)
Which asset types are High / Standard / Low risk — drives how strict Governance reads them.
| Tier | Asset types | Read |
|---|---|---|
| High | regulated-product ads · performance claims · public paid · health/financial claims | strictest; counsel sign-off may be mandatory (§8) |
| Standard | organic social · blog · general email | default |
| Low | internal notes · no-claim brand pieces | light or skip |

## §10 Source & freshness
- **Sourced from**: <counsel doc / operator brief / AI industry research (which) / regulator sites>
- **Last reviewed**: <date>   **Review cadence**: <regime-change-triggered + periodic, e.g. quarterly>
- **"Not legal advice" acknowledgement**: present (see top-of-file banner).
```

---

## Entry discipline

- **Verbatim for legal text** — disclaimers (§1) and mandatory wording (§3) are stored exactly; never paraphrased. CM inserts them character-for-character.
- **Evidence-tagged** — each regime/rule leads with **FINDING** (confirmed by counsel/officer or a cited regulator source) or **HYPOTHESIS** (AI research, unconfirmed). HYPOTHESIS rules are usable but flagged everywhere they surface, so the operator sees their weight honestly.
- **Source-cited** — name the regime + clause + URL where a rule comes from.
- **Counsel-confirmed status** in the header is honest: `no` means AI-drafted and pending review — Governance treats every High-tier verdict as advisory until confirmed.

## How it's used (and how it no-ops)

| Consumer | With a profile | Without a profile (existing campaigns / pre-Phase-0) |
|---|---|---|
| **Phase 0** | Governance Manager authors it (industry research + operator input) | n/a — Phase 0 is opt-in per tenant |
| **Brief** (Phase 1) | "Compliance (FIXED INPUT)" subsection cites it | subsection absent |
| **CD trio** (Phase 2) | `compliance-clearable` convergence filter | filter is a no-op |
| **Per-step brief** (Phase 4a) | CM injects the relevant **compliance slice** (disclaimers + prohibited claims for this asset) | no slice |
| **Stage-2b gate** | Governance Manager verdicts the asset against it | **gate no-ops; Brand Manager keeps its mandatory-check fallback** |

This table IS the no-retrofit guarantee: every path degrades to current behaviour when no profile exists.

## Lifecycle — how it's created, evolves, and learns

**Created** — authored in **Phase 0** by the **Governance Manager** agent (its authoring role): it takes the tenant's industry + jurisdiction(s), researches the applicable regimes (tagging FINDING/HYPOTHESIS), and captures the company-specific rules from the operator/counsel, drafting against this schema. Operator (+ counsel where §8 requires) approves before it goes `Active`. Never auto-created for existing tenants.
- *Do we need a skill?* The **agent does the cognitive work**; a `/compliance-profile` **skill that wraps the flow** (scope → research → draft → operator/counsel review → save → render) is worth extracting **after 2–3 manual runs** — the same skill-extraction discipline as `onboard-tenant` → `/establish-tenant`. Until then: the agent + the onboard §2.5 runbook step.

**Evolves over time — yes, deliberately.** A durable artifact (like Brand Context). It updates when: (a) a **regime changes** (law / regulator guidance), (b) the Governance Manager's **drift workflow** flags a gap, or (c) the operator/counsel add a rule. **Every update is operator/counsel-gated — never auto-applied.** Reviewed on the §10 cadence + whenever a regime changes.

**Learns from campaign data — yes, learn-then-confirm.** Every Stage-2b gate review is a data point. When a pattern emerges — a disclaimer keeps being needed on an asset type, a claim type keeps recurring, a regime gap keeps surfacing — the Governance Manager **proposes a profile update** (a drift recommendation) that graduates into §1/§2/§3/§4 **only on operator/counsel approval**. This mirrors the tenant-playbook *graduate-then-cite* model: the gate surfaces the candidate, the human confirms it. Given the legal sensitivity, a compliance rule **never evolves silently from data** — it's always surfaced as a red flag for review first.

## The red-flag guardrail (not advice)

The Governance Manager is a **red-flag aid — not counsel, and not a compliance authority**. It surfaces *what* to check, *which* rule appears to apply, and a *recommended* fix (e.g. "insert approved disclaimer `gen-advice`"; "this performance claim needs §4 substantiation") — framed as **"here's a thing you should review,"** never as "this is legally / compliance correct." Where §8 marks counsel sign-off mandatory, the Stage-2b gate returns **Hold-for-operator** rather than auto-clearing — the human/counsel decision is structurally required, not optional.

## Cross-references

- `governance-manager/AGENT.md` — the agent that authors + enforces this profile
- `docs/specs/phase-0-tenant-baseline.md` — where it's authored
- `docs/specs/brief.md` — the Compliance (FIXED INPUT) subsection
- `docs/specs/per-step-brief.md` — the compliance slice
- `docs/specs/asset.md` — the `compliance:` audit block written at the gate
- `docs/specs/_proposals/three-evolutions-implementation-plan.md` — the build plan + NO-RETROFIT constraint
