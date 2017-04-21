# -*- coding: utf-8 -*-
from scrapy import Item, Field


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

