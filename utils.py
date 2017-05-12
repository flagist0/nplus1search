import logging
from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import Model

logger = logging.getLogger('peewee')
logger.setLevel(logging.INFO)

db = SqliteExtDatabase('nplus1.sqlite')


class BaseModel(Model):
    class Meta:
        database = db
