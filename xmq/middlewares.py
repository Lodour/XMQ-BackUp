# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
from urllib.parse import urlsplit

from xmq.api import XmqApi, XmqApiResponse


class ConvertToXmqApiResponseMiddleware(object):
    """
    将来自api的Response转换为XmqApiResponse了不受其影响，本middleware的顺序应小于590[2]

    References:
        [1] scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware
        [2] https://doc.scrapy.org/en/latest/topics/settings.html?highlight=settings#downloader-middlewares-base
        [3] https://github.com/scrapy/scrapy/issues/1877
    """

    def process_response(self, request, response, spider):
        if request.url.startswith(XmqApi.URL_API):
            return response.replace(cls=XmqApiResponse)
        return response


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
        request.headers[XmqApi.HEADER_TOKEN_FIELD] = self.TOKEN

    def process_response(self, request, response, spider):
        if isinstance(response, XmqApiResponse) and response.code == 401:
            spider.logger.warn('access_token(%s)已失效: %r' % (self.TOKEN, response.data))
            AccessTokenMiddleware.TOKEN = XmqApi.get_access_token()
            return request
        return response


class HttpHostCheckMiddleware(object):
    """
    自动检测并修正request头部中host的中间件
    """

    def process_request(self, request, spider):
        url, host = request.url, request.headers.get('Host')
        real_host = urlsplit(url).netloc
        if not host or host != real_host:
            request.headers['Host'] = real_host
