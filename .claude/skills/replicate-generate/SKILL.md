---
name: replicate-generate
description: Generate images and short-form videos via Replicate's API. Centralised pixel-production skill called by hybrid copywriter+designer agents (Social/Community Manager and the other Wave 2 hybrids when propagated) for in-agent visual production. Wraps Replicate's REST API — creates a prediction, polls until succeeded, downloads outputs to the specified path, returns file paths + cost + metadata for the agent to bundle into the Asset. Supports static image models (FLUX 1.1 Pro / FLUX schnell / FLUX dev / Recraft V3 / Ideogram V2 / SDXL / Imagen 3) and video models (Pika 1.5 / Kling 1.5 Pro / MiniMax video-01 / Hunyuan / Veo when available). Invoke when an agent's visual production workflow step needs to generate one or more visuals from a self-contained prompt. Triggers include "generate the tile via Replicate", "produce the carousel slides", "generate the TikTok shots", or any agent-internal call where Mode A direct-generation is the selected execution mode per the Agent Plan.
---

# `/replicate-generate` — Replicate API wrapper for pixel production

## What this skill does

Takes a self-contained generation prompt (per [craft/visual-craft-shared.md#generation-prompt-craft](../../../craft/visual-craft-shared.md#generation-prompt-craft)) + a model selection + an output spec; calls Replicate's REST API; polls the prediction until it succeeds or fails; downloads the output file(s) to the specified path; returns structured metadata (file paths + Replicate prediction ID + cost estimate + timing) so the calling agent can:

1. Multimodal-read the generated file(s)
2. Run visual sub-edit (brand-fidelity + composition + visual AI tells)
3. Decide reroll vs accept
4. Log into Asset §5c Generation log
5. Bundle into the Asset's Final asset gate §9 block

## When this skill is invoked

By hybrid agents (Social/Community Manager primary; the other Wave 2 hybrids when propagated) during their visual production workflow steps. **Mode A** — direct generation, no manual handoff.

Not invoked by:
- User directly (this is an agent-internal skill; user invokes the parent agent)
- Campaign Manager (CM orchestrates gates, not pixel production)
- Brand Manager (reviews; doesn't produce)
- Creative Director (writes Concept §4c generation prompts that hybrid agents then execute via this skill)

## Inputs (required + optional)

| Field | Required | Type | Description |
|---|---|---|---|
| `prompt` | Required | string | The self-contained generation prompt. Must include style direction, composition direction, lighting (if applicable), color direction, aspect ratio if model doesn't take it as a separate param. Named style reference required (per craft/visual-craft-shared.md generation-prompt-craft). |
| `model` | Required | string | Replicate model identifier (e.g. `black-forest-labs/flux-1.1-pro`). See [Model catalogue](#model-catalogue). |
| `aspect_ratio` | Optional | string | E.g. `"1:1"`, `"4:5"`, `"9:16"`, `"16:9"`. Passed to model if model supports it as a parameter; ignored otherwise (some models infer from prompt). |
| `num_outputs` | Optional | int (1–4) | How many variants to generate in parallel. Default: 4 for first generation; 1 for refinement rerolls. |
| `output_dir` | Required | string | Absolute or repo-relative path where output files should be saved. E.g. `campaigns/<slug>/assets/<asset-slug>/visual/`. Created if doesn't exist. |
| `output_basename` | Required | string | Filename prefix (without extension). E.g. `launch-tile`. Variants append `-1`, `-2`, etc. |
| `negative_prompt` | Optional | string | What to avoid (supported by some models). E.g. `"no text overlay, no watermarks, no stock-photo lighting"`. |
| `seed` | Optional | int | For deterministic regeneration. Random by default. |
| `model_specific_params` | Optional | object | Pass-through for model-specific params (e.g. `guidance_scale`, `num_inference_steps`, `prompt_strength`). |
| `cost_cap_usd` | Optional | float | Reject the call if estimated cost exceeds this. Default: $0.50 per call (safety guard). |
| `caller_agent` | Required | string | Which agent invoked this skill (e.g. `social-community-manager`). For audit logging. |
| `caller_campaign` | Required | string | Campaign slug. For cost rollup. |
| `caller_asset_id` | Optional | string | Asset ID being produced. For audit. |

## Outputs (return envelope)

```json
{
  "ok": true | false,
  "skill": "replicate-generate",
  "code": null | "missing_token" | "replicate_api_error" | "model_failed" | "cost_cap_exceeded" | "timeout" | "download_failed",
  "model_used": "<model identifier>",
  "prediction_id": "<Replicate prediction ID>",
  "output_files": ["campaigns/.../launch-tile-1.png", "campaigns/.../launch-tile-2.png", "..."],
  "num_outputs_requested": 4,
  "num_outputs_received": 4,
  "cost_estimate_usd": 0.04,
  "duration_seconds": 12.3,
  "model_metadata": { "seed": 12345, "..." },
  "audit_log_path": "campaigns/<slug>/visual-generation-log.jsonl",
  "errors": []
}
```

The agent then multimodal-reads each `output_files` entry, runs visual sub-edit, picks best variant or rerolls.

## Procedure

### Step 1 — Validate inputs

- `prompt`: must be present, non-empty, ≥20 chars (shorter than that is too vague — reject)
- `model`: must be in the [Model catalogue](#model-catalogue) OR user has explicitly added a custom model (check `tenant/config/replicate-models.json` if present)
- `output_dir`: create if doesn't exist via PowerShell `New-Item -ItemType Directory -Force`
- `cost_cap_usd`: default $0.50 if not specified

### Step 2 — Check Replicate API token

- Read `$env:REPLICATE_API_TOKEN`
- If empty: return `ok: false`, `code: missing_token`. Surface clear setup instruction: "Set REPLICATE_API_TOKEN env var. Get token from https://replicate.com/account/api-tokens"
- Don't log the token; don't echo it; don't write it to files

### Step 3 — Estimate cost (cost-cap guard)

Estimate per-image / per-second cost from [Model catalogue](#model-catalogue) × `num_outputs`. If > `cost_cap_usd`, return `ok: false`, `code: cost_cap_exceeded` with the estimate. The agent can re-invoke with a higher cap if intentional (logged in Agent Plan).

### Step 4 — Create the prediction (synchronous-wait preferred for static)

POST to the model endpoint with the `Prefer: wait=60` header — Replicate then waits synchronously up to 60 seconds before returning. For static images this almost always returns the completed `output` array in a single round-trip (FLUX schnell ~1–3s; FLUX Pro ~3–8s). Eliminates the polling loop for the static path.

```powershell
$body = @{
  input = @{
    prompt = $prompt
    aspect_ratio = $aspect_ratio
    num_outputs = $num_outputs
    output_format = "png"
    # ...other model-specific params merged in
  }
} | ConvertTo-Json -Depth 6

$headers = @{
  "Authorization" = "Bearer $env:REPLICATE_API_TOKEN"
  "Content-Type" = "application/json"
  "Prefer" = "wait=60"  # synchronous return path
}

$prediction = Invoke-RestMethod -Method Post `
  -Uri "https://api.replicate.com/v1/models/$model_owner/$model_name/predictions" `
  -Headers $headers -Body $body
```

**If `$prediction.status -eq "succeeded"` and `$prediction.output` is populated**: skip to Step 6 (download). The synchronous wait succeeded.

**If `$prediction.status -in @("starting", "processing")`**: Step 5 polling loop required (model exceeded the 60s wait — common for video, rare for static).

### Step 5 — Poll for completion (fallback when synchronous wait insufficient)

Used when `Prefer: wait=60` returned before the prediction completed — predominantly the video path.

Poll `prediction.urls.get` every 2 seconds. Status progression:
- `starting` → `processing` → `succeeded` (success path)
- `starting` → `processing` → `failed` (model error path)
- `starting` → `processing` → `canceled` (timeout / canceled)

Max poll duration: 5 minutes for static (rare — most exit on synchronous wait); 15 minutes for video. Beyond that → return `ok: false`, `code: timeout` with the prediction ID (it may still finish; can be retrieved later via Replicate dashboard).

### Step 6 — Download outputs

On `succeeded`:
- `prediction.output` is either a string (single output URL) or an array (multiple)
- Download each via `Invoke-WebRequest -Uri $url -OutFile "$output_dir/$output_basename-$i.<ext>"`
- Infer extension from Content-Type header (image/png → .png, image/jpeg → .jpg, video/mp4 → .mp4)
- Verify file size > 0 and matches expected magic bytes (PNG / JPEG / MP4 header) — if not, retry once, then `code: download_failed`

### Step 7 — Append to audit log

Append one JSONL entry to `campaigns/<slug>/visual-generation-log.jsonl` with: timestamp, caller_agent, caller_asset_id, model, prompt (truncated to 500 chars for log size), prediction_id, output_files, cost_estimate_usd, duration_seconds. This is the cost-rollup source for per-campaign spend visibility.

### Step 8 — Return envelope

Return the structured envelope above. The calling agent takes it from there.

## Model catalogue

Default models per asset class. Agent can override per Agent Plan.

### Static image models

| Model | Replicate ID | Cost per image (USD) | Best for | Strengths | Weaknesses |
|---|---|---|---|---|---|
| **FLUX 1.1 Pro** (default for hero static) | `black-forest-labs/flux-1.1-pro` | ~$0.04 | Hero tiles, brand-fidelity work, photography-style outputs | Strong photo realism, follows prompts precisely, aspect-ratio aware | Costlier than schnell; limited text rendering |
| **FLUX schnell** (iteration / variants) | `black-forest-labs/flux-schnell` | ~$0.003 | Variant generation, rapid iteration, fast feedback | Very fast (<5s), cheapest, same prompt grammar as FLUX Pro | Lower fidelity than Pro |
| **FLUX dev** (middle ground) | `black-forest-labs/flux-dev` | ~$0.025 | Most general work where Pro is overkill | Faster than Pro, higher quality than schnell | Slightly inconsistent vs Pro |
| **Recraft V3** | `recraft-ai/recraft-v3` | ~$0.04 | Typography-led work (limited; AI typography still risky for brand fidelity) | Better in-image text than other models | Brand fonts still won't render — use Figma for serious typography work |
| **Ideogram V2** | `ideogram-ai/ideogram-v2` | ~$0.06 | Text-in-image with controlled placement | Best-in-class at rendering specified text | More expensive; aesthetic less refined |
| **SDXL** | `stability-ai/sdxl` | ~$0.0023 | Cheap iteration where quality bar is low | Mature, cheap | Older model; weaker prompt adherence |
| **Imagen 3** | `google/imagen-3` | ~$0.05 | Google Imagen aesthetic, photo-realistic | Strong photo realism | Less predictable for stylised work |

### Video models

| Model | Replicate ID | Cost per second (USD, approx) | Best for | Strengths | Weaknesses |
|---|---|---|---|---|---|
| **Pika 1.5** | `pika-labs/pika-1.5` | ~$0.10/sec | Short-form social video (TikTok / Reels / Shorts), motion graphics | Reasonable motion coherence, multi-shot capability | 1-in-3 takes usable |
| **Kling 1.5 Pro** | `kwaivgi/kling-v1.5-pro` | ~$0.10/sec | Realistic motion, longer takes (5–10s) | Better motion physics than Pika | Slower generation (1–3 min per clip) |
| **MiniMax video-01** | `minimax/video-01` | ~$0.05/sec | Stylised motion, anime-leaning aesthetics | Lower cost, decent quality | Less photo-realistic |
| **Hunyuan Video** | `tencent/hunyuan-video` | ~$0.08/sec | Cinematic shots, branded aesthetic | Higher quality cinematic | Slow; expensive at length |

**Notes**:
- Costs above are **approximate** based on Replicate's pricing as of skill author date; check current Replicate pricing dashboard for exact figures
- Video models all have ~25–40% reroll rate (1 in 3–4 clips usable) — budget accordingly
- For brand-defining cinematic work, escalate to Motion Designer (when built) rather than using Replicate

### Adding custom models

Tenant or campaign can add to the catalogue by writing `tenant/config/replicate-models.json`:

```json
{
  "models": [
    {
      "id": "custom-fine-tune/brand-style-v1",
      "version": "abc123...",
      "type": "static",
      "cost_per_image_usd": 0.05,
      "best_for": "Brand-style-fine-tuned static images",
      "default_params": { "guidance_scale": 7.5 }
    }
  ]
}
```

Skill reads this on every invocation and merges with the default catalogue.

## Iteration discipline

The skill executes one call (one prediction with 1–4 outputs). **Iteration is the agent's responsibility**, not the skill's. The agent:

1. Calls `/replicate-generate` with `num_outputs: 4`
2. Multimodal-reads all 4 outputs
3. Runs visual sub-edit on each
4. If any pass clean → accept, log, bundle into Asset
5. If best foundation needs minor fix → refine prompt, call again with `num_outputs: 1` (cheaper reroll)
6. If all 4 fail brand-fidelity → broader prompt rethink, generate another 4
7. Max 3 rounds (12 generations total at worst) before refuse-to-surface per the agent's sub-edit pipeline

Cost budget per asset: ~$0.16 worst-case for FLUX Pro static (4 × $0.04 × 1 round); ~$0.50 worst-case for 3 rounds of refinement.

For video: ~$0.30–$0.60 per shot (Pika at 3 seconds × $0.10 = $0.30; 30% reroll rate = avg ~$0.45 per shot). A 30-second TikTok with 10 shots ≈ $4.50 worst-case for full video production.

## Audit logging + cost rollup

Every successful + failed call appends to `campaigns/<slug>/visual-generation-log.jsonl`:

```json
{"timestamp":"2026-05-20T14:23:45Z","caller_agent":"social-community-manager","caller_asset_id":"AST-042","model":"black-forest-labs/flux-1.1-pro","prompt":"<truncated to 500 chars>","prediction_id":"abc123xyz","output_files":["campaigns/launch/assets/AST-042/visual/launch-tile-1.png","..."],"cost_estimate_usd":0.16,"duration_seconds":8.2}
```

Campaign Manager's Workflow 2 standup can sum these to report per-campaign visual-spend. Use the script `tools/visual-spend-rollup.ps1` (build later) to generate per-campaign + per-month cost reports.

## Error handling

| Code | Cause | Agent action |
|---|---|---|
| `missing_token` | `REPLICATE_API_TOKEN` not set | Surface to user: "Set REPLICATE_API_TOKEN env var; get from https://replicate.com/account/api-tokens" |
| `replicate_api_error` | API returned non-2xx | Log error body; retry once with backoff; if fails again, escalate to operator |
| `model_failed` | Prediction status = failed | Read failure reason from API; if prompt issue, agent refines prompt; if model issue, switch model |
| `cost_cap_exceeded` | Estimated cost > cap | Agent reduces num_outputs OR switches to cheaper model OR escalates to user for approval |
| `timeout` | Polling exceeded max duration | Log prediction ID; let user check Replicate dashboard; agent can re-invoke if needed |
| `download_failed` | Output URL didn't download | Retry once; if fails, log and surface — the prediction may still be retrievable from Replicate's dashboard |

## Security + secrets discipline

- API token read from env, never written to files, never echoed in output, never logged
- Generated files saved with restricted permissions (default umask is fine; no need for special handling)
- Prompts are NOT secrets — they're logged in the audit trail for cost-rollup and debugging
- Generated content IS the asset and lives in the campaign folder per project conventions

## When NOT to use this skill

- **Tenant brand explicitly flags AI-generation as off-brand for the asset** — use Mode B (operator-execute) or escalate to Designer
- **Typography-led carousel slides** where exact brand font + weight + tracking matters — use Mode C (Figma hand-direction); AI typography still fails brand fidelity
- **Brand-defining hero film** (cinematic, sound-led, >2 min) — escalate to Motion Designer for primary authoring
- **Premium photography** requiring real photographer, casting, location — escalate; AI substitute will fail brand bar
- **Lottie / After Effects animation** — AI can't produce these natively; hand-craft in After Effects
- **Asset requires precise edits / inpaint** on an existing image — current Replicate workflow is generation-from-scratch; for inpaint use OpenAI Images directly (add separate skill if needed)

## Cross-references

- **Generation prompt craft** (how the calling agent writes the prompt): [craft/visual-craft-shared.md#generation-prompt-craft](../../../craft/visual-craft-shared.md#generation-prompt-craft)
- **Visual sub-edit pipeline** (what the agent runs on outputs): [craft/sub-edit-pipeline.md](../../../craft/sub-edit-pipeline.md) + [craft/visual-craft-shared.md#common-visual-ai-tells](../../../craft/visual-craft-shared.md#common-visual-ai-tells) + [craft/static-design.md#static-design-ai-tells](../../../craft/static-design.md#static-design-ai-tells) + [craft/motion-design.md#common-motion-design-ai-tells](../../../craft/motion-design.md#common-motion-design-ai-tells)
- **Asset spec — §5c Generation log**: where the calling agent records prediction IDs + costs + iteration counts
- **Replicate API docs**: https://replicate.com/docs/reference/http
- **Setup the API token**: https://replicate.com/account/api-tokens (set `REPLICATE_API_TOKEN` env var)
