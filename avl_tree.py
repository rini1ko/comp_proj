from tree_adt import BST_ADT, BSTNode

class AVLNode(BSTNode):
    def __init__(self, data, left=None, right=None):
        super().__init__(data, left, right)
        self.height=1

class AVL_Tree(BST_ADT):
    def __init__(self, root=None):
        super().__init__(root)

    def add(self, item):
        def _add_recursion(node, item):
            if not node:
                self._size += 1
                return AVLNode(item)
            if node.data>item:
                node.left = _add_recursion(node.left, item)
            elif node.data<item:
                node.right =_add_recursion(node.right, item)
            else:
                return node
            # update nodes height
            node.height = 1+max(self._get_height(node.left), self._get_height(node.right))
            balance= self._get_balance(node)
            #l-l
            if balance > 1 and item < node.left.data:
                return self._rotate_right(node)
            #r-r
            if balance < -1 and item > node.right.data:
                return self._rotate_left(node)
            #l-r
            if balance > 1 and item > node.left.data:
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node)
            #r-l
            if balance < -1 and item < node.right.data:
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node)

            return node

        self._root = _add_recursion(self._root, item)

    def _get_min_value_node(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    def delete(self, item):
        found, _ = self.find(item)
        if not found:
            return

        self._size -= 1
        def _delete_recursive(node, item):
            if not node:
                return node

            if item < node.data:
                node.left = _delete_recursive(node.left, item)
            elif item > node.data:
                node.right = _delete_recursive(node.right, item)
            else:
                if not node.left:
                    return node.right
                elif not node.right:
                    return node.left

                node.data = self._get_min_value_node(node.right).data
                node.right = _delete_recursive(node.right, node.data)

            if not node:
                return node
            node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
            balance = self._get_balance(node)

            # l-l
            if balance > 1 and self._get_balance(node.left) >= 0:
                return self._rotate_right(node)
            # r-r
            if balance < -1 and self._get_balance(node.right) <= 0:
                return self._rotate_left(node)
            # l-r
            if balance > 1 and self._get_balance(node.left) < 0:
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node)
            # r-l
            if balance < -1 and self._get_balance(node.right) > 0:
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node)

            return node
        self._root = _delete_recursive(self._root, item)

    def _get_height(self, node):
        if not node:
            return 0
        return node.height

    def _get_balance(self,node):
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)

    def _rotate_right(self, y):
        x = y.left
        t = x.right
        x.right = y
        y.left = t
        y.height = 1+max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1+max(self._get_height(x.left), self._get_height(x.right))
        return x

    def _rotate_left(self, x):
        y = x.right
        t = y.left
        y.left = x
        x.right = t
        x.height = 1+max(self._get_height(x.left), self._get_height(x.right))
        y.height = 1+max(self._get_height(y.left), self._get_height(y.right))
        return y
