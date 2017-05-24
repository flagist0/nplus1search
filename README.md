# nplus1search
Скрейпер и telegram-бот для nplus1.ru

Состоит из двух программ:
1. Скрейпер -- обходит сайт, ищет необработанные статьи, парсит их, извлекает важные данные (автор, название, текст, рубрики, жанры, сложность, внутренние и внешние ссылки), после чего сохраняет их в базу.
2. Telegram-бот -- ищет запросы в базе.

Скрейпер
========
Написан на Scrapy. Можно запустить руками командой `scrapy crawl nplus1`

База данных
===========
Основной компонент, разделяемый между скрейпером и ботом. Написана на восхитительном ORM Peewee. Внутри SQLite.

В таблице article хранятся сами статьи, а articleindex -- их полнотекстовый индекс, позволяющий делать сложные запросы (главная фишка).

SQLite (и оборачивающий её Peewee) поддерживает полнотекстовый поиск, но в случае с русским языком есть проблема: для нормального поиска текст должен быть лемматизирован (должны быть отрезаны окончания), но SQLite ничего не знает о русском языке.

Так что нужен лемматизатор c поддержкой русского языка, например Snowball. Но... лемматизатор надо передать через специальный интерфейс внутрь sqlite, а он написан на C, а проект написан на Python. В общем, слава проекту sqlitefts, генерирующему через FFI обертку для питоновских лемматизаторов.

Бот
==========
Просто бот (но с inline-кнопочками!)

Запускается `python ./bot.py`

Для работы ему нужен токен, лежащий в token.txt, который я по понятным причинам не выкладываю.

Если где-то еще запущен такой же бот, будет конфликт.
