from asyncio.log import logger
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
    "ea": "https://forum.effectivealtruism.org/topics",
    "lw": "https://www.lesswrong.com/tag",
    "af": "https://www.alignmentforum.org/tag",
}


def timestamp_to_time_ago_str(post):
    seconds_passed = post.age_in_seconds
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

        # load similar tags html template
        similar_tags_template_filename = template_folder / "similar_tags_template.html"
        with open(similar_tags_template_filename, "r") as f:
            self.similar_tags_template = f.read()

    def build_tag_html(self, tag_url, tag_name, white=False):
        tag_html = self.tag_template
        tag_html = tag_html.replace("__TAG_URL__", tag_url)
        tag_html = tag_html.replace("__TAG_NAME__", tag_name)
        if white:
            tag_html = tag_html.replace(
                'class="FilterMode-tag"', 'class="FooterTag-root FooterTag-core"'
            )
        return tag_html

    def build_post_html(self, post, forum, cracy):
        post_html = self.post_template
        post_html = post_html.replace("__POST_URL__", f"{forum_urls[forum]}/posts/{post['_id']}")
        post_html = post_html.replace("__POST_TITLE__", post["title"])
        if post["user"] is not None:
            user_url = post["user"]["pageUrl"]
            user_name = post["user"]["displayName"]
            if user_name is None:
                user_name = post["user"]["username"]
        else:
            user_url = ""
            user_name = ""
        post_html = post_html.replace("__USER_URL__", user_url)
        post_html = post_html.replace("__USER_NAME__", user_name)
        score = str(post["t" + cracy])  # display the score accorting to chosen cracy
        if score == "-inf":
            score = "-"
        post_html = post_html.replace("__SCORE__", score)
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
        post_html = post_html.replace("__FORUM__", forum)

        return post_html

    def build_page(
        self,
        filename,
        forum,
        tags_left,
        tags_right,
        posts_left,
        posts_right,
        num_of_left,
        num_of_right,
    ):
        tree_version = filename[0]
        ranking_method = filename[1]
        cracy = filename[2]
        branch_id = filename[3:]

        # build content

        # build the left tags
        tags_left_html = self.build_tag_html("", f"{num_of_left} posts", white=True)
        num_of_left_tags = 0
        for tag, side_score in tags_left:
            if side_score > 0 or tag["name"] == "_deleted_":
                # skip tags which belong to the right side or were deleted
                continue
            tag_url = f"{forum_tag_urls[forum]}/{tag['slug']}"
            tags_left_html += self.build_tag_html(tag_url, tag["name"])
            num_of_left_tags += 1

        # build the right tags
        tags_right_html = self.build_tag_html("", f"{num_of_right} posts", white=True)
        num_of_right_tags = 0
        for tag, side_score in tags_right:
            if side_score <= 0 or tag["name"] == "_deleted_":
                # skip tags which belong to the left side or were deleted
                continue
            tag_url = f"{forum_tag_urls[forum]}/{tag['slug']}"
            tags_right_html += self.build_tag_html(tag_url, tag["name"])
            num_of_right_tags += 1

        posts_left_html = ""
        for post in posts_left:
            posts_left_html += self.build_post_html(post, forum, cracy)

        posts_right_html = ""
        for post in posts_right:
            posts_right_html += self.build_post_html(post, forum, cracy)

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
        page_html = page_html.replace("__MERITOCRATIC_URL__", tree_version + ranking_method + "m" + branch_id)
        page_html = page_html.replace("__REGULAR_URL__",      tree_version + ranking_method + "r" + branch_id)
        page_html = page_html.replace("__DEMOCRATIC_URL__",   tree_version + ranking_method + "d" + branch_id)
        page_html = page_html.replace("__HOT_URL__",          tree_version + "h" + cracy + branch_id)
        page_html = page_html.replace("__TOP_URL__",          tree_version + "t" + cracy + branch_id)
        page_html = page_html.replace("__ALIVE_URL__",        tree_version + "a" + cracy + branch_id)
        if cracy == "m":
            page_html = page_html.replace('"control-button">m', '"control-button-selected">m')
        elif cracy == "r":
            page_html = page_html.replace('"control-button">r', '"control-button-selected">r')
        elif cracy == "d":
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

    def build_similar_tags(self, data, num_of_tags=30):
        forum = data.forum
        for tag in data.Tag_cooccurence.nodes:
            # find the most similar tags
            neighbors = list(data.Tag_cooccurence.neighbors(tag))
            similar_tags = sorted(
                neighbors, key=lambda x: data.Tag_cooccurence[tag][x]["weight"], reverse=True
            )

            links_html = ""
            tags_html = ""
            for tag_id in similar_tags[1 : num_of_tags + 1]:
                tag2 = data.tags[tag_id]
                tag_url = f"{forum_tag_urls[forum]}/{tag2['slug']}"
                tag_html = self.build_tag_html(tag_url, tag2["name"])

                link_html = self.build_tag_html(tag2["slug"] + ".html", "Show similar", white=True)
                links_html += f"<div class='tagbox'>{link_html}</div>"
                tags_html += f"<div class='tagbox'>{tag_html}</div>"

            page_html = self.similar_tags_template
            page_html = page_html.replace("__LINKS__", links_html)
            page_html = page_html.replace("__TAGS__", tags_html)
            title = f'Tags similar to: {data.tags[tag]["name"]}'
            page_html = page_html.replace("__TITLE__", title)

            # save html file
            pages_folder = Path(__file__).parent.parent / "_site"
            filename = data.tags[tag]["slug"] + ".html"
            page_name = pages_folder / forum / filename
            with open(page_name, "w") as f:
                f.write(page_html)

    def build_most_popular_tags(self, data, num_of_tags=30):
        forum = data.forum
        # get most popular tags
        tag_ids = [tag for tag in data.Tag_cooccurence.nodes]
        most_popular_tags = sorted(
            tag_ids, key=lambda tag: data.Tag_cooccurence[tag][tag]["weight"], reverse=True
        )

        links_html = ""
        tags_html = ""
        for tag_id in most_popular_tags[:num_of_tags]:
            tag = data.tags[tag_id]
            tag_url = f"{forum_tag_urls[forum]}/{tag['slug']}"
            tag_html = self.build_tag_html(tag_url, tag["name"])

            link_html = self.build_tag_html(tag["slug"] + ".html", "Show similar", white=True)
            links_html += f"<div class='tagbox'>{link_html}</div>"
            tags_html += f"<div class='tagbox'>{tag_html}</div>"

        page_html = self.similar_tags_template
        page_html = page_html.replace("__TAGS__", tags_html)
        page_html = page_html.replace("__LINKS__", links_html)
        page_html = page_html.replace("__TITLE__", "Most popular tags")

        # save html file
        pages_folder = Path(__file__).parent.parent / "_site"
        page_name = pages_folder / forum / "most_popular_tags.html"
        with open(page_name, "w") as f:
            f.write(page_html)
