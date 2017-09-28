# -*- coding: utf-8 -*-
import scrapy

from xmq import settings
from xmq.api import XmqApi
from xmq.items import TopicImagesItem, TopicFilesItem, GroupItem, TopicItem


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

            # 最新话题
            yield scrapy.Request(XmqApi.URL_TOPICS(group_id), callback=self.parse_topic)

    def parse_topic(self, response):
        topics = response.data['topics']

        for topic in topics:
            topic_id, group_name = topic['topic_id'], topic['group']['name']
            yield TopicItem(_id=topic_id, data=topic)

            if topic['type'] == 'talk':

                # 图片
                for images in topic['talk'].get('images', []):
                    image_urls = map(XmqApi.get_image_url, images)
                    yield TopicImagesItem(_id=topic_id, data=images,
                                          group_name=group_name, image_urls=image_urls)

                # 文件
                for files in topic['talk'].get('files', []):
                    item = TopicFilesItem(_id=topic_id, data=files,
                                          group_name=group_name, file_urls=list())
                    url = XmqApi.URL_FILE_DOWNLOAD(item['data'][0]['file_id'])
                    yield scrapy.Request(url, callback=self.parse_file, meta={'item': item, 'next': 1})

        # 下一批话题
        if topics:
            last_topic = topics[-1]
            url = XmqApi.URL_TOPICS(last_topic['group']['group_id'], last_topic['create_time'])
            yield scrapy.Request(url, callback=self.parse_topic)

    def parse_file(self, response):
        item, next = map(response.meta.get, ['item', 'next'])
        item['file_urls'].append(response.data['download_url'])
        if next < len(item['data']):
            url = XmqApi.URL_FILE_DOWNLOAD(item['data'][next]['file_id'])
            yield scrapy.Request(url, callback=self.parse_file, meta={'item': item, 'next': next + 1})
        else:
            yield item
