from forum_queries import get_all_posts, get_all_tags
from persistence import save_object, load_object

import numpy as np
import networkx as nx
from krakow import krakow
from scipy.cluster.hierarchy import to_tree

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Data:
    def __init__(self, use_cached_forum_data=True, use_cached_tree=True, alpha=1.5, forum="ea"):
        self.alpha = alpha
        # load data
        filename = f"{forum}_posts_and_tags"
        if use_cached_forum_data:
            forum_data = load_object(filename)
            if forum_data is None:
                logger.warn("No cached forum data found, fetching it...")
                self.posts = get_all_posts(forum)
                self.tags = get_all_tags(forum)
                save_object((self.posts, self.tags), filename)
            else:
                self.posts, self.tags = forum_data
        else:
            self.posts = get_all_posts(forum)
            self.tags = get_all_tags(forum)
            save_object((self.posts, self.tags), filename)

        # create the cooccurence graph
        self.create_cooccurence_graph()
        self.build_tree()

    def create_cooccurence_graph(self):
        Tag_cooccurence = nx.Graph()

        for post in self.posts.values():
            tags_in_post = post["tagRelevance"]
            if tags_in_post is None:
                continue

            for tag1 in tags_in_post:
                for tag2 in tags_in_post:
                    if not Tag_cooccurence.has_edge(tag1, tag2):
                        Tag_cooccurence.add_edge(tag1, tag2, weight=0)

                    cooccurence_strength = tags_in_post[tag1] * tags_in_post[tag2]
                    if tag1 != tag2:
                        # we divide by two because each pair is counted twice
                        cooccurence_strength /= 2
                    Tag_cooccurence[tag1][tag2]["weight"] += cooccurence_strength

        # remove tags which were not fetched for some reason, but are present in posts
        num_of_removed = 0
        for node in list(Tag_cooccurence.nodes):
            if node not in self.tags:
                Tag_cooccurence.remove_node(node)
                num_of_removed += 1
        logger.info(f"Removed {num_of_removed} tags present in posts but not in fetched tags")

        # skip tags which don't cooccure with any other tag, or form a disconnected graph
        components = sorted(nx.connected_components(Tag_cooccurence), key=len, reverse=True)
        main_component = components[0]
        Tag_cooccurence_trimmed = Tag_cooccurence.subgraph(main_component)
        logger.info(
            f"Removed {len(Tag_cooccurence) - len(Tag_cooccurence_trimmed)} tags which don't cooccure with any other tags"
        )
        # removed_tags = set(Tag_cooccurence.nodes) - set(Tag_cooccurence_trimmed.nodes)
        # for tag in removed_tags:
        #     print(self.tags[tag]["name"])
        self.Tag_cooccurence = Tag_cooccurence_trimmed

    def build_tree(self):
        self._dendrogram = krakow(self.Tag_cooccurence, alpha=self.alpha, beta=1)
        tree = to_tree(self._dendrogram)

        # convert leaf values to original ids
        ids_list = np.array(self.Tag_cooccurence.nodes)

        def substitute_id(leaf):
            leaf.id = ids_list[leaf.id]

        tree.pre_order(substitute_id)
        self.tree = tree
