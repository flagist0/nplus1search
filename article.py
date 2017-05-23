from pprint import pformat

import scrapy
from peewee import CharField, DateField, TextField, IntegerField, fn
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import JSONField, SearchField, FTSModel

from utils import BaseModel, db


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

    def save(self, force_insert=False, only=None):
        super(Article, self).save(force_insert, only)
#        ArticleIndex.index_article(self)


class ArticleIndex(FTSModel):
    title = SearchField()
    content = SearchField()

    class Meta:
        database = db
        # Use our custom tokenizer
        extension_options = {'tokenize': 'snowball_russian'}

    @staticmethod
    def index_article(article):
        ArticleIndex.insert({
            ArticleIndex.docid: article.id,
            ArticleIndex.title: article.title,
            ArticleIndex.content: article.text}).execute()

    @staticmethod
    def search_by_text(phrase):
        # Query the search_by_text index and join the corresponding Document
        # object on each search_by_text result.
        # Adds "snippets" field containing matches
        return (Article
                .select(Article,
                        fn.snippet(ArticleIndex.as_entity(), '*', '*', '...').alias('snippets'))
                .join(
                      ArticleIndex,
                      on=(Article.id == ArticleIndex.docid))
                .where(ArticleIndex.match(phrase))
                .order_by(ArticleIndex.bm25()))
