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

        self.updater.dispatcher.add_handler(CommandHandler('start', SearchBot.show_help))
        self.updater.dispatcher.add_handler(CommandHandler('info', SearchBot.show_database_info))
        self.updater.dispatcher.add_handler(CommandHandler('author', SearchBot.search_by_author, pass_args=True))
        self.updater.dispatcher.add_handler(CommandHandler('search', SearchBot.search_text, pass_args=True))

        self.updater.start_polling()

    @staticmethod
    def show_database_info(bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text=u'В базе {} статей'.format(Article.parsed_num()))

    @staticmethod
    def show_help(bot, update):
        message = u"""
        Привет!
        Я бот-поисковик по http://nplus1.ru
        Сейчас в моей базе {} статей
        Команды:
        /author <автор> -- поиск по имени автора
        /search <запрос> -- поиск по тексту статьи
        PS: пока ничего не работает
        """.format(Article.parsed_num())
        bot.send_message(chat_id=update.message.chat_id,
                         text=message)

    @staticmethod
    def search_by_author(bot, update, args):
        author = ' '.join(args)

        articles = Article.select().where(Article.author == author).order_by(Article.date.desc())
        if articles.count():
            lines = [u'Найдено {} статей:'.format(articles.count())]
            lines += [u'*{}* {} {}'.format(article.title, article.date, article.url) for article in articles]
            output = '\n\n'.join(lines)
        else:
            output = u'Статей автора "{}" не найдено'.format(author)

        bot.send_message(chat_id=update.message.chat_id,
                         text=output,
                         parse_mode=ParseMode.MARKDOWN)

    @staticmethod
    def search_text(bot, update, args):
        try:
            query = ' '.join(args)

            articles = ArticleIndex.search(query)
            if articles.count():
                lines = [u'Найдено {} статей:'.format(articles.count())]
                lines += [u'*{}* {} {}'.format(article.title, article.date, article.url) for article in articles]
                output = '\n\n'.join(lines)
            else:
                output = u'Статей по запросу "{}" не найдено'.format(query)

            bot.send_message(chat_id=update.message.chat_id,
                             text=output,
                             parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            bot.send_message(chat_id=update.message.chat_id,
                             text=str(e))


    @staticmethod
    def get_token():
        with open('token.txt') as fh:
            return fh.readline().strip()

if __name__ == '__main__':
    b = SearchBot()


