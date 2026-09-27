"""Road-following map polylines (always on OSM street geometry, never straight CSV hops)."""

from __future__ import annotations

from typing import Any

import networkx as nx
import osmnx as ox

from routify.data.location_catalog import PlaceOption


def _ensure_node_type(G: nx.MultiDiGraph, node: Any) -> Any:
    if node in G.nodes:
        return node
    try:
        if int(node) in G.nodes:
            return int(node)
    except (ValueError, TypeError):
        pass
    if str(node) in G.nodes:
        return str(node)
    return node

def _node_latlon(G: nx.MultiDiGraph, node: Any) -> tuple[float, float]:
    key = _ensure_node_type(G, node)
    if key not in G.nodes:
        raise KeyError(node)
    data = G.nodes[key]
    return float(data["y"]), float(data["x"])


def _undirected_osm_graph(G: nx.MultiDiGraph) -> nx.Graph:
    """Undirected street view for display routing when one-ways block a path."""
    uG = nx.Graph()
    for u, v, _k, data in G.edges(keys=True, data=True):
        w = float(data.get("travel_time") or data.get("length") or 1.0)
        if uG.has_edge(u, v):
            if uG[u][v]["weight"] > w:
                uG[u][v]["weight"] = w
        else:
            uG.add_edge(u, v, weight=w)
    return uG


