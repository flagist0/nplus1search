from web2py_dal import DAL, Field


class DB(object):
    def __init__(self, article_url_re):
        self.article_url_re = article_url_re
        self.db = DAL('sqlite://nplus1.sqlite', pool_size=10, check_reserved=['sqlite', 'mysql'])

        self.db.define_table('articles',
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

        self.a = self.db.articles

    def article_is_already_parsed(self, url):
        return self.db((self.a.url == url) & (self.a.title != None)).count() == 1

    def create_article_stub(self, url):
        if self.db(self.a.url == url).count() == 0:
            self.a.insert(url=url)
            self.db.commit()

    def iter_unparsed_articles_urls(self):
        # Article urls go first
        for row in self.db((self.a.url != None) & self.a.url.regexp(self.article_url_re) &
                                   (self.a.title == None)).select():
            yield row.url

        # All the other urls go next (web2py dal regexp negation doesn't work, but duplicates will be filtered)
        for row in self.db((self.a.url != None) & (self.a.title == None)).select():
            yield row.url

    def save_article(self, article):
        self.db(self.a.url == article['url']).update(**article)
        self.db.commit()

    def parsed_articles_num(self):
        return self.db(self.a.title != None).count()

    def article_stubs_num(self):
        return self.db((self.a.title == None) & (self.a.url.regexp(self.article_url_re))).count()

    def remove_url(self, url):
        self.db(self.a.url == url).delete()