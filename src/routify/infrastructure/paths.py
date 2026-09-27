"""Path helpers for data, exports, and vendored web assets."""

from __future__ import annotations

from pathlib import Path

from routify.config import DATA_DIR, DEFAULT_OSM_PATH, PROJECT_ROOT


def data_path(name: str) -> Path:
    return DATA_DIR / name


def default_osm_path() -> Path:
    if DEFAULT_OSM_PATH.is_file():
        return DEFAULT_OSM_PATH
    legacy = PROJECT_ROOT.parent / "project" / "export.osm"
    return legacy if legacy.is_file() else DEFAULT_OSM_PATH


def web_vendor_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "presentation" / "gui" / "web_vendor"


def default_map_html_path() -> Path:
    return web_vendor_dir() / "routify_map.html"
