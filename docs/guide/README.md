# `docs/guide/` — hand-authored operator guides (intentional exception)

**Read this before editing anything in this folder.**

The system is *markdown-authoritative, HTML-rendered*: almost every page is a `.md` file that
`render-html` turns into HTML, so you edit the markdown and the surface follows. **This folder is
the deliberate exception.** The files here are hand-authored HTML with **no markdown source** — they
are not produced by the render pipeline and there is nothing to "re-render."

## Why they're an exception

These are the first pages a new operator sees — the onboarding front door. They use bespoke design
(step boxes, guide cards, callouts, a top nav, their own `style.css`) that the generic markdown
template can't reproduce. Forcing them into markdown would flatten the thing that makes them good, so
they are maintained by hand, on purpose.

## The files

| File | What it is | Ships in Seed? |
|---|---|---|
| `deployment-guide.html` | Non-technical install/setup runbook — **canonical** deployment guide | Yes |
| `operator-guide.html` | Full stage-by-stage walk-through of running the system | Yes |
| `help.html` | Help & guides hub + the **canonical** operator FAQ (embedded, `#faq`) | Yes |
| `getting-started.html` | Short first-run orientation (content merged into operator-guide) | No (internal) |
| `uat-*.html` | UAT run sheets — internal release artifacts | No (internal) |
| `style.css` | Shared styling for the above | Yes |

"Ships in Seed?" is defined by the `build_seed` allowlist (`.claude/lib/build_seed.py`).

## The maintenance rule

1. **Edit the `.html` directly.** There is no `.md` to change — the HTML *is* the source. Do not
   create a parallel markdown copy of any of these; that reintroduces the drift this note exists to
   prevent (a change landing in one copy and missing the one the operator opens — the SYS-070 bug).
2. **These are the canonical operator-facing copies.** Point operator links here — specifically
   `help.html` for the FAQ (`help.html#faq`) and `deployment-guide.html` for setup. The
   `docs/playbooks/deployment-guide.md` and `docs/playbooks/faq.md` files are **retired redirect
   stubs**, not live content — do not edit them expecting the operator to see it.
3. **`help.html` embeds the FAQ on purpose.** The standalone `docs/playbooks/faq.html` is *not*
   shipped in the Seed, so linking out to it would break in a deployed copy. Keep the FAQ inline in
   `help.html`.

*History: this folder's exception was made explicit by SYS-075 (2026-07-15), after SYS-070's ownership
framing was edited into a markdown copy while the operator kept opening the un-updated hand-authored
HTML. See `system/backlog.yaml` SYS-075.*
