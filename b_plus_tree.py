import math
from tree_adt import Tree_ADT
from visual import save_tree_snapshot

class BPlusTreeNode:
    def __init__(self, m, leaf=False):
        self.m = m
        self.max_keys = m - 1
        self.min_keys = math.ceil(m / 2) - 1

        self.keys = []
        self.children = []
        self.leaf = leaf
        self.next = None

class BPlusTree(Tree_ADT):
    def __init__(self, m):
        super().__init__()
        if m < 3:
            raise ValueError("m must be >= 3")
        self.m = m
        self._root = BPlusTreeNode(self.m, True)
        self._first_leaf = self._root

    def find(self, value):
        node = self._root
        while not node.leaf:
            i = 0
            while i < len(node.keys) and value >= node.keys[i]:
                i += 1
            node = node.children[i]

        for key in node.keys:
            if key == value:
                return True
        return False

    def inorder(self):
        result = []
        curr = self._first_leaf
        while curr is not None:
            result.extend(curr.keys)
            curr = curr.next
        return result

    def preorder(self, node=None, result=None):
        if result is None:
            result = []
            node = self._root
        if node is not None:
            for i in range(len(node.keys)):
                result.append(node.keys[i])
            if not node.leaf:
                for child in node.children:
                    self.preorder(child, result)
        return result

    def postorder(self, node=None, result=None):
        if result is None:
            result = []
            node = self._root
        if node is not None:
            if not node.leaf:
                for child in node.children:
                    self.postorder(child, result)
            for i in range(len(node.keys)):
                result.append(node.keys[i])
        return result

    def add(self, item):
        promoted_key, new_right = self._insert_recursive(self._root, item)

        if promoted_key is not None:
            new_root = BPlusTreeNode(self.m, False)
            new_root.keys.append(promoted_key)
            new_root.children.append(self._root)
            new_root.children.append(new_right)
            self._root = new_root

        self._size += 1
        save_tree_snapshot(self)

    def _insert_recursive(self, node, item):
        if node.leaf:
            idx = 0
            while idx < len(node.keys) and item > node.keys[idx]:
                idx += 1
            node.keys.insert(idx, item)

            if len(node.keys) > node.max_keys:
                return self._split_leaf(node)
            return None, None
        else:
            idx = 0
            while idx < len(node.keys) and item >= node.keys[idx]:
                idx += 1

            promoted_key, new_right = self._insert_recursive(node.children[idx], item)

            if promoted_key is not None:
                node.keys.insert(idx, promoted_key)
                node.children.insert(idx + 1, new_right)

                if len(node.keys) > node.max_keys:
                    return self._split_internal(node)
            return None, None

    def _split_leaf(self, node):
        mid = len(node.keys) // 2
        promoted_key = node.keys[mid]

        new_right = BPlusTreeNode(self.m, True)
        new_right.keys = node.keys[mid:]
        node.keys = node.keys[:mid]

        new_right.next = node.next
        node.next = new_right
        save_tree_snapshot(self)
        return promoted_key, new_right

    def _split_internal(self, node):
        mid = len(node.keys) // 2
        promoted_key = node.keys[mid]

        new_right = BPlusTreeNode(self.m, False)
        new_right.keys = node.keys[mid + 1:]
        new_right.children = node.children[mid + 1:]

        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        save_tree_snapshot(self)
        return promoted_key, new_right

    def delete(self, item):
        if not self._root:
            return

        self._delete_recursive(self._root, item)

        if len(self._root.keys) == 0:
            if not self._root.leaf:
                self._root = self._root.children[0]

        self._size -= 1
        save_tree_snapshot(self)

    def _delete_recursive(self, node, item):
        if node.leaf:
            idx = 0
            while idx < len(node.keys) and node.keys[idx] < item:
                idx += 1
            if idx < len(node.keys) and node.keys[idx] == item:
                node.keys.pop(idx)
            return

        idx = 0
        while idx < len(node.keys) and item >= node.keys[idx]:
            idx += 1

        self._delete_recursive(node.children[idx], item)

        if len(node.children[idx].keys) < node.min_keys:
            self._handle_underflow(node, idx)

    def _handle_underflow(self, parent, idx):
        child = parent.children[idx]

        if idx > 0 and len(parent.children[idx - 1].keys) > parent.min_keys:
            self._borrow_prev(parent, idx)
        elif idx < len(parent.children) - 1 and len(parent.children[idx + 1].keys) > parent.min_keys:
            self._borrow_next(parent, idx)
        else:
            if idx > 0:
                self._merge(parent, idx - 1)
            else:
                self._merge(parent, idx)

    def _borrow_prev(self, parent, idx):
        child = parent.children[idx]
        sibling = parent.children[idx - 1]

        if child.leaf:
            child.keys.insert(0, sibling.keys.pop())
            parent.keys[idx - 1] = child.keys[0]
        else:
            child.keys.insert(0, parent.keys[idx - 1])
            parent.keys[idx - 1] = sibling.keys.pop()
            child.children.insert(0, sibling.children.pop())

    def _borrow_next(self, parent, idx):
        child = parent.children[idx]
        sibling = parent.children[idx + 1]

        if child.leaf:
            child.keys.append(sibling.keys.pop(0))
            parent.keys[idx] = sibling.keys[0]
        else:
            child.keys.append(parent.keys[idx])
            parent.keys[idx] = sibling.keys.pop(0)
            child.children.append(sibling.children.pop(0))

    def _merge(self, parent, idx):
        left_child = parent.children[idx]
        right_child = parent.children[idx + 1]

        if left_child.leaf:
            left_child.keys.extend(right_child.keys)
            left_child.next = right_child.next
        else:
            left_child.keys.append(parent.keys[idx])
            left_child.keys.extend(right_child.keys)
            left_child.children.extend(right_child.children)

        parent.keys.pop(idx)
        parent.children.pop(idx + 1)

    def _rotate_right(self, y):
        pass

    def _rotate_left(self, x):
        pass

# if __name__ == '__main__':
#     import shutil
#     import os
#     import visual
#     from visual import set_label, make_gif
#     if os.path.exists("frames"):
#         shutil.rmtree("frames")
#     visual._default_viz = visual.BPlusVisualizer()
#     tree = BPlusTree(m=3)
#     values_to_add = [5, 15, 25, 35, 45, 55, 20]
#     for val in values_to_add:
#         set_label(f"Add: {val}")
#         tree.add(val)
#     set_label("Delete: 15 (Leaf modifications)")
#     tree.delete(15)
#     make_gif("frames", "bplus_animation.gif", frame_ms=1000, last_ms=3000)
#     print("Done")
