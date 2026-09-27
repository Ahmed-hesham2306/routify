"""Binary min-heap with decrease-key support (Member 3)."""

# Allow forward references in type hints
from __future__ import annotations

from copy import deepcopy  # Used to snapshot heap state before destructive to_sorted_list traversal

# ---------------------------------------------------------------------------
# DATA STRUCTURE – Binary Min-Heap with Decrease-Key
# ---------------------------------------------------------------------------
# A complete binary tree stored in an array where every parent is ≤ its
# children (min-heap property). A companion position map enables O(log n)
# decrease-key, which is critical for Dijkstra's algorithm.
#
# Space complexity: O(n) — one slot in _heap and one entry in _pos_map per node
# ┌──────────────────────┬─────────────┬
# │ Operation            │ Time (worst)│
# ├──────────────────────┼─────────────┼
# │ insert()             │ O(log n)    │
# │ pop_min()            │ O(log n)    │ 
# │ decrease_priority()  │ O(log n)    │ 
# │ contains()           │ O(1)        │ 
# │ is_empty() / len()   │ O(1)        │ 
# │ to_sorted_list()     │ O(n log n)  │ 
# └──────────────────────┴─────────────┴
# _sift_up and _sift_down each traverse at most O(log n) levels of the tree.
# ---------------------------------------------------------------------------


class MinHeap:
    def __init__(self) -> None:
        self._heap: list[tuple[float, Any]] = []   # Underlying array storing (priority, node) pairs
        self._pos_map: dict[Any, int] = {}          # Maps each node to its current index in _heap for O(log n) decrease-key

    def __len__(self) -> int:
        # Time: O(1) — reads the length of the backing list
        return len(self._heap)  # Expose heap size via the built-in len() function

    def is_empty(self) -> bool:
        # Time: O(1)
        return len(self._heap) == 0  # True when no elements remain

    @staticmethod
    def _parent(i: int) -> int:
        # Time: O(1) — integer arithmetic only
        return (i - 1) // 2  # Standard zero-based binary heap parent formula

    @staticmethod
    def _left(i: int) -> int:
        # Time: O(1)
        return 2 * i + 1  # Index of the left child in a zero-based heap array

    @staticmethod
    def _right(i: int) -> int:
        # Time: O(1)
        return 2 * i + 2  # Index of the right child in a zero-based heap array

    def _swap(self, i: int, j: int) -> None:
        # Time: O(1) — two list swaps and two dict updates
        node_i, node_j = self._heap[i][1], self._heap[j][1]  # Capture node identities before swapping
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]  # Swap the heap entries
        self._pos_map[node_i] = j  # Update node_i's recorded position to its new index j
        self._pos_map[node_j] = i  # Update node_j's recorded position to its new index i

    def insert(self, node: Any, priority: float) -> None:
        # Time: O(log n) — O(1) append + O(log n) sift_up
        # Space: O(1) extra — one new entry added to _heap and _pos_map
        index = len(self._heap)                  # New element goes at the end of the array
        self._heap.append((priority, node))      # Append the (priority, node) tuple
        self._pos_map[node] = index              # Record the new element's position
        self._sift_up(index)                     # Restore heap order by bubbling up

    def pop_min(self) -> tuple[float, Any] | None:
        # Time: O(log n) — O(1) swap + O(1) pop + O(log n) sift_down
        if self.is_empty():
            return None                          # Nothing to pop from an empty heap
        min_priority, min_node = self._heap[0]  # The root always holds the minimum element
        self._swap(0, len(self._heap) - 1)      # Swap root with the last element to prepare removal
        self._heap.pop()                         # Remove the old minimum (now at the end) — O(1) amortized
        del self._pos_map[min_node]              # Clean up the position map entry for the removed node — O(1)
        if not self.is_empty():
            self._sift_down(0)                   # Restore heap order by sifting the new root down
        return min_priority, min_node            # Return the extracted minimum as a (priority, node) tuple

    def decrease_priority(self, node: Any, new_priority: float) -> bool:
        # Time: O(log n) — O(1) lookup in _pos_map + O(log n) sift_up
        if node not in self._pos_map:
            return False                         # Node is not in the heap; nothing to update
        index = self._pos_map[node]
        if new_priority >= self._heap[index][0]:
            return False                         # New priority is not smaller; no update needed
        self._heap[index] = (new_priority, node) # Overwrite the old priority with the smaller one
        self._sift_up(index)                     # Bubble up to restore heap order
        return True                              # Successfully updated

    def contains(self, node: Any) -> bool:
        # Time: O(1) — hash map lookup in _pos_map
        return node in self._pos_map  # O(1) membership check via the position map

    def _sift_up(self, i: int) -> None:
        # Time: O(log n) — climbs at most the full height of the tree
        # Move element at index i upward until heap order is restored
        while i > 0:
            parent = self._parent(i)
            if self._heap[i][0] >= self._heap[parent][0]:
                break                            # Current node is >= parent; heap property satisfied
            self._swap(i, parent)               # Current node is smaller than parent; swap them
            i = parent                           # Continue checking from the parent's position

    def _sift_down(self, i: int) -> None:
        # Time: O(log n) — descends at most the full height of the tree
        n = len(self._heap)
        # Move element at index i downward until heap order is restored
        while True:
            smallest = i                         # Assume current node is the smallest until proven otherwise
            left, right = self._left(i), self._right(i)
            if left < n and self._heap[left][0] < self._heap[smallest][0]:
                smallest = left                  # Left child is smaller than current candidate
            if right < n and self._heap[right][0] < self._heap[smallest][0]:
                smallest = right                 # Right child is smaller than current candidate
            if smallest == i:
                break                            # Current node is already the smallest; heap is valid
            self._swap(i, smallest)             # Swap current node with the smallest child
            i = smallest                         # Continue sifting down from the swapped position

    def to_sorted_list(self) -> list[tuple[float, Any]]:
        # Time:  O(n log n) — n pop_min() calls, each O(log n); equivalent to heap sort
        # Space: O(n)       — deepcopy duplicates both _heap and _pos_map in full
        # Snapshot the current heap state so we can restore it after destructive extraction
        heap_copy = deepcopy(self._heap)
        map_copy = deepcopy(self._pos_map)
        result = []
        # Repeatedly pop the minimum to produce a fully sorted list
        while not self.is_empty():
            item = self.pop_min()
            if item:
                result.append(item)
        # Restore the original heap contents so the object remains usable
        self._heap = heap_copy
        self._pos_map = map_copy
        return result  # List of (priority, node) tuples in ascending priority order
