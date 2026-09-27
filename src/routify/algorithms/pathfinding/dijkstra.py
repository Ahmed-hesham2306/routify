"""Dijkstra shortest paths on the custom adjacency-list graph (Member 2)."""

# Allow forward references in type hints (e.g. list[Any] before Any is used)
from __future__ import annotations

import math    # Used for math.inf to represent unreachable nodes
import time    # Used for high-resolution timing via perf_counter
from collections import defaultdict  # Lazy-init dicts to avoid O(V) upfront allocation
from typing import Any

from routify.algorithms.graph.adjacency_list import Graph
from routify.algorithms.heap.min_heap import MinHeap
from routify.domain.exceptions import RoutingError
from routify.domain.models import RouteResult

# ---------------------------------------------------------------------------
# ALGORITHM – Dijkstra's Shortest Path
# ---------------------------------------------------------------------------
# Single-source shortest path on a weighted directed graph with non-negative
# edge weights, implemented with a binary min-heap and lazy deletion.
#
# Variables: V = number of vertices, E = number of directed edges
#
# Time:  O((V + E) log V)
#   — Each vertex is inserted into the heap once:           O(V log V)
#   — Each edge may trigger a decrease_priority or insert:  O(E log V)
#   — Total dominated by the heap operations
#
# Space: O(V + E)
#   — dist[] and prev[] dictionaries:  O(V) each
#   — MinHeap can hold at most V nodes: O(V)
#   — The graph itself (adjacency list): O(V + E)
#
# alternative_paths_edge_removal runs Dijkstra up to (max_alternatives + 1)
# times, so its overall time is O(max_alternatives * (V + E) log V).
# ---------------------------------------------------------------------------


def _dijkstra_core(
    rg: Graph,
    origin: Any,
    destination: Any,
    weight_mode: str,
    *,
    edge_iter,                                  # Callable that yields (neighbor, weight) for a given node
    blocked_edges: set[tuple[Any, Any]] | None = None,  # Edges to skip (for alternative path generation)
) -> list[Any]:
    # Time:  O((V + E) log V) — see module-level complexity note above
    # Space: O(V)             — dist, prev, and heap each scale with vertex count
    # Validate that both endpoints exist in the graph before doing any work
    if origin not in rg.network or destination not in rg.network:
        raise RoutingError("Origin or destination not in Routify graph.")
    # Trivial case: origin and destination are the same node
    if origin == destination:
        return [origin]

    blocked_edges = blocked_edges or set()  # Use an empty set if no edges are blocked
    # Lazy-init: only nodes actually visited get an entry (saves O(V) upfront on 71k graphs)
    dist: dict[Any, float] = defaultdict(lambda: math.inf)
    # prev tracks the preceding node on the shortest path (for path reconstruction)
    prev: dict[Any, Any | None] = defaultdict(lambda: None)
    dist[origin] = 0.0  # The origin is 0 distance from itself

    # Use the custom MinHeap as the priority queue for the algorithm
    heap = MinHeap()
    heap.insert(origin, 0.0)  # Seed the heap with the origin at cost 0

    while not heap.is_empty():
        du, u = heap.pop_min()    # Pop the node with the current smallest known distance — O(log V)
        if du > dist[u]:
            continue            # Stale entry in the heap; skip it (lazy deletion pattern)
        if u == destination:
            break               # Shortest path to destination found; no need to continue
        for v, w in edge_iter(rg, u, weight_mode):      # Iterate over outgoing (or undirected) neighbors
            if (u, v) in blocked_edges:
                continue        # This edge is blocked; do not traverse it
            alt = dist[u] + w  # Candidate distance to v via u
            if alt < dist[v]:  # Relaxation: found a shorter path to v
                dist[v] = alt
                prev[v] = u    # Record u as v's predecessor on the new shortest path
                if heap.contains(v):
                    heap.decrease_priority(v, alt)  # Update v's priority if already in the heap — O(log V)
                else:
                    heap.insert(v, alt)             # Otherwise add v to the heap for the first time — O(log V)

    # If destination's distance is still infinity, no path exists
    if math.isinf(dist[destination]):
        raise RoutingError("No path between origin and destination.")

    # Reconstruct the path by following prev pointers back from destination to origin
    # Time: O(V) in the worst case (path visits every node)
    path: list[Any] = []
    cur: Any | None = destination
    while cur is not None:
        path.append(cur)   # Walk backwards, appending each predecessor
        cur = prev[cur]
    path.reverse()         # Reverse so the path runs from origin to destination
    return path


