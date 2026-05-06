"""
visual.py — покадровий візуалізатор для п'яти видів дерев.

Класи:
    Visualizer       — базовий, для бінарних дерев (AVL, Splay)
    RBVisualizer     — успадковує Visualizer, додає кольори R/B
    AVLVisualizer    — успадковує Visualizer, додає balance factor
    BTreeVisualizer  — окремий клас для B-дерева (вузли-прямокутники)
    BPlusVisualizer  — успадковує BTreeVisualizer, виділяє листові зв'язки

Допоміжні функції (зворотна сумісність із splay_tree.py):
    set_label(text)          — встановити підпис наступного кадру
    save_tree_snapshot(tree) — зробити знімок через глобальний візуалізатор
    make_gif(...)            — зібрати GIF

Залежності: pip install matplotlib pillow
"""

import os
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image

_label = ""

def set_label(text: str):
    """Встановити текстовий підпис для наступного кадру."""
    global _label
    _label = text


def _bin_positions(node, depth, lo, hi, px, py, nil=None):
    """
    Рекурсивно обчислює координати кожного вузла бінарного дерева.
    x = середина діапазону [lo, hi] — гарантує рівномірний розподіл.
    y = глибина рівня (потім множиться на y_step для відступу).
    nil — сентинел (для RB-дерева), його не малюємо.
    """
    if node is None or node is nil:
        return
    mid = (lo + hi) / 2
    px[id(node)] = mid
    py[id(node)] = depth
    _bin_positions(node.left,  depth + 1, lo,  mid, px, py, nil)
    _bin_positions(node.right, depth + 1, mid, hi,  px, py, nil)

def _bin_depth(node, nil=None):
    """Повертає максимальну глибину бінарного дерева."""
    if node is None or node is nil:
        return 0
    return 1 + max(_bin_depth(node.left, nil), _bin_depth(node.right, nil))


