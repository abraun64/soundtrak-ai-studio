"""Shared top-right pill nav (Help & guides + Library) for operator surfaces that are
built OUTSIDE the render-html pipeline — the asset-gallery and the System Manager
dashboard. Keeps their header identical to every render-html surface.

Mirrors render-html/render.py::build_library_nav: each pill renders ONLY if its target
file exists, so a link here can never 404. In a fresh client Seed the library ships
EMPTY, so the Library pill is simply omitted until the operator builds one
(/library-add creates tenant/library/INDEX.html); Help & guides (docs/guide/help.html)
ships with every deployment, so it is always present.

Keep the pill markup in sync with build_library_nav so all surfaces match.
"""
from __future__ import annotations

from pathlib import Path


def top_nav_pills(project_root: Path, prefix: str) -> str:
    """Return the <nav class="library-nav"> pill bar, or "" if nothing to show.

    project_root : the deployment root (where docs/ and tenant/ live).
    prefix       : relative path from the OUTPUT page's directory up to project_root,
                   e.g. "../" for system/dashboard.html, "../../" for
                   campaigns/<slug>/gallery.html.
    """
    links = []
    if (project_root / "docs/guide/help.html").exists():
        links.append(
            f'<a class="lib-link" href="{prefix}docs/guide/help.html" '
            f'title="Help &amp; guides — deployment, operator guide, FAQ">📖 Help &amp; guides</a>'
        )
    if (project_root / "tenant/library/INDEX.html").exists():
        links.append(
            f'<a class="lib-link" href="{prefix}tenant/library/INDEX.html" '
            f'title="Best-Practice Library — creative exemplars &amp; gold standards">📚 Best-Practice Library</a>'
        )
    if (project_root / "tenant/research-library/INDEX.html").exists():
        links.append(
            f'<a class="lib-link" href="{prefix}tenant/research-library/INDEX.html" '
            f'title="Insights Library — the shared research corpus the Insights Manager cites">🔎 Insights Library</a>'
        )
    if not links:
        return ""
    return f'<nav class="library-nav" aria-label="Site links">{"".join(links)}</nav>'
