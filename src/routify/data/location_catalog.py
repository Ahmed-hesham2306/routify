"""Named places from project database (CSV) snapped to the road graph."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import osmnx as ox

from routify.algorithms.graph.adjacency_list import Graph as RoutifyGraph
from routify.algorithms.search.binary_search import binary_search
from routify.algorithms.sorting.sorts import quick_sort
from routify.config import DATA_DIR
from routify.data.graph_snap import node_latlon_on_osm, snap_latlon_to_route_graph

log = logging.getLogger("routify")

NAMED_PLACES_CSV = DATA_DIR / "named_places.csv"


# ---------------------------------------------------------------------------
# DATA STRUCTURE – Location Catalog
# ---------------------------------------------------------------------------
# Maintains a curated list of named places and a hash table for database lookups.
# The internal list is sorted alphabetically by display_name to allow O(log N)
# lookups via binary search.
#
# Variables: N = number of named places, V = graph vertices, E = graph edges, C = csv size
#
# Space complexity: O(N) — O(N) for the list of places + O(N) for the sets
# ┌────────────────────────────┬───────────────────────────────┐
# │ Operation                  │  Time (worst)                 │
# ├────────────────────────────┼───────────────────────────────┤
# │ get_by_display_name(name)  │ O(log N)                      │
# │ get_node_id(name)          │ O(log N)                      │
# │ build_from_graph()         │ O(N log N + N * snap_time)    │
# └────────────────────────────┴───────────────────────────────┘
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlaceOption:
    """One selectable origin/destination from the location database."""

    node_id: Any
    display_name: str
    lat: float
    lon: float
    source: str  # "landmark" | "database"


class LocationCatalog:
    """Curated named locations + optional lookup in locations.csv."""

    def __init__(self) -> None:
        self._places: list[PlaceOption] = []  # Main storage for sorted place options
        self._seen_names: set[str] = set()    # O(1) deduplication cache during build phase

    @property
    def places(self) -> list[PlaceOption]:
        # Time: O(N) — creates a shallow copy of the internal list
        return list(self._places)

    def display_names(self) -> list[str]:
        # Time: O(N) — one pass over the list to extract strings
        return [p.display_name for p in self._places]

    def get_by_display_name(self, name: str) -> PlaceOption | None:
        # Time: O(log N) — binary search on the alphabetically sorted places list
        target = name.strip().lower()
        idx = binary_search(self._places, target, key_func=lambda p: p.display_name.lower())
        if idx != -1:
            return self._places[idx]
        return None

    def get_node_id(self, display_name: str) -> Any | None:
        # Time: O(log N) — delegates to binary search
        p = self.get_by_display_name(display_name)
        return p.node_id if p else None

    def build_from_graph(
        self,
        osm_graph: nx.MultiDiGraph,
        route_graph: RoutifyGraph | None = None,
        *,
        named_places_path: Path | None = None,
    ) -> int:
        """
        Build named picker options snapped to the road network.
        Uses CSV graph when provided; otherwise validates against the OSM street graph.
        """
        # Time: O(N log N + N * S) — reads N points, does spatial query S for each, then quicksorts O(N log N)
        self._places.clear()
        self._seen_names.clear()
        path = named_places_path or NAMED_PLACES_CSV

        if path.is_file():
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = (row.get("name") or "").strip()
                    if not name:
                        continue
                    try:
                        lat = float(row["lat"])
                        lon = float(row["lon"])
                    except (KeyError, ValueError):
                        continue
                    try:
                        # Attempt to snap the raw coordinates to actual graph nodes
                        if route_graph is not None:
                            node_key = snap_latlon_to_route_graph(
                                lat, lon, osm_graph, route_graph
                            )
                        else:
                            node_key = ox.distance.nearest_nodes(osm_graph, X=lon, Y=lat)
                            if node_key not in osm_graph:
                                continue
                    except Exception as exc:  # noqa: BLE001
                        log.debug("skip %s: %s", name, exc)
                        continue
                    lat, lon = node_latlon_on_osm(
                        osm_graph, node_key, fallback_lat=lat, fallback_lon=lon
                    )
                    self._add_place(node_key, name, lat, lon, "landmark")

        # Sort the entire list alphabetically to enable O(log N) binary search lookups later
        quick_sort(self._places, key_func=lambda p: p.display_name.lower())
        log.info("Location catalog: %d named places (database)", len(self._places))
        return len(self._places)

    def _add_place(
        self, node_id, display_name: str, lat: float, lon: float, source: str
    ) -> None:
        # Time: O(1) average — set lookup and list append
        key = display_name.strip()
        lower_key = key.lower()
        if lower_key in self._seen_names:
            return  # Prevent exact name duplicates
        opt = PlaceOption(
            node_id=node_id, display_name=key, lat=lat, lon=lon, source=source
        )
        self._places.append(opt)
        self._seen_names.add(lower_key)
