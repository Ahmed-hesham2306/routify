"""Binary search on sorted arrays (Member 5)."""

# Any allows the list and target to hold any comparable type; Callable types a key extractor function
from typing import Any, Callable

# ---------------------------------------------------------------------------
# ALGORITHM – Binary Search
# ---------------------------------------------------------------------------
# Iterative halving search on a *sorted* random-access array.
# Precondition: arr must be sorted in ascending order of key_func(element).
#
# Time:  O(log n) — the search window halves on every iteration
# Space: O(1)     — only a fixed set of index variables; no extra allocation
# ---------------------------------------------------------------------------

def binary_search(arr: list[Any], target: Any, key_func: Callable[[Any], Any] = lambda x: x) -> int:
    
    left, right = 0, len(arr) - 1  # Initialize search boundaries to the full array
    while left <= right:            # Continue as long as the search window has at least one element
        middle = (left + right) // 2        # Compute the midpoint, avoiding overflow
        mid_val = key_func(arr[middle])     # Extract the comparable key from the middle element
        if mid_val == target:
            return middle           # Target found; return its index
        if mid_val < target:
            left = middle + 1      # Middle is too small; discard left half and search right
        else:
            right = middle - 1     # Middle is too large; discard right half and search left
    return -1                       # Target not found; return sentinel value -1
