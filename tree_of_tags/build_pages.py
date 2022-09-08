from data import Data
from engine import Engine, TreeClimber
from html_builder import HTMLBuilder

import time
import sys


builder = HTMLBuilder()
depth = int(sys.argv[1]) if len(sys.argv) > 1 else 50

ranking_func_symbols = ["hm", "hr", "hd", "tm", "tr", "td", "am", "ar", "ad"]


def generate_branches(forum, engine, tree_version, id_, depth=50):
    if depth == 0:
        return

    # generate pages for current node
    for ranking_func_symbol in ranking_func_symbols:
        builder.build_page(
            f"{tree_version}{ranking_func_symbol}{id_}.html",
            forum,
            engine.get_best_left_tags(),
            engine.get_best_right_tags(),
            engine.get_best_left_posts(ranking_func_symbol=ranking_func_symbol),
            engine.get_best_right_posts(ranking_func_symbol=ranking_func_symbol),
        )

    # generate left branch
    if not engine.climber.current_branch.left.is_leaf():
        engine.choose_left()
        generate_branches(forum, engine, tree_version, id_ + "0", depth - 1)
        engine.go_back()

    # generate right branch
    if not engine.climber.current_branch.right.is_leaf():
        engine.choose_right()
        generate_branches(forum, engine, tree_version, id_ + "1", depth - 1)
        engine.go_back()


for forum, alphas in [
    ("lw", (18, 15, 4)),
    ("ea", (9, 13, 1.8)),
    ("af", (1.6, 8, 16)),
]:
    for alpha, tree_version in zip(alphas, ("a", "b", "c")):
        start_time = time.time()
        data = Data(alpha=alpha, use_cached_forum_data=True, forum=forum)
        print(f"{forum}: {tree_version}: Fetching time: {time.time() - start_time:.3f}s")

        start_time = time.time()
        climber = TreeClimber(data)
        engine = Engine(data, climber)
        print(f"{forum}: {tree_version}: Tree building time: {time.time() - start_time:.3f}s")

        start_time = time.time()
        generate_branches(forum, engine, tree_version, "", depth=depth)
        print(f"{forum}: {tree_version}: Page building time: {time.time() - start_time:.3f}s")

        print()
