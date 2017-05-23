import logging
from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import Model
from tokenizer import register_tokenizer

logging.getLogger('peewee').setLevel(logging.INFO)
logger = logging.getLogger('utils')
logger.setLevel(logging.DEBUG)


class SqliteDatabaseCustom(SqliteExtDatabase):
    def initialize_connection(self, conn):
        register_tokenizer(conn)
        logger.debug('Initialized tokenizer with conn {}'.format(conn))


db = SqliteDatabaseCustom('nplus1.sqlite')
db.connect()


class BaseModel(Model):
    class Meta:
        database = db
