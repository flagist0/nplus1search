# encoding: utf-8
import logging
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from article import Article, ArticleIndex

ARTICLES_ON_PAGE_NUM = 15


class SearchBot(object):
    def __init__(self):
        logging.basicConfig()
        self.log = logging.getLogger('bot')
        self.log.setLevel(logging.DEBUG)
        token = self.get_token()
        self.updater = Updater(token=token)

        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler('start', SearchBot.show_help))
        dispatcher.add_handler(CommandHandler('info', SearchBot.show_database_info))
        dispatcher.add_handler(CommandHandler('author', SearchBot.search_by_author, pass_args=True))
        dispatcher.add_handler(CallbackQueryHandler(SearchBot.button))
        dispatcher.add_handler(MessageHandler(Filters.text, SearchBot.search_text))

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
        <текст> -- поиск по тексту статей
        /author <автор> -- поиск по имени автора
        PS: пока ничего не работает
        """.format(Article.parsed_num())
        keyboard = [[InlineKeyboardButton('Nplus1', url='http://nplus1.ru')]]
        markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=update.message.chat_id,
                         text=message,
                         reply_markup=markup)

    @staticmethod
    def search_by_author(bot, update, args):
        reply_markup = None
        author = ' '.join(args)

        count = Article.select().where(Article.author == author).count()
        if count:
            lines = [u'Найдено {} статей:'.format(count)]

            cur_page = 0
            offset = cur_page * ARTICLES_ON_PAGE_NUM
            limit = min(ARTICLES_ON_PAGE_NUM, count - offset)
            lines.append(u'Статьи {}-{}/{}'.format(offset, offset + limit, count))

            articles = Article.search_by_author(author, offset, limit)
            lines += [u'*{}* {} {}'.format(article.title, article.date, article.url) for article in articles]
            output = '\n\n'.join(lines)

            buttons = []
            if cur_page:
                callback_data = {'method': 'by_author', 'page': cur_page - 1}
                back_button = InlineKeyboardButton('<', callback_data=json.dumps(callback_data))
                buttons.append(back_button)

            if offset + limit < count:
                callback_data = {'method': 'by_author', 'page': cur_page + 1}
                forth_button = InlineKeyboardButton('>', callback_data=json.dumps(callback_data))
                buttons.append(forth_button)

            if buttons:
                reply_markup = InlineKeyboardMarkup([buttons])
        else:
            output = u'Статей автора "{}" не найдено'.format(author)

        bot.send_message(chat_id=update.message.chat_id,
                         text=output,
                         parse_mode=ParseMode.MARKDOWN,
                         reply_markup=reply_markup)

    @staticmethod
    def button(bot, update):
        query = update.callback_query
        data = json.loads(query.data)

        bot.edit_message_text(text="Selected option: %s" % data,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

    @staticmethod
    def search_text(bot, update):
        try:
            query = update.message.text

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
            bot.logger.exception(e)
            raise

    @staticmethod
    def get_token():
        with open('token.txt') as fh:
            return fh.readline().strip()

if __name__ == '__main__':
    b = SearchBot()


