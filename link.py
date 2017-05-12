from peewee import CharField, BooleanField
from utils import BaseModel


class Link(BaseModel):
    url = CharField(unique=True)
    parsed = BooleanField(default=False)

    @staticmethod
    def by_url(url):
        return Link.get_or_create(defaults={'url': url},
                                  url=url)[0]

    @staticmethod
    def unparsed_num():
        return Link.select().where(Link.url != None, Link.parsed == False).count()

    @staticmethod
    def iter_unparsed_urls():
        for link in Link.select().where(Link.url != None, Link.parsed == False):
            yield link.url

    @staticmethod
    def is_parsed(url):
        try:
            link = Link.get(Link.url == url)
        except Link.DoesNotExist:
            return False
        else:
            return link.parsed

    def set_parsed(self):
        self.parsed = True
        self.save()
