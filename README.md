# Soundtrak AI Studio

*The AI studio that 10Xs your marketing — from Soundtrak Consulting.*

> **⚠️ COMMERCIAL USE IS NOT PERMITTED.**
> This software is licensed only for the **internal business use** of you and your own company
> (including marketing your own business). **Agency use, client work, SaaS or hosted offerings,
> resale, OEM use, and any other commercialisation require a separate commercial licence** from
> Soundtrak Consulting. **By cloning, downloading, installing, or using this repository you agree
> to the licence** — see [`LICENSE`](LICENSE). Not open source.

A multi-agent marketing system built on Claude Code. A **Campaign Manager** skill
orchestrates specialist agents (Creative Director, Brand Manager, Producer, Governance,
Insights) to take a campaign from brief to shipped, brand-checked assets - with the
operator approving at every gate. Markdown-authoritative on disk; HTML operator surfaces
rendered on every change; no third-party platform lock-in.

This is a **single-tenant instance**: set it up for one business, run campaigns, own and
evolve the code.

## First run (about 5 minutes)

**Prerequisites:** Python 3.10+ (with the `python` command on your PATH) and Claude Code.
New to this? Follow **`docs/guide/deployment-guide.html`** - it walks the whole install from zero.

1. Open Claude Code in this folder and say **"set yourself up"**. It shows the licence, installs
   what's needed (`markdown`, `pyyaml`, and optional `playwright` for gallery thumbnails), turns on
   backup, and reports **READY**. *(Prefer the terminal? `pip install -r requirements.txt`, then
   `python .claude/skills/system-smoke-test/doctor.py --fix --accept-license`.)*
2. Then say **"Onboard <your business>"**. The Campaign Manager runs **Phase 0** (your tenant
   baseline) - required before any campaign can start.

The operating manual is `docs/workflow.md`; the illustrated guides live in `docs/guide/`
(open `docs/guide/help.html`).

## Layout

| Path | What |
|---|---|
| `.claude/` | the engine - skills, agents, hooks, settings |
| `docs/` | operating manual (`workflow.md`), specs, playbooks, role overviews |
| `craft/` | the Producer's craft lenses |
| `tenant-brand/` / `tenant/` | your tenant baseline (empty until you onboard) |
| `campaigns/` | your campaigns (empty until you start one) |
| `system/` | the System Manager - backlog/ideas/audit for improving the system itself |

## Help & guides

Open **`docs/guide/help.html`** in your browser — the home for everything: the deployment
guide, getting started, the illustrated training guide, and the FAQ.

## License

Licensed under the **PolyForm Internal Use License 1.0.0** — free for the internal business
operations of you and your company (including marketing your own business). It is **not** for
serving clients, reselling, hosting, or redistribution. Agencies may use it for their own
business but not for their clients. For agency/client, reseller, or hosted use, contact
Soundtrak Consulting for a commercial license. Full terms: `LICENSE`; trademark + data notes: `docs/legal/`.
