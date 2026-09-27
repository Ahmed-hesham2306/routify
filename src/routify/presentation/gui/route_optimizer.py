"""Nearest-neighbor stop-order optimization for multi-stop routes."""

from __future__ import annotations

import math

from routify.data.location_catalog import PlaceOption


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon points."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def optimize_stop_order(
    origin: PlaceOption,
    waypoints: list[PlaceOption],
) -> list[int]:
    """Return indices into waypoints in visit order (nearest-neighbor from origin).

    Origin and final destination stay fixed; only intermediate waypoints
    are reordered to minimize total travel distance.
    """
    # Time:  O(W²)   — W = len(waypoints); each iteration scans remaining list
    # Space: O(W)    — order and remaining lists
    if not waypoints:
        return []
    remaining = list(range(len(waypoints)))
    order: list[int] = []
    cur_lat, cur_lon = origin.lat, origin.lon

    while remaining:
        best_i, best_d = remaining[0], math.inf
        for i in remaining:
            w = waypoints[i]
            d = _haversine_m(cur_lat, cur_lon, w.lat, w.lon)
            if d < best_d:
                best_d, best_i = d, i
        order.append(best_i)
        remaining.remove(best_i)
        cur_lat, cur_lon = waypoints[best_i].lat, waypoints[best_i].lon
    return order
