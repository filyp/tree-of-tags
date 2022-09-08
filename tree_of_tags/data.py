from forum_queries import get_all_posts, get_all_tags
from persistence import save_object, load_object

import datetime
import numpy as np
import networkx as nx
from collections import Counter
from krakow import krakow
from scipy.cluster.hierarchy import to_tree

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class dotdict(dict):
    """dot.notation access to dictionary attributes
    credit: https://stackoverflow.com/a/23689767/1093087
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def score_calculation(post, base_score, time_decay_factor=1.15):
    # use the HN algorithm
    # https://github.com/ForumMagnum/ForumMagnum/blob/fd1d6cb5e746ae0e77aab73464c705bddcb87517/packages/lesswrong/lib/scoring.ts
    age_in_hours = post.age_in_seconds / 3600
    return base_score / ((age_in_hours + 2) ** time_decay_factor)


class Data:
    def __init__(self, use_cached_forum_data=True, alpha=2, forum="ea", cracy_margin=0):
        self.alpha = alpha
        # * load data
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

        # * load tree
        tree_filename = f"{forum}_tree_{alpha:.1f}"
        tree_info = load_object(tree_filename)
        if tree_info is not None:
            logger.info("Loading tree from cache")
            self.tree, self.dendrogram, self.Tag_cooccurence, self.alpha = tree_info
        else:
            logger.warn("No cached tree found, generating it...")
            self.Tag_cooccurence = self.create_cooccurence_graph()
            self.tree, self.dendrogram = self.build_tree(self.Tag_cooccurence)
            tree_info = (self.tree, self.dendrogram, self.Tag_cooccurence, self.alpha)
            save_object(tree_info, tree_filename)
        
        # * convert items to dotdicts for ease of access
        for id_, post in self.posts.items():
            self.posts[id_] = dotdict(post)
        for id_, tag in self.tags.items():
            self.tags[id_] = dotdict(tag)

        # * calculate cracy scores
        for post in self.posts.values():
            counts = Counter(vote["voteType"] for vote in post.allVotes)
            post.bigUpvotes = counts["bigUpvote"]
            post.smallUpvotes = counts["smallUpvote"]
            post.smallDownvotes = counts["smallDownvote"]
            post.bigDownvotes = counts["bigDownvote"]
            post.democraticScore = post.bigUpvotes + post.smallUpvotes - post.smallDownvotes - post.bigDownvotes
            post.meritocraticScore = post.baseScore - post.democraticScore
        # filter out posts where one of the scores is negative
        filtered_posts = [post for post in self.posts.values() if post.democraticScore > 0 and post.meritocraticScore > 0]
        # find the median ratio
        median_ratio = np.median([p.meritocraticScore / p.democraticScore for p in filtered_posts])
        logger.info(f"Median ratio of meritocratic to democratic score: {median_ratio:.2f}")
        for post in filtered_posts:
            post.cracy = post.meritocraticScore / post.democraticScore / median_ratio
        # note that filtered out posts don't have a cracy score

        # * calculate how many seconds passed since the post was created
        for post in self.posts.values():
            timestamp = post.postedAt
            # convert timestamp of the form "%Y-%m-%dT%H:%M:%S.%fZ" string to a unix timestamp
            timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            # get current UTC time
            now = datetime.datetime.utcnow()
            post.age_in_seconds = int((now - timestamp).total_seconds())

        # * calculate all the possible scores that the engine may ask for
        _minus_inf = float("-inf")
        for p in self.posts.values():
            p.hr = p.score
            p.tr = p.baseScore
            if "cracy" not in p:
                p.tm = p.hm = p.td = p.hd = _minus_inf
            elif 1 + cracy_margin < p.cracy:
                # meritocratic post
                p.tm = p.meritocraticScore
                p.hm = score_calculation(p, p.meritocraticScore)
                p.td = p.hd = _minus_inf
            elif p.cracy <= 1 - cracy_margin:
                # democratic post
                p.td = p.democraticScore
                p.hd = score_calculation(p, p.democraticScore)
                p.tm = p.hm = _minus_inf
            else:
                p.tm = p.hm = p.td = p.hd = _minus_inf
            
        if None in (p.score for p in self.posts.values()):
            logger.warn("Some posts have no score, so all scores will be recomputed")
            for p in self.posts.values():
                # note we don't change p.score
                p.hr = score_calculation(p, p.baseScore)


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
        return Tag_cooccurence_trimmed

    def build_tree(self, Tag_cooccurence):
        _dendrogram = krakow(Tag_cooccurence, alpha=self.alpha, beta=1)
        tree = to_tree(_dendrogram)

        # convert leaf values to original ids
        ids_list = np.array(Tag_cooccurence.nodes)

        def substitute_id(leaf):
            leaf.id = ids_list[leaf.id]

        tree.pre_order(substitute_id)
        return tree, _dendrogram
