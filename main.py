import argparse
import os
import shutil
import visual
from database import DatabaseEngine
from avl_tree import AVL_Tree
from splay_tree import Splay_tree
from rb_tree import RBTree

def main():
    parser = argparse.ArgumentParser(description="Tree-based Database Engine")
    parser.add_argument("--tree", choices=["avl", "splay", "rb"], default="avl", help="Choose tree structure")
    args = parser.parse_args()

    if os.path.exists("frames"):
        shutil.rmtree("frames", ignore_errors=True)

    if args.tree == "avl":
        selected_tree = AVL_Tree()
    elif args.tree == "splay":
        selected_tree = Splay_tree()
    elif args.tree == "rb":
        selected_tree = RBTree()
    else:
        selected_tree = AVL_Tree()

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