def dijkstra_shortest_path(
    rg: Graph,
    origin: Any,
    destination: Any,
    weight_mode: str,
    *,
    blocked_edges: set[tuple[Any, Any]] | None = None,
) -> list[Any]:
    """Return node sequence from origin to destination, or raise RoutingError."""
    # Time: O((V + E) log V) — delegates entirely to _dijkstra_core
    # Run the core algorithm with only outgoing (directed) edges
    return _dijkstra_core(
        rg,
        origin,
        destination,
        weight_mode,
        edge_iter=lambda g, u, m: g.iter_out_edges(u, m),  # Directed traversal only
        blocked_edges=blocked_edges,
    )


def dijkstra_undirected_shortest_path(
    rg: Graph,
    origin: Any,
    destination: Any,
    weight_mode: str,
) -> list[Any]:
    """Shortest path allowing reverse traversal (longer but connects more places)."""
    # Time: O((V + E) log V) — same as directed; edge count E may be up to 2× directed
    # Run the core algorithm with both forward and reverse edges (undirected fallback)
    return _dijkstra_core(
        rg,
        origin,
        destination,
        weight_mode,
        edge_iter=lambda g, u, m: g.iter_undirected_edges(u, m),  # Bidirectional traversal
    )


def flexible_shortest_path(
    rg: Graph,
    origin: Any,
    destination: Any,
    weight_mode: str,
) -> tuple[list[Any], bool]:
    """
    Prefer A* (fastest) → Dijkstra directed → Dijkstra undirected fallback.
    Returns (path, used_undirected_fallback).
    """
    # Time: O((V + E) log V) per attempt; A* is fastest in practice due to heuristic pruning
    try:
        # First attempt: A* with haversine heuristic (auto-falls back to Dijkstra if no coords)
        return (
            astar_shortest_path(rg, origin, destination, weight_mode),
            False,
        )
    except RoutingError:
        pass
    try:
        # Second attempt: plain directed Dijkstra (guaranteed optimal without heuristic)
        return (
            dijkstra_shortest_path(rg, origin, destination, weight_mode),
            False,
        )
    except RoutingError:
        # Third attempt: undirected Dijkstra (traverse one-way roads in reverse)
        return (
            dijkstra_undirected_shortest_path(rg, origin, destination, weight_mode),
            True,
        )


