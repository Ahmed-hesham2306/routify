"""Routing facade: Dijkstra, alternatives, POI search on OSMnx + custom graph."""

from __future__ import annotations

from typing import Any

import networkx as nx

from routify.algorithms.graph.adjacency_list import Graph as RoutifyGraph
from routify.algorithms.pathfinding.bfs import filter_pois_near_route_bfs
from routify.algorithms.pathfinding.dfs import depth_first_preorder
from routify.algorithms.pathfinding.dijkstra import (
    alternative_paths_edge_removal,
    astar_shortest_path,
    dijkstra_shortest_path,
    dijkstra_with_metrics,
)
from routify.algorithms.trees import avl_tree
from routify.domain.models import RouteResult
from routify.services.graph_bridge import get_cached_routify_graph


def fastest_route(G: nx.MultiDiGraph, origin: Any, destination: Any) -> list[Any]:
    """A* with haversine heuristic — expands fewer nodes than Dijkstra."""
    rg = get_cached_routify_graph(G)
    return astar_shortest_path(rg, origin, destination, "time")


def shortest_route(G: nx.MultiDiGraph, origin: Any, destination: Any) -> list[Any]:
    rg = get_cached_routify_graph(G)
    return dijkstra_shortest_path(rg, origin, destination, "length")


def _path_cost(rg: RoutifyGraph, path: list[Any], weight_mode: str) -> float:
    """Sum of edge weights along a path — used to rank alternatives."""
    total = 0.0
    for i in range(len(path) - 1):
        for nv, w in rg.iter_out_edges(path[i], weight_mode):
            if nv == path[i + 1]:
                total += w
                break
    return total


def alternative_routes(
    G: nx.MultiDiGraph, origin: Any, destination: Any, *, max_alternatives: int = 3
) -> list[list[Any]]:
    """Return alternative paths sorted by cost using an AVL tree."""
    rg = get_cached_routify_graph(G)
    alts = alternative_paths_edge_removal(
        rg, origin, destination, "time", max_alternatives=max_alternatives
    )
    # Use AVL tree to maintain alternatives sorted by path cost;
    # in-order traversal yields them cheapest-first — O(A log A) where A = alternatives count
    tree = None
    for path in alts:
        cost = _path_cost(rg, path, "time")
        tree = avl_tree.insert(tree, cost, path)
    return list(avl_tree.in_order_traversal(tree))


def _as_routify_graph(G: nx.MultiDiGraph | RoutifyGraph) -> RoutifyGraph:
    if isinstance(G, RoutifyGraph):
        return G
    return get_cached_routify_graph(G)


def route_with_metrics(
    G: nx.MultiDiGraph | RoutifyGraph,
    origin: Any,
    destination: Any,
    weight_mode: str,
) -> RouteResult:
    return dijkstra_with_metrics(_as_routify_graph(G), origin, destination, weight_mode)


def pois_near_route(
    G: nx.MultiDiGraph, route_nodes: list[Any], poi_type: str
) -> list[dict[str, Any]]:
    rg = get_cached_routify_graph(G)
    return filter_pois_near_route_bfs(G, rg, route_nodes, poi_type)


def explore_area_dfs(
    G: nx.MultiDiGraph | RoutifyGraph, origin: Any, max_visit: int = 10_000
) -> list[Any]:
    rg = _as_routify_graph(G)
    return depth_first_preorder(rg, origin, max_visit=max_visit)
