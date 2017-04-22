# -*- coding: utf-8 -*-

# Scrapy settings for nplus1 project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'nplus1'

SPIDER_MODULES = ['nplus1.spiders']
NEWSPIDER_MODULE = 'nplus1.spiders'

USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)'
AUTOTHROTTLE_ENABLED = True

ITEM_PIPELINES = {
    'nplus1.pipelines.Nplus1Pipeline': 300
}

#DOWNLOAD_DELAY = 2
