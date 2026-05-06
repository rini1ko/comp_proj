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
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image

_label = ""

def set_label(text: str):
    global _label
    _label = text

# ==========================================
# ЛОГІКА ДЛЯ БІНАРНИХ ДЕРЕВ (AVL, Splay, RB)
# ==========================================

def _bin_positions(node, depth, x_pos, px, py, nil=None, dx=1.0):
    if node is None or node is nil:
        return
    
    px[id(node)] = x_pos
    py[id(node)] = depth

    _bin_positions(node.left,  depth + 1, x_pos - dx, px, py, nil, dx / 2)
    _bin_positions(node.right, depth + 1, x_pos + dx, px, py, nil, dx / 2)

def _bin_depth(node, nil=None):
    if node is None or node is nil:
        return 0
    return 1 + max(_bin_depth(node.left, nil), _bin_depth(node.right, nil))


class Visualizer:
    BG         = "#111318"
    EDGE       = "#2a2f3d"
    NODE_FILL  = "#2a5298"
    NODE_RING  = "#4a7fd4"
    TEXT       = "#f0f0f0"
    HEADER_BG  = "#1a1d26"
    TITLE_CLR  = "#6ab0f5"
    STEP_CLR   = "#5dbb6e"
    DIM_CLR    = "#555c6e"

    NODE_R  = 0.5 
    FIG_W   = 10
    FIG_H   = 7

    def __init__(self, folder="frames"):
        self.folder = folder
        self._idx   = 0
        os.makedirs(folder, exist_ok=True)

    def node_color(self, node):
        return self.NODE_FILL, self.NODE_RING

    def node_label(self, node):
        if hasattr(node, 'key'):
            return str(node.key)
        if hasattr(node, 'data') and hasattr(node.data, 'key'):
            return str(node.data.key)
        if hasattr(node, 'data'):
            return str(node.data)
        return str(node)

    def nil_node(self, tree):
        return None

    def snapshot(self, tree, label=""):
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

        fig.add_artist(plt.Line2D([0, 1], [0.88, 0.88], transform=fig.transFigure, color="#252830", lw=1))

        path = os.path.join(self.folder, f"frame_{self._idx:04d}.png")
        fig.savefig(path, dpi=110, bbox_inches="tight", facecolor=self.BG, edgecolor="none")
        plt.close(fig)
        self._idx += 1

    def make_gif(self, output="animation.gif", frame_ms=600, last_ms=3000):
        files = sorted(glob.glob(os.path.join(self.folder, "frame_*.png")))
        if not files:
            print("Немає кадрів.")
            return
        imgs = [Image.open(f).convert("RGBA") for f in files]
        dur  = [frame_ms] * len(imgs)
        dur[-1] = last_ms
        imgs[0].save(output, save_all=True, append_images=imgs[1:], duration=dur, loop=0, disposal=2)
        print(f"✓ GIF згенеровано: {output} ({len(imgs)} кадрів)")

    def reset(self):
        self._idx = 0

    def _draw_header(self, ax, label):
        op, _, detail = label.partition(":")
        ax.text(0.02, 0.62, op.strip(), transform=ax.transAxes, color=self.TITLE_CLR,
                fontsize=12, fontfamily="monospace", fontweight="bold", va="center")
        if detail.strip():
            ax.text(0.02, 0.18, detail.strip(), transform=ax.transAxes, color=self.STEP_CLR,
                    fontsize=10, fontfamily="monospace", va="center")
        ax.text(0.98, 0.5, f"#{self._idx:03d}", transform=ax.transAxes, color=self.DIM_CLR,
                fontsize=9, fontfamily="monospace", va="center", ha="right")

    def _draw_tree(self, ax, tree):
        nil  = self.nil_node(tree)
        root = tree._root
        
        if root is None or root is nil:
            ax.text(0.0, -2.0, "Порожнє дерево", ha="center", va="center", color=self.DIM_CLR, fontsize=14)
            ax.set_xlim(-6.0, 6.0)
            ax.set_ylim(-8.0, 2.0)
            return

        d = _bin_depth(root, nil)
        initial_dx = max(1.5, 2 ** (d - 2) * 1.5)

        px, py = {}, {}
        _bin_positions(root, 0, 0.0, px, py, nil, dx=initial_dx)

        min_x, max_x = min(px.values()), max(px.values())
        max_extent = max(abs(min_x), abs(max_x))
        
        # ЗАХИСТ ВІД ВИЛАЗІННЯ ПО ШИРИНІ (додано 4 радіуси запасу)
        half_width = max(6.0, max_extent + self.NODE_R * 4.0)
        ax.set_xlim(-half_width, half_width)

        y_step = 2.5
        # ЗАХИСТ ВІД ВИЛАЗІННЯ ЗНИЗУ ТА ЗВЕРХУ
        y_bottom = -max(3, d) * y_step - self.NODE_R * 4.0
        ax.set_ylim(y_bottom, 2.0 + self.NODE_R * 2.0)
        
        ax.set_aspect('equal', adjustable='box')

        self._draw_edges_rec(ax, root, px, py, y_step, nil)
        self._draw_nodes_rec(ax, root, px, py, y_step, nil)

    def _draw_edges_rec(self, ax, node, px, py, ys, nil):
        if node is None or node is nil:
            return
        x, y = px[id(node)], -py[id(node)] * ys
        for child in (node.left, node.right):
            if child and child is not nil:
                cx, cy = px[id(child)], -py[id(child)] * ys
                ax.plot([x, cx], [y, cy], color=self.EDGE, lw=2.0, zorder=1)
        self._draw_edges_rec(ax, node.left,  px, py, ys, nil)
        self._draw_edges_rec(ax, node.right, px, py, ys, nil)

    def _draw_nodes_rec(self, ax, node, px, py, ys, nil):
        if node is None or node is nil:
            return
        x, y  = px[id(node)], -py[id(node)] * ys
        fill, ring = self.node_color(node)

        circle = plt.Circle((x, y), self.NODE_R, facecolor=fill, edgecolor=ring, linewidth=2.5, zorder=3)
        ax.add_patch(circle)

        label = self.node_label(node)
        font_size = 9 if "\n" in label else 11
        ax.text(x, y, label, ha="center", va="center", fontsize=font_size, fontfamily="monospace", color=self.TEXT, zorder=4)

        self._draw_nodes_rec(ax, node.left,  px, py, ys, nil)
        self._draw_nodes_rec(ax, node.right, px, py, ys, nil)


