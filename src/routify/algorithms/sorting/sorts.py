"""Merge sort and quick sort for route prioritization (Member 4)."""

# Callable lets us type-hint a function parameter; Any accepts any value type
from typing import Callable, Any

# ---------------------------------------------------------------------------
# ALGORITHM – Merge Sort
# ---------------------------------------------------------------------------
# Stable, divide-and-conquer comparison sort
# Time:  O(n log n) — best, average, and worst case
# Space: O(n)       — auxiliary arrays created during the merge step
# ---------------------------------------------------------------------------

def merge_sort(arr: list, key_func: Callable[[Any], Any] = lambda x: x) -> list:
    # Time:  O(n log n) — log n levels of recursion, O(n) work per level
    # Space: O(n)       — each _merge() call allocates a new result list; peak usage is O(n)
    # Base case: a list of 0 or 1 elements is already sorted
    if len(arr) <= 1:
        return arr
    # Find the midpoint to split the list into two roughly equal halves
    mid = len(arr) // 2
    # Recursively sort each half and merge the results together
    return _merge(merge_sort(arr[:mid], key_func), merge_sort(arr[mid:], key_func), key_func)


def _merge(left: list, right: list, key_func: Callable[[Any], Any]) -> list:
    # Time:  O(n) — each element from left and right is appended exactly once; n = len(left)+len(right)
    # Space: O(n) — result list grows to hold all n elements
    result, i, j = [], 0, 0  # result accumulates merged output; i and j are pointers into left and right
    # Compare front elements of both halves and append the smaller one to result
    while i < len(left) and j < len(right):
        if key_func(left[i]) < key_func(right[j]):
            result.append(left[i])  # Left element is smaller; take it
            i += 1
        else:
            result.append(right[j])  # Right element is smaller or equal; take it
            j += 1
    result.extend(left[i:])   # Append any remaining elements from the left half
    result.extend(right[j:])  # Append any remaining elements from the right half
    return result


# ---------------------------------------------------------------------------
# ALGORITHM – Quick Sort
# ---------------------------------------------------------------------------
# In-place, divide-and-conquer comparison sort. Uses last element as pivot.
# Time:  O(n log n) average — O(n²) worst case (already-sorted input with last-element pivot)
# Space: O(log n) average call stack — O(n) worst case (degenerate partitioning)
# ---------------------------------------------------------------------------

def quick_sort(arr: list, low: int = 0, high: int | None = None, key_func: Callable[[Any], Any] = lambda x: x) -> None:
    # Time:  O(n log n) average, O(n²) worst case
    # Space: O(log n) average recursive stack depth, O(n) worst case
    # Default high to the last valid index on the first call
    if high is None:
        high = len(arr) - 1
    # Only recurse if there are at least two elements in the current sub-array
    if low < high:
        # Partition the array and get the final position of the pivot element
        pi = _partition(arr, low, high, key_func)
        quick_sort(arr, low, pi - 1, key_func)   # Recursively sort elements before the pivot
        quick_sort(arr, pi + 1, high, key_func)  # Recursively sort elements after the pivot


def _partition(arr: list, low: int, high: int, key_func: Callable[[Any], Any]) -> int:
    # Time:  O(n) — single linear scan of the sub-array from low to high-1; n = high-low+1
    # Space: O(1) — sorts in-place with only a few index variables
    pivot = key_func(arr[high])  # Choose the last element as the pivot value
    i = low - 1                  # i tracks the boundary of elements smaller than the pivot
    for j in range(low, high):   # Scan every element except the pivot itself
        if key_func(arr[j]) < pivot:
            i += 1               # Expand the "less-than" region by one
            arr[i], arr[j] = arr[j], arr[i]  # Swap the current element into the less-than region
    arr[i + 1], arr[high] = arr[high], arr[i + 1]  # Place the pivot between the two regions
    return i + 1                 # Return the pivot's final sorted index
