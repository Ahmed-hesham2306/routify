"""AVL tree for sorted route / delivery prioritization (Member 4)."""

# Allow using class names as type hints before they are fully defined
from __future__ import annotations

# ---------------------------------------------------------------------------
# DATA STRUCTURE – AVL Tree
# ---------------------------------------------------------------------------
# A self-balancing BST that keeps its height at O(log n) by enforcing a
# balance factor of -1, 0, or +1 at every node via rotations after insert
#
# Space complexity : O(n) — one node allocated per unique key
# ┌──────────────────────┬──────────────┬
# │ Operation            │ Time (worst) │
# ├──────────────────────┼──────────────┼
# │ insert()             │ O(log n)     │ 
# │ search()             │ O(log n)     │ 
# │ in_order_traversal() │ O(n)         │ 
# │ _right/_left_rotate()│ O(1)         │ 
# └──────────────────────┴──────────────┴
# Unlike a plain BST, the O(log n) worst-case is *guaranteed* because
# rotations prevent degeneration into a linear chain.
# ---------------------------------------------------------------------------


class AVLNode:
    # Each node stores a comparable key, a list of associated data items, child pointers, and height
    def __init__(self, key, data):
        self.key = key          # The sort key used for BST ordering
        self.data = [data]      # All data items sharing this key are stored in a list
        self.left = None        # Left child node (keys smaller than self.key)
        self.right = None       # Right child node (keys larger than self.key)
        self.height = 1         # Newly inserted node starts at height 1 (leaf)


def _height(node: AVLNode | None) -> int:
    # Time: O(1) — reads a cached attribute; no traversal needed
    # Return 0 for None (empty subtree), otherwise return the stored height
    return node.height if node else 0


def _balance(node: AVLNode) -> int:
    # Time: O(1) — two O(1) _height() calls
    # Balance factor = left subtree height minus right subtree height
    # Positive means left-heavy, negative means right-heavy
    return _height(node.left) - _height(node.right)


def _right_rotate(y: AVLNode) -> AVLNode:
    # Time: O(1) — fixed number of pointer reassignments and two height updates
    # y is the unbalanced node; x becomes the new subtree root after rotation
    x, t2 = y.left, y.left.right  # x is y's left child; t2 is x's right subtree
    x.right, y.left = y, t2       # x takes y as its right child; y adopts t2 as its new left child
    # Recalculate heights bottom-up: y is now lower, so update it first
    y.height = 1 + max(_height(y.left), _height(y.right))
    x.height = 1 + max(_height(x.left), _height(x.right))
    return x                       # x is the new root of this subtree


def _left_rotate(x: AVLNode) -> AVLNode:
    # Time: O(1) — fixed number of pointer reassignments and two height updates
    # x is the unbalanced node; y becomes the new subtree root after rotation
    y, t2 = x.right, x.right.left  # y is x's right child; t2 is y's left subtree
    y.left, x.right = x, t2        # y takes x as its left child; x adopts t2 as its new right child
    # Recalculate heights bottom-up: x is now lower, so update it first
    x.height = 1 + max(_height(x.left), _height(x.right))
    y.height = 1 + max(_height(y.left), _height(y.right))
    return y                        # y is the new root of this subtree


def insert(node: AVLNode | None, key, data) -> AVLNode:
    # Time:  O(log n) — descends one root-to-leaf path (height = O(log n)),
    #                    then performs at most one single or double rotation O(1) on the way back up
    # Space: O(log n) — recursive call stack depth equals the tree height
    # Base case: reached an empty spot, create a fresh leaf node
    if not node:
        return AVLNode(key, data)
    # Recurse left if the new key is smaller than the current node's key
    if key < node.key:
        node.left = insert(node.left, key, data)
    # Recurse right if the new key is larger
    elif key > node.key:
        node.right = insert(node.right, key, data)
    else:
        # Duplicate key: append data to the existing node's list instead of inserting a new node
        node.data.append(data)
        return node                 # No structural change, return immediately
    # Update this node's height after the recursive insert changed a subtree
    node.height = 1 + max(_height(node.left), _height(node.right))
    # Compute balance factor to check if rebalancing is needed
    bal = _balance(node)
    # Case 1 – Left-Left: new key went into the left child's left subtree
    if bal > 1 and key < node.left.key:  
        return _right_rotate(node)
    # Case 2 – Right-Right: new key went into the right child's right subtree
    if bal < -1 and key > node.right.key:  
        return _left_rotate(node)
    # Case 3 – Left-Right: new key went into the left child's right subtree; double rotation needed
    if bal > 1 and key > node.left.key:  
        node.left = _left_rotate(node.left)   # First rotate the left child left
        return _right_rotate(node)            # Then rotate the current node right
    # Case 4 – Right-Left: new key went into the right child's left subtree; double rotation needed
    if bal < -1 and key < node.right.key:  
        node.right = _right_rotate(node.right)  # First rotate the right child right
        return _left_rotate(node)               # Then rotate the current node left
    return node  # Tree was already balanced; return unchanged


def search(node: AVLNode | None, key) -> AVLNode | None:
    # Time:  O(log n) — visits at most one node per level; height is O(log n)
    # Space: O(log n) — recursive call stack depth equals the tree height
    # Base case: empty subtree means key is not present
    if node is None:
        return None
    # Found the node with the matching key
    if key == node.key:
        return node
    # Key is smaller; search in the left subtree
    if key < node.key:
        return search(node.left, key)
    # Key is larger; search in the right subtree
    return search(node.right, key)


def in_order_traversal(node: AVLNode | None):
    # Time:  O(n) — every node is visited exactly once
    # Space: O(log n) — generator frame stack depth equals the tree height
    # In-order visits left subtree, then current node, then right subtree
    # This yields all data items in ascending key order
    if node is not None:
        yield from in_order_traversal(node.left)   # Yield all items from smaller keys first
        for d in node.data:                        # Yield every data item stored at this key
            yield d
        yield from in_order_traversal(node.right)  # Yield all items from larger keys last
