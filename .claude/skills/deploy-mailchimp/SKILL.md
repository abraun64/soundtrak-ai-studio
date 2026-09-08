---
name: deploy-mailchimp
description: |
  Mailchimp publishing adapter — Build Phase 5 of Rollout Architecture v2.
  Reads an asset.yaml deployment block + tenant integrations.yaml#platforms.mailchimp,
  pushes the asset's HTML + linked assets to a Mailchimp draft campaign in the tenant's
  account. Operator clicks Send. Falls back to cookbook generation if credentials
  unavailable or has_adapter is false.

  TRIGGER when: CM dispatches an Approved asset with deployment.platform == "mailchimp"
  AND deployment.publish_method in [api, hybrid] AND tenant integrations.yaml has
  has_adapter: true for mailchimp.

  DO NOT TRIGGER when: publish_method == "cookbook" (use deploy-cookbook skill instead),
  has_adapter: false in tenant config, or credentials env vars unset (warn loudly +
  surface as Phase 4 setup task).
---

# Mailchimp Adapter

**Status**: v1 SCHEMA ONLY · 2026-06-03. Working adapter awaits Beta Corp Mailchimp API credentials (P3 dashboard item).

## What this skill does

1. Reads asset path from invoker prompt
2. Reads sibling `asset.yaml` for `deployment:` block (destination, format requirements, verification)
3. Reads `tenant/<name>/integrations.yaml` for `platforms.mailchimp` (credentials env-vars + defaults like audience_id, from_name, from_email, send_time_local)
4. Resolves env-vars at runtime (`os.environ.get(...)`). If any required env-var unset, ABORT + write a Phase 4 setup-task entry to operations.html
5. Uploads referenced image assets to Mailchimp Content Studio via API (POST `/3.0/file-manager/files`)
6. Replaces local image src refs in HTML with returned hosted URLs
7. Creates draft campaign via API (POST `/3.0/campaigns`) with:
   - `type`: regular
   - `recipients.list_id`: from defaults.audience_id
   - `settings.subject_line`: from asset's email subject (parsed from asset MD or asset.yaml)
   - `settings.preview_text`: from asset.yaml or defaults.preview_text_default
   - `settings.from_name`: from defaults.from_name
   - `settings.reply_to`: from defaults.reply_to
8. Sets campaign HTML content via API (PUT `/3.0/campaigns/{campaign_id}/content`)
9. Runs `deployment.verification` checks:
   - Automated: API call to verify draft created + content set
   - Manual: surfaces in operations.html for operator (Mailchimp preview, test send)
10. Returns adapter envelope:
    ```json
    {
      "status": "draft_created",
      "campaign_id": "<id>",
      "preview_url": "<mailchimp draft preview URL>",
      "manual_verification_needed": [<list of manual checks>],
      "operator_action": "Open draft in Mailchimp, preview, click Send when ready"
    }
    ```

## What this skill does NOT do

- **Click Send**. That's operator-controlled. Adapter creates draft only.
- **Schedule send time**. Operator handles via Mailchimp UI.
- **Manage audience segmentation**. Adapter uses the tenant-default audience_id; per-asset segmentation would require asset.yaml override + extended skill.
- **Cookbook fallback**. If skill cannot run (no creds, has_adapter false), exit + flag invoker to use `deploy-cookbook` skill instead.

## Implementation (Build Phase 5 v2 — when Beta Corp Mailchimp creds available)

`adapter.py` — Python script with:
- `mailchimp-marketing` SDK (`pip install mailchimp-marketing`)
- Env-var resolution per integrations.yaml
- Image upload + HTML src rewrite via Mailchimp's File Manager API
- Draft campaign creation via Campaigns API
- Verification automation

## Failure modes

- **Env-var unset**: ABORT + write setup task. Don't proceed.
- **Invalid credentials**: ABORT + escalation path "Mailchimp credentials invalid or expired" (per integrations.yaml escalation block).
- **API rate limit**: retry with exponential backoff up to 3 attempts; then escalate.
- **Asset content malformed**: surface error to invoker with diagnostic; do NOT create draft.

## Cross-references

- `docs/specs/integrations.md` — schema this skill consumes
- `docs/specs/asset.md` §deployment — per-asset block this skill reads
- `docs/specs/rollout-architecture.md` §7 + §7.1 — inheritance flow that fills the block
- `.claude/skills/deploy-cookbook/` — fallback when this skill can't run
