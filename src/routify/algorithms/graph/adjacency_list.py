"""Road network as hash map of vertices + linked-list adjacency (Member 1)."""

# Allow forward references in type hints
from __future__ import annotations

from routify.data.hash_table import HashTable  # Custom hash table used as the primary vertex store

# ---------------------------------------------------------------------------
# DATA STRUCTURE – Adjacency List Graph
# ---------------------------------------------------------------------------
# Vertices are stored in a hash table (O(1) average lookup).
# Each vertex's outgoing edges are stored as a singly-linked list prepended
# in O(1); iteration is O(deg(u)) where deg(u) is the out-degree of u.
#
# Variables: V = vertices, E = total directed edges, deg(u) = out-degree of u
#
# Space complexity: O(V + E) — O(V) for the hash table + O(E) total edge nodes
# ┌────────────────────────────┬──────────────────┬
# │ Operation                  │  Time (worst)    │
# ├────────────────────────────┼──────────────────┼
# │ add_location()             │ O(1)             │
# │ add_road() / add_directed  │ O(1)             │ 
# │ iter_out_edges(u)          │ O(deg(u))        │ 
# │ iter_out_neighbors(u)      │ O(deg(u))        │ 
# │ ensure_reverse_neighbors() │ O(V + E) one-off │ 
# │ iter_undirected_edges(u)   │ O(deg(u))        │ 
# │ display_graph()            │ O(V + E)         │ 
# └────────────────────────────┴──────────────────┴
# ---------------------------------------------------------------------------


class EdgeNode:
    """Directed road segment to one neighbor."""

    # __slots__ restricts instance attributes to save memory across potentially millions of edge nodes
    __slots__ = ("destination_id", "travel_time", "length_m", "next")

    def __init__(self, destination_id, travel_time, length_m=None):
        self.destination_id = destination_id            # The node ID this edge leads to
        self.travel_time = float(travel_time)           # Edge weight when routing by time
        self.length_m = float(length_m) if length_m is not None else float(travel_time)  # Edge weight when routing by distance; falls back to travel_time if not provided
        self.next = None                                 # Pointer to the next EdgeNode in the linked list


class EdgeLinkedList:
    def __init__(self) -> None:
        self.head: EdgeNode | None = None  # Head of the singly-linked list of outgoing edges

    def add_edge(self, destination_id, travel_time, length_m=None) -> None:
        # Time: O(1) — prepend to the head of the linked list; no traversal needed
        new_edge = EdgeNode(destination_id, travel_time, length_m)  # Create a new edge node
        new_edge.next = self.head   # Prepend: new edge points to the old head
        self.head = new_edge        # New edge becomes the new head (O(1) insertion)

    def iter_edges(self):
        # Time: O(deg) — visits every edge node in the list once; deg = number of outgoing edges
        cur = self.head
        while cur is not None:
            yield cur       # Yield each EdgeNode in linked-list order
            cur = cur.next  # Advance to the next node in the chain

    def get_all_edges_as_string(self) -> str:
        # Time: O(deg) — one pass over the linked list to build the string
        if self.head is None:
            return "No outgoing roads."      # Friendly message when there are no edges
        parts = []
        for cur in self.iter_edges():
            # Format each edge as "[destination (t=time, len=length)]"
            parts.append(
                f"[{cur.destination_id} (t={cur.travel_time:.2g}s, len={cur.length_m:.1f}m)]"
            )
        return " -> ".join(parts)  # Join all edge descriptions with arrows for readability


class LocationVertex:
    def __init__(self, location_id, name: str) -> None:
        self.location_id = location_id              # Unique identifier for this graph node
        self.name = name                             # Human-readable place name for display
        self.adjacent_roads = EdgeLinkedList()       # All outgoing roads from this location


