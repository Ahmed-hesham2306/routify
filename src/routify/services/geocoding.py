"""Nominatim geocoding with throttle and cache."""

from __future__ import annotations

import threading
import time
import urllib.parse
from typing import Any

import requests

from routify.config import NOMINATIM_USER_AGENT

_BASE = "https://nominatim.openstreetmap.org"
_last_call = 0.0
_lock = threading.Lock()
_reverse_cache: dict[tuple[int, int], str] = {}
_forward_cache: dict[str, tuple[float, float]] = {}


def _throttle() -> None:
    global _last_call
    with _lock:
        now = time.monotonic()
        wait = 1.15 - (now - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()


def reverse_geocode(lat: float, lon: float) -> str:
    key = (round(lat, 4), round(lon, 4))
    if key in _reverse_cache:
        return _reverse_cache[key]
    _throttle()
    params = urllib.parse.urlencode(
        {"lat": lat, "lon": lon, "format": "json", "addressdetails": "1"}
    )
    try:
        r = requests.get(
            f"{_BASE}/reverse?{params}",
            headers={"User-Agent": NOMINATIM_USER_AGENT, "Accept-Language": "en"},
            timeout=15,
        )
        r.raise_for_status()
        payload: Any = r.json()
    except Exception:
        return f"{lat:.5f}, {lon:.5f}"
    name = payload.get("display_name") or payload.get("name")
    if not name:
        return f"{lat:.5f}, {lon:.5f}"
    label = str(name).strip()
    if len(label) > 120:
        label = label[:117] + "…"
    _reverse_cache[key] = label
    return label


def forward_geocode(query: str, *, viewbox: str | None = None) -> tuple[float, float] | None:
    qkey = query.strip().lower()
    if not qkey:
        return None
    cache_key = f"{qkey}|{viewbox or ''}"
    if cache_key in _forward_cache:
        return _forward_cache[cache_key]
    _throttle()
    payload: dict[str, str] = {"q": query, "format": "json", "limit": "1"}
    if viewbox:
        payload["viewbox"] = viewbox
        payload["bounded"] = "1"
    params = urllib.parse.urlencode(payload)
    try:
        r = requests.get(
            f"{_BASE}/search?{params}",
            headers={"User-Agent": NOMINATIM_USER_AGENT, "Accept-Language": "en"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None
    if not isinstance(data, list) or not data:
        return None
    lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
    _forward_cache[cache_key] = (lat, lon)
    return lat, lon
