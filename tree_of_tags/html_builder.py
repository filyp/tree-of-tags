import datetime
from pathlib import Path


seconds_in_minute = 60
seconds_in_hour = 60 * seconds_in_minute
seconds_in_day = 24 * seconds_in_hour
seconds_in_month = 30 * seconds_in_day
seconds_in_year = 365 * seconds_in_day

full_time_indicator = 30  # how many minutes will fill the whole reading time indicator

colors = {
    "ea": "#0c869b",
    "lw": "#5f9b65",
    "af": "#3f51b5",
}

forum_urls = {
    "ea": "https://forum.effectivealtruism.org",
    "lw": "https://www.lesswrong.com",
    "af": "https://www.alignmentforum.org",
}
forum_tag_urls = {
    "ea": "https://forum.effectivealtruism.org/topic",
    "lw": "https://www.lesswrong.com/tag",
    "af": "https://www.alignmentforum.org/tag",
}


def timestamp_to_time_ago_str(post):
    timestamp = post["postedAt"]

    # convert timestamp of the form "%Y-%m-%dT%H:%M:%S.%fZ" string to a unix timestamp
    timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    # get current UTC time
    now = datetime.datetime.utcnow()
    seconds_passed = int((now - timestamp).total_seconds())

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

    def build_post_html(self, post, forum):
        post_html = self.post_template
        post_html = post_html.replace("__POST_URL__", f"{forum_urls[forum]}/posts/{post['_id']}")
        post_html = post_html.replace("__POST_TITLE__", post["title"])
        if post["user"] is not None:
            user_url = post["user"]["pageUrl"]
            user_name = post["user"]["displayName"]
        else:
            user_url = ""
            user_name = ""
        post_html = post_html.replace("__USER_URL__", user_url)
        post_html = post_html.replace("__USER_NAME__", user_name)
        post_html = post_html.replace("__SCORE__", str(post["baseScore"]))
        comment_count = str(post["commentCount"]) if post["commentCount"] is not None else "0"
        post_html = post_html.replace("__COMMENT_COUNT__", comment_count)
        post_html = post_html.replace("__TIME_AGO__", timestamp_to_time_ago_str(post))

        # inject reading time
        if post["wordCount"] is not None:
            reading_time = int(post["wordCount"] / 250) + 1
        else:
            reading_time = 0
        reading_time_indicator_height = min(int(reading_time / full_time_indicator * 100), 100)
        post_html = post_html.replace("__HEIGHT__", str(reading_time_indicator_height))
        post_html = post_html.replace(
            "__HEIGHT_INVERSE__", str(100 - reading_time_indicator_height)
        )

        return post_html

    def build_page(self, filename, forum, tags_left, tags_right, posts_left, posts_right):
        # build content
        tags_left_html = ""
        num_of_left_tags = 0
        for tag, side_score in tags_left:
            if side_score > 0:
                # skip tags which belong to the right side
                continue
            tag_url = f"{forum_tag_urls[forum]}/{tag['slug']}"
            tags_left_html += self.build_tag_html(tag_url, tag["name"])
            num_of_left_tags += 1

        tags_right_html = ""
        num_of_right_tags = 0
        for tag, side_score in tags_right:
            if side_score <= 0:
                # skip tags which belong to the left side
                continue
            tag_url = f"{forum_tag_urls[forum]}/{tag['slug']}"
            tags_right_html += self.build_tag_html(tag_url, tag["name"])
            num_of_right_tags += 1

        posts_left_html = ""
        for post in posts_left:
            posts_left_html += self.build_post_html(post, forum)

        posts_right_html = ""
        for post in posts_right:
            posts_right_html += self.build_post_html(post, forum)

        # build the whole page
        page_html = self.main_template
        page_html = page_html.replace("__TAGS1__", tags_left_html)
        page_html = page_html.replace("__TAGS2__", tags_right_html)
        page_html = page_html.replace("__POSTS1__", posts_left_html)
        page_html = page_html.replace("__POSTS2__", posts_right_html)
        page_html = page_html.replace("__MAIN_COLOR__", colors[forum])

        # set links to branches
        filename_base = filename.split(".")[0]
        if num_of_left_tags > 1:
            page_html = page_html.replace("__BUTTON1_URL__", filename_base + "0.html")
            page_html = page_html.replace("__BUTTON1_TEXT__", "Choose this branch")
        else:
            page_html = page_html.replace('href="__BUTTON1_URL__"', "")
            page_html = page_html.replace("__BUTTON1_TEXT__", "You can't go any further")
        if num_of_right_tags > 1:
            page_html = page_html.replace("__BUTTON2_URL__", filename_base + "1.html")
            page_html = page_html.replace("__BUTTON2_TEXT__", "Choose this branch")
        else:
            page_html = page_html.replace('href="__BUTTON2_URL__"', "")
            page_html = page_html.replace("__BUTTON2_TEXT__", "You can't go any further")
        if len(filename_base) == 3:
            # we are at the top already
            page_html = page_html.replace('href="__BUTTON_BACK_URL__"', "")
        else:
            page_html = page_html.replace("__BUTTON_BACK_URL__", filename_base[:-1] + ".html")

        # build UI contols
        # fmt: off
        tree_version = filename[0]
        ranking_method = filename[1]
        karma_manipulation = filename[2]
        branch_id = filename[3:]
        page_html = page_html.replace("__MERITOCRATIC_URL__", tree_version + ranking_method + "m" + branch_id)
        page_html = page_html.replace("__REGULAR_URL__",      tree_version + ranking_method + "r" + branch_id)
        page_html = page_html.replace("__DEMOCRATIC_URL__",   tree_version + ranking_method + "d" + branch_id)
        page_html = page_html.replace("__HOT_URL__",          tree_version + "h" + karma_manipulation + branch_id)
        page_html = page_html.replace("__TOP_URL__",          tree_version + "t" + karma_manipulation + branch_id)
        page_html = page_html.replace("__ALIVE_URL__",        tree_version + "a" + karma_manipulation + branch_id)
        if karma_manipulation == "m":
            page_html = page_html.replace('"control-button">m', '"control-button-selected">m')
        elif karma_manipulation == "r":
            page_html = page_html.replace('"control-button">r', '"control-button-selected">r')
        elif karma_manipulation == "d":
            page_html = page_html.replace('"control-button">d', '"control-button-selected">d')
        if ranking_method == "h":
            page_html = page_html.replace('"control-button">h', '"control-button-selected">h')
        elif ranking_method == "t":
            page_html = page_html.replace('"control-button">t', '"control-button-selected">t')
        elif ranking_method == "a":
            page_html = page_html.replace('"control-button">a', '"control-button-selected">a')
        # fmt: on

        # save html file
        pages_folder = Path(__file__).parent.parent / "_site"
        page_name = pages_folder / forum / filename
        with open(page_name, "w") as f:
            f.write(page_html)
