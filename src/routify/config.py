"""Application configuration and default paths."""

from __future__ import annotations

from pathlib import Path

# Repository root (Routify/) — two levels above this file: src/routify/config.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OSM_PATH = DATA_DIR / "export.osm"
DEFAULT_LOCATIONS_CSV = DATA_DIR / "locations.csv"
DEFAULT_ROADS_CSV = DATA_DIR / "roads.csv"

# Map focus: New Cairo, Egypt
DEFAULT_CENTER_LAT = 30.02
DEFAULT_CENTER_LON = 31.49
DEFAULT_ZOOM = 14

NOMINATIM_USER_AGENT = "RoutifyDesktop/1.0 (university project; OSM routing UI)"
