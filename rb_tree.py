from tree_adt import Tree_ADT
class RBNode:
    def __init__(self, data, color="R", left=None, right=None, parent=None):
        self.data = data
        self.color = color  #"R" or "B"
        self.left = left
        self.right = right
        self.parent = parent
NIL = RBNode(None, color="B") #this is the end point of every leaf
class RBTree(Tree_ADT):
    def _insert_fixup(self, node):
        pass
    def _delete_fixup(self, node):
        pass
    def _transplant(self, u, v):
        pass
    def _minimum(self, node):
        pass
    def _get_uncle(self, node):
        pass
