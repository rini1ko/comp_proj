from abc import ABC, abstractmethod

class TreeNode:
    def __init__(self, data):
        self.data = data

class Tree_ADT(ABC):
    def __init__(self, root=None):
        self._root=root
        self._size=0

    def is_empty(self):
        return self._size==0

    @abstractmethod
    def find(self, value):
        pass

    @abstractmethod
    def inorder(self):
        pass

    @abstractmethod
    def preorder(self):
        pass

    @abstractmethod
    def postorder(self):
        pass

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
    def _rotate_left(self, x):
        pass
