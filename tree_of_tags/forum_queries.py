import json
import requests
import datetime

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


posts_query = """
{
  posts(input: {terms: {limit: %d, offset: %d}}) {
    results {
      _id
      title
      postedAt
      user {
        username
        displayName
        pageUrl
      }
      allVotes {
        voteType
      }
			tagRelevance
      wordCount
      voteCount
      baseScore
      score
      commentCount
    }
  }  
}

"""

tags_query = """
{
  tags(input: {terms: {limit: %d, offset: %d}}) {
    results {
      createdAt
      name
      slug
      core
      suggestedAsFilter
      postCount
      userId
      adminOnly
      deleted
      needsReview
      reviewedByUserId
      wikiGrade
      wikiOnly
      contributionStats
      introSequenceId
      _id
    }
  }
}
"""

comments_query_full = """
{
  comments(input: {terms: {limit: %d, offset: %d}}){
    results {
      allVotes {
        voteType
        _id
      }
  	  parentCommentId
  	  postedAt
  	  author
  	  postId
  	  tagId
  	  userId
  	  pageUrlRelative
  	  answer
  	  parentAnswerId
  	  directChildrenCount
  	  lastSubthreadActivity
  	  wordCount
  	  _id
  	  voteCount
  	  baseScore
  	  score
  	}
  }
}
"""

comments_query = """
{
  comments(input: {terms: {limit: %d, offset: %d}}){
    results {
  	  postedAt
  	  postId
  	}
  }
}
"""

forum_apis = {
    "ea": "https://forum.effectivealtruism.org/graphql",
    "lw": "https://www.lesswrong.com/graphql",
    "af": "https://www.alignmentforum.org/graphql",
}


def _timestamp_to_age_in_seconds(timestamp):
    # convert timestamp of the form "%Y-%m-%dT%H:%M:%S.%fZ" string to a unix timestamp
    timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    # get current UTC time
    now = datetime.datetime.utcnow()
    return int((now - timestamp).total_seconds())


def run_query(query, args, forum):
    url = forum_apis[forum]
    headers = {"User-Agent": "Tree of Tags"}
    full_query = query % args
    r = requests.post(url, json={"query": full_query}, headers=headers)
    # check for errors
    if r.status_code != 200:
        raise Exception(
            f"Query failed to run by returning code of {r.status_code}.\nurl: {url}\nheaders: {headers}\nquery: {full_query}"
        )
    data = json.loads(r.text)
    return data["data"]


def get_all_posts(forum="ea", chunk_size=4000):
    all_posts = dict()
    offset = 0
    skipped_posts_no_tags = 0
    while True:
        current_posts = run_query(posts_query, (chunk_size, offset), forum)
        current_posts = current_posts["posts"]["results"]
        offset += chunk_size

        if len(current_posts) == 0:
            break

        for post in current_posts:
            # skip posts with no tags
            if post["tagRelevance"] is None:
                skipped_posts_no_tags += 1
                continue
            all_posts[post["_id"]] = post

    # * calculate how many seconds passed since the post was created
    for post in all_posts.values():
        post["age_in_seconds"] = _timestamp_to_age_in_seconds(post["postedAt"])

    logger.info(f"Skipped {skipped_posts_no_tags} posts with no tags")
    assert len(all_posts) > 2000

    return all_posts


def get_all_tags(forum="ea", chunk_size=1000):
    all_tags = dict()
    offset = 0
    while True:
        current_tags = run_query(tags_query, (chunk_size, offset), forum)
        current_tags = current_tags["tags"]["results"]
        offset += chunk_size

        if len(current_tags) == 0:
            break

        for tag in current_tags:
            all_tags[tag["_id"]] = tag

    assert len(all_tags) > 700
    return all_tags


def get_all_comments(forum="ea", chunk_size=1000, younger_than=None):
    """
    Watch out, getting all comments takes ~3 minutes for EA Forum, for LW probably longer
    """
    all_comments = dict()
    offset = 0
    while True:
        current_comments = run_query(comments_query, (chunk_size, offset), forum)
        current_comments = current_comments["comments"]["results"]
        offset += chunk_size

        if len(current_comments) == 0:
            return all_comments

        for comment in current_comments:
            postId = comment["postId"]
            comment["age_in_seconds"] = _timestamp_to_age_in_seconds(comment["postedAt"])

            if postId not in all_comments:
                all_comments[postId] = []
            all_comments[postId].append(comment)

            if younger_than is not None and comment["age_in_seconds"] > younger_than:
                return all_comments
