# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time

from scrapy import signals
from scrapy.exporters import JsonItemExporter


class XmqPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        time_label = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
        file = open('%s %s.json' % (spider.name, time_label), 'wb')
        self.files[spider] = file
        self.exporter = JsonItemExporter(file, indent=2, ensure_ascii=False)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        for i in item['data']:
            self.exporter.export_item(i)
        return item
