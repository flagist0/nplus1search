# encoding: utf-8
import logging
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from article import Article, ArticleIndex

ARTICLES_ON_PAGE_NUM = 10

logging.basicConfig()
log = logging.getLogger('bot')
log.setLevel(logging.DEBUG)


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
    author = ' '.join(args)

    response_opts = get_search_by_author_response(author, cur_page=0)
    bot.send_message(chat_id=update.message.chat_id, **response_opts)


def get_search_by_author_response(author, cur_page):
    reply_markup = None
    count = Article.select().where(Article.author == author).count()
    if count:
        cursor = Article.select().where(Article.author == author).order_by(Article.date.desc())
        offset, limit, total = get_pagination(cursor, cur_page)
        output = get_count_header(offset, limit, total)
        output += get_search_response_text(cursor, offset, limit)
        reply_markup = get_reply_markup(cur_page, offset, limit, total,
                                        # callback data len is limited to 64b
                                        {'meth': 's_b_a', 'ar': author})  # search_by_author
    else:
        output = u'Статей автора "{}" не найдено'.format(author)

    result = {
        'text': output,
        'parse_mode': ParseMode.MARKDOWN,
        'reply_markup': reply_markup
    }
    return result


def get_pagination(cursor, cur_page):
    total_count = cursor.count()
    offset = cur_page * ARTICLES_ON_PAGE_NUM
    limit = min(ARTICLES_ON_PAGE_NUM, total_count - offset)
    return offset, limit, total_count


def get_count_header(offset, limit, total):
    return u'Найдено {} статей\nСтатьи {}-{}/{}:\n\n'.format(total, offset, offset + limit, total)


def get_search_response_text(cursor, offset, limit):
    articles = cursor.offset(offset).limit(limit)
    lines = [u'*{}* {} {}'.format(article.title, article.date, article.url) for article in articles]

    return '\n\n'.join(lines)


def get_reply_markup(cur_page, offset, limit, total, cb_data_additions):
    buttons = []
    if cur_page:
        callback_data = {'page': cur_page - 1}
        callback_data.update(cb_data_additions)
        callback_data = json.dumps(callback_data)
        back_button = InlineKeyboardButton('<', callback_data=callback_data)
        buttons.append(back_button)

    if offset + limit < total:
        callback_data = {'page': cur_page + 1}
        callback_data.update(cb_data_additions)
        callback_data = json.dumps(callback_data)
        forth_button = InlineKeyboardButton('>', callback_data=callback_data)
        buttons.append(forth_button)

    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
    return reply_markup


def button(bot, update):
    query = update.callback_query
    data = json.loads(query.data)

    response_opts = {'text': data}
    if data['meth'] == 's_b_a':
        response_opts = get_search_by_author_response(data['ar'], cur_page=data['page'])

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          **response_opts)


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


def error_handler(bot, update, error):
    log.exception(error)


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
    dispatcher.add_error_handler(error_handler)


if __name__ == '__main__':
    updater = Updater(token=get_token())
    add_handlers(updater)
    updater.start_polling()
    updater.idle()
