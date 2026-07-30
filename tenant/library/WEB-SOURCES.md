# Tier 2 — Live Web Source Allowlist

The Creative Director may `WebFetch` against the URLs/domains below for currency — recent campaign launches, cultural moments, "what's working right now" signal — when the curated repository doesn't have a relevant or recent enough example.

**Rule**: live fetch is for *augmentation* of the curated set, not the primary source. Most invocations should satisfy from Tier 1 (`INDEX.md` + `campaigns/`). Use Tier 2 when:

- Brief implies a "current cultural moment" play
- Tenant industry has shifted significantly since last repository refresh
- A competitor has just launched and the brief context needs it
- Operator explicitly asks "what's the cultural temperature on X right now"

## Allowlist

### Campaign archives & analysis
- `adsoftheworld.com` — large free campaign archive, searchable by industry / format
- `adage.com` — trade press, campaign launches + analysis
- `thedrum.com` — UK/global trade press, campaign launches + analysis
- `campaignlive.com` — UK Campaign magazine, deep creative coverage
- `contagious.com` — strategic case-study write-ups (paywalled, fetch abstracts only)
- `lbbonline.com` — Little Black Book, campaign + craft coverage
- `creativereview.co.uk` — craft + design culture

### Awards databases (publicly viewable cases)
- `lovethework.com` — Cannes Lions case archive
- `dandad.org` — D&AD awarded work
- `effie.org` — Effie Awards effectiveness cases
- `oneclub.org` — One Show archive
- `webbyawards.com` — Webby digital awards

### Newsletters & cultural-context (when blog/web versions exist)
- `marketingbrew.com` — Marketing Brew daily; consumer marketing pulse
- `embeddedmarketing.com` — Embedded; cultural / internet-native marketing
- `arkive.com` — ARK; craft-led brand work
- `therebooting.com` — Brian Morrissey on media + marketing business
- `notboring.co` — Packy McCormick; tech-adjacent brand strategy

### Platform-native culture (be selective — high noise)
- `trends.google.com` — for surfacing live trend signal
- `reddit.com/r/advertising` — campaign reactions, dunking + praise
- `reddit.com/r/marketing` — practitioner discussion
- `tiktok.com` (search `#brandedcontent` etc. via Bash + tooling) — current format trends

### Specific high-signal brand archives
- `apple.com/newsroom` — Apple campaign + product announcements
- `nikenews.com` — Nike communications
- `about.fb.com/news/` — Meta marketing announcements
- `stripe.com/press` — Stripe (design-as-marketing canonical)

## Out of scope

- Open-web search via WebSearch — only the URLs above. The constraint is intentional; it keeps signal high and prevents the CD pulling from low-quality SEO-spam sources.
- Social media platforms beyond what's listed — Phase 2 may add Instagram, LinkedIn brand pages explicitly.
- Tenant's own assets / Notion / Drive — those live in `tenant/` directly, not via WebFetch.

## Adding to the allowlist

If the CD repeatedly needs a source not on this list, flag it to the operator in the handoff. The operator (or a future setup-phase tool) curates new entries in. The CD does NOT silently expand the allowlist itself.

## Citation discipline

When a Tier 2 fetch surfaces something the CD uses in a concept, the entry MUST appear in concept §11 (References) with the URL and a one-line "what this informed." This makes inspiration provenance auditable.