class RBVisualizer(Visualizer):
    RED_FILL, RED_RING = "#7a1c2e", "#e05c6a"
    BLK_FILL, BLK_RING = "#252525", "#777777"

    def nil_node(self, tree): return tree._nil
    def node_color(self, node): return (self.RED_FILL, self.RED_RING) if node.color == "R" else (self.BLK_FILL, self.BLK_RING)


class AVLVisualizer(Visualizer):
    def node_color(self, node):
        bf = self._bf(node)
        if bf == 0: return "#1a4a8a", "#4a7fd4"
        if abs(bf) == 1: return "#1a6b3a", "#4dab6e"
        return "#7a5a00", "#d4a820"

    def node_label(self, node):
        base_label = super().node_label(node)
        return f"{base_label}\n({self._bf(node):+d})"

    def _bf(self, node):
        lh = node.left.height  if (node.left  and hasattr(node.left,  "height")) else 0
        rh = node.right.height if (node.right and hasattr(node.right, "height")) else 0
        return lh - rh


# ==========================================
# ЛОГІКА ДЛЯ B-TREE ТА B+ TREE
# ==========================================

def _btree_positions(node, depth, lo, hi, px, py):
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

def _count_btree_leaves(node):
    if node is None: return 0
    if not getattr(node, 'children', []): return 1
    return sum(_count_btree_leaves(c) for c in node.children)

def _btree_depth(node):
    if node is None: return 0
    if not node.children: return 1
    return 1 + max(_btree_depth(c) for c in node.children)


