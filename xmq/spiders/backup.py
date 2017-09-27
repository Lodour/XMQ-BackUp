# -*- coding: utf-8 -*-
import scrapy

from xmq.api import XmqApi
from xmq.items import GroupItem, TopicItem


class BackupSpider(scrapy.Spider):
    name = 'backup'
    allowed_domains = ['xiaomiquan.com']
    start_urls = [XmqApi.URL_GROUPS]

    def parse(self, response):
        for group in response.data['groups']:
            group_id = group['group_id']
            yield GroupItem(_id=group_id, data=group)

            meta = {'group_id': group_id, 'group_name': group['name']}
            yield scrapy.Request(XmqApi.URL_TOPICS(group_id), callback=self.parse_topic, meta=meta)

    def parse_topic(self, response):
        topics = response.data['topics']
        group_id, group_name = response.meta['group_id'], response.meta['group_name']

        for topic in topics:
            topic_id = topic['topic_id']
            yield TopicItem(_id=topic_id, data=topic, group_name=group_name)

        if topics:
            url = XmqApi.URL_TOPICS(group_id, topics[-1]['create_time'])
            yield scrapy.Request(url, callback=self.parse_topic, meta=response.meta)
