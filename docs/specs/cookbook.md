# Cookbook — Schema

A **Cookbook** is a step-by-step recipe that lets the operator execute a technical task they may not know how to do. Authored when CM's knowledge-gap classification on a task flags *technical execution* (not *marketing decision*).

**Length target**: as long as needed to execute cleanly. Compression is a feature; cookbook completeness trumps brevity.

**Stored**: alongside the asset or pre-flight item that needs it. Path pattern:
- Inline inside an asset: `campaigns/<slug>/assets/<asset>/cookbooks/<task-slug>.md`
- Standalone (cross-campaign, e.g. reusable platform setup): `cookbooks/<task-slug>.md` at project root
- Pre-flight: `campaigns/<slug>/pre-flight/cookbooks/<task-slug>.md`

**Locked**: each cookbook is versioned. When the underlying tool changes (UI redesign, deprecated feature), the cookbook gets vN+1.

---

## Audience assumption (locked default — Retro 001 / 2026-05-27)

Cookbooks assume **B2B-marketer baseline knowledge**:
- ✅ Reader knows what a UTM is, what a tracking pixel is, what an event listener is, what a conversion is, what a marketing funnel does
- ❌ Reader does NOT know the click-by-click of GA / GTM / Posthog / Segment / Mixpanel / specific platform UIs
- ❌ Reader does NOT know platform-specific terminology (e.g. "Tag" vs "Trigger" vs "Variable" in GTM; "Custom Definitions" in GA4)

This audience model maps to a senior CMO who understands the *purpose* of analytics but doesn't run the implementation themselves. Operator confirmed default 2026-05-27.

**Advanced toggle**: every cookbook MAY include an optional `## Advanced shortcut` block at the end for users who already know the platform — collapsed by default; reveals the same outcome via fewer / different steps. Operator decides per task whether to include.

---

## Schema

```markdown
# Cookbook — <task name>

**Use this when**: <one sentence — when does this cookbook fire? e.g. "You need to add GA4 event tracking for the new utility-tool downloads on /how-we-work">
**Platform**: <e.g. Google Analytics 4 + Google Tag Manager>
**Time estimate**: <e.g. "~20 min for first time; ~5 min thereafter">
**Prerequisites**: <what must be true before you start — e.g. "GA4 + GTM are already installed on the site (per Pre-flight P1 baseline check)">

---

## What you'll have when you're done

<2–3 sentences describing the outcome. The reader should know exactly what success looks like before starting. Not "the tag will be set up" — but "the GA4 event `tool_download_click` will fire whenever a visitor clicks any of the three utility-download buttons on `/how-we-work`, and you'll be able to see it in GA4's real-time view within 5 minutes.">

---

## Steps

1. **<verb-first action>** — <one sentence imperative>.
   <If the step has a sub-action: indented bullet with the sub-action>.
   <Screenshot or interface-name annotation as needed>.

2. **<next action>** — ...

3. ...

---

## Verify it worked

<3–5 explicit checks the reader runs to confirm success. Each one names the exact place to look and what they should see. e.g. "Open GA4 → Reports → Realtime. Click a utility button on /how-we-work. Within 30 seconds, you should see `tool_download_click` appear in the 'Event count by Event name' card.">

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| <e.g. "Event doesn't appear in Realtime"> | <e.g. "GTM container not published"> | <e.g. "GTM → Submit → Publish. Wait 2 min. Refresh GA4 Realtime.">|
| ... | ... | ... |

---

## Advanced shortcut *(optional — collapsed by default in rendered HTML)*

<For readers who already know the platform — same outcome via fewer steps. e.g. "If you're comfortable in GTM: create a Click Trigger filtered by CSS selector `.utility-download-btn`, fire a GA4 Event tag with name `tool_download_click`, pass `data-utility` as event_parameter `utility_slug`. Publish.">

---

## What to do next

<Single next step or "Done — return to <upstream task name> on the dashboard.">
```

---

## Drafting discipline

- **Verb-first imperatives** in step text — "Click X" not "You should click X" not "X should be clicked".
- **Name the exact UI element** every time — "Click the 'Submit' button (top-right of the GTM workspace, blue)" not "Submit your changes".
- **One outcome per step** — if a step does two things, split it.
- **Verification is mandatory** — every cookbook ends with explicit success checks. Without verification, the operator finishes and isn't sure if it worked. The verification step is part of the recipe, not optional.
- **Troubleshooting covers the top 3 failure modes** — for each, name the symptom (what they'll see), the likely cause, and the fix.
- **Time estimate must be honest** — if it's a 45-min first-time setup, say so. Don't compress.
- **Screenshots** — embed when a UI element would be hard to find by description alone. Save to `cookbooks/<task-slug>/screenshots/` and reference inline. Annotate with red callouts if needed.

### File-handoff discipline (post-Retro-001 capture-process feedback, 2026-05-28)

Any cookbook step that asks the operator to **save a file to disk** MUST include:

1. **Full absolute path in a copy-paste code block** — never "save to this folder" or relative paths. The operator may open this file in a future session with no surrounding context; they need to copy the path into their Save As dialog directly.
2. **Exact filename specified** — if the pipeline depends on a specific filename for downstream automation (Producer's annotation pass expects `chatgpt-screenshot.png`, not `chatgpt-screenshot-utility-marketing.png`), say so explicitly. Add a note that the operator can ALSO save a descriptive copy alongside; both files coexist; pipeline reads the exact-name version.

### Capture / screenshot discipline (post-Retro-001 feedback, 2026-05-28)

Any cookbook step that asks the operator to **take a screenshot** MUST include:

1. **Browser window resize tip** — instruct the operator to resize to a screenshot-friendly width (~1000–1100px for chat-app screenshots; ~1400px for full-page web app screenshots). Full-width windows produce awkward text wrapping in the capture; too-narrow produces overly-tall screenshots.
2. **High-resolution display preference** — if the operator has multiple monitors (laptop Retina / 4K external), instruct them to take the screenshot on the highest-DPI display. Sharper text matters for downstream annotation passes.
3. **What MUST be visible in the frame** — explicitly name the in-screenshot elements the cookbook depends on (e.g. "model identifier", "timestamp", "full prompt + full output"). If those can't fit in one frame, instruct on taking a second screenshot with overlap.

## What a Cookbook is NOT

- A spec document (specs describe what should happen; cookbooks describe how to make it happen)
- A reference manual (a cookbook fires for one task; a reference is consulted across many)
- A strategy decision (decisions don't get cookbooks; they get decision frames)
- A "FYI" — every cookbook is actionable; if there's no action to take, it's reference content, not a cookbook

## Anti-pattern: spec-shaped cookbook

If a cookbook reads like a spec ("Configure event `tool_download_click` with parameters X, Y, Z to fire on the utility-download buttons") — it's wrong. The operator can't act on that. Re-author as numbered click-by-click steps in the platform UI.

The spec belongs in the Asset's own markdown (alongside the Per-Step Brief). The cookbook is how the operator gets the spec executed.

## Anti-pattern: missing verification step

If a cookbook ends with the last setup action — it's incomplete. Every cookbook ends with verification. The reader's not done until they've confirmed success.

## Render

Cookbooks render via `/render-html` with template `cookbook` (or default fallback). Template should:
- Pin "What you'll have when you're done" + "Prerequisites" + "Time estimate" at the top in a callout block
- Number the steps prominently with anchor links (`#step-3`)
- Display the Verify section in a distinct visual block (success-green-tinted)
- Collapse the "Advanced shortcut" block by default (`<details>`)
- Collapse the "Troubleshooting" table by default (`<details>`)
- Footer link to "What to do next"
