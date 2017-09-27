# -*- coding: utf-8 -*-

import os
import re
import time
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from collections import defaultdict

import scrapy
from scrapy import signals
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline

from xmq.api import XmqApi
from xmq.items import XmqItemExporter, GroupItem, TopicItem, ImageItem


class DuplicatesPipeline(object):
    """
    同一个spider下不同class的item分别去重

    References:
        [1] https://doc.scrapy.org/en/latest/topics/item-pipeline.html#duplicates-filter
    """

    def __init__(self):
        self.populated_ids = defaultdict(set)

    def process_item(self, item, spider):
        _class, _id = item.__class__, item['_id']
        if _id in self.populated_ids[_class]:
            raise DropItem('重复的 %s (%s)' % (_class, _id))
        self.populated_ids[_class].add(_id)
        return item


class BasePipeline(object):
    """
    基本的管道，包括绑定了信号的spider_opened和spider_closed两个方法
    """

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        pass

    def spider_closed(self, spider):
        pass


class XmqPipeline(BasePipeline):
    """
    项目pipeline，此处用于创建导出数据的目录
    """
    TIME_LABEL = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
    EXPORT_PATH = os.path.join(os.getcwd(), 'downloads', TIME_LABEL)

    def spider_opened(self, spider):
        if not os.path.exists(self.EXPORT_PATH):
            os.makedirs(self.EXPORT_PATH)


class GroupItemExportPipeline(BasePipeline):
    """
    处理Group的pipeline
    """
    EXPORT_PATH = os.path.join(XmqPipeline.EXPORT_PATH, 'groups.json')

    def spider_opened(self, spider):
        self.file = open(self.EXPORT_PATH, 'wb')
        self.exporter = XmqItemExporter(self.file)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        if isinstance(item, GroupItem):
            self.exporter.export_item(item)
        return item


class TopicItemExportPipeline(BasePipeline):
    """
    处理Topic的pipeline

    每个group下的topics分别存储在不同的json文件中
    """
    EXPORT_PATH = os.path.join(XmqPipeline.EXPORT_PATH, 'topics-{name}.json')

    def __init__(self, *args, **kwargs):
        self.files, self.exporters = {}, {}

    def spider_closed(self, spider):
        for exporter in self.exporters.values():
            exporter.finish_exporting()
        for file in self.files.values():
            file.close()

    def process_item(self, item, spider):
        if isinstance(item, TopicItem):
            exporter = self.__get_exporter(item['group_name'])
            exporter.export_item(item)
        return item

    def __get_file(self, name):
        file = self.files.get(name)
        if not file:
            file = open(self.EXPORT_PATH.format(name=name), 'wb')
            self.files[name] = file
        return file

    def __get_exporter(self, name):
        exporter = self.exporters.get(name)
        if not exporter:
            exporter = XmqItemExporter(self.__get_file(name))
            exporter.start_exporting()
            self.exporters[name] = exporter
        return exporter


class XmqImagesPipeline(ImagesPipeline):
    """
    下载TopicImages的pipeline

    以image_id为文件名，按group_name分组存储在images目录下
    """

    @classmethod
    def from_settings(cls, settings):
        export_path = os.path.join(XmqPipeline.EXPORT_PATH, 'images')
        return cls(export_path, settings=settings)

    def get_media_requests(self, item, info):
        for url in item['image_urls']:
            meta = {'params': (item['group_name'], item['_id'], self.__image_type(url))}
            yield scrapy.Request(url, headers={'Host': XmqApi.IMAGE_HOST}, meta=meta)

    def process_item(self, item, spider):
        if not isinstance(item, ImageItem):
            return item
        return super(XmqImagesPipeline, self).process_item(item, spider)

    def file_path(self, request, response=None, info=None):
        return '{}/{}{}'.format(*request.meta['params'])

    def __image_type(self, url):
        result = re.search(r'\.\w+$', url)
        return result and result.group() or '.webp'