def osm_street_path_nodes(
    G: nx.MultiDiGraph,
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> list[Any]:
    """Shortest path on the OSM street layer between two coordinates."""
    o = ox.distance.nearest_nodes(G, X=lon1, Y=lat1)
    d = ox.distance.nearest_nodes(G, X=lon2, Y=lat2)
    if o == d:
        return [o]
    try:
        return nx.shortest_path(G, o, d, weight="travel_time")
    except nx.NetworkXNoPath:
        uG = _undirected_osm_graph(G)
        return nx.shortest_path(uG, o, d, weight="weight")


def _edge_geometry_bidirectional(
    G: nx.MultiDiGraph, u: Any, v: Any
) -> tuple[Any | None, bool]:
    """
    Return (geometry, reversed) for edge u→v or v→u.
    reversed=True means coordinates should be flipped to walk u→v.
    """
    u_key = _ensure_node_type(G, u)
    v_key = _ensure_node_type(G, v)
    if G.has_edge(u_key, v_key):
        edges = G.get_edge_data(u_key, v_key)
        forward = True
    elif G.has_edge(v_key, u_key):
        edges = G.get_edge_data(v_key, u_key)
        forward = False
    else:
        return None, False

    best, best_len = None, -1.0
    for _k, data in edges.items():
        geom = data.get("geometry")
        if geom is None:
            continue
        length = getattr(geom, "length", 0.0) or 0.0
        if length > best_len:
            best_len, best = length, geom
    return best, not forward


def _orient_segment(
    G: nx.MultiDiGraph, u: Any, v: Any, geom, *, reversed_geom: bool
) -> list[list[float]]:
    if geom is None:
        return []
    latlon = [[float(c[1]), float(c[0])] for c in geom.coords]
    if reversed_geom:
        latlon.reverse()
    return latlon


def _edge_latlon_segment(G: nx.MultiDiGraph, u: Any, v: Any) -> list[list[float]]:
    """One hop using stored OSM edge geometry, or node coordinates if none."""
    geom, rev = _edge_geometry_bidirectional(G, u, v)
    if geom is not None:
        seg = _orient_segment(G, u, v, geom, reversed_geom=rev)
        if len(seg) >= 2:
            return seg
    try:
        uy, ux = _node_latlon(G, u)
        vy, vx = _node_latlon(G, v)
        return [[uy, ux], [vy, vx]]
    except KeyError:
        return []


def _street_segment_latlon(G: nx.MultiDiGraph, u: Any, v: Any) -> list[list[float]]:
    """Follow drivable streets between two graph nodes (never a straight off-road hop)."""
    geom, rev = _edge_geometry_bidirectional(G, u, v)
    if geom is not None:
        seg = _orient_segment(G, u, v, geom, reversed_geom=rev)
        if len(seg) >= 2:
            return seg
    try:
        uy, ux = _node_latlon(G, u)
        vy, vx = _node_latlon(G, v)
        subpath = osm_street_path_nodes(G, uy, ux, vy, vx)
        return _latlon_from_path_geometry(G, subpath)
    except (KeyError, nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def _latlon_from_path_geometry(G: nx.MultiDiGraph, path_nodes: list[Any]) -> list[list[float]]:
    """Concatenate edge geometries along a node path (no extra street routing)."""
    if len(path_nodes) < 2:
        return []
    out: list[list[float]] = []
    for i in range(len(path_nodes) - 1):
        seg = _edge_latlon_segment(G, path_nodes[i], path_nodes[i + 1])
        if len(seg) < 2:
            continue
        if not out:
            out.extend(seg)
        elif out[-1] == seg[0]:
            out.extend(seg[1:])
        else:
            out.extend(seg)
    return out


def path_to_road_aligned_latlon(G: nx.MultiDiGraph, path_nodes: list[Any]) -> list[list[float]]:
    """Build a dense polyline that follows road centerlines between consecutive path nodes."""
    if len(path_nodes) < 2:
        if len(path_nodes) == 1:
            try:
                lat, lon = _node_latlon(G, path_nodes[0])
            except KeyError:
                return []
            return [[lat, lon]]
        return []

    out: list[list[float]] = []
    for i in range(len(path_nodes) - 1):
        u, v = path_nodes[i], path_nodes[i + 1]
        seg = _street_segment_latlon(G, u, v)
        if len(seg) < 2:
            continue
        if not out:
            out.extend(seg)
        elif out[-1] == seg[0]:
            out.extend(seg[1:])
        else:
            out.extend(seg)
    return out


def _same_point(a: list[float], b: list[float], *, eps: float = 1e-5) -> bool:
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


def anchor_polyline_to_places(
    line: list[list[float]],
    origin: PlaceOption,
    destination: PlaceOption,
) -> list[list[float]]:
    """Connect road polyline to pin coordinates (short connector if needed)."""
    start = [origin.lat, origin.lon]
    end = [destination.lat, destination.lon]
    if not line:
        return [start, end]
    out = [list(p) for p in line]
    if not _same_point(out[0], start):
        out.insert(0, start)
    if not _same_point(out[-1], end):
        out.append(end)
    return out


def _merge_polylines(base: list[list[float]], extra: list[list[float]]) -> list[list[float]]:
    if not extra:
        return base
    if not base:
        return list(extra)
    if base[-1] == extra[0]:
        base.extend(extra[1:])
    else:
        base.extend(extra)
    return base


def leg_polyline_on_osm(
    G: nx.MultiDiGraph,
    origin: PlaceOption,
    destination: PlaceOption,
    csv_path_nodes: list[Any] | None = None,
) -> list[list[float]]:
    """
    Map display polyline for one leg — always follows OSM street geometry.

    Routing may use the larger CSV graph; the map line is drawn on the OSM street
    layer between the stop coordinates so it never cuts across blocks off-road.
    """
    line: list[list[float]] = []
    try:
        path = osm_street_path_nodes(
            G, origin.lat, origin.lon, destination.lat, destination.lon
        )
        line = _latlon_from_path_geometry(G, path)
    except (nx.NetworkXNoPath, nx.NodeNotFound, KeyError, ValueError):
        line = []

    if len(line) < 2 and csv_path_nodes is not None and len(csv_path_nodes) > 1:
        try:
            line = path_to_road_aligned_latlon(G, csv_path_nodes)
        except (KeyError, nx.NetworkXNoPath, nx.NodeNotFound):
            line = []

    return anchor_polyline_to_places(line, origin, destination)
