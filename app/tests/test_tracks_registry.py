"""Registry integrity (multi-track WP-R / R8) — the declarative nav in
`app/frontend/tracks.py` must stay internally consistent so the router, the
Overview page and the deep links never drift from what is on disk.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.frontend import tracks

_ROOT = Path(__file__).resolve().parents[2]
# Metadata checks span all declared tracks; import/orphan checks span only
# INSTALLED tracks, so `rm -rf app/tracks/<t04|t05>` keeps this suite green.
_ALL_PAGES = [p for t in tracks.TRACKS for p in t.pages]
_INSTALLED_PAGES = [p for t in tracks.installed_tracks() for p in t.pages]


def test_every_page_module_resolves():
    """Each INSTALLED PageSpec imports and exposes its render callable."""
    for p in _INSTALLED_PAGES:
        mod = importlib.import_module(p.module)
        fn = getattr(mod, p.attr, None)
        assert callable(fn), f"{p.key}: {p.module}.{p.attr} is not callable"


def test_registry_keys_unique():
    keys = [p.key for p in _ALL_PAGES]
    assert len(keys) == len(set(keys)), "duplicate registry keys"


def test_titles_unique():
    titles = [p.title for p in _ALL_PAGES]
    assert len(titles) == len(set(titles)), "duplicate page titles"


def test_url_paths_unique_and_flat():
    """url_paths must be unique (hash collisions otherwise) and flat (no '/')."""
    non_default = [p for p in _ALL_PAGES if not p.default]
    paths = [p.url_path for p in non_default]
    assert len(paths) == len(set(paths)), "duplicate url_paths"
    assert all("/" not in up and up for up in paths), "url_path must be flat and non-empty"


def test_exactly_one_default_page():
    defaults = [p for p in _ALL_PAGES if p.default]
    assert len(defaults) == 1, f"expected exactly one default page, got {len(defaults)}"
    assert defaults[0].url_path == "", "the default (root) page's url_path must be ''"


def test_submission_deep_links_present():
    """D11 stable deep links must map to the track start pages."""
    by_path = {p.url_path: p.key for p in _ALL_PAGES}
    assert by_path.get("track03") == "t03.run"
    assert by_path.get("track04") == "t04.portfolio"
    assert by_path.get("track05") == "t05.desk"


def test_no_orphan_page_files():
    """Every page module on disk (under track pages/ or frontend/views/) is
    registered — no page ships that the nav never lists."""
    registered = {importlib.import_module(p.module).__file__ for p in _INSTALLED_PAGES}
    registered = {str(Path(f).resolve()) for f in registered}
    on_disk = set()
    for base in [_ROOT / "app" / "frontend" / "views",
                 *( _ROOT / "app" / "tracks").glob("*/pages")]:
        if base.exists():
            for f in base.glob("*.py"):
                if f.name != "__init__.py":
                    on_disk.add(str(f.resolve()))
    orphans = on_disk - registered
    assert not orphans, f"unregistered page files: {sorted(orphans)}"


def test_installed_tracks_autodetect():
    """Platform + Reference are always present; track folders drive the rest."""
    installed_ids = {t.id for t in tracks.installed_tracks()}
    assert {"platform", "ref"} <= installed_ids
    # t03 folder exists in the live tree, so t03 must be detected as installed.
    assert (_ROOT / "app" / "tracks" / "t03_financial_health").exists()
    assert "t03" in installed_ids
