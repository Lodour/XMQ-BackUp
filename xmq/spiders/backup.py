# -*- coding: utf-8 -*-
import scrapy

from xmq.api import XmqApi
from xmq.items import GroupItem


class BackupSpider(scrapy.Spider):
    name = 'backup'
    allowed_domains = ['xiaomiquan.com']
    start_urls = [XmqApi.URL_GROUPS]

    def parse(self, response):
        for group in response.data['groups']:
            group_id = group['group_id']
            yield GroupItem(_id=group_id, data=group)
