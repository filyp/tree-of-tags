from data import Data
from engine import Engine, TreeClimber
from html_builder import HTMLBuilder

import time
import sys


start_time = time.time()
data = Data(alpha=1.5, use_cached_forum_data=True)
fetching_time = time.time() - start_time
print(f"Fetching time: {fetching_time:.3f}s")

start_time = time.time()
climber = TreeClimber(data)
engine = Engine(data, climber)
tree_building_time = time.time() - start_time
print(f"Tree building time: {tree_building_time:.3f}s")

builder = HTMLBuilder()


def generate_branches(id_, depth=3):
    if depth == 0:
        return

    # generate current node
    builder.build_page(
        f"{id_}.html",
        engine.get_best_left_tags(),
        engine.get_best_right_tags(),
        engine.get_best_left_posts(),
        engine.get_best_right_posts(),
    )

    # generate left branch
    if not engine.climber.current_branch.left.is_leaf():
        engine.choose_left()
        generate_branches(id_ + "0", depth - 1)
        engine.go_back()

    # generate right branch
    if not engine.climber.current_branch.right.is_leaf():
        engine.choose_right()
        generate_branches(id_ + "1", depth - 1)
        engine.go_back()

start_time = time.time()
depth = int(sys.argv[1]) if len(sys.argv) > 1 else 50
generate_branches("a", depth=depth)
page_building_time = time.time() - start_time
print(f"Page building time: {page_building_time:.3f}s")