class BTreeVisualizer:
    BG        = "#111318"
    EDGE      = "#2a2f3d"
    NODE_FILL = "#1a3a6a"
    NODE_RING = "#4a7fd4"
    TEXT      = "#f0f0f0"
    HEADER_BG = "#1a1d26"
    TITLE_CLR = "#6ab0f5"
    STEP_CLR  = "#5dbb6e"
    DIM_CLR   = "#555c6e"

    BOX_H     = 1.0
    KEY_W     = 0.8
    FIG_W, FIG_H = 11, 7

    def __init__(self, folder="frames"):
        self.folder = folder
        self._idx   = 0
        os.makedirs(folder, exist_ok=True)

    def node_fill(self, node): return self.NODE_FILL, self.NODE_RING

    def snapshot(self, tree, label=""):
        global _label
        if label: _label = label

        fig = plt.figure(figsize=(self.FIG_W, self.FIG_H), facecolor=self.BG)
        ax_hdr  = fig.add_axes([0.0, 0.88, 1.0, 0.12], facecolor=self.HEADER_BG)
        ax_tree = fig.add_axes([0.02, 0.01, 0.96, 0.86], facecolor=self.BG)
        ax_hdr.set_axis_off()
        ax_tree.set_axis_off()

        self._draw_header(ax_hdr, _label)
        self._draw_tree(ax_tree, tree)

        fig.add_artist(plt.Line2D([0, 1], [0.88, 0.88], transform=fig.transFigure, color="#252830", lw=1))

        path = os.path.join(self.folder, f"frame_{self._idx:04d}.png")
        fig.savefig(path, dpi=110, bbox_inches="tight", facecolor=self.BG, edgecolor="none")
        plt.close(fig)
        self._idx += 1

    def make_gif(self, output="animation.gif", frame_ms=600, last_ms=3000):
        files = sorted(glob.glob(os.path.join(self.folder, "frame_*.png")))
        if not files: return
        imgs = [Image.open(f).convert("RGBA") for f in files]
        dur  = [frame_ms] * len(imgs)
        dur[-1] = last_ms
        imgs[0].save(output, save_all=True, append_images=imgs[1:], duration=dur, loop=0, disposal=2)
        print(f"✓ GIF згенеровано: {output}")

    def _draw_header(self, ax, label):
        op, _, detail = label.partition(":")
        ax.text(0.02, 0.62, op.strip(), transform=ax.transAxes, color=self.TITLE_CLR, fontsize=12, fontfamily="monospace", fontweight="bold", va="center")
        if detail.strip():
            ax.text(0.02, 0.18, detail.strip(), transform=ax.transAxes, color=self.STEP_CLR, fontsize=10, fontfamily="monospace", va="center")
        ax.text(0.98, 0.5, f"#{self._idx:03d}", transform=ax.transAxes, color=self.DIM_CLR, fontsize=9, fontfamily="monospace", va="center", ha="right")

    def _draw_tree(self, ax, tree):
        if tree._root is None or not tree._root.keys:
            ax.text(0.0, -2.0, "Порожнє дерево", ha="center", va="center", color=self.DIM_CLR, fontsize=14)
            ax.set_xlim(-6.0, 6.0)
            ax.set_ylim(-8.0, 2.0)
            return

        d = _btree_depth(tree._root)
        leaves = _count_btree_leaves(tree._root)
        
        total_width = max(15.0, leaves * tree.m * self.KEY_W * 1.5)

        px, py = {}, {}
        _btree_positions(tree._root, 0, -total_width/2, total_width/2, px, py)

        min_x, max_x = min(px.values()), max(px.values())
        max_extent = max(abs(min_x), abs(max_x))
        
        # ЗАХИСТ ВІД ВИЛАЗІННЯ БЛОКІВ
        half_width = max(8.0, max_extent + self.KEY_W * 4.0)
        ax.set_xlim(-half_width, half_width)

        y_step = 2.5
        y_bottom = -max(3, d) * y_step - self.BOX_H * 3.0
        ax.set_ylim(y_bottom, 2.0 + self.BOX_H * 2.0)
        
        ax.set_aspect('equal', adjustable='box')

        self._draw_edges_rec(ax, tree._root, px, py, y_step)
        self._draw_nodes_rec(ax, tree._root, px, py, y_step)

    def _node_width(self, node):
        return max(len(node.keys), 1) * self.KEY_W

    def _draw_edges_rec(self, ax, node, px, py, ys):
        if node is None: return
        x, y = px[id(node)], -py[id(node)] * ys
        for child in node.children:
            cx, cy = px[id(child)], -py[id(child)] * ys
            ax.plot([x, cx], [y - self.BOX_H / 2, cy + self.BOX_H / 2], color=self.EDGE, lw=2.0, zorder=1)
            self._draw_edges_rec(ax, child, px, py, ys)

    def _draw_nodes_rec(self, ax, node, px, py, ys):
        if node is None: return
        x, y = px[id(node)], -py[id(node)] * ys
        w    = self._node_width(node)
        fill, ring = self.node_fill(node)

        rect = mpatches.FancyBboxPatch(
            (x - w / 2, y - self.BOX_H / 2), w, self.BOX_H,
            boxstyle="round,pad=0.1",
            facecolor=fill, edgecolor=ring, linewidth=2.0, zorder=3
        )
        ax.add_patch(rect)

        n = len(node.keys)
        kw = w / n
        for i, key in enumerate(node.keys):
            kx = x - w / 2 + (i + 0.5) * kw
            label = str(key.key) if hasattr(key, 'key') else str(key)
            ax.text(kx, y, label, ha="center", va="center", fontsize=11, fontfamily="monospace", color=self.TEXT, zorder=4)
            if i < n - 1:
                lx = x - w / 2 + (i + 1) * kw
                ax.plot([lx, lx], [y - self.BOX_H / 2, y + self.BOX_H / 2], color=ring, lw=1.2, zorder=4)

        for child in node.children:
            self._draw_nodes_rec(ax, child, px, py, ys)


