# -*- coding: utf-8 -*-
import scrapy

from xmq import settings
from xmq.api import XmqApi
from xmq.items import ImageItem, TopicItem, GroupItem


class BackupSpider(scrapy.Spider):
    name = 'backup'
    allowed_domains = ['xiaomiquan.com']
    start_urls = [XmqApi.URL_GROUPS]

    def parse(self, response):
        for group in response.data['groups']:
            group_id = group['group_id']

            if group_id in settings.IGNORE_GROUP_ID:
                continue

            yield GroupItem(_id=group_id, data=group)

            # 圈子话题
            meta = {'group_id': group_id, 'group_name': group['name']}
            yield scrapy.Request(XmqApi.URL_TOPICS(group_id), callback=self.parse_topic, meta=meta)

    def parse_topic(self, response):
        topics = response.data['topics']
        group_id, group_name = response.meta['group_id'], response.meta['group_name']

        for topic in topics:
            yield TopicItem(_id=topic['topic_id'], data=topic, group_name=group_name)

            if topic['type'] == 'talk':
                for image in topic['talk'].get('images', []):
                    yield ImageItem(_id=image['image_id'], group_name=group_name,
                                    image_urls=[XmqApi.get_image_url(image)])

            # 下一批话题
            if topics:
                url = XmqApi.URL_TOPICS(group_id, topics[-1]['create_time'])
                yield scrapy.Request(url, callback=self.parse_topic, meta=response.meta)