class Visualizer:
    """
    Малює бінарне дерево: круглі вузли, ребра, заголовок.
    Підкласи перевизначають node_color() і node_label() — і більше нічого.
    """

    BG         = "#111318"
    EDGE       = "#2a2f3d"
    NODE_FILL  = "#2a5298"
    NODE_RING  = "#4a7fd4"
    TEXT       = "#f0f0f0"
    HEADER_BG  = "#1a1d26"
    TITLE_CLR  = "#6ab0f5"
    STEP_CLR   = "#5dbb6e"
    DIM_CLR    = "#555c6e"

    NODE_R  = 0.030
    FIG_W   = 9
    FIG_H   = 6

    def __init__(self, folder="frames"):
        self.folder = folder
        self._idx   = 0
        os.makedirs(folder, exist_ok=True)

    def node_color(self, node):
        """Повертає (fill, ring) — кольори заливки і обводки вузла."""
        return self.NODE_FILL, self.NODE_RING

    def node_label(self, node):
        """Повертає рядок, що буде надрукований всередині вузла."""
        return str(node.data)

    def nil_node(self, tree):
        """
        Повертає NIL-сентинел дерева або None.
        Перевизначити у RBVisualizer — там NIL є tree._nil.
        """
        return None

    def snapshot(self, tree, label=""):
        """
        Зробити один PNG-кадр поточного стану дерева.
        Викликається або вручну, або як callback після кожної операції.
        """
        global _label
        if label:
            _label = label

        fig = plt.figure(figsize=(self.FIG_W, self.FIG_H), facecolor=self.BG)
        ax_hdr  = fig.add_axes([0.0, 0.88, 1.0, 0.12], facecolor=self.HEADER_BG)
        ax_tree = fig.add_axes([0.02, 0.01, 0.96, 0.86], facecolor=self.BG)
        ax_hdr.set_axis_off()
        ax_tree.set_axis_off()

        self._draw_header(ax_hdr, _label)
        self._draw_tree(ax_tree, tree)

        fig.add_artist(plt.Line2D([0, 1], [0.88, 0.88],
                       transform=fig.transFigure, color="#252830", lw=1))

        path = os.path.join(self.folder, f"frame_{self._idx:04d}.png")
        fig.savefig(path, dpi=110, bbox_inches="tight",
                    facecolor=self.BG, edgecolor="none")
        plt.close(fig)
        self._idx += 1

    def make_gif(self, output="animation.gif", frame_ms=500, last_ms=2500):
        """Зібрати всі PNG з папки у GIF-анімацію."""
        files = sorted(glob.glob(os.path.join(self.folder, "frame_*.png")))
        if not files:
            print("Немає кадрів.")
            return
        imgs = [Image.open(f).convert("RGBA") for f in files]
        dur  = [frame_ms] * len(imgs)
        dur[-1] = last_ms
        imgs[0].save(output, save_all=True, append_images=imgs[1:],
                     duration=dur, loop=0, disposal=2)
        print(f"✓  {output}  ({len(imgs)} кадрів)")

    def reset(self):
        """Скинути лічильник кадрів (перед новою анімацією)."""
        self._idx = 0

    def _draw_header(self, ax, label):
        """Малює рядок заголовка: назва операції зліва, номер кадру справа."""
        op, _, detail = label.partition(":")
        ax.text(0.02, 0.62, op.strip(),
                transform=ax.transAxes, color=self.TITLE_CLR,
                fontsize=11, fontfamily="monospace", fontweight="bold", va="center")
        if detail.strip():
            ax.text(0.02, 0.18, detail.strip(),
                    transform=ax.transAxes, color=self.STEP_CLR,
                    fontsize=9, fontfamily="monospace", va="center")
        ax.text(0.98, 0.5, f"#{self._idx:03d}",
                transform=ax.transAxes, color=self.DIM_CLR,
                fontsize=8, fontfamily="monospace", va="center", ha="right")

    def _draw_tree(self, ax, tree):
        """Координує малювання всього дерева в осі ax."""
        nil  = self.nil_node(tree)
        root = tree._root
        if root is None or root is nil:
            ax.text(0.5, 0.5, "порожнє дерево",
                    ha="center", va="center", color=self.DIM_CLR,
                    fontsize=11, fontfamily="monospace")
            ax.set_xlim(0, 1); ax.set_ylim(-1, 1)
            return

        d      = _bin_depth(root, nil)
        y_step = min(0.18, 0.82 / max(d, 1))

        px, py = {}, {}
        _bin_positions(root, 0, 0.0, 1.0, px, py, nil)

        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-d * y_step - 0.1, 0.12)

        self._draw_edges_rec(ax, root, px, py, y_step, nil)
        self._draw_nodes_rec(ax, root, px, py, y_step, nil)

    def _draw_edges_rec(self, ax, node, px, py, ys, nil):
        """Рекурсивно малює ребра від батька до дітей."""
        if node is None or node is nil:
            return
        x, y = px[id(node)], -py[id(node)] * ys
        for child in (node.left, node.right):
            if child and child is not nil:
                ax.plot([x, px[id(child)]], [y, -py[id(child)] * ys],
                        color=self.EDGE, lw=1.8,
                        solid_capstyle="round", zorder=1)
        self._draw_edges_rec(ax, node.left,  px, py, ys, nil)
        self._draw_edges_rec(ax, node.right, px, py, ys, nil)

    def _draw_nodes_rec(self, ax, node, px, py, ys, nil):
        """
        Рекурсивно малює вузли як круглі патчі.
        Розмір і колір фіксовані — вузли ЗАВЖДИ круглі незалежно від вмісту.
        Текст підганяється під коло, не навпаки.
        """
        if node is None or node is nil:
            return
        x, y  = px[id(node)], -py[id(node)] * ys
        fill, ring = self.node_color(node)

        circle = plt.Circle((x, y), self.NODE_R,
                             facecolor=fill, edgecolor=ring,
                             linewidth=2.0, zorder=3)
        ax.add_patch(circle)

        label = self.node_label(node)
        font_size = 7 if "\n" in label else 8
        ax.text(x, y, label,
                ha="center", va="center",
                fontsize=font_size, fontfamily="monospace",
                color=self.TEXT, zorder=4)

        self._draw_nodes_rec(ax, node.left,  px, py, ys, nil)
        self._draw_nodes_rec(ax, node.right, px, py, ys, nil)

