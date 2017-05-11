from peewee import *
from playhouse.sqlite_ext import JSONField

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


class Link(BaseModel):
    url = CharField(unique=True)
    parsed = BooleanField(default=False)
