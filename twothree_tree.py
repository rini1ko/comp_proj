from b_tree import BTree


class TwoThreeTree(BTree):
    """
    2-3 дерево — окремий випадок B-дерева з параметром m = 3.
    Кожен внутрішній вузол має 2 або 3 дітей і містить 1 або 2 ключі.
    Уся логіка пошуку, вставки, видалення та обходів повністю успадковується від BTree.
    """

    def __init__(self):
        super().__init__(m=3)


# if __name__ == '__main__':
#     import shutil
#     import os
#     import visual
#     from visual import set_label, make_gif
#     if os.path.exists("frames"):
#         shutil.rmtree("frames")
#     visual._default_viz = visual.BTreeVisualizer()
#     tree = TwoThreeTree()
#     values_to_add = [10, 20, 5, 6, 12, 30, 7, 17]
#     for val in values_to_add:
#         set_label(f"Add: {val}")
#         tree.add(val)
#     set_label("Delete: 6 (Merge/Borrow)")
#     tree.delete(6)
#     gif_dir = os.path.join("results", "GIFs")
#     os.makedirs(gif_dir, exist_ok=True)
#     make_gif("frames", os.path.join(gif_dir, "2-3_animation.gif"), frame_ms=1000, last_ms=3000)
#     print("Done")
