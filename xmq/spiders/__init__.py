# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import scrapy

from xmq.api import XmqLogin


class XmqBaseSpider(scrapy.Spider):
    allowed_domains = ['xiaomiquan.com']
    export_name = NotImplemented

    def __init__(self, token=None, *args, **kwargs):
        super(XmqBaseSpider, self).__init__(*args, **kwargs)
        self.token = XmqLogin.get_access_token(self) if token is None else token
        self.headers = {'authorization': self.token}

    def start_requests(self):
        for u in self.start_urls:
            yield scrapy.Request(u, headers=self.headers, callback=self.parse)

    def parse(self, response):
        return NotImplemented
