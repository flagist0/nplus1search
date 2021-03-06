# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
from itertools import chain
import lxml

from scrapy.spiders import Spider
from scrapy.http import Request

from article import Article, ArticleIndex
from link import Link
from utils import db

DIGEST_CHANGEABLE_DAYS_NUM = 2


class PageType(object):
    article = 'article'
    digest = 'digest'
    other = 'other'


class Nplus1Spider(Spider):
    """Nplus1 spider class"""
    name = 'nplus1'
    handle_httpstatus_list = [404]  # Handle 404 status code
    base_url_re = r'/(news|material|blog)/(\d+/\d+/\d+)'
    digest_url_re = base_url_re + r'$'
    article_url_re = base_url_re + r'/.+'

    def __init__(self, *args, **kwargs):
        """Initialize spider"""
        self.allowed_domains = ['nplus1.ru']
        self.base_url = 'https://nplus1.ru'
        self.start_urls = [self.base_url]

        self.create_db()
        super(Nplus1Spider, self).__init__(*args, **kwargs)

    @staticmethod
    def create_db():
        db.create_tables([Article, Link, ArticleIndex], True)

    def start_requests(self):
        yield Request(self.start_urls[0])
        self.log('There are {} parsed articles, {} unparsed article urls and {} unparsed links in db'.format(
            Article.parsed_num(),
            Article.unparsed_num(),
            Link.unparsed_num()))
        for url in chain(Article.iter_unparsed_urls(), Link.iter_unparsed_urls()):
            yield Request(url)

    def parse(self, response):
        if response.status == 200:
            if self.page_type(response.url) == PageType.article:
                yield self.parse_article(response)

            urls = self.extract_links(response)
            for url in urls:
                page_type = self.page_type(url)
                if (page_type == PageType.article and Article.is_parsed(url)) or\
                    (page_type == PageType.digest and Link.is_parsed(url) and
                        not self.digest_could_change(url)):
                    continue
                (Article if self.page_type(url) == PageType.article else Link).by_url(url)  # This will create page stub

                yield Request(url)

            if self.page_type(response.url) == PageType.digest:
                Link.by_url(response.url).set_parsed()

            # Remove redirecting urls to avoid rescraping
            if 'redirect_urls' in response.request.meta:
                redirecting_url = response.request.meta['redirect_urls'][0]
                self.log('Removing forwarding url {}'.format(redirecting_url))
                Article.by_url(redirecting_url).delete_instance()

        elif response.status == 404:
            self.log('Removing non-existent url {}'.format(response.url))
            Article.by_url(response.url).delete_instance()

    def page_type(self, url):
        if re.search(self.article_url_re, url):
            return PageType.article
        elif re.search(self.digest_url_re, url):
            return PageType.digest
        else:
            return PageType.other

    def digest_could_change(self, url):
        digest_date_str = re.search(self.digest_url_re, url).group(2)
        digest_date = datetime.strptime(digest_date_str, '%Y/%m/%d')
        return datetime.today() - digest_date <= timedelta(days=DIGEST_CHANGEABLE_DAYS_NUM)

    def parse_article(self, response):
        """Extract item from the response"""
        self.log('Extracting data from url %s' % response.url)
        article = Article.by_url(response.url)

        article.title = response.xpath('//meta[@property="og:title"]/@content').extract_first().strip()

        description = response.xpath('//meta[@property="og:description"]/@content').extract_first().strip()
        if description:
            article.description = description

        date = response.xpath('//time[@itemprop="datePublished"]/@content').extract_first()
        article.date = datetime.strptime(date, '%Y-%m-%d')

        meta_sel = response.xpath('//div[@class="meta"]')

        article.rubrics = [re.search(r'rubric/(.+)$', url).group(1) for url in
                           meta_sel.xpath('.//p/a[contains(@href, "rubric")]/@href').extract()]
        article.themes = [re.search(r'theme/(.+)$', url).group(1) for url in
                          meta_sel.xpath('.//p/a[contains(@href, "theme")]/@href').extract()]

        if meta_sel.xpath('.//span[@class="difficult-value"]'):
            article.difficulty = float(meta_sel.xpath('.//span[@class="difficult-value"]/text()').extract_first())

        body_xpath = '//article/div[contains(@class, "body")]'
        article.text = cleanup_text(extract_nested_text(response, body_xpath))

        article.internal_links = []
        article.external_links = []
        # Without http can contain mailto links
        for url in response.xpath(body_xpath + '//a[contains(@href, "http")]/@href').extract():
            if self.base_url in url:
                article.internal_links.append(url)
            else:
                article.external_links.append(url)

        article.author = self.extract_author(response)

        article.save()
        return article.to_scrapy_item()

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
    text = re.sub(r'(\r*\n)\1+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return unicode(text, 'utf-8')
