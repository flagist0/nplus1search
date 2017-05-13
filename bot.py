# encoding: utf-8
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from article import Article, ArticleIndex


class SearchBot(object):
    def __init__(self):
        logging.basicConfig()
        self.log = logging.getLogger('bot')
        self.log.setLevel(logging.DEBUG)
        token = self.get_token()
        self.updater = Updater(token=token)

        self.updater.dispatcher.add_handler(CommandHandler('start', SearchBot.show_database_info))
        self.updater.dispatcher.add_handler(CommandHandler('info', SearchBot.show_database_info))
        self.updater.dispatcher.add_handler(CommandHandler('author', SearchBot.search_by_author, pass_args=True))
        self.updater.start_polling()

    @staticmethod
    def show_database_info(bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text=u'В базе {} статей'.format(Article.parsed_num()))


    @staticmethod
    def search_by_author(bot, update, args):
        author = ' '.join(args)

        articles = Article.select().where(Article.author == author).order_by(Article.date.desc())
        if articles.count():
            lines = [u'Найдено {} статей:'.format(articles.count())]
            lines += [u'[{}]({}) {}'.format(article.title, article.url, article.date) for article in articles]
            output = '\n\n'.join(lines)
        else:
            output = u'Статей автора "{}" не найдено'.format(author)

        bot.send_message(chat_id=update.message.chat_id,
                         text=output,
                         parse_mode=ParseMode.MARKDOWN)

    @staticmethod
    def get_token():
        with open('token.txt') as fh:
            return fh.readline().strip()

if __name__ == '__main__':
    b = SearchBot()


