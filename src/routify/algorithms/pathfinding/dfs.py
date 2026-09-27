"""Depth-first search traversals (Member 2)."""

# Allow forward references in type hints
from __future__ import annotations

from typing import Any

from routify.algorithms.graph.adjacency_list import Graph

# ---------------------------------------------------------------------------
# ALGORITHM – Depth-First Search (Iterative Pre-order)
# ---------------------------------------------------------------------------
# Explores as far as possible along each branch before backtracking.
# Uses an explicit stack so the Python call stack is not exhausted on large graphs.
#
# Variables: V = vertices visited, E = edges examined
#
# Time:  O(V + E) — each reachable vertex is popped once; each edge is pushed at most once
# Space: O(V)     — stack and seen set each hold at most V entries
#                   (worst case: a path graph where the stack grows to V)
# ---------------------------------------------------------------------------


def depth_first_preorder(rg: Graph, start: Any, *, max_visit: int = 10_000) -> list[Any]:
    # Time:  O(V + E) — bounded by max_visit in practice
    # Space: O(V)     — stack + seen set; order list also grows to O(V)
    # Return an empty list immediately if the start node doesn't exist in the graph
    if start not in rg.network:
        return []
    order: list[Any] = []          # Stores nodes in the order they are first visited
    stack = [start]                # Explicit stack replaces the call stack for iterative DFS
    seen: set[Any] = set()         # Tracks already-visited nodes to prevent revisiting
    while stack and len(order) < max_visit:  # Stop when stack is empty or visit limit reached
        u = stack.pop()            # Pop the most recently added node (LIFO order = depth-first)
        if u in seen:
            continue               # Node was already visited via a different path; skip it
        seen.add(u)                # Mark the node as visited before processing its neighbors
        order.append(u)            # Record the node in preorder (visit before children)
        nbrs = list(rg.iter_out_neighbors(u))   # Collect all outgoing neighbors of u
        for v in reversed(nbrs):               # Push neighbors in reverse so the first neighbor is processed first
            if v not in seen:
                stack.append(v)    # Only push unvisited neighbors to avoid redundant work
    return order                   # Return the complete preorder traversal sequence