class BPlusVisualizer(BTreeVisualizer):
    LEAF_FILL, LEAF_RING = "#0f3d2a", "#3dbb7a"

    def node_fill(self, node):
        return (self.LEAF_FILL, self.LEAF_RING) if node.leaf else (self.NODE_FILL, self.NODE_RING)

    def _draw_tree(self, ax, tree):
        super()._draw_tree(ax, tree)
        if tree._root and tree._root.keys:
            d = _btree_depth(tree._root)
            leaves = _count_btree_leaves(tree._root)
            total_width = max(15.0, leaves * tree.m * self.KEY_W * 1.5)
            px, py = {}, {}
            _btree_positions(tree._root, 0, -total_width/2, total_width/2, px, py)
            self._draw_leaf_links(ax, tree, px, py, 2.5)

    def _draw_leaf_links(self, ax, tree, px, py, ys):
        curr = getattr(tree, '_first_leaf', None)
        while curr is not None and curr.next is not None:
            if id(curr) in px and id(curr.next) in px:
                x1 = px[id(curr)]       + self._node_width(curr)       / 2
                x2 = px[id(curr.next)]  - self._node_width(curr.next)  / 2
                y1 = y2 = -py[id(curr)] * ys
                ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                            arrowprops=dict(arrowstyle="->", color=self.LEAF_RING, lw=2.0, linestyle="dashed"), zorder=5)
            curr = curr.next


_default_viz = None

def _get_viz():
    global _default_viz
    if _default_viz is None:
        _default_viz = Visualizer()
    return _default_viz

def save_tree_snapshot(tree, folder="frames"):
    viz = _get_viz()
    viz.folder = folder
    os.makedirs(folder, exist_ok=True)
    viz.snapshot(tree, _label)

def make_gif(folder="frames", output="animation.gif", frame_ms=600, last_ms=3000):
    _get_viz().make_gif(output, frame_ms, last_ms)