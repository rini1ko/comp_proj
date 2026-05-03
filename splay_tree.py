from tree_adt import Tree_ADT
class SplayNode:
    def __init__(self, data, left=None, right=None, parent=None):
        self.data = data
        self.left = left
        self.right = right
        self.parent = parent

class Splay_tree(Tree_ADT):
    def _rotate_left(self, node):
        p = node.parent
        p.right = node.left
        if node.left:
            node.left.parent = p
        node.parent = p.parent
        if not p.parent:
            self._root = node
        elif p.parent.left == p:
            p.parent.left = node
        else:
            p.parent.right = node
        node.left = p
        p.parent = node

    def _rotate_right(self, node):
        p = node.parent
        p.left = node.right
        if node.right:
            node.right.parent = p
        node.parent = p.parent
        if not p.parent:
            self._root = node
        elif p.parent.left == p:
            p.parent.left = node
        else:
            p.parent.right = node
        node.right = p
        p.parent = node

    def zig(self, node):
        if node.parent.left==node:
            self._rotate_right(node)
        elif node.parent.right==node:
            self._rotate_left(node)

    def zigzig(self, node):
        parent=node.parent
        if parent.parent.left==parent:
            self._rotate_right(parent)
            self._rotate_right(node)
        elif parent.parent.right==parent:
            self._rotate_left(parent)
            self._rotate_left(node)

    def zigzag(self, node):
        parent = node.parent
        if parent.parent.left == parent:
            self._rotate_left(node)
            self._rotate_right(node)
        elif parent.parent.right == parent:
            self._rotate_right(node)
            self._rotate_left(node)

    def find(self, value):
        node = self._root
        last=None
        while node is not None:
            if value == node.data:
                self.splay(node)
                return (True, node)
            elif value < node.data:
                last=node
                node = node.left
            else:
                last=node
                node = node.right
        if last:
            self.splay(last)
        return (False, None)

    def splay(self, node):
        while node.parent:
            if node.parent.parent:
                g=node.parent.parent
                if (g.left and g.left.right and g.left.right==node) or (g.right and g.right.left and g.right.left==node):
                    self.zigzag(node)
                else:
                    self.zigzig(node)
            else:
                self.zig(node)

    def add(self, item):
        if self.is_empty():
            self._size=1
            self._root=SplayNode(item)
        else:
            curr=self._root
            while True:
                if item<curr.data:
                    if not curr.left:
                        new=SplayNode(item)
                        curr.left=new
                        new.parent=curr
                        self._size+=1
                        self.splay(new)
                        break
                    curr=curr.left
                elif item>curr.data:
                    if not curr.right:
                        new=SplayNode(item)
                        curr.right=new
                        new.parent=curr
                        self._size+=1
                        self.splay(new)
                        break
                    curr=curr.right
                else:
                    self.splay(curr)
                    break


    def delete(self, item):
        if self.is_empty():
            raise ValueError
        curr = self._root
        while True:
            if item<curr.data:
                if not curr.left:
                    raise ValueError
                curr=curr.left
            elif item>curr.data:
                if not curr.right:
                    raise ValueError
                curr=curr.right
            else:
                self.splay(curr)
                break

        left=self._root.left
        right=self._root.right
        if left:
            left.parent=None
        if right:
            right.parent=None

        if not left:
            self._root=right
        else:
            max_node=left
            while max_node.right:
                max_node=max_node.right
            self.splay(max_node)
            max_node.right=right
            if right:
                right.parent=max_node
            self._root=max_node
        self._size-=1

    def inorder(self):
        lst = []

        def recurse(node):
            if node != None:
                recurse(node.left)
                lst.append(node.data)
                recurse(node.right)

        recurse(self._root)
        return iter(lst)

    def preorder(self):
        lst = []

        def recurse(node):
            if node != None:
                lst.append(node.data)
                recurse(node.left)
                recurse(node.right)

        recurse(self._root)
        return iter(lst)

    def postorder(self):
        lst = []

        def recurse(node):
            if node != None:
                recurse(node.left)
                recurse(node.right)
                lst.append(node.data)

        recurse(self._root)
        return iter(lst)
def validate_tree_integrity(tree):
    """
    перевірка на інордер обхід, на коректне сполучення нод.
    """
    if tree.is_empty():
        return True, "Дерево порожнє."
    values = list(tree.inorder())
    if values != sorted(values):
        return False, f"Порушено порядок BST: {values}"
    if len(values) != len(set(values)):
        return False, "Дерево містить дублікати (для BST це зазвичай помилка)."
    if tree._root.parent is not None:
        return False, "Помилка: Корінь має посилання на батька."
    def check_links(node):
        if node is None:
            return True
        if node.left:
            if node.left.parent != node:
                print(f"Помилка зв'язку: {node.left.data} <-X- {node.data}")
                return False
        if node.right:
            if node.right.parent != node:
                print(f"Помилка зв'язку: {node.data} -X-> {node.right.data}")
                return False
        return check_links(node.left) and check_links(node.right)
    if not check_links(tree._root):
        return False, "Структурна цілісність (parent pointers) порушена."
    return True, f"OK: {len(values)} вузлів, BST та структура в нормі."

if __name__=='__main__':
    tree1 = Splay_tree()
    for i in range(1, 6):
        tree1.add(i)
    success, message = validate_tree_integrity(tree1)
    print(message)
    tree1.delete(3)
    success, message = validate_tree_integrity(tree1)
    print(message)
    tree1.add(19)
    success, message = validate_tree_integrity(tree1)
    print(message)
