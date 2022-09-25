from forum_queries import get_all_posts, get_all_tags, get_all_comments
from persistence import save_object, load_object

import numpy as np
import networkx as nx
from collections import Counter
from krakow import krakow
from scipy.cluster.hierarchy import to_tree

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

seconds_in_month = 60 * 60 * 24 * 30


class dotdict(dict):
    """dot.notation access to dictionary attributes
    credit: https://stackoverflow.com/a/23689767/1093087
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def score_calculation(item, base_score, time_decay_factor=1.15):
    # use the HN algorithm
    # https://github.com/ForumMagnum/ForumMagnum/blob/fd1d6cb5e746ae0e77aab73464c705bddcb87517/packages/lesswrong/lib/scoring.ts
    age_in_hours = item["age_in_seconds"] / 3600
    return base_score / ((age_in_hours + 2) ** time_decay_factor)


class Data:
    def __init__(
        self,
        use_cached_forum_data=True,
        alpha=2,
        forum="ea",
        comments_time_decay_factor=1.15,
    ):
        self.alpha = alpha
        self.forum = forum

        # * load data
        filename = f"{forum}_posts_and_tags"
        forum_data = None
        if use_cached_forum_data:
            forum_data = load_object(filename)
            if forum_data is None:
                logger.warn("No cached forum data found, fetching it...")
        if forum_data is not None:
            self.posts, self.tags, self.comments = forum_data
        else:
            self.posts = get_all_posts(forum)
            self.tags = get_all_tags(forum)
            self.comments = get_all_comments(forum, younger_than=seconds_in_month * 6)
            save_object((self.posts, self.tags, self.comments), filename)

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

        all_posts = self.posts.values()
        # * calculate cracy scores
        for post in all_posts:
            counts = Counter(vote["voteType"] for vote in post.allVotes)
            post.bigUpvotes = counts["bigUpvote"]
            post.smallUpvotes = counts["smallUpvote"]
            post.smallDownvotes = counts["smallDownvote"]
            post.bigDownvotes = counts["bigDownvote"]
            post.smallBalance = post.smallUpvotes - post.smallDownvotes
            post.bigBalance = post.bigUpvotes - post.bigDownvotes
        avg_big_vote_component = np.mean([p.baseScore - p.smallBalance for p in all_posts])
        avg_big_balance = np.mean([p.bigBalance for p in all_posts])
        avg_vote_power = avg_big_vote_component / avg_big_balance
        for post in all_posts:
            post.democraticScore = int(post.smallBalance + avg_vote_power * post.bigBalance)
            post.meritocraticScore = int(2 * post.baseScore - post.democraticScore)
        # # normalize scores
        # avg_score = np.mean([post.baseScore for post in all_posts])
        # avg_democratic_score = np.mean([post.democraticScore for post in all_posts])
        # avg_meritocratic_score = np.mean([post.meritocraticScore for post in all_posts])
        # for post in all_posts:
        #     post.democraticScore = int(post.democraticScore / avg_democratic_score * avg_score)
        #     post.meritocraticScore = int(post.meritocraticScore / avg_meritocratic_score * avg_score)

        # * calculate all the possible scores that the engine may ask for
        _minus_inf = float("-inf")
        for p in all_posts:
            p.hr = p.score
            p.tr = p.baseScore
            # meritocratic post
            p.tm = p.meritocraticScore
            p.hm = score_calculation(p, p.meritocraticScore)
            # democratic post
            p.td = p.democraticScore
            p.hd = score_calculation(p, p.democraticScore)
            # calculate aliveness of that post
            comments = self.comments.get(p._id, [])
            aliveness = sum(score_calculation(c, 1, comments_time_decay_factor) for c in comments)
            p.ad = p.ar = p.am = aliveness

        if None in (p.score for p in all_posts):
            logger.warn("Some posts have no score, so all scores will be recomputed")
            for p in all_posts:
                # note we don't change p.score
                p.hr = score_calculation(p, p.baseScore)

        # * cached tree can have same tags which are already deleted on the forum
        # * so we need to add their stubs
        deleted_tags = 0
        for cached_tag in self.tree.pre_order():
            if cached_tag not in self.tags:
                deleted_tags += 1
                self.tags[cached_tag] = dotdict(
                    _id=cached_tag,
                    name="_deleted_",
                    slug="",
                )
        if deleted_tags:
            logger.warn(f"Added stubs of {deleted_tags} deleted tags")

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
