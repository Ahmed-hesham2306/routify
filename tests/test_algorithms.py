"""Comprehensive test suite for all Routify algorithms and data structures.

Run with:  python -m pytest tests/test_algorithms.py -v
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

# Ensure project source is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ═══════════════════════════════════════════════════════════════════════════
# 1. HASH TABLE
# ═══════════════════════════════════════════════════════════════════════════

class TestHashTable:
    def _make(self):
        from routify.data.hash_table import HashTable
        return HashTable

    def test_insert_search(self):
        HT = self._make()
        ht = HT(16)
        ht.insert("A", 100)
        assert ht.search("A") == 100

    def test_bracket_access(self):
        HT = self._make()
        ht = HT()
        ht["key1"] = "val1"
        assert ht["key1"] == "val1"

    def test_contains(self):
        HT = self._make()
        ht = HT()
        ht.insert("x", 42)
        assert "x" in ht
        assert "y" not in ht

    def test_remove(self):
        HT = self._make()
        ht = HT()
        ht.insert("k", 1)
        ht.remove("k")
        assert "k" not in ht

    def test_resize(self):
        HT = self._make()
        ht = HT(4)  # Very small — forces multiple resizes
        for i in range(50):
            ht.insert(f"node_{i}", i)
        assert len(ht) == 50
        for i in range(50):
            assert ht.search(f"node_{i}") == i

    def test_update_existing_key(self):
        HT = self._make()
        ht = HT()
        ht.insert("k", 1)
        ht.insert("k", 999)
        assert ht.search("k") == 999
        assert len(ht) == 1  # Should not duplicate

    def test_get_default(self):
        HT = self._make()
        ht = HT()
        assert ht.get("missing", "default") == "default"
        ht["k"] = 1
        assert ht.get("k", "default") == 1

    def test_iter_keys_values_items(self):
        HT = self._make()
        ht = HT()
        ht["a"] = 1
        ht["b"] = 2
        assert set(ht.keys()) == {"a", "b"}
        assert set(ht.values()) == {1, 2}
        assert set(ht.items()) == {("a", 1), ("b", 2)}

    def test_polynomial_hash_no_anagram_collision(self):
        """The polynomial hash must NOT collide on anagrams like 'ab' vs 'ba'."""
        HT = self._make()
        ht = HT(16)
        assert ht._hash("ab") != ht._hash("ba")


# ═══════════════════════════════════════════════════════════════════════════
# 2. MIN HEAP
# ═══════════════════════════════════════════════════════════════════════════

class TestMinHeap:
    def _make(self):
        from routify.algorithms.heap.min_heap import MinHeap
        return MinHeap

    def test_insert_pop(self):
        MH = self._make()
        h = MH()
        h.insert("A", 5.0)
        h.insert("B", 2.0)
        h.insert("C", 8.0)
        pri, item = h.pop_min()
        assert item == "B" and pri == 2.0

    def test_decrease_priority(self):
        MH = self._make()
        h = MH()
        h.insert("X", 10.0)
        h.insert("Y", 20.0)
        h.decrease_priority("Y", 1.0)
        pri, item = h.pop_min()
        assert item == "Y" and pri == 1.0

    def test_contains(self):
        MH = self._make()
        h = MH()
        h.insert("A", 1.0)
        assert h.contains("A")
        assert not h.contains("Z")

    def test_empty(self):
        MH = self._make()
        h = MH()
        assert h.is_empty()
        h.insert("A", 1.0)
        assert not h.is_empty()


# ═══════════════════════════════════════════════════════════════════════════
# 3. MERGE SORT
# ═══════════════════════════════════════════════════════════════════════════

class TestMergeSort:
    def _sort(self):
        from routify.algorithms.sorting.sorts import merge_sort
        return merge_sort

    def test_sort_integers(self):
        ms = self._sort()
        assert ms([3, 1, 4, 1, 5, 9]) == [1, 1, 3, 4, 5, 9]

    def test_empty(self):
        ms = self._sort()
        assert ms([]) == []

    def test_single(self):
        ms = self._sort()
        assert ms([42]) == [42]

    def test_key_func(self):
        ms = self._sort()
        data = [{"name": "B", "v": 2}, {"name": "A", "v": 1}]
        result = ms(data, key_func=lambda d: d["v"])
        assert result[0]["name"] == "A"

    def test_stability(self):
        """Merge sort is stable: equal-key elements keep their original order."""
        ms = self._sort()
        data = [(1, "first"), (2, "x"), (1, "second")]
        result = ms(data, key_func=lambda t: t[0])
        ones = [t[1] for t in result if t[0] == 1]
        assert ones == ["first", "second"]


# ═══════════════════════════════════════════════════════════════════════════
# 4. QUICK SORT
# ═══════════════════════════════════════════════════════════════════════════

class TestQuickSort:
    def _sort(self):
        from routify.algorithms.sorting.sorts import quick_sort
        return quick_sort

    def test_sort_integers(self):
        qs = self._sort()
        arr = [5, 2, 8, 1, 9, 3]
        qs(arr)
        assert arr == [1, 2, 3, 5, 8, 9]

    def test_already_sorted(self):
        qs = self._sort()
        arr = [1, 2, 3, 4]
        qs(arr)
        assert arr == [1, 2, 3, 4]

    def test_reverse_sorted(self):
        qs = self._sort()
        arr = [5, 4, 3, 2, 1]
        qs(arr)
        assert arr == [1, 2, 3, 4, 5]

    def test_key_func(self):
        qs = self._sort()
        arr = ["banana", "apple", "cherry"]
        qs(arr, key_func=lambda s: s)
        assert arr == ["apple", "banana", "cherry"]


# ═══════════════════════════════════════════════════════════════════════════
# 5. BINARY SEARCH
# ═══════════════════════════════════════════════════════════════════════════

class TestBinarySearch:
    def _search(self):
        from routify.algorithms.search.binary_search import binary_search
        return binary_search

    def test_found(self):
        bs = self._search()
        arr = [10, 20, 30, 40, 50]
        assert bs(arr, 30) == 2

    def test_not_found(self):
        bs = self._search()
        assert bs([1, 2, 3], 99) == -1

    def test_empty(self):
        bs = self._search()
        assert bs([], 1) == -1

    def test_key_func(self):
        bs = self._search()
        arr = [{"n": "a"}, {"n": "b"}, {"n": "c"}]
        idx = bs(arr, "b", key_func=lambda d: d["n"])
        assert idx == 1


# ═══════════════════════════════════════════════════════════════════════════
# 6. AVL TREE
# ═══════════════════════════════════════════════════════════════════════════

class TestAVLTree:
    def _mod(self):
        from routify.algorithms.trees import avl_tree
        return avl_tree

    def test_insert_and_search(self):
        avl = self._mod()
        tree = None
        tree = avl.insert(tree, 10, "ten")
        tree = avl.insert(tree, 5, "five")
        tree = avl.insert(tree, 15, "fifteen")
        assert avl.search(tree, 10).data == ["ten"]
        assert avl.search(tree, 99) is None

    def test_in_order(self):
        avl = self._mod()
        tree = None
        for k in [30, 10, 20, 50, 40]:
            tree = avl.insert(tree, k, f"d{k}")
        result = list(avl.in_order_traversal(tree))
        assert result == ["d10", "d20", "d30", "d40", "d50"]

    def test_duplicate_key(self):
        avl = self._mod()
        tree = None
        tree = avl.insert(tree, 1, "first")
        tree = avl.insert(tree, 1, "second")
        node = avl.search(tree, 1)
        assert node.data == ["first", "second"]

    def test_balance(self):
        """Inserting sorted keys should still produce a balanced tree (height ≈ log n)."""
        avl = self._mod()
        tree = None
        for i in range(100):
            tree = avl.insert(tree, i, i)
        # A balanced AVL tree of 100 nodes has height <= 8
        assert tree.height <= 8

    def test_all_four_rotations(self):
        """Test LL, RR, LR, RL rotation cases."""
        avl = self._mod()
        # LL case: 30, 20, 10
        t = None
        for k in [30, 20, 10]:
            t = avl.insert(t, k, k)
        assert t.key == 20  # 20 should be root after right rotation

        # RR case: 10, 20, 30
        t = None
        for k in [10, 20, 30]:
            t = avl.insert(t, k, k)
        assert t.key == 20  # 20 should be root after left rotation

        # LR case: 30, 10, 20
        t = None
        for k in [30, 10, 20]:
            t = avl.insert(t, k, k)
        assert t.key == 20  # 20 should be root after left-right rotation

        # RL case: 10, 30, 20
        t = None
        for k in [10, 30, 20]:
            t = avl.insert(t, k, k)
        assert t.key == 20  # 20 should be root after right-left rotation


# ═══════════════════════════════════════════════════════════════════════════
# 7. GRAPH (Adjacency List)
# ═══════════════════════════════════════════════════════════════════════════

class TestGraph:
    def _make_graph(self):
        from routify.algorithms.graph.adjacency_list import Graph
        g = Graph(quiet=True)
        g.add_location("A", "City A", quiet=True)
        g.add_location("B", "City B", quiet=True)
        g.add_location("C", "City C", quiet=True)
        g.add_location("D", "City D", quiet=True)
        g.add_road("A", "B", 10, is_two_way=True, length_m=1000)
        g.add_road("B", "C", 5,  is_two_way=True, length_m=500)
        g.add_road("C", "D", 8,  is_two_way=False, length_m=800)
        return g

    def test_add_location(self):
        g = self._make_graph()
        assert "A" in g.network
        assert "D" in g.network

    def test_neighbors(self):
        g = self._make_graph()
        neighbors = list(g.iter_out_neighbors("A"))
        assert "B" in neighbors

    def test_edge_weights(self):
        g = self._make_graph()
        edges = list(g.iter_out_edges("A", "time"))
        assert any(dest == "B" and w == 10.0 for dest, w in edges)

    def test_one_way(self):
        g = self._make_graph()
        # C→D should exist, D→C should NOT
        c_neighbors = list(g.iter_out_neighbors("C"))
        d_neighbors = list(g.iter_out_neighbors("D"))
        assert "D" in c_neighbors
        assert "C" not in d_neighbors


# ═══════════════════════════════════════════════════════════════════════════
# 8. DIJKSTRA
# ═══════════════════════════════════════════════════════════════════════════

class TestDijkstra:
    def _make_graph(self):
        from routify.algorithms.graph.adjacency_list import Graph
        g = Graph(quiet=True)
        for n in ["A", "B", "C", "D"]:
            g.add_location(n, n, quiet=True)
        g.add_road("A", "B", 4, length_m=400)
        g.add_road("B", "C", 3, length_m=300)
        g.add_road("A", "C", 10, length_m=1000)
        g.add_road("C", "D", 2, length_m=200)
        return g

    def test_shortest_path(self):
        from routify.algorithms.pathfinding.dijkstra import dijkstra_shortest_path
        g = self._make_graph()
        path = dijkstra_shortest_path(g, "A", "D", "time")
        assert path == ["A", "B", "C", "D"]

    def test_no_path(self):
        from routify.algorithms.pathfinding.dijkstra import dijkstra_shortest_path
        from routify.domain.exceptions import RoutingError
        from routify.algorithms.graph.adjacency_list import Graph
        g = Graph(quiet=True)
        g.add_location("X", "X", quiet=True)
        g.add_location("Y", "Y", quiet=True)
        # No edge between X and Y
        try:
            dijkstra_shortest_path(g, "X", "Y", "time")
            assert False, "Should raise RoutingError"
        except RoutingError:
            pass

    def test_metrics(self):
        from routify.algorithms.pathfinding.dijkstra import dijkstra_with_metrics
        g = self._make_graph()
        result = dijkstra_with_metrics(g, "A", "D", "time")
        assert result.total_cost == 9.0  # 4 + 3 + 2
        assert result.path == ["A", "B", "C", "D"]
        assert result.elapsed_ms > 0

    def test_alternative_paths(self):
        from routify.algorithms.pathfinding.dijkstra import alternative_paths_edge_removal
        g = self._make_graph()
        alts = alternative_paths_edge_removal(g, "A", "D", "time")
        assert len(alts) >= 1  # At least one alternative exists (A→C→D)


# ═══════════════════════════════════════════════════════════════════════════
# 9. A* SEARCH
# ═══════════════════════════════════════════════════════════════════════════

class TestAStar:
    def _make_graph(self):
        from routify.algorithms.graph.adjacency_list import Graph
        g = Graph(quiet=True)
        # Triangle graph with coordinates for A* heuristic
        for n in ["A", "B", "C", "D"]:
            g.add_location(n, n, quiet=True)
        g.add_road("A", "B", 4, length_m=400)
        g.add_road("B", "C", 3, length_m=300)
        g.add_road("A", "C", 10, length_m=1000)
        g.add_road("C", "D", 2, length_m=200)
        # Set fake coordinates (Cairo-ish area)
        g._coords = {
            "A": (30.0, 31.0),
            "B": (30.01, 31.01),
            "C": (30.02, 31.02),
            "D": (30.03, 31.03),
        }
        return g

    def test_finds_optimal_path(self):
        from routify.algorithms.pathfinding.dijkstra import astar_shortest_path
        g = self._make_graph()
        path = astar_shortest_path(g, "A", "D", "time")
        assert path == ["A", "B", "C", "D"]  # Same optimal path as Dijkstra

    def test_fallback_no_coords(self):
        """When no coordinates exist, A* falls back to Dijkstra."""
        from routify.algorithms.pathfinding.dijkstra import astar_shortest_path
        from routify.algorithms.graph.adjacency_list import Graph
        g = Graph(quiet=True)
        for n in ["A", "B"]:
            g.add_location(n, n, quiet=True)
        g.add_road("A", "B", 5, length_m=500)
        path = astar_shortest_path(g, "A", "B", "time")
        assert path == ["A", "B"]

    def test_no_path_raises(self):
        from routify.algorithms.pathfinding.dijkstra import astar_shortest_path
        from routify.domain.exceptions import RoutingError
        from routify.algorithms.graph.adjacency_list import Graph
        g = Graph(quiet=True)
        g.add_location("X", "X", quiet=True)
        g.add_location("Y", "Y", quiet=True)
        g._coords = {"X": (30.0, 31.0), "Y": (30.1, 31.1)}
        try:
            astar_shortest_path(g, "X", "Y", "time")
            assert False, "Should raise RoutingError"
        except RoutingError:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# 10. BFS
# ═══════════════════════════════════════════════════════════════════════════

class TestBFS:
    def test_traversal_order(self):
        from routify.algorithms.graph.adjacency_list import Graph
        from routify.algorithms.pathfinding.bfs import breadth_first_order
        g = Graph(quiet=True)
        for n in ["A", "B", "C", "D"]:
            g.add_location(n, n, quiet=True)
        g.add_road("A", "B", 1)
        g.add_road("A", "C", 1)
        g.add_road("B", "D", 1)
        visited = breadth_first_order(g, "A")
        assert visited[0] == "A"
        assert set(visited) == {"A", "B", "C", "D"}

    def test_max_visit(self):
        from routify.algorithms.graph.adjacency_list import Graph
        from routify.algorithms.pathfinding.bfs import breadth_first_order
        g = Graph(quiet=True)
        for n in ["A", "B", "C"]:
            g.add_location(n, n, quiet=True)
        g.add_road("A", "B", 1)
        g.add_road("B", "C", 1)
        visited = breadth_first_order(g, "A", max_visit=2)
        assert len(visited) == 2


# ═══════════════════════════════════════════════════════════════════════════
# 11. DFS
# ═══════════════════════════════════════════════════════════════════════════

class TestDFS:
    def test_traversal(self):
        from routify.algorithms.graph.adjacency_list import Graph
        from routify.algorithms.pathfinding.dfs import depth_first_preorder
        g = Graph(quiet=True)
        for n in ["A", "B", "C", "D"]:
            g.add_location(n, n, quiet=True)
        g.add_road("A", "B", 1)
        g.add_road("B", "C", 1)
        g.add_road("C", "D", 1)
        visited = depth_first_preorder(g, "A")
        assert visited[0] == "A"
        assert set(visited) == {"A", "B", "C", "D"}


# ═══════════════════════════════════════════════════════════════════════════
# 12. ROUTE OPTIMIZER (Nearest Neighbor)
# ═══════════════════════════════════════════════════════════════════════════

class TestRouteOptimizer:
    def test_nearest_neighbor_order(self):
        from routify.presentation.gui.route_optimizer import optimize_stop_order
        from routify.data.location_catalog import PlaceOption
        origin = PlaceOption(node_id=0, display_name="O", lat=30.0, lon=31.0, source="test")
        w1 = PlaceOption(node_id=1, display_name="Far", lat=30.1, lon=31.1, source="test")
        w2 = PlaceOption(node_id=2, display_name="Near", lat=30.001, lon=31.001, source="test")
        order = optimize_stop_order(origin, [w1, w2])
        # w2 is closer to origin, so it should come first
        assert order[0] == 1  # index of w2 in the [w1, w2] list
        assert order[1] == 0  # index of w1

    def test_empty_waypoints(self):
        from routify.presentation.gui.route_optimizer import optimize_stop_order
        from routify.data.location_catalog import PlaceOption
        origin = PlaceOption(node_id=0, display_name="O", lat=0, lon=0, source="test")
        assert optimize_stop_order(origin, []) == []


# ═══════════════════════════════════════════════════════════════════════════
# Run with:  python tests/test_algorithms.py
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import traceback
    passed = 0
    failed = 0
    errors = []

    # Discover all test classes and methods
    test_classes = [
        TestHashTable, TestMinHeap, TestMergeSort, TestQuickSort,
        TestBinarySearch, TestAVLTree, TestGraph, TestDijkstra,
        TestAStar, TestBFS, TestDFS, TestRouteOptimizer,
    ]

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in sorted(methods):
            label = f"{cls.__name__}.{method_name}"
            try:
                getattr(instance, method_name)()
                passed += 1
                print(f"   {label}")
            except Exception:
                failed += 1
                tb = traceback.format_exc()
                errors.append((label, tb))
                print(f"   {label}")

    print(f"\n{'='*50}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    for label, tb in errors:
        print(f"\n--- FAIL: {label} ---")
        print(tb)

    raise SystemExit(1 if failed else 0)
