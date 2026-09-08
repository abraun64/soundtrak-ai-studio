# integrations.yaml — Tenant Integration Schema

**Spec version**: v1 · Authored 2026-06-03 per Rollout Architecture v2 (`docs/specs/rollout-architecture.md` §8.1).

The `tenant/<name>/integrations.yaml` file is the **per-tenant configuration** for publishing-platform adapters + credentials + channel defaults. Lives in each tenant's brand folder alongside Brand Context. **Sourced from** Brief `tech_stack` (which platforms) + `human_roles` (escalation contacts).

**Critical**: this file contains CREDENTIALS. Never commit to any shared repo. Credentials are env-var references (resolved at adapter runtime), not literal secrets.

**Read by**: CM at deploy time (per-asset adapter dispatch); Producer at build time (per-asset `deployment:` block inheritance via `channel_defaults`); operations.html generator (escalation paths display).

---

## Schema

```yaml
tenant: "<Tenant Name>"
last_updated: "<YYYY-MM-DD>"

# Per-platform configuration. Keys map to asset.yaml's deployment.platform.
# Common platform keys: mailchimp, sharepoint, notion, confluence, linkedin,
# youtube, netlify, vercel, github, wordpress, webflow, sendgrid, hubspot, etc.
platforms:
  <platform-key>:
    # Whether CM can push assets to this platform via coded API adapter (true)
    # or only generate paste-cookbook (false). When false, publish_method
    # defaults to "cookbook" for any asset deploying to this platform.
    has_adapter: true

    # Credentials. NEVER literal values. Use env-var refs ${ENV_VAR_NAME}
    # resolved by the adapter at runtime. May be null if has_adapter: false.
    credentials:
      api_key: "${TENANT_PLATFORM_API_KEY}"
      # ... per-platform specific keys

    # Per-platform defaults that asset.yaml deployment block inherits.
    # Producer can override per-asset; usually doesn't need to.
    defaults:
      # Per-platform specific defaults — see §Platform Reference below
      <key>: <value>

# Channel → Platform mapping. Drives asset.yaml deployment block inheritance.
# Producer reads asset.default_channel → looks up channel_defaults[<channel>]
# → gets the platform name → looks up platforms[<platform>] for the rest.
# The KEYS MUST match this tenant's Plan channel vocabulary VERBATIM — an asset's
# `default_channel` equals its Plan `Channel` (v3 one-vocabulary), so an off-Plan key
# here silently fails to route the asset at deploy time. Keep in sync with the Plan channels.
channel_defaults:
  Substack: { platform: "substack" }
  Website: { platform: "your-website" }
  "LinkedIn + social": { platform: "linkedin" }
  "Email — <list name>": { platform: "mailchimp" }
  # ... one key per PUBLISHING Plan channel; internal channels (Brand foundation,
  #     Measurement, Ads & paid) need no entry — they don't deploy.

# Escalation paths displayed in per-campaign operations.html §4
escalation:
  - condition: "<what's broken or surfaced>"
    contact: "<who to contact + how>"
    sla: "<response timeframe>"
  # ...
```

---

## Platform reference (common platforms + their defaults)

### `mailchimp`
```yaml
mailchimp:
  has_adapter: true
  credentials:
    api_key: "${TENANT_MAILCHIMP_API_KEY}"
    server_prefix: "us1"  # the dc1, us2, etc. prefix from API key
  defaults:
    audience_id: "<audience hash from Mailchimp>"
    from_name: "<sender name>"
    from_email: "<sender email>"
    reply_to: "<reply-to email>"
    send_time_local: "Friday 09:00 AEST"  # default send-time pattern
    footer_address_block_id: <integer>
    preview_text_default: "<default preview text>"
```

