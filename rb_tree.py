from tree_adt import Tree_ADT, TreeNode


class RBNode(TreeNode):
    """Вузол червоно-чорного дерева: колір, посилання на лівого/правого сина та батька."""

    def __init__(self, data, color="R", left=None, right=None, parent=None):
        super().__init__(data)
        self.color = color  # "R" or "B"
        self.left = left
        self.right = right
        self.parent = parent


class RBTree(Tree_ADT):
    """Червоно-чорне дерево пошуку з листовим сентинелом `_nil` (єдиний чорний «порожній» вузол)."""

    def __init__(self):
        self._nil = RBNode(None, color="B", left=None, right=None, parent=None)
        super().__init__(root=self._nil)

    def _rotate_left(self, x):
        """Ліве обертання навколо x: піднімає правого сина, зберігає порядок ключів."""
        y = x.right
        x.right = y.left
        if y.left is not self._nil:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None:
            self._root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _rotate_right(self, y):
        """Праве обертання навколо y: піднімає лівого сина, дзеркально до _rotate_left."""
        x = y.left
        y.left = x.right
        if x.right is not self._nil:
            x.right.parent = y
        x.parent = y.parent
        if y.parent is None:
            self._root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x

    def _transplant(self, u, v):
        """Замінює піддерево з коренем u на v у батька u; батько v оновлюється."""
        if u.parent is None:
            self._root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _minimum(self, node):
        """Найменший ключ у піддереві: іде вліво до сентинела."""
        while node.left is not self._nil:
            node = node.left
        return node

    def _insert_fixup_zig_zig_left(self, z):
        """Виправлення після вставки: чорний дядько, шлях LL — перефарбування та праве обертання у діда."""
        z.parent.color = "B"
        z.parent.parent.color = "R"
        self._rotate_right(z.parent.parent)

    def _insert_fixup_zig_zag_left(self, z):
        """Чорний дядько, шлях LR: ліве обертання у батька, далі як у zig-zig зліва."""
        z = z.parent
        self._rotate_left(z)
        self._insert_fixup_zig_zig_left(z)
        return z

    def _insert_fixup_zig_zig_right(self, z):
        """Чорний дядько, шлях RR — перефарбування та ліве обертання у діда."""
        z.parent.color = "B"
        z.parent.parent.color = "R"
        self._rotate_left(z.parent.parent)

    def _insert_fixup_zig_zag_right(self, z):
        """Чорний дядько, шлях RL: праве обертання у батька, далі як у zig-zig справа."""
        z = z.parent
        self._rotate_right(z)
        self._insert_fixup_zig_zig_right(z)
        return z

    def _insert_fixup(self, z):
        """Відновлює інваріанти RB-після вставки червоного листа (перефарбування та обертання)."""
        while z.parent is not None and z.parent.color == "R":
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right
                if y.color == "R":
                    z.parent.color = "B"
                    y.color = "B"
                    z.parent.parent.color = "R"
                    z = z.parent.parent
                else:
                    if z == z.parent.right:
                        z = self._insert_fixup_zig_zag_left(z)
                    else:
                        self._insert_fixup_zig_zig_left(z)
            else:
                y = z.parent.parent.left
                if y.color == "R":
                    z.parent.color = "B"
                    y.color = "B"
                    z.parent.parent.color = "R"
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = self._insert_fixup_zig_zag_right(z)
                    else:
                        self._insert_fixup_zig_zig_right(z)
            if z == self._root:
                break
        self._root.color = "B"

    def _delete_fixup(self, x):
        """Виправлення після видалення чорного вузла: баланс подвійно-чорного через брата w та обертання."""
        while x != self._root and x.color == "B":
            if x == x.parent.left:
                w = x.parent.right
                if w.color == "R":
                    w.color = "B"
                    x.parent.color = "R"
                    self._rotate_left(x.parent)
                    w = x.parent.right
                if w.left.color == "B" and w.right.color == "B":
                    w.color = "R"
                    x = x.parent
                else:
                    if w.right.color == "B":
                        w.left.color = "B"
                        w.color = "R"
                        self._rotate_right(w)
                        w = x.parent.right
                    w.color = x.parent.color
                    x.parent.color = "B"
                    w.right.color = "B"
                    self._rotate_left(x.parent)
                    x = self._root
            else:
                w = x.parent.left
                if w.color == "R":
                    w.color = "B"
                    x.parent.color = "R"
                    self._rotate_right(x.parent)
                    w = x.parent.left
                if w.right.color == "B" and w.left.color == "B":
                    w.color = "R"
                    x = x.parent
                else:
                    if w.left.color == "B":
                        w.right.color = "B"
                        w.color = "R"
                        self._rotate_left(w)
                        w = x.parent.left
                    w.color = x.parent.color
                    x.parent.color = "B"
                    w.left.color = "B"
                    self._rotate_right(x.parent)
                    x = self._root
        x.color = "B"

    def add(self, item):
        """Вставляє item як новий червоний лист; дублікати ігноруються. Після вставки викликається балансування."""
        z = RBNode(item, color="R", left=self._nil, right=self._nil, parent=None)
        y = None
        x = self._root
        while x is not self._nil:
            y = x
            if z.data < x.data:
                x = x.left
            elif z.data > x.data:
                x = x.right
            else:
                return
        z.parent = y
        if y is None:
            self._root = z
        elif z.data < y.data:
            y.left = z
        else:
            y.right = z
        self._size += 1
        self._insert_fixup(z)

    def delete(self, item):
        """Видаляє item за стандартним алгоритмом (наступник у піддереві, якщо два сини); балансування якщо видалено чорний."""
        z = self._search_node(item)
        if z is self._nil:
            return

        y = z
        y_orig_color = y.color

        if z.left is self._nil:
            x = z.right
            self._transplant(z, z.right)
        elif z.right is self._nil:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_orig_color = y.color
            x = y.right
            if y.parent == z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

        self._size -= 1
        if y_orig_color == "B":
            self._delete_fixup(x)

    def _search_node(self, k):
        """Повертає вузол з ключем k або сентинел `_nil`, якщо ключа немає."""
        x = self._root
        while x is not self._nil and k != x.data:
            if k < x.data:
                x = x.left
            else:
                x = x.right
        return x

    def find(self, value):
        """Шукає value: (True, значення) якщо знайдено, інакше (False, None)."""
        x = self._search_node(value)
        if x is self._nil:
            return False, None
        return True, x.data

    def inorder(self):
        lst = []

        def recurse(node):
            if node is not self._nil:
                recurse(node.left)
                lst.append(node.data)
                recurse(node.right)

        recurse(self._root)
        return iter(lst)

    def preorder(self):
        lst = []

        def recurse(node):
            if node is not self._nil:
                lst.append(node.data)
                recurse(node.left)
                recurse(node.right)

        recurse(self._root)
        return iter(lst)

    def postorder(self):
        lst = []

        def recurse(node):
            if node is not self._nil:
                recurse(node.left)
                recurse(node.right)
                lst.append(node.data)

        recurse(self._root)
        return iter(lst)
