from peewee import CharField, BooleanField
from utils import BaseModel


class Link(BaseModel):
    url = CharField(unique=True)
    parsed = BooleanField(default=False)

    @staticmethod
    def iter_unparsed_urls():
        for link in Link.select().where(Link.url != None, Link.parsed == False):
            yield link.url