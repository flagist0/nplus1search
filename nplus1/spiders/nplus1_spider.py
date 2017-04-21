# -*- coding: utf-8 -*-
import re
from datetime import datetime
import lxml

from scrapy.spiders import Spider
from scrapy.http import Request

from nplus1.items import Nplus1Item
from nplus1.db import DB


def is_article_url(url):
    return bool(re.search(r'/(news|material|blog)/\d+/\d+/\d+/.+', url))


class Nplus1Spider(Spider):
    """Nplus1 spider class"""
    name = 'nplus1'

    def __init__(self, *args, **kwargs):
        """Initialize spider"""
        self.allowed_domains = ['nplus1.ru']
        self.start_urls = ['https://nplus1.ru']
        self.base_url = self.start_urls[0]

        self.db = DB()

        super(Nplus1Spider, self).__init__(*args, **kwargs)

    def start_requests(self):
        yield Request(self.start_urls[0])
        for url in self.db.iter_unparsed_articles_urls():
            yield Request(url)

    def parse(self, response):
        if is_article_url(response.url):
            yield self.parse_article(response)
        urls = self.extract_links(response)
        for url in urls:
            if not self.db.article_is_already_parsed(url):
                self.db.create_article_stub(url)
                yield Request(url)
            else:
                self.log('Will not scrape "{}" as it is parsed already'.format(url))

    def parse_article(self, response):
        """Extract item from the response"""
        self.log('Extracting data from url %s' % response.url)
        item = Nplus1Item()

        item['url'] = response.url
        item['title'] = response.xpath('//meta[@property="og:title"]/@content').extract_first().strip()

        description = response.xpath('//meta[@property="og:description"]/@content').extract_first().strip()
        if description:
            item['description'] = description

        date = response.xpath('//time[@itemprop="datePublished"]/@content').extract_first()
        item['date'] = datetime.strptime(date, '%Y-%m-%d')

        meta_sel = response.xpath('//div[@class="meta"]')

        item['rubrics'] = [re.search('rubric/(.+)$', url).group(1) for url in
                           meta_sel.xpath('.//p/a[contains(@href, "rubric")]/@href').extract()]
        item['themes'] = [re.search('theme/(.+)$', url).group(1) for url in
                          meta_sel.xpath('.//p/a[contains(@href, "theme")]/@href').extract()]

        if meta_sel.xpath('.//span[@class="difficult-value"]'):
            item['difficulty'] = float(meta_sel.xpath('.//span[@class="difficult-value"]/text()').extract_first())

        body_xpath = '//article/div[contains(@class, "body")]'
        text = extract_nested_text(response, body_xpath)
        text = re.sub('\r*\n', ' ', text)
        text = re.sub('\w+', ' ', text)
        item['text'] = text

        item['internal_links'] = []
        item['external_links'] = []
        # Without http can contain mailto links
        for url in response.xpath(body_xpath + '//a[contains(@href, "http")]/@href').extract():
            if self.base_url in url:
                item['internal_links'].append(url)
            else:
                item['external_links'].append(url)

        item['author'] = self.extract_author(response)

        return item

    @staticmethod
    def extract_author(response):
        author = None
        if response.xpath('//meta[@name="author"]'):
            author = response.xpath('//meta[@name="author"]/@content').extract_first()
        elif response.xpath('//div[@class="author"]/div[@class="meta"]/p[@class="name"]/text()'):
            author = response.xpath('//div[@class="author"]/div[@class="meta"]/p[@class="name"]/text()').extract_first()
        elif response.xpath('//article/div[@class="body"]/*[last() and name()="i"]'):
            author = response.xpath('//article/div[@class="body"]/*[last() and name()="i"]/text()').extract_first()
        elif response.xpath('//article/div[@class="body"]/p[last()]//i'):
            author_sel = response.xpath('//article/div[@class="body"]/p[last()]')
            author = extract_nested_text(author_sel, './*')
        return author.strip()

    def extract_links(self, response):
        urls = []
        for url in set(response.xpath('//a/@href').extract()):
            if self.base_url in url or url.startswith('/'):
                if url.endswith('.jpg'):
                    continue
                url = (url if self.base_url in url else self.base_url + url).strip()
                urls.append(url)

        return urls


def extract_nested_text(response, xpath):
    """Extract text from element with nested elements"""
    html = response.xpath(xpath).extract_first()
    tree = lxml.html.fromstring(html)
    text = lxml.html.tostring(tree, method='text', encoding='utf-8').strip()
    return text
