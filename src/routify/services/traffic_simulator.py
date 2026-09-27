"""Dynamic traffic simulation by scaling edge weights (Member 2 extension)."""

from __future__ import annotations

import random
from typing import Any

from routify.algorithms.graph.adjacency_list import EdgeNode, Graph
from routify.domain.models import TrafficEvent


class TrafficSimulator:
    """Applies multipliers to travel_time on selected edges."""

    def __init__(self, graph: Graph) -> None:
        self._graph = graph
        self._events: list[TrafficEvent] = []

    def apply_event(self, event: TrafficEvent) -> None:
        self._events.append(event)
        self._scale_edge(event.source_id, event.dest_id, event.multiplier)

    def _scale_edge(self, src: Any, dest: Any, multiplier: float) -> None:
        if src not in self._graph.network:
            return
        for edge in self._graph.network[src].adjacent_roads.iter_edges():
            if edge.destination_id == dest:
                edge.travel_time *= multiplier
                break

    def simulate_random_congestion(
        self, *, fraction: float = 0.05, multiplier: float = 1.8, seed: int | None = None
    ) -> int:
        """Randomly congest a fraction of edges; returns count affected."""
        rng = random.Random(seed)
        edges: list[tuple[Any, Any, EdgeNode]] = []
        for u, vertex in self._graph.network.items():
            for edge in vertex.adjacent_roads.iter_edges():
                edges.append((u, edge.destination_id, edge))
        if not edges:
            return 0
        k = max(1, int(len(edges) * fraction))
        chosen = rng.sample(edges, min(k, len(edges)))
        for u, v, edge in chosen:
            edge.travel_time *= multiplier
            self._events.append(TrafficEvent(u, v, multiplier))
        return len(chosen)

    def clear(self) -> None:
        self._events.clear()
