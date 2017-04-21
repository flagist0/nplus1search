# -*- coding: utf-8 -*-
class Nplus1Pipeline(object):
    def process_item(self, item, spider):
        spider.db.save_article(item)
        return item