class RBVisualizer(Visualizer):
    """
    Відрізняється від базового лише кольорами вузлів:
      - червоні вузли (node.color == "R") — темно-червоні
      - чорні вузли  (node.color == "B") — темно-сірі
    """

    RED_FILL = "#7a1c2e"
    RED_RING = "#e05c6a"
    BLK_FILL = "#252525"
    BLK_RING = "#777777"

    def nil_node(self, tree):
        """RBTree зберігає сентинел у tree._nil."""
        return tree._nil

    def node_color(self, node):
        """Повертає кольори залежно від поля node.color."""
        if node.color == "R":
            return self.RED_FILL, self.RED_RING
        return self.BLK_FILL, self.BLK_RING

class AVLVisualizer(Visualizer):
    """
    Відрізняється від базового:
      - колір залежить від balance factor (bf):
          bf == 0      → синій (ідеально збалансований)
          |bf| == 1    → зелений (допустимо)
          |bf| >= 2    → жовтий (тимчасовий дисбаланс під час ротації)
      - підпис містить значення + bf у дужках
    """

    def node_color(self, node):
        """Колір залежить від balance factor вузла."""
        bf = self._bf(node)
        if bf == 0:
            return "#1a4a8a", "#4a7fd4"
        if abs(bf) == 1:
            return "#1a6b3a", "#4dab6e"
        return "#7a5a00", "#d4a820"

    def node_label(self, node):
        """Значення вузла + balance factor у дужках."""
        return f"{node.data}\n({self._bf(node):+d})"

    def _bf(self, node):
        """Обчислює balance factor = height(left) - height(right)."""
        lh = node.left.height  if (node.left  and hasattr(node.left,  "height")) else 0
        rh = node.right.height if (node.right and hasattr(node.right, "height")) else 0
        return lh - rh


def _btree_positions(node, depth, lo, hi, px, py):
    """
    Рекурсивно розраховує позиції для B/B+-дерева.
    Логіка та сама що для бінарного, але дітей може бути > 2.
    Кожна дитина отримує рівну частку діапазону батька.
    """
    if node is None:
        return
    mid = (lo + hi) / 2
    px[id(node)] = mid
    py[id(node)] = depth
    if node.children:
        n = len(node.children)
        w = (hi - lo) / n
        for i, child in enumerate(node.children):
            _btree_positions(child, depth + 1, lo + i * w, lo + (i + 1) * w, px, py)

def _btree_depth(node):
    """Максимальна глибина B-дерева."""
    if node is None:
        return 0
    if not node.children:
        return 1
    return 1 + max(_btree_depth(c) for c in node.children)


