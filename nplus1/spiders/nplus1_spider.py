# -*- coding: utf-8 -*-
import re
from datetime import datetime
import lxml

from scrapy.spiders import Spider
from scrapy.http import Request

from nplus1.items import Nplus1Item
from nplus1.db import DB


class Nplus1Spider(Spider):
    """Nplus1 spider class"""
    name = 'nplus1'
    handle_httpstatus_list = [404]
    article_url_re = r'/(news|material|blog)/\d+/\d+/\d+/.+'

    def __init__(self, *args, **kwargs):
        """Initialize spider"""
        self.allowed_domains = ['nplus1.ru']
        self.start_urls = ['https://nplus1.ru']
        self.base_url = self.start_urls[0]

        self.db = DB(self.article_url_re)

        super(Nplus1Spider, self).__init__(*args, **kwargs)

    def start_requests(self):
        yield Request(self.start_urls[0])
        self.log('There are {} parsed articles and {} unparsed article urls in db'.format(
            self.db.parsed_articles_num(),
            self.db.article_stubs_num()))
        for url in self.db.iter_unparsed_articles_urls():
            yield Request(url)

    def parse(self, response):
        if response.status == 200:
            if self.is_article_url(response.url):
                yield self.parse_article(response)
            urls = self.extract_links(response)
            for url in urls:
                if not self.db.article_is_already_parsed(url):
                    self.db.create_article_stub(url)
                    yield Request(url)
                # else:
                #     self.log('Will not scrape "{}" as it is parsed already'.format(url))
        elif response.status == 404:
            self.log('Removing non-existent url {}'.format(response.url))
            self.db.remove_url(response.url)

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
        item['text'] = cleanup_text(extract_nested_text(response, body_xpath))

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

    def is_article_url(self, url):
        return bool(re.search(self.article_url_re, url))

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
        junk_exts = ['.jpg', '.pdf']
        junk_re = '\.{}$'.format('|'.join(junk_exts))
        urls = []
        for url in set(response.xpath('//a/@href').extract()):
            if self.base_url in url or url.startswith('/'):
                if re.search(junk_re, url):
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


def cleanup_text(text):
    text = re.sub(r'\t', ' ', text)
    text = re.sub(r'(\r*\n)\1+', '\n', text)
    text = re.sub(r'\w', ' ', text)
    return text
