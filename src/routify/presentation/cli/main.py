"""Terminal CLI for CSV-backed graph inspection and routing demos."""

from __future__ import annotations

import random
import time

from routify.config import DEFAULT_LOCATIONS_CSV, DEFAULT_ROADS_CSV
from routify.data.csv_repository import load_graph_from_csv
from routify.infrastructure.logging_config import setup_logging
from routify.algorithms.pathfinding.dijkstra import (
    astar_shortest_path,
    dijkstra_with_metrics,
)
from routify.algorithms.pathfinding.bfs import breadth_first_order
from routify.algorithms.pathfinding.dfs import depth_first_preorder
from routify.domain.exceptions import RoutingError
from routify.services.traffic_simulator import TrafficSimulator

log = setup_logging()


def run_interactive() -> int:
    try:
        graph, index = load_graph_from_csv(DEFAULT_LOCATIONS_CSV, DEFAULT_ROADS_CSV)
    except Exception as exc:
        log.error("%s", exc)
        return 1

    ids = list(graph.network.keys())
    if not ids:
        log.error("Graph is empty.")
        return 1

    while True:
        print("\n" + "=" * 50)
        print("       ROUTIFY — CSV ROAD NETWORK")
        print("=" * 50)
        print("1. Random intersection + neighbors")
        print("2. Network statistics")
        print("3. Shortest path — Dijkstra (random pair)")
        print("4. Shortest path — A* search  (random pair)")
        print("5. Simulate traffic congestion")
        print("6. BFS exploration from random node")
        print("7. DFS exploration from random node")
        print("8. Exit")
        choice = input("Select (1-8): ").strip()

        if choice == "1":
            rid = random.choice(ids)
            v = graph.network.search(rid)
            print(f"\n[{rid}] {v.name}")
            print(f"  → {v.adjacent_roads.get_all_edges_as_string()}")
        elif choice == "2":
            print(f"\nVertices: {len(graph.network):,}")
            if index:
                print(f"Hash index entries: {len(index):,}")
        elif choice == "3":
            o, d = random.choice(ids), random.choice(ids)
            if o == d:
                continue
            try:
                result = dijkstra_with_metrics(graph, o, d, "time")
                print(f"\nDijkstra: {o} → {d}")
                print(f"  cost={result.total_cost:.1f}s  hops={len(result.path)}  "
                      f"time={result.elapsed_ms:.2f}ms")
            except RoutingError:
                print("No path found.")
        elif choice == "4":
            o, d = random.choice(ids), random.choice(ids)
            if o == d:
                continue
            try:
                t0 = time.perf_counter()
                path = astar_shortest_path(graph, o, d, "time")
                elapsed = (time.perf_counter() - t0) * 1000
                print(f"\nA*: {o} → {d}")
                print(f"  hops={len(path)}  time={elapsed:.2f}ms")
            except RoutingError:
                print("No path found.")
        elif choice == "5":
            sim = TrafficSimulator(graph)
            n = sim.simulate_random_congestion(fraction=0.02, seed=42)
            print(f"\nApplied congestion to ~{n} edges. Re-run routing to see slower paths.")
        elif choice == "6":
            start = random.choice(ids)
            visited = breadth_first_order(graph, start, max_visit=50)
            print(f"\nBFS from [{start}]: visited {len(visited)} nodes")
            for nid in visited[:10]:
                v = graph.network.search(nid)
                print(f"  → [{nid}] {v.name}")
            if len(visited) > 10:
                print(f"  … and {len(visited) - 10} more")
        elif choice == "7":
            start = random.choice(ids)
            visited = depth_first_preorder(graph, start, max_visit=50)
            print(f"\nDFS from [{start}]: visited {len(visited)} nodes")
            for nid in visited[:10]:
                v = graph.network.search(nid)
                print(f"  → [{nid}] {v.name}")
            if len(visited) > 10:
                print(f"  … and {len(visited) - 10} more")
        elif choice == "8":
            print("Goodbye.")
            return 0
        else:
            print("Invalid choice.")


def main(argv: list[str] | None = None) -> int:
    return run_interactive()


if __name__ == "__main__":
    raise SystemExit(main())
