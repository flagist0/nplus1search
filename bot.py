# encoding: utf-8
import logging
import json
import subprocess
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from article import Article, ArticleIndex

ARTICLES_ON_PAGE_NUM = 10

query_by_hash = {}

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
    Сейчас в моей базе {} статей, последнее обновление базы было {}
    
    Полнотекстовый поиск:
    динозавр -- поиск по тексту статей
    кошка *OR* кот *OR* панголин -- в выдаче будут статьи, в которых встречается одно из указанных слов
    кошка *-*предок -- убирает из выдачи статьи, в которых встречается слово "предок"
    рибо\* -- поиск по префиксу, найдет и рибосомы, и рибозимы, и Жана Рибо
    
    Команды:
    */author <автор>* -- поиск по имени автора
    */update* -- обновление базы
    */help* -- эта справка

    Исходники доступны тут: https://github.com/flagist0/nplus1search
    """.format(Article.parsed_num(),
               open('last_update.txt').readline().strip())
    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode=ParseMode.MARKDOWN)


def rescrape(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=u'Начинаю обновление базы')

    process = subprocess.Popen(['scrapy', 'crawl', 'nplus1'], stdout=subprocess.PIPE)
    process.communicate()
    bot.send_message(chat_id=update.message.chat_id,
                     text=u'Обновление базы закончено!')
    with open('last_update.txt', 'w') as fh:
        fh.write('{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M')))


def search_by_author(bot, update, args):
    author = ' '.join(args)

    response_opts = get_search_by_author_response(author, cur_page=0)
    bot.send_message(chat_id=update.message.chat_id, **response_opts)


def search_by_text(bot, update):
    query = update.message.text

    response_opts = get_search_by_text_response(query, cur_page=0)
    bot.send_message(chat_id=update.message.chat_id, **response_opts)


def get_search_by_author_response(author, cur_page):
    reply_markup = None
    where = Article.author == author
    count = Article.select().where(where).count()
    if count:
        cursor = Article.select().where(where).order_by(Article.date.desc())
        offset, limit, total = get_pagination(cursor, cur_page)
        output = get_count_header(offset, limit, total)
        output += get_search_by_author_response_text(cursor, offset, limit)
        author_hash = hash(author)
        query_by_hash[author_hash] = author
        reply_markup = get_reply_markup(cur_page, offset, limit, total,
                                        # callback data len is limited to 64b
                                        {'meth': 's_b_a', # search_by_author
                                         'ah': author_hash})  # author hash, dirty stateful hack because of cb data limits
    else:
        output = u'Статей автора "{}" не найдено'.format(author)

    result = {
        'text': output,
        'parse_mode': ParseMode.MARKDOWN,
        'reply_markup': reply_markup
    }
    return result


def get_search_by_text_response(query_text, cur_page):
    reply_markup = None

    cursor = ArticleIndex.search_by_text(query_text)
    count = cursor.count()
    if count:
        offset, limit, total = get_pagination(cursor, cur_page)
        output = get_count_header(offset, limit, total)
        output += get_search_by_text_response_text(cursor, offset, limit)
        query_hash = hash(query_text)
        query_by_hash[query_hash] = query_text
        reply_markup = get_reply_markup(cur_page, offset, limit, total,
                                        # callback data len is limited to 64b
                                        {'meth': 's_b_t',  # search_by_text
                                         'qth': query_hash})  # query_text hash, dirty stateful hack because of cb data limits
    else:
        output = u'Статей по запросу "{}" не найдено'.format(query_text)

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


def get_search_by_author_response_text(cursor, offset, limit):
    articles = cursor.offset(offset).limit(limit)
    lines = [u'*{}* {} {}'.format(article.title, article.date, article.url) for article in articles]

    return '\n\n'.join(lines)


def get_search_by_text_response_text(cursor, offset, limit):
    articles = cursor.offset(offset).limit(limit)
    lines = [u'*{}* {}\n{}\n{}'.format(article.title, article.date, article.snippets, article.url)
             for article in articles]

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


def callback_handler(bot, update):
    query = update.callback_query
    data = json.loads(query.data)

    response_opts = {'text': data}
    if data['meth'] == 's_b_a':
        author = query_by_hash.pop(data['ah'])
        response_opts = get_search_by_author_response(author, cur_page=data['page'])
    elif data['meth'] == 's_b_t':
        query_text = query_by_hash.pop(data['qth'])
        response_opts = get_search_by_text_response(query_text, cur_page=data['page'])

    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          **response_opts)


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
    dispatcher.add_handler(CommandHandler('update', rescrape))
    dispatcher.add_handler(CommandHandler('author', search_by_author, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(callback_handler))
    dispatcher.add_handler(MessageHandler(Filters.text, search_by_text))
    dispatcher.add_error_handler(error_handler)


if __name__ == '__main__':
    updater = Updater(token=get_token())
    add_handlers(updater)
    updater.start_polling()
    updater.idle()