class Graph:
    """Road network: dict of vertices + per-vertex linked-list adjacency."""

    def __init__(self, *, quiet: bool = False) -> None:
        self.network = HashTable(8192)  # Stores location_id → LocationVertex; initial capacity 8192 buckets
        self._quiet = quiet             # When True, suppresses informational print statements
        self._coords: dict = {}         # Optional node_id → (lat, lon) for A* heuristic

    def add_location(self, location_id, name, *, quiet: bool | None = None) -> bool:
        # Time: O(1) average — one hash table contains check + one insert, both O(1) avg
        q = self._quiet if quiet is None else quiet  # Allow per-call quiet override
        if location_id in self.network:
            if not q:
                print(f"[-] Location ID '{location_id}' already exists.")  # Warn about duplicates
            return False   # Location already exists; do not insert again
        self.network.insert(location_id, LocationVertex(location_id, name))  # Add the new vertex
        return True        # Insertion succeeded

    def add_road(
        self,
        source_id,
        dest_id,
        travel_time,
        is_two_way=True,   # True means add an edge in both directions
        length_m=None,
        *,
        quiet: bool | None = None,
    ) -> bool:
        # Time: O(1) average — two hash table lookups + one or two O(1) edge prepends
        q = self._quiet if quiet is None else quiet
        if source_id not in self.network or dest_id not in self.network:
            if not q:
                print("[-] Source or destination not in network.")  # Both endpoints must exist
            return False
        # Add a directed edge from source to destination
        self.network.search(source_id).adjacent_roads.add_edge(dest_id, travel_time, length_m)
        if is_two_way:
            # Also add a directed edge from destination back to source for bidirectional roads
            self.network.search(dest_id).adjacent_roads.add_edge(source_id, travel_time, length_m)
        return True

    def add_directed_edge(
        self, source_id, dest_id, travel_time, length_m=None, *, quiet: bool | None = None
    ) -> bool:
        # Time: O(1) average — at most two add_location calls + one edge prepend, all O(1) avg
        q = self._quiet if quiet is None else quiet
        if source_id not in self.network:
            self.add_location(source_id, f"Node_{source_id}", quiet=q)  # Auto-create missing source node
        if dest_id not in self.network:
            self.add_location(dest_id, f"Node_{dest_id}", quiet=q)      # Auto-create missing destination node
        self.network.search(source_id).adjacent_roads.add_edge(dest_id, travel_time, length_m)  # Add one-way edge
        return True

    def iter_out_edges(self, u, weight_mode: str):
        """Yield (neighbor, weight) for Dijkstra; weight_mode is 'time' or 'length'."""
        # Time: O(deg(u)) — one traversal of u's edge linked list
        if u not in self.network:
            return  # Silently yield nothing for unknown nodes
        for edge in self.network.search(u).adjacent_roads.iter_edges():
            # Select the appropriate weight based on the routing mode
            w = edge.travel_time if weight_mode == "time" else edge.length_m
            yield edge.destination_id, float(w)

    def iter_out_neighbors(self, u):
        # Time: O(deg(u)) — one traversal of u's edge linked list plus O(1) set operations per edge
        seen = set()                          # Deduplicate neighbors (parallel edges may share a destination)
        if u not in self.network:
            return
        for edge in self.network.search(u).adjacent_roads.iter_edges():
            v = edge.destination_id
            if v not in seen:
                seen.add(v)
                yield v                       # Yield each unique neighbor exactly once

    def ensure_reverse_neighbors(self) -> None:
        """Cache incoming edges so undirected routing can traverse one-ways in reverse."""
        # Time: O(V + E) — one full scan of all vertices and all edge lists; runs only once
        # Space: O(E)    — reverse adjacency list stores one entry per directed edge
        if hasattr(self, "_reverse_neighbors"):
            return  # Already built; avoid rebuilding on repeated calls
        rev: dict = {}
        for u, vtx in self.network.items():
            for edge in vtx.adjacent_roads.iter_edges():
                # For each directed edge u→v, record u as a reverse neighbor of v
                rev.setdefault(edge.destination_id, []).append(
                    (u, edge.travel_time, edge.length_m)
                )
        self._reverse_neighbors = rev  # Cache the result as an instance attribute

    def iter_undirected_edges(self, u, weight_mode: str):
        """Outgoing plus reverse incoming edges (for paths when directed routing fails)."""
        # Time: O(deg(u) + in-deg(u)) — scans both outgoing and cached incoming edges
        if u not in self.network:
            return
        seen: set = set()
        # First yield all normal outgoing edges (directed)
        for v, w in self.iter_out_edges(u, weight_mode):
            if v not in seen:
                seen.add(v)
                yield v, w
        # Ensure the reverse neighbor cache exists before accessing it
        self.ensure_reverse_neighbors()  # O(V + E) on first call; O(1) thereafter
        # Then yield reverse edges (incoming edges treated as traversable in reverse)
        for src, travel_time, length_m in self._reverse_neighbors.get(u, ()):
            w = travel_time if weight_mode == "time" else length_m
            if src not in seen:
                seen.add(src)
                yield src, float(w)

    def display_graph(self) -> None:
        # Time: O(V + E) — iterates every vertex and every edge list
        print("\n" + "=" * 40)
        print("     ROUTIFY ACTIVE ROAD NETWORK")
        print("=" * 40)
        for loc_id, vertex in self.network.items():
            # Print each vertex with its outgoing edges on a separate indented line
            print(f"{vertex.name} ({loc_id}) connects to:")
            print(f"  └─ {vertex.adjacent_roads.get_all_edges_as_string()}")
        print("=" * 40 + "\n")
