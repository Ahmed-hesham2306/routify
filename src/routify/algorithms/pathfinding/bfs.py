"""Breadth-first search traversals (Member 2)."""

# Allow forward references in type hints
from __future__ import annotations

from collections import deque  # Double-ended queue for O(1) popleft (FIFO behavior)
from typing import Any

import networkx as nx  # Used for its MultiDiGraph type and OSM node attribute access

from routify.algorithms.graph.adjacency_list import Graph
from routify.algorithms.sorting.sorts import merge_sort

# ---------------------------------------------------------------------------
# ALGORITHM – Breadth-First Search
# ---------------------------------------------------------------------------
# Explores all neighbors at the current hop distance before moving further.
# Guarantees the shortest hop-count path in an unweighted graph.
#
# Variables: V = vertices reachable from start, E = edges examined
#
# Time:  O(V + E) — each reachable vertex is dequeued once; each edge is checked once
# Space: O(V)     — queue and seen set each hold at most V entries
# ---------------------------------------------------------------------------


def breadth_first_order(rg: Graph, start: Any, *, max_visit: int = 10_000) -> list[Any]:
    # Time:  O(V + E) — bounded by max_visit in practice
    # Space: O(V)     — queue + seen set; order list also grows to O(V)
    # Return an empty list immediately if the start node doesn't exist in the graph
    if start not in rg.network:
        return []
    order: list[Any] = []                # Accumulates nodes in BFS visit order
    q: deque[Any] = deque([start])       # Seed the queue with the starting node
    seen = {start}                        # Mark start as discovered to avoid re-adding it
    while q and len(order) < max_visit:  # Continue until queue is empty or limit is hit
        u = q.popleft()                  # Dequeue the oldest node (FIFO = breadth-first) — O(1) with deque
        order.append(u)                  # Record the node in traversal order
        for v in rg.iter_out_neighbors(u):  # Visit all outgoing neighbors of u
            if v not in seen:
                seen.add(v)              # Mark as discovered immediately to prevent duplicate enqueues
                q.append(v)             # Add to the back of the queue for later processing — O(1)
    return order                         # Return the full BFS visit sequence


def filter_pois_near_route_bfs(
    G: nx.MultiDiGraph,        # Full OSM graph containing node attribute data (name, amenity, etc.)
    rg: Graph,                 # Routify custom graph for neighbor traversal
    route_nodes: list[Any],    # Ordered list of nodes forming the route corridor
    poi_type: str,             # OSM amenity value to match (e.g. "restaurant", "pharmacy")
    *,
    max_hops: int = 60,        # Maximum BFS hops away from a seed node before stopping expansion
    max_results: int = 20,     # Maximum number of matching POIs to return
) -> list[dict[str, Any]]:
    """BFS from route seeds to find OSM amenities near the corridor."""
    # Time:  O(V + E) within the hop-limited subgraph rooted at the seed nodes
    #        In practice tightly bounded by max_hops and max_results
    # Space: O(V) — queue, dist_hop dict, and seen_visit set each scale with visited nodes
    # Return early if no route nodes are provided
    if not route_nodes:
        return []

    def _matches(node_data: dict) -> bool:
        # Time: O(1) — single dict lookup and string comparison
        # Extract the amenity attribute and compare case-insensitively to the requested poi_type
        amenity = (node_data or {}).get("amenity")
        return amenity is not None and str(amenity).lower() == str(poi_type).lower()

    # Use only the first 8 route nodes as BFS seeds to limit search scope near the route start
    seeds = route_nodes[: min(8, len(route_nodes))]
    q: deque[tuple[Any, int]] = deque()   # Queue entries are (node_id, hop_distance)
    dist_hop: dict[Any, int] = {}          # Best known hop distance from any seed to each node
    for s in seeds:
        if s in rg.network:               # Only seed with nodes that exist in the routable graph
            q.append((s, 0))              # Start each seed at hop distance 0
            dist_hop[s] = 0

    collected: list[dict[str, Any]] = []  # Stores POI records that match the requested type
    seen_visit: set[Any] = set()          # Prevents re-processing the same node twice

    while q and len(collected) < max_results:
        u, h = q.popleft()   # Dequeue the next node along with its hop distance — O(1)
        if u in seen_visit:
            continue          # Already processed this node from a shorter path; skip
        seen_visit.add(u)

        # Check if this node exists in the OSM graph and matches the requested amenity type
        if u in G.nodes:
            data = dict(G.nodes[u])
            if _matches(data):
                # Build a minimal POI record with display name, coordinates, and hop distance
                collected.append(
                    {
                        "name": str(data.get("name") or data.get("name:en") or poi_type),  # Prefer English name
                        "lat": float(data.get("y", 0.0)),   # OSM stores latitude as "y"
                        "lon": float(data.get("x", 0.0)),   # OSM stores longitude as "x"
                        "hops": h,                           # Hop distance from route for sorting
                    }
                )

        # Do not expand further if this node is already at the hop limit
        if h >= max_hops:
            continue
        for v in rg.iter_out_neighbors(u):
            nh = h + 1                             # Neighbor is one hop farther than u
            if v not in dist_hop or nh < dist_hop[v]:  # Only enqueue if this is a shorter path to v
                dist_hop[v] = nh
                q.append((v, nh))                  # Add neighbor to the queue for future expansion — O(1)

    # Sort POI results by hop distance using merge sort so nearest amenities appear first
    # Time: O(R log R) where R = len(collected); merge sort is stable
    collected = merge_sort(collected, key_func=lambda p: p["hops"])
    return collected
