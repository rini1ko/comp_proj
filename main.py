import argparse
import os
import shutil
import visual
from database import DatabaseEngine
from avl_tree import AVL_Tree
from splay_tree import Splay_tree
from rb_tree import RBTree
from b_tree import BTree
from b_plus_tree import BPlusTree

def main():
    parser = argparse.ArgumentParser(description="Tree-based Database Engine")
    # Додали btree та bplus у choices
    parser.add_argument("--tree", choices=["avl", "splay", "rb", "btree", "bplus"], default="avl", help="Choose tree structure")
    args = parser.parse_args()

    if os.path.exists("frames"):
        shutil.rmtree("frames", ignore_errors=True)

    # Вибір дерева та прив'язка візуалізатора
    if args.tree == "avl":
        selected_tree = AVL_Tree()
        visual._default_viz = visual.AVLVisualizer()
    elif args.tree == "splay":
        selected_tree = Splay_tree()
        visual._default_viz = visual.Visualizer()
    elif args.tree == "rb":
        selected_tree = RBTree()
        visual._default_viz = visual.RBVisualizer()
    elif args.tree == "btree":
        selected_tree = BTree(m=4)  # m - це максимальна кількість дітей
        visual._default_viz = visual.BTreeVisualizer()
    elif args.tree == "bplus":
        selected_tree = BPlusTree(m=4)
        visual._default_viz = visual.BPlusVisualizer()
    else:
        selected_tree = AVL_Tree()
        visual._default_viz = visual.AVLVisualizer()

    db = DatabaseEngine(selected_tree)

    print(f"Database started (Tree: {args.tree.upper()}).")
    print("Example commands:")
    print('  INSERT 101 {"name": "Mykyta", "faculty": "CS"}')
    print('  SELECT 101')
    print('  UPDATE 101 {"name": "Mykyta", "faculty": "DA"}')
    print('  DELETE 101')
    print("Enter 'q' to quit.")

    while True:
        try:
            user_input = input("\n> ")
            if user_input.strip().lower() == 'q':
                print("Exiting database...")
                break
            if user_input.strip():
                result = db.execute(user_input)
                print(result)
        except KeyboardInterrupt:
            print("\nExiting database...")
            break

    visual.make_gif("frames", f"{args.tree}_db_animation.gif", frame_ms=800, last_ms=3000)

if __name__ == "__main__":
    main()