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
        self.posts_alphabetical = sorted(data.posts.values(), key=lambda post: post["_id"])
        self.tags_alphabetical = sorted(data.tags.values(), key=lambda tag: tag["_id"])

        self.current_post_ids = np.ones(len(self.posts_alphabetical))
        self.state_history = []
        self.climber = climber

        # create a matrix of tag relevances for each tag and post pair
        self.relevances = np.zeros((len(self.tags_alphabetical), len(self.posts_alphabetical)))
        self.tag_indexes = dict()
        for i, tag in enumerate(self.tags_alphabetical):
            self.tag_indexes[tag["_id"]] = i
        for j, post in enumerate(self.posts_alphabetical):
            tag_relevances = post["tagRelevance"]
            for tag, relevance in tag_relevances.items():
                if tag in self.tag_indexes:
                    i = self.tag_indexes[tag]
                    self.relevances[i][j] = relevance
                else:
                    logger.debug(f"Tag {tag} listed by post {post['_id']} is not in the tags list")

        self.refresh()

    def separate_posts_using_given_tags(self, left_tags, right_tags):
        """
        posts, should be a sorted list of all posts
        returns a numpy array of side attribution of each post
        """
        post_sides = np.zeros(len(self.posts_alphabetical))  # negative is left, positive is right
        for tag in left_tags:
            post_sides -= self.relevances[self.tag_indexes[tag]]
        for tag in right_tags:
            post_sides += self.relevances[self.tag_indexes[tag]]

        return post_sides

    def get_most_separating_tags(self, desired_separation, candidate_tags):
        """
        returns a list of tags sorted from the most typical on left branch, to the most typical to the right branch
        relevance is taken into account
        """
        tag_usefulness = dict()
        mask = np.sign(desired_separation)
        for tag in candidate_tags:
            tag_usefulness[tag] = mask @ self.relevances[self.tag_indexes[tag]]

        tag_usefulness_sorted = sorted(tag_usefulness.items(), key=lambda x: x[1])
        return tag_usefulness_sorted

    def refresh(self):
        post_sides = self.separate_posts_using_given_tags(self.climber.left, self.climber.right)
        self.left_posts = (post_sides < 0) * self.current_post_ids
        self.right_posts = (post_sides >= 0) * self.current_post_ids
        candidate_tags = self.climber.left | self.climber.right
        self.tags_spectrum = self.get_most_separating_tags(post_sides, candidate_tags)

    def get_best_left_tags(self, n=9):
        for tag_id, side_score in self.tags_spectrum[:n]:
            yield self.data.tags[tag_id], side_score

    def get_best_right_tags(self, n=9):
        for tag_id, side_score in reversed(self.tags_spectrum[-n:]):
            yield self.data.tags[tag_id], side_score

    def get_best_left_posts(self, n=14, ranking_func_symbol="hr"):
        left_post_indexes = np.nonzero(self.left_posts)[0]
        left_posts = [self.posts_alphabetical[i] for i in left_post_indexes]
        sorted_left_posts = sorted(
            left_posts, key=lambda post: post[ranking_func_symbol], reverse=True
        )
        return sorted_left_posts[:n]

    def get_best_right_posts(self, n=14, ranking_func_symbol="hr"):
        right_post_idexes = np.nonzero(self.right_posts)[0]
        right_posts = [self.posts_alphabetical[i] for i in right_post_idexes]
        sorted_right_posts = sorted(
            right_posts, key=lambda post: post[ranking_func_symbol], reverse=True
        )
        return sorted_right_posts[:n]

    def choose_left(self):
        self.climber.choose_left()
        # TODO shouldn't post_ids_history be a part of climber?
        self.state_history.append(self._get_state())
        self.current_post_ids = self.left_posts
        self.refresh()

    def choose_right(self):
        self.climber.choose_right()
        self.state_history.append(self._get_state())
        self.current_post_ids = self.right_posts
        self.refresh()

    def go_back(self):
        self.climber.go_back()
        if len(self.state_history) == 0:
            logger.info("Post history is empty, doing nothing")
            return
        self._set_state(self.state_history.pop())

    def _get_state(self):
        return (self.current_post_ids, self.tags_spectrum, self.left_posts, self.right_posts)

    def _set_state(self, state):
        self.current_post_ids, self.tags_spectrum, self.left_posts, self.right_posts = state
