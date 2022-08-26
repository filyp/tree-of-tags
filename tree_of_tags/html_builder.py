import datetime
from pathlib import Path


seconds_in_minute = 60
seconds_in_hour = 60 * seconds_in_minute
seconds_in_day = 24 * seconds_in_hour
seconds_in_month = 30 * seconds_in_day
seconds_in_year = 365 * seconds_in_day


def timestamp_to_time_ago_str(post):
    timestamp = post["postedAt"]

    # convert timestamp of the form "%Y-%m-%dT%H:%M:%S.%fZ" string to a unix timestamp
    timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    # get current UTC time
    now = datetime.datetime.utcnow()
    seconds_passed = (now - timestamp).seconds

    years_passed = seconds_passed // seconds_in_year
    if years_passed > 0:
        return f"{years_passed}y"
    months_passed = seconds_passed // seconds_in_month
    if months_passed > 0:
        return f"{months_passed}mo"
    days_passed = seconds_passed // seconds_in_day
    if days_passed > 0:
        return f"{days_passed}d"
    hours_passed = seconds_passed // seconds_in_hour
    if hours_passed > 0:
        return f"{hours_passed}h"
    minutes_passed = seconds_passed // seconds_in_minute
    return f"{minutes_passed}m"


class HTMLBuilder:
    def __init__(self):
        template_folder = Path(__file__).parent.parent / "templates"

        # load site html template
        main_template_filename = template_folder / "main_template.html"
        with open(main_template_filename, "r") as f:
            self.main_template = f.read()

        # load post html template
        post_template_filename = template_folder / "post_template.html"
        with open(post_template_filename, "r") as f:
            self.post_template = f.read()

        # load tag html template
        tag_template_filename = template_folder / "tag_template.html"
        with open(tag_template_filename, "r") as f:
            self.tag_template = f.read()

    def build_tag_html(self, tag_url, tag_name):
        tag_html = self.tag_template
        tag_html = tag_html.replace("__TAG_URL__", tag_url)
        tag_html = tag_html.replace("__TAG_NAME__", tag_name)
        return tag_html

    def build_post_html(self, post):
        post_html = self.post_template
        post_html = post_html.replace(
            "__POST_URL__", f"https://forum.effectivealtruism.org/posts/{post['_id']}"
        )
        post_html = post_html.replace("__POST_TITLE__", post["title"])
        post_html = post_html.replace("__USER_URL__", post["user"]["pageUrl"])
        post_html = post_html.replace("__USER_NAME__", post["user"]["displayName"])
        post_html = post_html.replace("__SCORE__", str(post["baseScore"]))
        comment_count = str(post["commentCount"]) if post["commentCount"] is not None else "0"
        post_html = post_html.replace("__COMMENT_COUNT__", comment_count)
        post_html = post_html.replace("__TIME_AGO__", timestamp_to_time_ago_str(post))
        return post_html

    def build_page(self, filename, tags_left, tags_right, posts_left, posts_right):
        # build content
        tags_left_html = ""
        for tag, side_score in tags_left:
            tag_url = f"https://forum.effectivealtruism.org/topics/{tag['slug']}"
            tags_left_html += self.build_tag_html(tag_url, tag["name"])

        tags_right_html = ""
        for tag, side_score in tags_right:
            tag_url = f"https://forum.effectivealtruism.org/topics/{tag['slug']}"
            tags_right_html += self.build_tag_html(tag_url, tag["name"])

        posts_left_html = ""
        for post in posts_left:
            posts_left_html += self.build_post_html(post)

        posts_right_html = ""
        for post in posts_right:
            posts_right_html += self.build_post_html(post)

        # build the whole page
        page_html = self.main_template
        page_html = page_html.replace("__TAGS1__", tags_left_html)
        page_html = page_html.replace("__TAGS2__", tags_right_html)
        page_html = page_html.replace("__POSTS1__", posts_left_html)
        page_html = page_html.replace("__POSTS2__", posts_right_html)

        # save html file
        pages_folder = Path(__file__).parent.parent / "pages"
        page_name = pages_folder / filename
        with open(page_name, "w") as f:
            f.write(page_html)
