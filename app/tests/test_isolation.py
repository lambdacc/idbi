"""Track-isolation linter (multi-track D10) — enforces that:

  1. no track imports from a DIFFERENT track (`app.tracks.tXX` from `app.tracks.tYY`);
  2. platform core (`app/frontend`, `app/ml`, `app/data_gen`, `app/backend`) does
     not import `app.tracks.*` — except at the guarded discovery points (the
     registry, prefit warm, and state engine wrappers), which reach tracks only
     via runtime path-existence checks / lazy imports so a deleted track folder
     never breaks core.

This is what makes `rm -rf app/tracks/<any>` leave a fully-working app.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_TRACKS = _ROOT / "app" / "tracks"
_CORE_DIRS = ["app/frontend", "app/ml", "app/data_gen", "app/backend"]

# Core files allowed to reference app.tracks.* (guarded discovery points). These
# reach tracks lazily / behind path-existence checks, never as hard top-level deps.
_CORE_TRACK_ALLOWLIST = {
    "app/frontend/tracks.py",       # the registry (importlib, folder-existence gated)
    "app/frontend/components/state.py",   # engine wrappers + guarded require_assessment link
    "app/ml/prefit.py",             # track-aware engine warm (guarded discovery)
}


def _imported_modules(path: Path) -> set[str]:
    """All dotted module names referenced by import statements in `path`."""
    tree = ast.parse(path.read_text(), filename=str(path))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module)
    return mods


def _track_of(module: str) -> str | None:
    """Return the track package name (e.g. 't03_financial_health') a dotted
    module belongs to, or None if it is not under app.tracks."""
    parts = module.split(".")
    if len(parts) >= 3 and parts[0] == "app" and parts[1] == "tracks":
        return parts[2]
    return None


def test_no_cross_track_imports():
    """A track's files never import another track's package."""
    violations = []
    for py in _TRACKS.rglob("*.py"):
        owner = _track_of("app.tracks." + py.relative_to(_TRACKS).parts[0])
        for mod in _imported_modules(py):
            other = _track_of(mod)
            if other is not None and other != owner:
                violations.append(f"{py.relative_to(_ROOT)} imports {mod}")
    assert not violations, "cross-track imports found:\n" + "\n".join(violations)


def test_core_does_not_import_tracks_except_guarded():
    """Core packages never hard-import app.tracks.* outside the allowlist."""
    violations = []
    for d in _CORE_DIRS:
        for py in (_ROOT / d).rglob("*.py"):
            rel = str(py.relative_to(_ROOT))
            if rel in _CORE_TRACK_ALLOWLIST:
                continue
            for mod in _imported_modules(py):
                if _track_of(mod) is not None:
                    violations.append(f"{rel} imports {mod}")
    assert not violations, ("core imports a track outside the guarded allowlist:\n"
                            + "\n".join(violations))
