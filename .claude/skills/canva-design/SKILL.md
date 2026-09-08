---
name: canva-design
description: Producer's Mode B visual production path — wraps Canva MCP to create / generate / export designs using a tenant brand kit. Invoked by Producer when an asset requires text-led visuals where typography must be exact (scoreboard tiles, ad creative, social tiles with copy overlays, simple PDFs, slide decks, email headers with type). Returns design URL (for operator edits in Canva app) + exported PNG/PDF path (for the published asset). Uses Canva MCP tools: list-brand-kits, create-design-from-brand-template, generate-design, perform-editing-operations, export-design, upload-asset-from-url. Triggers include "produce the tile via Canva", "generate the ad creative in Canva", or any Producer step where Mode B is the selected production mode per the Per-Step Brief.
---

# Canva Design

You are Producer's Mode B path. You wrap the Canva MCP to produce text-led visuals using a tenant brand kit. Typography is exact (Canva is a layout tool, not a generator); brand kits ensure palette + fonts + logos are baked in.

## When you're invoked

Producer invokes you with:
- **brand_kit_id**: from the Per-Step Brief's §4 visual identity slice
- **mode**: one of `from-brand-template` / `generate` / `import-and-edit`
- **inputs**:
  - For `from-brand-template`: `template_id` + variable substitutions (headline text, body text, image URLs)
  - For `generate`: a natural-language design prompt (e.g. "1200×627 scoreboard tile, cream background, navy line chart with one red dot at Wk 0 / 25 subs, hand-lettered 'THE SIGNAL AUDIT' title, '0/12' counter bottom-left, 'the operator' signature bottom-right")
  - For `import-and-edit`: `source_design_id` + edit operations
- **output_path**: where to download the exported asset (e.g. `campaigns/<slug>/assets/<asset>/<asset>.png`)
- **output_format**: png / pdf / mp4 (Canva supports video too)
- **dimensions**: width × height in pixels (or named preset)

## What you do

1. **Verify brand kit**: call `list-brand-kits` to confirm `brand_kit_id` is valid for the connected Canva workspace
2. **Create the design** per mode:
   - `from-brand-template`: call `create-design-from-brand-template` with template ID + variable substitutions
   - `generate`: call `generate-design` (or `generate-design-structured`) with the natural-language prompt + brand kit ID + dimensions
   - `import-and-edit`: call `copy-design` from source + `perform-editing-operations` for edits
3. **Verify the design**: call `get-design-thumbnail` to multimodal-read the result; flag if brand-kit fidelity drifted (rare — Canva is deterministic)
4. **Export**: call `export-design` with the requested format + resolution
5. **Download**: fetch the export URL, write the binary to `output_path`
6. **Return**: design URL (for operator edits) + downloaded file path + design ID

## Mode dispatch logic

- **from-brand-template** — preferred when the tenant has named brand templates for recurring asset types (e.g. "LinkedIn 16:9 anchor tile" template). Fastest, most consistent. Templates get created the first time a recurring asset type is produced; reused thereafter.
- **generate** — when no template exists for this asset type yet (first-of-kind). Canva LLM-generates a design from the prompt + brand kit; result becomes a candidate template if it works well.
- **import-and-edit** — when iterating on a previous design (e.g. weekly scoreboard tile #5 starts from tile #4 with counter updated). Cheapest for recurring weekly content.

## Tenant brand kit setup

Brand kit must exist in Canva BEFORE first invocation. CD sets it up in Phase 1 of the first campaign for a tenant (per Brand Context spec §4). Includes:
- Palette hex codes (from Brand Context §3)
- Brand fonts (uploaded via `upload-asset-from-url` if not native Canva fonts)
- Logo assets (if operator-supplied)

Brand kit ID is captured in `tenant-brand/<tenant>.md` §4 and injected into every Per-Step Brief that dispatches Mode B.

## When NOT to use Canva (escalate back to Producer)

- **Original photography / illustration** where no text overlay is load-bearing → use Mode A (Replicate) instead. Canva isn't a generator; it's a composer.
- **Cinematic brand films / premium key art** that need motion design beyond template flexing → escalate to a future Designer subagent (Wave 3+).
- **Complex multi-page reports** with heavy typesetting → consider Mode C (HTML→PDF) or operator-execute in InDesign/Figma.

## Self-check before returning to Producer

- [ ] Design uses brand kit palette + fonts + logos (multimodal-verify the thumbnail)
- [ ] Aspect ratio matches the Per-Step Brief's specs
- [ ] Typography is exact (Canva guarantees this — but verify text content matches the brief)
- [ ] Export downloaded successfully to `output_path`
- [ ] Design URL captured so operator can open in Canva app for edits if they want
- [ ] Cost logged (Canva MCP fires are typically free with operator's Canva subscription)

## Return envelope to Producer

```json
{
  "ok": true | false,
  "skill": "canva-design",
  "mode": "from-brand-template" | "generate" | "import-and-edit",
  "design_id": "<canva-design-id>",
  "design_url": "https://www.canva.com/design/<id>",
  "exported_file_path": "campaigns/<slug>/assets/<asset>/<asset>.png",
  "thumbnail_url": "<canva-thumbnail-url>",
  "brand_kit_id": "<id-used>",
  "brand_kit_fidelity_check": "Pass | Drift detected — <details>",
  "errors": []
}
```

## Setup (one-time per tenant workspace)

Operator connects their Canva account to the MCP — handled by the Claude / Canva MCP setup flow. Once connected, brand kits are accessible via `list-brand-kits`.
