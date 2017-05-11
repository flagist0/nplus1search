from web2py_dal import DAL, Field


class PageType(object):
    article = 'article'
    digest = 'digest'
    other = 'other'


class DB(object):
    def __init__(self, article_url_re):
        self.article_url_re = article_url_re
        self.db = DAL('sqlite://nplus1.sqlite', pool_size=10, check_reserved=['sqlite', 'mysql'], fake_migrate=True)

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

    def article_is_parsed(self, url):
        return self.db((self.a.url == url) & (self.a.title != None)).count() == 1

    def digest_is_parsed(self, url):
        return self.db((self.l.url == url) & (self.l.parsed == True)).count()

    def mark_digest_as_parsed(self, url):
        self.db(self.l.url == url).update(parsed=True)
        self.db.commit()

    def iter_unparsed_articles_urls(self):
        # Article urls go first
        for row in self.db((self.a.url != None) & self.a.url.regexp(self.article_url_re) &
                                   (self.a.title == None)).select():
            yield row.url

        # All the other urls go next
        for row in self.db((self.l.url != None) & (self.l.parsed == False)).select():
            yield row.url

    def save_article(self, article):
        self.db(self.a.url == article['url']).update(**article)
        self.db.commit()

    def parsed_articles_num(self):
        return self.db(self.a.title != None).count()

    def article_stubs_num(self):
        return self.db((self.a.title == None) & (self.a.url.regexp(self.article_url_re))).count()

    def unparsed_links_num(self):
        return self.db((self.l.url != None) & (self.l.parsed == False)).count()

    def remove_article_url(self, url):
        self.db(self.a.url == url).delete()
