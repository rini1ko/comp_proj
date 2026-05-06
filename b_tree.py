import math
from tree_adt import Tree_ADT
from visual import save_tree_snapshot

class BTreeNode:
    def __init__(self, m, leaf=False):
        self.m = m
        self.max_keys = m - 1
        self.min_keys = math.ceil(m / 2) - 1

        self.keys = []
        self.children = []
        self.leaf = leaf

class BTree(Tree_ADT):
    def __init__(self, m):
        super().__init__()
        if m < 3:
            raise ValueError("m must be >= 3")
        self.m = m
        self._root = BTreeNode(self.m, True)

    def find(self, value, node=None):
        if node is None:
            node = self._root
        i = 0
        while i < len(node.keys) and value > node.keys[i]:
            i += 1
        if i < len(node.keys) and value == node.keys[i]:
            return True
        elif node.leaf:
            return False
        else:
            return self.find(value, node.children[i])

    def inorder(self, node=None, result=None):
        if result is None:
            result = []
            node = self._root
        if node is not None:
            for i in range(len(node.keys)):
                if not node.leaf:
                    self.inorder(node.children[i], result)
                result.append(node.keys[i])
            if not node.leaf:
                self.inorder(node.children[len(node.keys)], result)
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
            new_root = BTreeNode(self.m, False)
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
                return self._split(node)
            return None, None
        else:
            idx = 0
            while idx < len(node.keys) and item > node.keys[idx]:
                idx += 1

            promoted_key, new_right = self._insert_recursive(node.children[idx], item)

            if promoted_key is not None:
                node.keys.insert(idx, promoted_key)
                node.children.insert(idx + 1, new_right)

                if len(node.keys) > node.max_keys:
                    return self._split(node)
            return None, None

    def _split(self, node):
        mid = len(node.keys) // 2
        promoted_key = node.keys[mid]

        new_right = BTreeNode(self.m, node.leaf)
        new_right.keys = node.keys[mid + 1:]
        node.keys = node.keys[:mid]

        if not node.leaf:
            new_right.children = node.children[mid + 1:]
            node.children = node.children[:mid + 1]
        save_tree_snapshot(self)
        return promoted_key, new_right

    def delete(self, item):
        if not self._root:
            return
        self._delete_internal(self._root, item)
        if len(self._root.keys) == 0:
            if self._root.leaf:
                self._root = BTreeNode(self.m, True)
            else:
                self._root = self._root.children[0]
        self._size -= 1
        save_tree_snapshot(self)

    def _delete_internal(self, node, item):
        idx = 0
        while idx < len(node.keys) and node.keys[idx] < item:
            idx += 1

        if idx < len(node.keys) and node.keys[idx] == item:
            if node.leaf:
                node.keys.pop(idx)
            else:
                self._delete_from_non_leaf(node, idx)
        else:
            if node.leaf:
                return

            flag = (idx == len(node.keys))
            if len(node.children[idx].keys) <= node.min_keys:
                self._fill(node, idx)

            if flag and idx > len(node.keys):
                self._delete_internal(node.children[idx - 1], item)
            else:
                self._delete_internal(node.children[idx], item)

    def _delete_from_non_leaf(self, node, idx):
        item = node.keys[idx]

        if len(node.children[idx].keys) > node.min_keys:
            pred = self._get_pred(node, idx)
            node.keys[idx] = pred
            self._delete_internal(node.children[idx], pred)
        elif len(node.children[idx + 1].keys) > node.min_keys:
            succ = self._get_succ(node, idx)
            node.keys[idx] = succ
            self._delete_internal(node.children[idx + 1], succ)
        else:
            self._merge(node, idx)
            self._delete_internal(node.children[idx], item)

    def _get_pred(self, node, idx):
        curr = node.children[idx]
        while not curr.leaf:
            curr = curr.children[len(curr.keys)]
        return curr.keys[-1]

    def _get_succ(self, node, idx):
        curr = node.children[idx + 1]
        while not curr.leaf:
            curr = curr.children[0]
        return curr.keys[0]

    def _fill(self, node, idx):
        if idx != 0 and len(node.children[idx - 1].keys) > node.min_keys:
            self._borrow_prev(node, idx)
        elif idx != len(node.keys) and len(node.children[idx + 1].keys) > node.min_keys:
            self._borrow_next(node, idx)
        else:
            if idx != len(node.keys):
                self._merge(node, idx)
            else:
                self._merge(node, idx - 1)

    def _borrow_prev(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx - 1]

        child.keys.insert(0, node.keys[idx - 1])
        if not child.leaf:
            child.children.insert(0, sibling.children.pop())
        node.keys[idx - 1] = sibling.keys.pop()

    def _borrow_next(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx + 1]

        child.keys.append(node.keys[idx])
        if not child.leaf:
            child.children.append(sibling.children.pop(0))
        node.keys[idx] = sibling.keys.pop(0)

    def _merge(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx + 1]

        child.keys.append(node.keys.pop(idx))
        child.keys.extend(sibling.keys)
        if not child.leaf:
            child.children.extend(sibling.children)

        node.children.pop(idx + 1)

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
#     visual._default_viz = visual.BTreeVisualizer()
#     tree = BTree(m=6)
#     values_to_add = [10, 20, 30, 40, 50, 25, 15, 45, 35, 27, 60, 18, 37, 29, 14, 43, 34]
#     for val in values_to_add:
#         set_label(f"Add: {val}")
#         tree.add(val)
#     set_label("Delete: 30 (Merge/Borrow)")
#     tree.delete(30)
#     make_gif("frames", "btree_animation.gif", frame_ms=1000, last_ms=3000)
#     print("Done")
