---
name: deploy-cookbook
description: |
  Cookbook-generator fallback for any asset whose deployment.platform has no
  coded adapter OR whose publish_method is "cookbook". Generates markdown
  paste-this-into-that instructions from the asset.yaml deployment block +
  tenant integrations.yaml platform defaults + asset format requirements.

  TRIGGER when: CM dispatches an Approved asset AND any of these is true:
    - tenant integrations.yaml has has_adapter: false for the platform
    - asset.yaml deployment.publish_method == "cookbook"
    - deploy-<platform> skill failed or unavailable
    - tenant credentials env-vars unset

  DO NOT TRIGGER when: deploy-<platform> coded adapter is available + creds present
  + publish_method in [api, hybrid]. Use the coded adapter instead.
---

# Cookbook Generator

**Status**: v1 SCHEMA · 2026-06-03. Reference implementation lands in Build Phase 5 v2 when first non-Mailchimp asset deploys.

## What this skill does

1. Reads asset path from invoker prompt
2. Reads sibling `asset.yaml` for `deployment:` block
3. Reads `tenant/<name>/integrations.yaml#platforms[<platform>]` for defaults
4. Generates a markdown cookbook with this structure:

```markdown
# Cookbook — Deploy <Asset Name> to <Platform>

**Asset**: `<path-to-asset>`
**Destination**: <platform> · <platform.defaults.location_pattern or asset.deployment.location>
**Method**: Manual paste/upload via <platform> UI
**Estimated time**: <best-guess minutes>

## Prerequisites

- [ ] Access to <platform> UI (<integrations.yaml platforms[<platform>].defaults.site_url or login URL>)
- [ ] Asset file rendered + ready (`<asset-path>`)
- [ ] Per-asset prerequisites from `asset.yaml#deployment.format_requirements`:
  - <each format_requirement>
  - ...

## Step-by-step deploy

### 1. <Platform-specific first step>
<Instruction with screenshot ref where useful>

### 2. <Next step>
...

### N. <Final step>
...

## Verification (from asset.yaml deployment.verification)

After deploy, confirm:
- [ ] <each verification.check>
  - <if automated: "CM checked automatically; status: ✅"; else: "manual check; mark when complete">

## Notes from Producer (asset.yaml deployment_notes)

<deployment_notes value, rendered as a quote block>

## Escalation (from integrations.yaml escalation block)

If something goes wrong:
- <relevant escalation rows that match this platform>
```

5. Saves cookbook to `campaigns/<slug>/operations/cookbooks/<asset-id>-<platform>.md`
6. Returns reference to CM for inclusion in `operations.html §2 "This week's manual steps"`

## Per-platform cookbook templates

The generator has platform-specific step templates for common destinations:

- **Mailchimp** (when used as fallback if adapter unavailable): paste HTML into Content Studio, upload images via File Manager, set subject/preview text, schedule send
- **SharePoint Pages**: navigate to Pages library, New Page, paste HTML via embed or import, set page settings, publish
- **LinkedIn (company page)**: navigate to company page, Start a post, paste copy, attach downloaded image, post
- **Instagram feed post**: on mobile, save image to camera roll, new feed post, paste caption (with link-in-bio caveat)
- **YouTube Shorts**: upload MP4 via Studio, fill metadata, publish (v1: PNG-only step + operator-MP4-production cookbook)
- **WordPress** (acmeco.com.au): admin login, new post, paste content, set categories/tags, publish
- **Generic file drop**: upload to specified folder; share link
- **Print**: paste content into print-shop template, submit order
- **API-with-no-adapter**: future-proof — generic "this platform exposes an API; in v2 we'll code an adapter; v1 cookbook-only"

## Implementation (Build Phase 5 v2)

`cookbook_generator.py` — Python script reading asset.yaml + integrations.yaml + platform-specific step templates from `templates/` dir, outputting markdown.

## Failure modes

- **Platform unknown to generator**: emit generic cookbook + flag for Producer to enrich `format_requirements` next iteration.
- **asset.yaml missing deployment block**: ABORT + emit Producer Step 4.6 warning (per build-gallery.py warning).

## Coded adapters — the standard contract

The cookbook is the FALLBACK. When a platform gets a coded adapter instead, that adapter must
conform to the **deploy-adapter contract**: [`ADAPTER-CONTRACT.md`](ADAPTER-CONTRACT.md) (sibling
file). It defines the four required files (interface `SKILL.md` + tested `adapter.py` + captured
`investigation-reference.md` + `smoke_test.py`) and the standard adapter envelope. New adapters
are scaffolded to that contract via `.claude/skills/integration-scaffolder/`; the reference
implementation proving it end-to-end is `.claude/skills/deploy-static-folder/`.

## Cross-references

- `docs/specs/integrations.md`
- `docs/specs/asset.md` §deployment
- `docs/specs/rollout-architecture.md` §5 (operations.html surface where cookbooks land)
- `.claude/skills/deploy-mailchimp/` — preferred path when adapter available + creds present
- [`ADAPTER-CONTRACT.md`](ADAPTER-CONTRACT.md) — the standard shape every coded deploy adapter conforms to
