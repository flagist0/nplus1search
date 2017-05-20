# encoding: utf-8
import logging
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from article import Article, ArticleIndex

ARTICLES_ON_PAGE_NUM = 15

logging.basicConfig()
log = logging.getLogger('bot')


def show_database_info(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=u'В базе {} статей'.format(Article.parsed_num()))


def show_help(bot, update):
    message = u"""
    Привет!
    Я бот-поисковик по http://nplus1.ru
    Сейчас в моей базе {} статей
    Команды:
    *<текст>* -- поиск по тексту статей
    */author <автор>* -- поиск по имени автора
    */help* -- эта справка
    
    PS: пока ничего не работает
    """.format(Article.parsed_num())
    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.MARKDOWN)


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


def button(bot, update):
    query = update.callback_query
    data = json.loads(query.data)

    bot.edit_message_text(text="Selected option: %s" % data,
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)


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
        log.exception(e)
        raise


def get_token():
    with open('token.txt') as fh:
        return fh.readline().strip()


def add_handlers(updater):
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', show_help))
    dispatcher.add_handler(CommandHandler('help', show_help))
    dispatcher.add_handler(CommandHandler('info', show_database_info))
    dispatcher.add_handler(CommandHandler('author', search_by_author, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text, search_text))


if __name__ == '__main__':
    updater = Updater(token=get_token())
    add_handlers(updater)
    updater.start_polling()
    updater.idle()
