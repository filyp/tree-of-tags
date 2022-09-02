import json
import requests

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
        _id
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

forum_apis = {
  "ea": "https://forum.effectivealtruism.org/graphql",
  "lw": "https://www.lesswrong.com/graphql",
  "af": "https://www.alignmentforum.org/graphql",
}


def run_query(query, args, forum):
    url = forum_apis[forum]
    headers = {"Content-Type": "application/json"}
    full_query = query % args
    r = requests.post(url, json={"query": full_query}, headers=headers)
    data = json.loads(r.text)
    return data["data"]


def get_all_posts(forum="ea", chunk_size=4000):
    all_posts = dict()
    offset = 0
    skipped_posts = 0
    while True:
        current_posts = run_query(posts_query, (chunk_size, offset), forum)
        current_posts = current_posts["posts"]["results"]
        offset += chunk_size

        if len(current_posts) == 0:
            break

        for post in current_posts:
            # skip posts with no tags
            if post["tagRelevance"] is None:
                skipped_posts += 1
                continue
            all_posts[post["_id"]] = post

    logger.info(f"Skipped {skipped_posts} posts with no tags")
    assert len(all_posts) > 9000

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

    assert len(all_tags) > 900
    return all_tags
