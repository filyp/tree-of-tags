import numpy as np

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TreeClimber:
    def __init__(self, data):
        self.data = data
        self.current_branch = data.tree
        self.history = []

        self.left = set(self.current_branch.left.pre_order())
        self.right = set(self.current_branch.right.pre_order())

    def choose_left(self):
        self.history.append(self.current_branch)
        self.current_branch = self.current_branch.left
        self.left = set(self.current_branch.left.pre_order())
        self.right = set(self.current_branch.right.pre_order())

    def choose_right(self):
        self.history.append(self.current_branch)
        self.current_branch = self.current_branch.right
        self.left = set(self.current_branch.left.pre_order())
        self.right = set(self.current_branch.right.pre_order())

    def go_back(self):
        if len(self.history) == 0:
            logger.info("Tree history is empty, doing nothing")
            return
        self.current_branch = self.history.pop()
        self.left = set(self.current_branch.left.pre_order())
        self.right = set(self.current_branch.right.pre_order())


class Engine:
    def __init__(self, data, climber):
        self.data = data
        self.sorted_posts = sorted(data.posts.values(), key=lambda post: post["_id"])
        self.current_post_ids = np.ones_like(self.sorted_posts)
        self.current_post_ids_history = []
        self.climber = climber

        self.tag_occurences_in_posts = dict()
        for tag in data.tags:
            self.tag_occurences_in_posts[tag] = self.separate_posts_using_given_tags([], [tag])
        self.refresh()

    def separate_posts_using_given_tags(self, left_tags, right_tags):
        """
        posts, should be a sorted list of all posts
        returns a numpy array of side attribution of each post
        """
        post_sides = np.zeros_like(self.sorted_posts)  # negative is left, positive is right
        for i, post in enumerate(self.sorted_posts):
            tag_relevances = post["tagRelevance"]
            for tag, relevance in tag_relevances.items():
                if tag in left_tags:
                    post_sides[i] -= relevance
                elif tag in right_tags:
                    post_sides[i] += relevance
        return post_sides

    def get_most_separating_tags(self, desired_separation, candidate_tags):
        """
        returns a list of tags sorted from the most typical on left branch, to the most typical to the right branch
        relevance is taken into account
        """
        tag_usefulness = dict()
        mask = np.sign(desired_separation)
        for tag in candidate_tags:
            tag_usefulness[tag] = np.sum(mask * self.tag_occurences_in_posts[tag])

        tag_usefulness_sorted = sorted(tag_usefulness.items(), key=lambda x: x[1])
        return tag_usefulness_sorted

    def refresh(self):
        self.post_sides = self.separate_posts_using_given_tags(
            self.climber.left, self.climber.right
        )
        self.left_posts = (self.post_sides < 0) * self.current_post_ids
        self.right_posts = (self.post_sides >= 0) * self.current_post_ids
        candidate_tags = self.climber.left | self.climber.right
        tag_usefulness_sorted = self.get_most_separating_tags(self.post_sides, candidate_tags)
        self.tags_spectrum = tag_usefulness_sorted

    def get_best_left_tags(self, n=12):
        for tag_id, side_score in self.tags_spectrum[:n]:
            yield self.data.tags[tag_id], side_score

    def get_best_right_tags(self, n=12):
        for tag_id, side_score in reversed(self.tags_spectrum[-n:]):
            yield self.data.tags[tag_id], side_score

    def get_best_left_posts(self, n=18, ranking_func=(lambda post: post["score"])):
        left_post_indexes = np.nonzero(self.left_posts)[0]
        left_posts = []
        for i in left_post_indexes:
            left_posts.append(self.sorted_posts[i])

        sorted_left_posts = sorted(left_posts, key=ranking_func, reverse=True)
        return sorted_left_posts[:n]

    def get_best_right_posts(self, n=18, ranking_func=(lambda post: post["score"])):
        right_post_idexes = np.nonzero(self.right_posts)[0]
        right_posts = []
        for i in right_post_idexes:
            right_posts.append(self.sorted_posts[i])

        sorted_right_posts = sorted(right_posts, key=ranking_func, reverse=True)
        return sorted_right_posts[:n]

    def choose_left(self):
        self.climber.choose_left()
        # TODO shouldn't post_ids_history be a part of climber?
        self.current_post_ids_history.append(self.current_post_ids)
        self.current_post_ids = self.left_posts
        self.refresh()

    def choose_right(self):
        self.climber.choose_right()
        self.current_post_ids_history.append(self.current_post_ids)
        self.current_post_ids = self.right_posts
        self.refresh()

    def go_back(self):
        self.climber.go_back()
        if len(self.current_post_ids_history) == 0:
            logger.info("Post history is empty, doing nothing")
            return
        self.current_post_ids = self.current_post_ids_history.pop()
        self.refresh()
