# -*- coding: utf-8 -*-

import os
import time
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from collections import defaultdict

from scrapy import signals
from scrapy.exceptions import DropItem

from xmq.items import XmqItemExporter


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


class XmqPipeline(object):
    """
    项目pipeline，此处用于创建导出数据的目录
    """
    TIME_LABEL = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
    EXPORT_PATH = os.path.join(os.getcwd(), 'downloads', TIME_LABEL)

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        return pipeline

    def spider_opened(self, spider):
        if not os.path.exists(XmqPipeline.EXPORT_PATH):
            os.makedirs(XmqPipeline.EXPORT_PATH)


class GroupItemExportPipeline(object):
    """
    处理Group的pipeline
    """
    EXPORT_PATH = os.path.join(XmqPipeline.EXPORT_PATH, 'groups.json')

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.file = open(GroupItemExportPipeline.EXPORT_PATH, 'wb')
        self.exporter = XmqItemExporter(self.file)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
