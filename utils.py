import logging
from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import Model
from tokenizer import register_tokenizer

logger = logging.getLogger('peewee')
logger.setLevel(logging.INFO)

db = SqliteExtDatabase('nplus1.sqlite')
db.connect()
conn = db._local.conn  # Yepp, we had to do it
register_tokenizer(conn)


class BaseModel(Model):
    class Meta:
        database = db