class BTreeVisualizer:
    """
    Окремий клас для B-дерева — вузли тут прямокутники зі списком ключів,
    а не кола. Структура зовсім інша ніж у бінарних дерев.
    Базовий клас Visualizer тут не підходить.
    """

    BG        = "#111318"
    EDGE      = "#2a2f3d"
    NODE_FILL = "#1a3a6a"
    NODE_RING = "#4a7fd4"
    TEXT      = "#f0f0f0"
    HEADER_BG = "#1a1d26"
    TITLE_CLR = "#6ab0f5"
    STEP_CLR  = "#5dbb6e"
    DIM_CLR   = "#555c6e"

    BOX_H     = 0.06
    KEY_W     = 0.055

    FIG_W = 11
    FIG_H = 7

    def __init__(self, folder="frames"):
        self.folder = folder
        self._idx   = 0
        os.makedirs(folder, exist_ok=True)

    def node_fill(self, node):
        """
        Колір прямокутника вузла.
        Перевизначається у BPlusVisualizer щоб виділяти листові вузли.
        """
        return self.NODE_FILL, self.NODE_RING

    def snapshot(self, tree, label=""):
        """Зробити один PNG-кадр поточного стану B-дерева."""
        global _label
        if label:
            _label = label

        fig = plt.figure(figsize=(self.FIG_W, self.FIG_H), facecolor=self.BG)
        ax_hdr  = fig.add_axes([0.0, 0.88, 1.0, 0.12], facecolor=self.HEADER_BG)
        ax_tree = fig.add_axes([0.02, 0.01, 0.96, 0.86], facecolor=self.BG)
        ax_hdr.set_axis_off()
        ax_tree.set_axis_off()

        self._draw_header(ax_hdr, _label)
        self._draw_tree(ax_tree, tree)

        fig.add_artist(plt.Line2D([0, 1], [0.88, 0.88],
                       transform=fig.transFigure, color="#252830", lw=1))

        path = os.path.join(self.folder, f"frame_{self._idx:04d}.png")
        fig.savefig(path, dpi=110, bbox_inches="tight",
                    facecolor=self.BG, edgecolor="none")
        plt.close(fig)
        self._idx += 1

    def make_gif(self, output="animation.gif", frame_ms=600, last_ms=2500):
        """Зібрати всі PNG з папки у GIF."""
        files = sorted(glob.glob(os.path.join(self.folder, "frame_*.png")))
        if not files:
            print("Немає кадрів.")
            return
        imgs = [Image.open(f).convert("RGBA") for f in files]
        dur  = [frame_ms] * len(imgs)
        dur[-1] = last_ms
        imgs[0].save(output, save_all=True, append_images=imgs[1:],
                     duration=dur, loop=0, disposal=2)
        print(f"✓  {output}  ({len(imgs)} кадрів)")

    def reset(self):
        self._idx = 0

    def _draw_header(self, ax, label):
        """Заголовок — назва операції + номер кадру."""
        op, _, detail = label.partition(":")
        ax.text(0.02, 0.62, op.strip(),
                transform=ax.transAxes, color=self.TITLE_CLR,
                fontsize=11, fontfamily="monospace", fontweight="bold", va="center")
        if detail.strip():
            ax.text(0.02, 0.18, detail.strip(),
                    transform=ax.transAxes, color=self.STEP_CLR,
                    fontsize=9, fontfamily="monospace", va="center")
        ax.text(0.98, 0.5, f"#{self._idx:03d}",
                transform=ax.transAxes, color=self.DIM_CLR,
                fontsize=8, fontfamily="monospace", va="center", ha="right")

    def _draw_tree(self, ax, tree):
        """Головна функція малювання B-дерева."""
        if tree._root is None or not tree._root.keys:
            ax.text(0.5, 0.5, "порожнє дерево",
                    ha="center", va="center", color=self.DIM_CLR,
                    fontsize=11, fontfamily="monospace")
            ax.set_xlim(0, 1); ax.set_ylim(-1, 1)
            return

        d      = _btree_depth(tree._root)
        y_step = min(0.20, 0.82 / max(d, 1))

        px, py = {}, {}
        _btree_positions(tree._root, 0, 0.0, 1.0, px, py)

        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-d * y_step - 0.12, 0.12)

        self._draw_edges_rec(ax, tree._root, px, py, y_step)
        self._draw_nodes_rec(ax, tree._root, px, py, y_step)

    def _node_width(self, node):
        """Ширина прямокутника залежить від кількості ключів."""
        return max(len(node.keys), 1) * self.KEY_W

    def _draw_edges_rec(self, ax, node, px, py, ys):
        """Малює ребра від центру нижньої межі батька до верху дитини."""
        if node is None:
            return
        x, y = px[id(node)], -py[id(node)] * ys
        for child in node.children:
            cx, cy = px[id(child)], -py[id(child)] * ys
            ax.plot([x, cx], [y - self.BOX_H / 2, cy + self.BOX_H / 2],
                    color=self.EDGE, lw=1.5,
                    solid_capstyle="round", zorder=1)
            self._draw_edges_rec(ax, child, px, py, ys)

    def _draw_nodes_rec(self, ax, node, px, py, ys):
        """
        Малює вузол як прямокутник із ключами.
        Ключі розділені вертикальними лініями всередині прямокутника.
        """
        if node is None:
            return
        x, y = px[id(node)], -py[id(node)] * ys
        w    = self._node_width(node)
        fill, ring = self.node_fill(node)

        rect = mpatches.FancyBboxPatch(
            (x - w / 2, y - self.BOX_H / 2), w, self.BOX_H,
            boxstyle="round,pad=0.005",
            facecolor=fill, edgecolor=ring, linewidth=1.5, zorder=3
        )
        ax.add_patch(rect)

        n = len(node.keys)
        kw = w / n
        for i, key in enumerate(node.keys):
            kx = x - w / 2 + (i + 0.5) * kw
            ax.text(kx, y, str(key),
                    ha="center", va="center",
                    fontsize=8, fontfamily="monospace",
                    color=self.TEXT, zorder=4)
            if i < n - 1:
                lx = x - w / 2 + (i + 1) * kw
                ax.plot([lx, lx], [y - self.BOX_H / 2, y + self.BOX_H / 2],
                        color=ring, lw=0.8, zorder=4)

        for child in node.children:
            self._draw_nodes_rec(ax, child, px, py, ys)

