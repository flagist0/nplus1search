# -*- coding: utf-8 -*-
from scrapy import Item, Field
from pprint import pformat


class Nplus1Item(Item):
    url = Field()
    title = Field()
    description = Field()
    date = Field()
    text = Field()
    rubrics = Field()
    themes = Field()
    difficulty = Field()
    internal_links = Field()
    external_links = Field()
    author = Field()

    def __repr__(self):
        req_fields = ['url', 'title', 'description', 'author', 'internal_links']
        return pformat({f: self[f] for f in req_fields})
