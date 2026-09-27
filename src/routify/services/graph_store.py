"""Process-wide graph handles (avoid passing huge graphs through Qt signals)."""

from __future__ import annotations

import os

import networkx as nx

from routify.algorithms.graph.adjacency_list import Graph as RoutifyGraph
from routify.data.location_catalog import LocationCatalog
from routify.services.graph_bridge import get_cached_routify_graph

_osm_graph: nx.MultiDiGraph | None = None
_route_graph: RoutifyGraph | None = None  # full CSV database (optional)
_catalog: LocationCatalog | None = None
# Full CSV road database (~71k nodes) is the default for routing accuracy.
# Set ROUTIFY_LIGHT=1 to use only the smaller OSM network (~13k nodes).
_use_light_osm_only: bool = os.environ.get("ROUTIFY_LIGHT", "").strip() in ("1", "true", "yes")


def use_full_csv_database() -> bool:
    return not _use_light_osm_only


def set_graphs(
    osm: nx.MultiDiGraph,
    catalog: LocationCatalog,
    route: RoutifyGraph | None = None,
) -> None:
    global _osm_graph, _route_graph, _catalog
    _osm_graph = osm
    _route_graph = route
    _catalog = catalog


def get_routify_graph() -> RoutifyGraph:
    """Routing graph: full CSV if loaded, otherwise OSM street network (~13k nodes)."""
    if _route_graph is not None:
        return _route_graph
    if _osm_graph is None:
        raise RuntimeError("Street graph not loaded.")
    return get_cached_routify_graph(_osm_graph)


def get_osm_graph() -> nx.MultiDiGraph | None:
    return _osm_graph


def get_route_graph() -> RoutifyGraph | None:
    """Full CSV graph when ROUTIFY_FULL_CSV=1 was used at startup."""
    return _route_graph


def get_catalog() -> LocationCatalog | None:
    return _catalog


def clear() -> None:
    global _osm_graph, _route_graph, _catalog
    _osm_graph = None
    _route_graph = None
    _catalog = None
