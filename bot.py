import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler


class SearchBot(object):
    def __init__(self):
        logging.basicConfig()
        self.log = logging.getLogger('bot')
        self.log.setLevel(logging.DEBUG)
        token = self.get_token()
        self.updater = Updater(token=token)

        self.updater.dispatcher.add_handler(CommandHandler('start', self.start_handler))
        self.updater.start_polling()

    @staticmethod
    def start_handler(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

    @staticmethod
    def get_token():
        with open('token.txt') as fh:
            return fh.readline().strip()

if __name__ == '__main__':
    b = SearchBot()


