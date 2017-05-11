import logging
from peewee import SqliteDatabase, Model

logger = logging.getLogger('peewee')
logger.setLevel(logging.INFO)

db = SqliteDatabase('nplus1.sqlite')


class BaseModel(Model):
    class Meta:
        database = db
