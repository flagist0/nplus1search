from pprint import pformat

import scrapy
from peewee import CharField, DateField, TextField, IntegerField
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import JSONField

from utils import BaseModel


class Article(BaseModel):
    url = CharField(unique=True)
    title = CharField()
    description = CharField()
    date = DateField()
    text = TextField()
    rubrics = JSONField()
    themes = JSONField()
    difficulty = IntegerField()
    internal_links = JSONField()
    external_links = JSONField()
    author = CharField()

    @classmethod
    def by_url(cls, url):
        return cls.get_or_create(defaults={'url': url},
                                 url=url)[0]

    @staticmethod
    def is_parsed(url):
        try:
            art = Article.get(Article.url == url)
        except Article.DoesNotExist:
            return False
        else:
            return art.title is not None

    @staticmethod
    def iter_unparsed_urls():
        for art in Article.select().where(Article.url != None, Article.title == None).select():
            yield art.url


    @staticmethod
    def parsed_num():
        return Article.select().where(Article.title != None).count()

    @staticmethod
    def unparsed_num():
        return Article.select().where(Article.title == None).count()

    class ScrapyItem(scrapy.Item):
        data = scrapy.Field()

        def __repr__(self):
            req_fields = ['url', 'title', 'description', 'author', 'internal_links']
            return pformat({f: self['data'][f] for f in req_fields})

    def to_scrapy_item(self):
        return self.ScrapyItem(data=model_to_dict(self))