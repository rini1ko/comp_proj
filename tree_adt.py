from abc import ABC, abstractmethod

class BSTNode:
    def __init__(self, data, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right

class BST_ADT(ABC):
    def __init__(self, root=None):
        self._root=root
        self._size=0

    def is_empty(self):
        return self._size==0

    def find(self, value):
        node = self._root
        while node is not None:
            if value == node.data:
                return True, node
            elif value < node.data:
                node = node.left
            else:
                node = node.right
        return False, None

    def inorder(self):
        lst = list()

        def recurse(node):
            if node != None:
                recurse(node.left)
                lst.append(node.data)
                recurse(node.right)

        recurse(self._root)
        return iter(lst)

    def preorder(self):
        lst = list()

        def recurse(node):
            if node != None:
                lst.append(node.data)
                recurse(node.left)
                recurse(node.right)

        recurse(self._root)
        return iter(lst)

    def postorder(self):
        lst = list()

        def recurse(node):
            if node != None:
                recurse(node.left)
                recurse(node.right)
                lst.append(node.data)

        recurse(self._root)
        return iter(lst)

    @abstractmethod
    def add(self, item):
        pass

    @abstractmethod
    def delete(self, item):
        pass

    @abstractmethod
    def _rotate_right(self, y):
        pass

    @abstractmethod
    def _rotate_left(self, y):
        pass