class BPlusVisualizer(BTreeVisualizer):
    """
    Відрізняється від BTreeVisualizer:
      - листові вузли (node.leaf == True) — зеленуватий колір
      - між листовими вузлами малюється пунктирна стрілка (зв'язний список)
    """

    LEAF_FILL = "#0f3d2a"
    LEAF_RING = "#3dbb7a"

    def node_fill(self, node):
        """Листові вузли — зелені, внутрішні — сині (як у BTree)."""
        if node.leaf:
            return self.LEAF_FILL, self.LEAF_RING
        return self.NODE_FILL, self.NODE_RING

    def _draw_tree(self, ax, tree):
        """
        Малює дерево і потім окремо — зв'язки між листовими вузлами
        (характерна особливість B+-дерева: листи утворюють зв'язний список).
        """
        if tree._root is None or not tree._root.keys:
            ax.text(0.5, 0.5, "порожнє дерево",
                    ha="center", va="center", color=self.DIM_CLR,
                    fontsize=11, fontfamily="monospace")
            ax.set_xlim(0, 1); ax.set_ylim(-1, 1)
            return

        d      = _btree_depth(tree._root)
        y_step = min(0.20, 0.82 / max(d, 1))

        px, py = {}, {}
        _btree_positions(tree._root, 0, 0.0, 1.0, px, py)

        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-d * y_step - 0.15, 0.12)

        self._draw_edges_rec(ax, tree._root, px, py, y_step)
        self._draw_nodes_rec(ax, tree._root, px, py, y_step)
        self._draw_leaf_links(ax, tree, px, py, y_step)

    def _draw_leaf_links(self, ax, tree, px, py, ys):
        """
        Малює пунктирні стрілки між сусідніми листовими вузлами
        (поле node.next — зв'язний список листів B+-дерева).
        """
        curr = tree._first_leaf
        while curr is not None and curr.next is not None:
            if id(curr) in px and id(curr.next) in px:
                x1 = px[id(curr)]       + self._node_width(curr)       / 2
                x2 = px[id(curr.next)]  - self._node_width(curr.next)  / 2
                y1 = y2 = -py[id(curr)] * ys
                ax.annotate("",
                    xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(
                        arrowstyle="->",
                        color=self.LEAF_RING,
                        lw=1.2,
                        linestyle="dashed",
                    ), zorder=5)
            curr = curr.next


_default_viz = None

def _get_viz():
    global _default_viz
    if _default_viz is None:
        _default_viz = Visualizer()
    return _default_viz

def save_tree_snapshot(tree, folder="frames"):
    """Зробити знімок через глобальний візуалізатор (для splay_tree.py)."""
    viz = _get_viz()
    viz.folder = folder
    os.makedirs(folder, exist_ok=True)
    viz.snapshot(tree, _label)

def make_gif(folder="frames", output="animation.gif", frame_ms=500, last_ms=2500):
    """Зібрати GIF через глобальний візуалізатор."""
    _get_viz().make_gif(output, frame_ms, last_ms)
