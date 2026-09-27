"""Multi-stop routing: chain Dijkstra segments on the full road database."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from routify.algorithms.graph.adjacency_list import Graph as RoutifyGraph
from routify.algorithms.pathfinding.dijkstra import (
    alternative_paths_edge_removal,
    flexible_shortest_path,
)
from routify.data.location_catalog import PlaceOption
from routify.presentation.gui.route_optimizer import optimize_stop_order


@dataclass(frozen=True)
class RoutedSegment:
    """One leg between consecutive stops."""

    path_nodes: list[Any]
    algorithm_label: str
    origin: PlaceOption
    destination: PlaceOption


@dataclass(frozen=True)
class RoutedTrip:
    """Full multi-stop route with per-leg metadata for the map."""

    full_path: list[Any]
    total_time_s: float
    total_length_m: float
    segments: list[RoutedSegment]
    alternative_legs: list[tuple[list[Any], str, float, float, float, float]]


def chain_shortest_path(
    route_graph: RoutifyGraph,
    stops: list[PlaceOption],
    *,
    weight_mode: str = "time",
    include_alternatives: bool = False,
    max_alternatives_per_leg: int = 2,
    optimize_order: bool = False,
) -> RoutedTrip:
    """
    Visit stops in order; concatenate segment paths (allows longer total routes).
    When optimize_order=True and there are intermediate waypoints, uses
    nearest-neighbor heuristic to reorder them for minimum total distance.
  """
    if len(stops) < 2:
        raise ValueError("At least two stops are required.")

    # Optionally reorder intermediate waypoints (keep origin and destination fixed)
    if optimize_order and len(stops) > 2:
        origin, destination = stops[0], stops[-1]
        waypoints = stops[1:-1]
        order = optimize_stop_order(origin, waypoints)
        stops = [origin] + [waypoints[i] for i in order] + [destination]

    full: list[Any] = []
    total_time = 0.0
    total_length = 0.0
    segments: list[RoutedSegment] = []
    alternative_legs: list[tuple[list[Any], str, float, float, float, float]] = []

    for i in range(len(stops) - 1):
        a, b = stops[i], stops[i + 1]
        seg, undirected = flexible_shortest_path(
            route_graph, a.node_id, b.node_id, weight_mode
        )
        if undirected:
            label = "Dijkstra (undirected fallback · travel time)"
        else:
            label = "Dijkstra (directed · travel time)"

        segments.append(
            RoutedSegment(path_nodes=seg, algorithm_label=label, origin=a, destination=b)
        )

        if full and seg:
            full.extend(seg[1:])
        else:
            full.extend(seg)

        for j in range(len(seg) - 1):
            u, v = seg[j], seg[j + 1]
            for nv, wt in route_graph.iter_out_edges(u, "time"):
                if nv == v:
                    total_time += wt
                    break
            else:
                route_graph.ensure_reverse_neighbors()
                for src, t, _ in route_graph._reverse_neighbors.get(v, ()):
                    if src == u:
                        total_time += t
                        break
            for nv, wt in route_graph.iter_out_edges(u, "length"):
                if nv == v:
                    total_length += wt
                    break
            else:
                for src, _t, length_m in route_graph._reverse_neighbors.get(v, ()):
                    if src == u:
                        total_length += length_m
                        break

        if include_alternatives:
            for alt_idx, alt in enumerate(
                alternative_paths_edge_removal(
                    route_graph,
                    a.node_id,
                    b.node_id,
                    weight_mode,
                    max_alternatives=max_alternatives_per_leg,
                )
            ):
                alternative_legs.append(
                    (
                        alt,
                        f"Alternative {alt_idx + 1} · edge-removal Dijkstra ({weight_mode})",
                        a.lat,
                        a.lon,
                        b.lat,
                        b.lon,
                    )
                )

    return RoutedTrip(
        full_path=full,
        total_time_s=total_time,
        total_length_m=total_length,
        segments=segments,
        alternative_legs=alternative_legs,
    )
