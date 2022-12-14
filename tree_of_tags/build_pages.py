from data import Data
from engine import Engine, TreeClimber
from html_builder import HTMLBuilder

import time
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

builder = HTMLBuilder()
depth = int(sys.argv[1]) if len(sys.argv) > 1 else 50

ranking_func_symbols = ["hm", "hr", "hd", "tm", "tr", "td", "am", "ar", "ad"]

num_of_tags = 12
num_of_posts = 14


def generate_branches(forum, engine, tree_version, id_, depth=50):
    if depth == 0:
        return

    # generate pages for current node
    for ranking_func_symbol in ranking_func_symbols:
        builder.build_page(
            f"{tree_version}{ranking_func_symbol}{id_}.html",
            forum,
            engine.get_best_left_tags(num_of_tags),
            engine.get_best_right_tags(num_of_tags),
            engine.get_best_left_posts(num_of_posts, ranking_func_symbol),
            engine.get_best_right_posts(num_of_posts, ranking_func_symbol),
            engine.get_number_of_left_posts(),
            engine.get_number_of_right_posts(),
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
    ("ea", (9, 13, 1.8)),
    ("lw", (18, 15, 4)),
    ("af", (1.6, 8, 16)),
]:
    for alpha, tree_version in zip(alphas, ("a", "b", "c")):
        start_time = time.time()
        data = Data(alpha=alpha, use_cached_forum_data=True, forum=forum)
        logger.info(f"{forum}: {tree_version}: Fetching time: {time.time() - start_time:.3f}s")

        start_time = time.time()
        climber = TreeClimber(data)
        engine = Engine(data, climber)
        logger.info(f"{forum}: {tree_version}: Tree building time: {time.time() - start_time:.3f}s")

        start_time = time.time()
        generate_branches(forum, engine, tree_version, "", depth=depth)
        logger.info(f"{forum}: {tree_version}: Page building time: {time.time() - start_time:.3f}s")

        logger.info("")

for forum, alpha in [
    ("ea", 9),
    ("lw", 18),
    ("af", 1.6),
]:
    start_time = time.time()
    data = Data(alpha=alpha, use_cached_forum_data=True, forum=forum)
    builder.build_similar_tags(data)
    builder.build_most_popular_tags(data)
    logger.info(f"{forum}: Similar tags building time: {time.time() - start_time:.3f}s")
