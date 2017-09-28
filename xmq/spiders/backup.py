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
            meta = {'group_id': group_id, 'group_name': group['name']}
            yield scrapy.Request(XmqApi.URL_TOPICS(group_id), callback=self.parse_topic, meta=meta)

    def parse_topic(self, response):
        topics = response.data['topics']
        group_id, group_name = response.meta['group_id'], response.meta['group_name']

        for topic in topics:
            topic_id = topic['topic_id']
            yield TopicItem(_id=topic_id, data=topic, group_name=group_name)

            if topic['type'] == 'talk':
                # 图片
                if topic['talk'].get('images'):
                    images = topic['talk']['images']
                    image_urls = map(XmqApi.get_image_url, images)
                    yield TopicImagesItem(_id=topic_id, data=images,
                                          group_name=group_name, image_urls=image_urls)

                # 文件
                if topic['talk'].get('files'):
                    item = TopicFilesItem(_id=topic_id, data=topic['talk']['files'],
                                          group_name=group_name, file_urls=list())
                    url = XmqApi.URL_FILE_DOWNLOAD(item['data'][0]['file_id'])
                    yield scrapy.Request(url, callback=self.parse_file, meta={'item': item, 'cnt': 0})

            # 下一批话题
            if topics:
                url = XmqApi.URL_TOPICS(group_id, topics[-1]['create_time'])
                yield scrapy.Request(url, callback=self.parse_topic, meta=response.meta)

    def parse_file(self, response):
        item, count = response.meta['item'], response.meta['cnt']
        item['file_urls'].append(response.data['download_url'])
        if count + 1 < len(item['data']):
            count += 1
            url = XmqApi.URL_FILE_DOWNLOAD(item['data'][count]['file_id'])
            yield scrapy.Request(url, callback=self.parse_file, meta={'item': item, 'cnt': count})
        else:
            yield item