### `sharepoint`
```yaml
sharepoint:
  has_adapter: false  # SharePoint REST API exists; coded adapter is Build Phase 5+ v2 work
  credentials: null   # not needed for cookbook deploy
  defaults:
    site_url: "https://<tenant>.sharepoint.com/sites/<site-name>"
    pages_library: "SitePages"
    default_template: "Standard SharePoint Page"
    notes: "v1 cookbook deploy: the operator copies HTML page into SharePoint Pages library manually"
```

### `linkedin`
```yaml
linkedin:
  has_adapter: false  # LinkedIn API is creaky for organic post automation; cookbook for v1
  credentials: null
  defaults:
    company_page_url: "linkedin.com/company/<tenant>"
    hashtags: ["<#tag1>", "<#tag2>", "<#tag3>"]
    image_aspect_default: "1:1"
```

### `youtube`
```yaml
youtube:
  has_adapter: false  # YouTube Data API exists; reserved for v2 (Shorts MP4 generation in scope)
  credentials: null
  defaults:
    channel_url: "youtube.com/@<tenant>"
    shorts_aspect: "9:16"
```

### `spotify-podcast-host`
```yaml
spotify-podcast-host:
  has_adapter: false  # Source-side; podcast publishing is upstream of this system
  credentials: null
  defaults:
    show_url: "open.spotify.com/show/<showId>"
    episode_url_pattern: "open.spotify.com/episode/{episode_id}?t={seconds}"
```

### `netlify` / `vercel` / `cloudflare-pages`
```yaml
netlify:
  has_adapter: true  # Git-push or API deploy
  credentials:
    api_key: "${TENANT_NETLIFY_API_KEY}"
    site_id: "<site identifier>"
  defaults:
    deploy_method: "git-push"  # or "api"
    default_branch: "main"
```

### `github`
```yaml
github:
  has_adapter: true
  credentials:
    pat: "${TENANT_GITHUB_PAT}"
  defaults:
    org: "<github-org>"
    default_repo: "<repo-name>"
    default_branch: "main"
```

---

## Publish-method semantics

When CM dispatches an asset for deployment:

1. Read `asset.yaml#deployment.platform`
2. Look up `tenant/<name>/integrations.yaml#platforms[<platform>]`
3. If `has_adapter: true` AND `credentials` not null AND `asset.yaml#deployment.publish_method` in `[api, hybrid]`:
   - Fire the platform adapter (Python script in `.claude/skills/deploy-<platform>/`)
   - Adapter pushes the asset, returns result
   - Run `asset.yaml#deployment.verification` checks (automated ones run immediately; manual ones surface in operations.html)
4. Else (no adapter, no creds, or `publish_method: cookbook`):
   - Generate cookbook from asset + platform defaults + `format_requirements` + `verification`
   - Surface in `campaigns/<slug>/operations.html` §2 "This week's manual steps"

The cookbook generator is a single skill (`.claude/skills/deploy-cookbook/`) that takes any asset.yaml + integrations.yaml + platform key and emits markdown for operator paste-this-into-that instructions.

---

## v1 adapter inventory (Build Phase 5 ships)

- `mailchimp` — coded adapter (push HTML email + tile assets to draft campaign; operator clicks Send)
- `cookbook` fallback — works for any platform with `has_adapter: false`

v2 adapter targets (built when first needed):
- `sharepoint` (when first tenant uses it as published destination)
- `netlify` / `vercel` / `github` (when first static-site campaign needs deploy)
- `linkedin` (when API friction proves cookbook insufficient)
- `youtube` (when Shorts MP4 generation in scope)

---

## Cross-references

- **Rollout Architecture v2 spec**: §7 (per-asset deployment block) · §7.1 (inheritance flow) · §8.1 (this schema)
- **Brief spec v2**: §Tech Setup is the source of platform decisions that flow into this file
- **Asset spec**: §deployment block inherits from `channel_defaults` here
- **CM SKILL.md** (will be extended in Phase 6): adds per-asset adapter dispatch behavior
- **operations.md spec** (Phase 6 artifact): §4 escalation paths sourced from `escalation:` block here
