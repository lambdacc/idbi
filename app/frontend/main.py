"""CreditPulse Platform — the st.navigation router entrypoint (multi-track D1/D2).

Launched via `streamlit run app/frontend/main.py`. Runs on every rerun: it sets
up the shell chrome once (`ui.shell_setup` — page config, CSS, brand, view
toggle), builds the grouped navigation from the declarative `tracks.py` registry
(installed tracks only, D10), and runs the selected page.

MUST be named `main.py`, NOT `app.py`: a file named `app.py` inside
`app/frontend/` shadows the top-level `app` package (Streamlit puts the
entrypoint's directory on sys.path), so `import app.backend …` resolves to the
router file → `ModuleNotFoundError: … 'app' is not a package`. See wp-s-findings.
"""
from __future__ import annotations

import sys
from pathlib import Path

# --- sys.path bootstrap (harden per wp-s CRITICAL note) ----------------------
# Insert the repo root at sys.path[0] UNCONDITIONALLY: remove any stale copy
# first, then insert at the front, so the entrypoint's own directory can never
# win `import app` resolution regardless of prior sys.path state.
_ROOT = Path(__file__).resolve().parents[2]
_root_str = str(_ROOT)
while _root_str in sys.path:
    sys.path.remove(_root_str)
sys.path.insert(0, _root_str)

import streamlit as st  # noqa: E402

from app.frontend import tracks  # noqa: E402
from app.frontend.components import ui  # noqa: E402

# Shell chrome first — set_page_config must be the run's first Streamlit command,
# ahead of the navigation delta and every page body.
ui.shell_setup()

# Grouped navigation from the registry (installed tracks only). Section order is
# dict insertion order: Platform, Track 03/04/05, Reference (wp-s Q1).
nav = st.navigation(tracks.build_navigation(), position="sidebar", expanded=True)
nav.run()
