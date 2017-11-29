# -*- coding: utf-8 -*-

# Copyright 2014-2017 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract images from https://gelbooru.com/"""

from .common import SharedConfigExtractor, Message
from .. import text, util


class GelbooruExtractor(SharedConfigExtractor):
    """Base class for gelbooru extractors"""
    basecategory = "booru"
    category = "gelbooru"
    filename_fmt = "{category}_{id}_{md5}.{extension}"

    def items(self):
        yield Message.Version, 1
        yield Message.Directory, self.get_metadata()

        for post_id in self.posts():
            data = self.get_post_data(post_id)
            url = data["file_url"]
            yield Message.Url, url, text.nameext_from_url(url, data)

    def posts(self):
        """Return an iterable containing all relevant post ids"""

    def get_metadata(self):
        """Return general metadata"""
        return {}

    def get_post_data(self, post_id):
        """Extract metadata of a single post"""
        page = self.request("https://gelbooru.com/index.php?page=post&s=view"
                            "&id=" + post_id).text
        data = text.extract_all(page, (
            (None        , '<meta name="keywords"', ''),
            ("tags"      , ' imageboard, ', '"'),
            ("id"        , '<li>Id: ', '<'),
            ("created_at", '<li>Posted: ', '<'),
            ("width"     , '<li>Size: ', 'x'),
            ("height"    , '', '<'),
            ("source"    , '<li>Source: <a href="', '"'),
            ("rating"    , '<li>Rating: ', '<'),
            (None        , '<li>Score: ', ''),
            ("score"     , '>', '<'),
            ("file_url"  , '<li><a href="http', '"'),
        ))[0]
        data["file_url"] = "http" + data["file_url"]
        data["md5"] = data["file_url"].rpartition("/")[2].partition(".")[0]
        for key in ("id", "width", "height", "score"):
            data[key] = util.safe_int(data[key])
        return data


class GelbooruTagExtractor(GelbooruExtractor):
    """Extractor for images from gelbooru.com based on search-tags"""
    subcategory = "tag"
    directory_fmt = ["{category}", "{tags}"]
    pattern = [r"(?:https?://)?(?:www\.)?gelbooru\.com/(?:index\.php)?"
               r"\?page=post&s=list&tags=([^&]+)"]
    test = [("https://gelbooru.com/index.php?page=post&s=list&tags=bonocho", {
        "count": 5,
    })]

    def __init__(self, match):
        GelbooruExtractor.__init__(self)
        self.tags = text.unquote(match.group(1).replace("+", " "))

    def get_metadata(self):
        return {"tags": self.tags}

    def posts(self):
        url = "https://gelbooru.com/index.php?page=post&s=list"
        params = {"tags": self.tags, "pid": 0}

        while True:
            page = self.request(url, params=params).text
            ids = list(text.extract_iter(page, '<a id="p', '"'))
            yield from ids
            if len(ids) < 42:
                return
            params["pid"] += 42


class GelbooruPoolExtractor(GelbooruExtractor):
    """Extractor for image-pools from gelbooru.com"""
    subcategory = "pool"
    directory_fmt = ["{category}", "pool", "{pool}"]
    pattern = [r"(?:https?://)?(?:www\.)?gelbooru\.com/(?:index\.php)?"
               r"\?page=pool&s=show&id=(\d+)"]
    test = [("https://gelbooru.com/index.php?page=pool&s=show&id=761", {
        "count": 6,
    })]

    def __init__(self, match):
        GelbooruExtractor.__init__(self)
        self.pool_id = match.group(1)

    def get_metadata(self):
        return {"pool": self.pool_id}

    def posts(self):
        page = self.request("https://gelbooru.com/index.php?page=pool&s=show"
                            "&id=" + self.pool_id).text
        return text.extract_iter(page, 'id="p', '"')


class GelbooruPostExtractor(GelbooruExtractor):
    """Extractor for single images from gelbooru.com"""
    subcategory = "post"
    pattern = [r"(?:https?://)?(?:www\.)?gelbooru\.com/(?:index\.php)?"
               r"\?page=post&s=view&id=(\d+)"]
    test = [("https://gelbooru.com/index.php?page=post&s=view&id=313638", {
        "content": "5e255713cbf0a8e0801dc423563c34d896bb9229",
        "count": 1,
    })]

    def __init__(self, match):
        GelbooruExtractor.__init__(self)
        self.post_id = match.group(1)

    def posts(self):
        return (self.post_id,)
