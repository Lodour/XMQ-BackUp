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

from xmq.items import XmqItemExporter, GroupItem, TopicItem


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
            if item['_id'] == '758548854':
                raise DropItem('忽略"帮助与反馈"圈子')
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
        for exporter in self.exporters:
            exporter.finish_exporting()
        for file in self.files:
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
