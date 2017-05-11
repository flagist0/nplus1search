import logging
from peewee import *
from playhouse.sqlite_ext import JSONField
from playhouse.shortcuts import model_to_dict
import scrapy
from pprint import pformat

logger = logging.getLogger('peewee')
logger.setLevel(logging.INFO)

db = SqliteDatabase('nplus1.sqlite')


class BaseModel(Model):
    class Meta:
        database = db


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

    class ScrapyItem(scrapy.Item):
        data = scrapy.Field()

        def __repr__(self):
            req_fields = ['url', 'title', 'description', 'author', 'internal_links']
            return pformat({f: self['data'][f] for f in req_fields})

    def to_scrapy_item(self):
        return self.ScrapyItem(data=model_to_dict(self))


class Link(BaseModel):
    url = CharField(unique=True)
    parsed = BooleanField(default=False)
