"""Bridge OSMnx street graphs to the custom adjacency-list Graph."""

from __future__ import annotations

from typing import Any

import networkx as nx
import osmnx as ox

from routify.algorithms.graph.adjacency_list import Graph


def build_routify_graph_from_osmnx(G: nx.MultiDiGraph) -> Graph:
    rg = Graph(quiet=True)
    for n, data in G.nodes(data=True):
        name = data.get("name") or data.get("ref") or f"Intersection_{n}"
        rg.add_location(n, str(name)[:120], quiet=True)
        # Store coordinates for A* haversine heuristic
        if "y" in data and "x" in data:
            rg._coords[n] = (float(data["y"]), float(data["x"]))

    for u, v, _k, d in G.edges(keys=True, data=True):
        length_m = float(d.get("length") or 0.0)
        travel_time = float(d.get("travel_time") or length_m or 1.0)
        if length_m <= 0.0:
            length_m = max(travel_time, 1e-6)
        rg.add_directed_edge(u, v, travel_time=travel_time, length_m=length_m, quiet=True)
    return rg


def get_cached_routify_graph(G: nx.MultiDiGraph) -> Graph:
    cached = getattr(G, "_routify_graph", None)
    if cached is None:
        cached = build_routify_graph_from_osmnx(G)
        G._routify_graph = cached  # type: ignore[attr-defined]
    return cached


def prepare_osmnx_graph(osm_path: str, *, retain_all: bool = False) -> nx.MultiDiGraph:
    path = str(osm_path)
    for tag in ("amenity", "shop", "healthcare", "name", "name:en"):
        if tag not in ox.settings.useful_tags_node:
            ox.settings.useful_tags_node.append(tag)
    G = ox.graph_from_xml(path, simplify=True, retain_all=retain_all)
    G = ox.routing.add_edge_speeds(G)
    G = ox.routing.add_edge_travel_times(G)
    return G


def resolve_endpoint(G: nx.MultiDiGraph, text: str) -> int | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        nid = int(raw)
        return nid if nid in G else None
    for sep in (",", ";"):
        if sep in raw:
            parts = [p.strip() for p in raw.split(sep, 1)]
            if len(parts) == 2:
                try:
                    lat, lon = float(parts[0]), float(parts[1])
                except ValueError:
                    return None
                return ox.distance.nearest_nodes(G, X=lon, Y=lat)
    tokens = raw.replace(",", " ").split()
    if len(tokens) == 2:
        try:
            lat, lon = float(tokens[0]), float(tokens[1])
        except ValueError:
            return None
        return ox.distance.nearest_nodes(G, X=lon, Y=lat)
    return None