# ---------------------------------------------------------------------------
# ALGORITHM – A* Search (informed pathfinding)
# ---------------------------------------------------------------------------
# A* extends Dijkstra by adding a heuristic h(n) to the priority, so the heap
# orders nodes by f(n) = g(n) + h(n) where g = known cost and h = estimated
# remaining cost.  With an admissible heuristic (haversine ≤ true road dist),
# A* is optimal and typically expands 50-80% fewer nodes than Dijkstra.
#
# Time:  O((V + E) log V) worst case (same as Dijkstra), but practical runtime
#        is much smaller because the heuristic prunes large swaths of the graph.
# Space: O(V)  — dist, prev, heap
# ---------------------------------------------------------------------------


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon points."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def astar_shortest_path(
    rg: Graph,
    origin: Any,
    destination: Any,
    weight_mode: str,
    *,
    blocked_edges: set[tuple[Any, Any]] | None = None,
) -> list[Any]:
    """A* search using haversine heuristic.  Falls back to Dijkstra if coords are unavailable."""
    # Time:  O((V + E) log V) worst — but heuristic makes practical time << Dijkstra
    # Space: O(V)             — dist, prev, heap
    coords = getattr(rg, '_coords', {})
    if destination not in coords or origin not in coords:
        # No coordinates available — fall back to plain Dijkstra
        return dijkstra_shortest_path(rg, origin, destination, weight_mode, blocked_edges=blocked_edges)

    if origin not in rg.network or destination not in rg.network:
        raise RoutingError("Origin or destination not in Routify graph.")
    if origin == destination:
        return [origin]

    blocked_edges = blocked_edges or set()
    dest_lat, dest_lon = coords[destination]

    # Heuristic: straight-line distance to destination, converted to time estimate
    # assuming a generous 120 km/h max speed (admissible because real roads are slower)
    def h(node: Any) -> float:
        if node not in coords:
            return 0.0  # No coordinate → conservative zero heuristic (degrades to Dijkstra)
        n_lat, n_lon = coords[node]
        dist_m = _haversine_m(n_lat, n_lon, dest_lat, dest_lon)
        if weight_mode == "time":
            return dist_m / 33.33  # 120 km/h → 33.33 m/s (admissible upper-bound speed)
        return dist_m              # For distance mode, haversine ≤ road distance (admissible)

    dist: dict[Any, float] = defaultdict(lambda: math.inf)
    prev: dict[Any, Any | None] = defaultdict(lambda: None)
    dist[origin] = 0.0

    heap = MinHeap()
    heap.insert(origin, 0.0 + h(origin))  # f(start) = g(start) + h(start)

    while not heap.is_empty():
        _f, u = heap.pop_min()  # Pop node with lowest f = g + h
        if u == destination:
            break
        if _f > dist[u] + h(u) + 1e-9:  # Stale entry check (with float tolerance)
            continue
        for v, w in rg.iter_out_edges(u, weight_mode):
            if (u, v) in blocked_edges:
                continue
            alt = dist[u] + w
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                f_v = alt + h(v)  # f(v) = g(v) + h(v)
                if heap.contains(v):
                    heap.decrease_priority(v, f_v)
                else:
                    heap.insert(v, f_v)

    if math.isinf(dist[destination]):
        raise RoutingError("No path between origin and destination.")

    path: list[Any] = []
    cur: Any | None = destination
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def dijkstra_with_metrics(
    rg: Graph,
    origin: Any,
    destination: Any,
    weight_mode: str,
    *,
    blocked_edges: set[tuple[Any, Any]] | None = None,
) -> RouteResult:
    """Dijkstra returning path, cost, and timing metadata."""
    # Time: O((V + E) log V) for Dijkstra + O(P * deg) for cost summation
    #       where P = path length and deg = average out-degree; dominated by Dijkstra
    # Space: O(V) for Dijkstra internals + O(P) for the returned path list
    t0 = time.perf_counter()  # Record start time for elapsed measurement
    path = dijkstra_shortest_path(
        rg, origin, destination, weight_mode, blocked_edges=blocked_edges
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0  # Convert seconds to milliseconds
    total = 0.0
    # Walk consecutive node pairs on the path to sum up the actual edge weights
    # Time: O(P * deg) — for each of the P-1 edges, scan the out-edge list of the source node
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for nv, w in rg.iter_out_edges(u, weight_mode):
            if nv == v:
                total += w  # Add the weight of this specific edge segment
                break       # Found the edge; no need to check further neighbors
    # Package the results into a RouteResult dataclass for structured access
    return RouteResult(
        path=path,
        total_cost=total,
        weight_mode=weight_mode,
        nodes_visited=len(path),
        elapsed_ms=elapsed_ms,
    )


def alternative_paths_edge_removal(
    rg: Graph,
    origin: Any,
    destination: Any,
    weight_mode: str,
    *,
    max_alternatives: int = 3,
) -> list[list[Any]]:
    """Detour alternatives by blocking each edge on the primary shortest path."""
    # Time: O(P * (V + E) log V) — one Dijkstra run per edge on the primary path of length P
    #       In practice P << V, so this is much faster than the worst-case bound
    # Space: O(V + P) — Dijkstra internals dominate; path lists are O(P) each
    try:
        primary = dijkstra_shortest_path(rg, origin, destination, weight_mode)  # Find the primary shortest path first
    except RoutingError:
        return []  # No primary path means no alternatives either

    alts: list[list[Any]] = []                          # Accumulates unique alternative paths
    seen_paths: set[tuple[Any, ...]] = {tuple(primary)} # Tracks already-found paths to avoid duplicates

    for i in range(len(primary) - 1):      # Iterate over each edge on the primary path
        if len(alts) >= max_alternatives:
            break                           # Stop once we have enough alternatives
        a, b = primary[i], primary[i + 1]  # The edge to block in this iteration
        try:
            # Run Dijkstra again with this single edge removed to force a detour
            cand = dijkstra_shortest_path(
                rg, origin, destination, weight_mode, blocked_edges={(a, b)}
            )
        except RoutingError:
            continue  # Removing this edge disconnects the graph; skip it
        key = tuple(cand)
        if key not in seen_paths and cand != primary:
            seen_paths.add(key)  # Mark this path as seen so it won't be added twice
            alts.append(cand)   # Add the new detour to the results
    return alts
