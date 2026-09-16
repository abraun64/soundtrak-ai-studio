---
name: insights-library-add
description: |
  Add a RESEARCH source — market data, behavioural science, a government or
  consultancy report, an academic paper — to the shared Insights Library at
  tenant/research-library/.

  Triggers: "add this to my Insights Library", "add this to the research library",
  "lodge this paper", "save this study", "add this report", "file this research",
  or an operator pasting a research link and asking to keep it.

  NOT for creative work. A campaign, an award winner, an ad worth learning from goes
  to the Best-Practice Library via `library-add` — a different library, a different
  schema, a different reader. If the source is an execution, use that skill instead.
---

# Add to the Insights Library

Schema: `docs/specs/research-library.md`. Catalogue: `tenant/research-library/INDEX.md`.

## Why this skill exists

`tenant/research-library/INDEX.md` has told operators to say *"add this to my Insights
Library"* since it was written, and nothing implemented it — the spec listed the skill as
something to extract "later". A surface that invites a phrase nobody handles is a promise
that fails quietly, at the moment someone tries to be helpful.

## The one rule that is not negotiable

**This library is SHARED across every tenant.** Lodging something here makes it readable
while working on any other client. So only ever lodge **published, external** research:
reports, papers, public data, trade features.

Never lodge a client's confidential material — their first-party data, their internal
decks, anything shared in confidence, anything not publicly available. If you are unsure
whether a source is public, ask before writing, and say why you are asking. That constraint
is what makes a shared library safe, and it cannot be re-decided per source.

## What to do

1. **Read the source.** Fetch the link, or read the file. Do not write an entry from a
   title alone — a summary invented from a headline is worse than no entry, because it
   will be cited as though someone read it.
2. **Classify it**, using the facets in the spec:
   - **Vertical** — `universal` for behavioural science, values and demographics that
     apply to anyone; otherwise the specific vertical. When in doubt prefer the specific
     one; a wrongly-universal entry pollutes every tenant's scan.
   - **Audience** — the segment the finding speaks to.
   - **Topic** — workforce · demographics · values · behavioural-science · attrition · …
   - **Layer** — `market` (what is happening) or `human-behaviour` (what makes people
     tick). The insight scan pulls human-behaviour entries first, so this one earns its
     keep.
   - **Source type** — consultancy · research-firm · government · academic · trade.
3. **Write `tenant/research-library/<source-slug>.md`**, following the shape of the
   entries already there: title, the facet line, who added it and why, sources with full
   citation and URL, then a faithful summary of the key findings with the actual numbers.
   Quote figures exactly. If a finding is the author's interpretation rather than their
   data, say so — the value of this library is that a claim can be traced.
4. **Add a row to `INDEX.md`**, matching the existing column order, with a one-line key
   finding. The row is what the scan reads; make the finding specific enough to be worth
   citing ("workload beats pay as the driver of exit", not "discusses attrition").
5. **Show the operator the draft before writing**, and say which facets you chose and why.
   Facets are judgment calls, and the person who found the source usually knows better.
6. Re-render the INDEX to HTML if the render pipeline is present.

## Before you finish

Say what you filed, where, and how it will be used — that it is now cited automatically
during research for any campaign whose vertical matches, including for other brands. People
add far more when they can see where it lands.
