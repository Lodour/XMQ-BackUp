# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json

from scrapy import signals

from xmq.api import XmqApi, XmqApiResponse


class XmqSpiderMiddleware(object):
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        setattr(response, 'json_data', json.loads(response.text))
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ConvertToXmqApiResponseMiddleware(object):
    """
    将来自api的Response转换为XmqApiResponse
    由于[1, 2]对response的class进行了分发，为了不受其影响，本middleware的顺序应小于590[2]

    References:
        [1] scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware
        [2] https://doc.scrapy.org/en/latest/topics/settings.html?highlight=settings#downloader-middlewares-base
        [3] https://github.com/scrapy/scrapy/issues/1877
    """

    def process_response(self, request, response, spider):
        if request.method == 'HEAD':
            return response
        if not request.url.startswith(XmqApi.URL_API):
            return response
        return response.replace(cls=XmqApiResponse)


class AccessTokenMiddleware(object):
    """
    自动获取、添加、请求更新access_token的中间件
    """

    # middleware是通过实例调用的，为了维护全局的token，需要放在类变量里
    TOKEN = None

    @classmethod
    def from_crawler(cls, crawler):
        cls.TOKEN = crawler.settings['XMQ_ACCESS_TOKEN'] or XmqApi.get_access_token()
        return cls()

    def process_request(self, request, spider):
        request.headers[XmqApi.HEADER_TOKEN_FIELD] = AccessTokenMiddleware.TOKEN

    def process_response(self, request, response, spider):
        if isinstance(response, XmqApiResponse) and response.code == 401:
            spider.logger.warn('access_token(%s)已失效: %r' % (AccessTokenMiddleware.TOKEN, response.data))
            AccessTokenMiddleware.TOKEN = XmqApi.get_access_token()
            return request
        return response
