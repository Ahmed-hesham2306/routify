"""Domain models for routes, locations, and performance metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Location:
    location_id: str
    name: str


@dataclass
class RouteResult:
    """Outcome of a shortest-path computation."""

    path: list[Any]
    total_cost: float
    weight_mode: str  # "time" | "length"
    nodes_visited: int = 0
    elapsed_ms: float = 0.0


@dataclass
class TrafficEvent:
    """Dynamic edge weight adjustment for traffic simulation."""

    source_id: Any
    dest_id: Any
    multiplier: float = 1.5

