"""snap lat/lon coordinates to nodes in the routable road database."""

from __future__ import annotations

import math
from typing import Any

import networkx as nx

from routify.algorithms.graph.adjacency_list import Graph as RoutifyGraph


#---------------------------------------------------------------------------
#data structure – spatial snapping logic
#---------------------------------------------------------------------------
#finds the nearest valid graph node to a raw gps coordinate using the
#haversine formula. relies on hash table lookups to cross-reference
#openstreetmap nodes with our custom routable network.
#
#variables: n = osm graph nodes, k = route graph nodes
#
#space complexity: o(1) — no new arrays created, just storing best distances
#┌────────────────────────────┬───────────────────────────────┐
#│ operation                  │ time (worst)                  │
#├────────────────────────────┼───────────────────────────────┤
#│ _haversine_m()             │ o(1)                          │
#│ snap_latlon_to_route_graph │ o(n + k)                      │
#│ node_latlon_on_osm()       │ o(1)                          │
#└────────────────────────────┴───────────────────────────────┘
#---------------------------------------------------------------------------


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    #calculates the direct physical distance in meters between two earth coordinates.
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def snap_latlon_to_route_graph(
    lat: float,
    lon: float,
    osm_graph: nx.MultiDiGraph,
    route_graph: RoutifyGraph,
) -> Any:
    """
    Snap a coordinate to the nearest routable node in the CSV database.
    Prefers nodes present on both OSM (for map coords) and the CSV graph.
    """
    #scans the network to find the closest physical road node to where you tapped.
    best_id: Any | None = None
    best_d = math.inf
    
    #first pass loops through map nodes and ignores ones not in our routing system.
    for nid in osm_graph.nodes:
        key = str(nid)
        if key not in route_graph.network:
            continue
        data = osm_graph.nodes[nid]
        d = _haversine_m(lat, lon, float(data["y"]), float(data["x"]))
        if d < best_d:
            best_d, best_id = d, key
            
    #bail out early if we found a good match.
    if best_id is not None:
        return best_id
        
    #fallback pass checking our internal routes against the map data.
    for key in route_graph.network:
        if key not in osm_graph.nodes and str(key) not in osm_graph.nodes:
            continue
        node = key if key in osm_graph.nodes else str(key)
        data = osm_graph.nodes[node]
        d = _haversine_m(lat, lon, float(data["y"]), float(data["x"]))
        if d < best_d:
            best_d, best_id = d, key
            
    #throw an error if absolutely no valid road exists near the coordinates.
    if best_id is None:
        raise ValueError("no routable node near this coordinate in the road database.")
        
    return best_id


def node_latlon_on_osm(
    osm_graph: nx.MultiDiGraph,
    node_id: Any,
    *,
    fallback_lat: float,
    fallback_lon: float,
) -> tuple[float, float]:
    """Coordinates for a graph node (markers and route endpoints align with the network)."""
    #fetches the exact map coordinates for a node so we can draw it accurately.
    key = node_id if node_id in osm_graph.nodes else str(node_id)
    if key in osm_graph.nodes:
        data = osm_graph.nodes[key]
        return float(data["y"]), float(data["x"])
    return fallback_lat, fallback_lon
