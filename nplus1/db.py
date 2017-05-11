from web2py_dal import DAL, Field

from article import Article
from link import Link


class PageType(object):
    article = 'article'
    digest = 'digest'
    other = 'other'


class DB(object):
    def __init__(self):
        self.db = DAL('sqlite://nplus1.sqlite', pool_size=10, check_reserved=['sqlite', 'mysql'])

        self.db.define_table('article',
                             Field('url', unique=True),
                             Field('title'),
                             Field('description'),
                             Field('date', 'date'),
                             Field('text', 'text'),
                             Field('rubrics', 'json'),
                             Field('themes', 'json'),
                             Field('difficulty', 'integer'),
                             Field('internal_links', 'json'),
                             Field('external_links', 'json'),
                             Field('author'))

        self.db.define_table('link',
                             Field('url', unique=True),
                             Field('parsed', 'boolean', default=False))

        self.a = self.db.article
        self.l = self.db.link

    def table_by_page_type(self, page_type):
        if page_type == PageType.article:
            return self.db.article
        else:
            return self.db.link

    def create_page_stub(self, url, page_type):
        table = self.table_by_page_type(page_type)
        if self.db(table.url == url).count() == 0:
            table.insert(url=url)
            self.db.commit()

    @staticmethod
    def remove_article_url(url):
        Article.get(Article.url == url).delete_instance()
