from data import Data
from engine import Engine, TreeClimber
from html_builder import HTMLBuilder

import time
import sys


builder = HTMLBuilder()
depth = int(sys.argv[1]) if len(sys.argv) > 1 else 50

prefix_to_ranking_func = {
    "h": lambda post: post["score"],
    "t": lambda post: post["baseScore"],
    "c": lambda post: post["commentCount"] if post["commentCount"] is not None else 0,
}


def generate_branches(forum, engine, id_, depth=50):
    if depth == 0:
        return

    # generate pages for current node
    for prefix, ranking_func in prefix_to_ranking_func.items():
        builder.build_page(
            f"{forum}/{prefix}{id_}.html",
            forum,
            engine.get_best_left_tags(),
            engine.get_best_right_tags(),
            engine.get_best_left_posts(ranking_func=ranking_func),
            engine.get_best_right_posts(ranking_func=ranking_func),
        )

    # generate left branch
    if not engine.climber.current_branch.left.is_leaf():
        engine.choose_left()
        generate_branches(forum, engine, id_ + "0", depth - 1)
        engine.go_back()

    # generate right branch
    if not engine.climber.current_branch.right.is_leaf():
        engine.choose_right()
        generate_branches(forum, engine, id_ + "1", depth - 1)
        engine.go_back()


for forum in ["ea", "lw", "af"]:
    start_time = time.time()
    data = Data(alpha=1.5, use_cached_forum_data=True)
    print(f"{forum}: Fetching time: {time.time() - start_time:.3f}s")

    start_time = time.time()
    climber = TreeClimber(data)
    engine = Engine(data, climber)
    print(f"{forum}: Tree building time: {time.time() - start_time:.3f}s")

    start_time = time.time()
    generate_branches(forum, engine, "", depth=depth)
    print(f"{forum}: Page building time: {time.time() - start_time:.3f}s")

    print()