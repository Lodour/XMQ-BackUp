# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.exporters import JsonItemExporter


class XmqItem(scrapy.Item):
    """
    因为不能确定api返回的具体字段，因此将所有字段存在data域中
    为了筛去重复item，指定了一个id域
    是本项目所有item的父类
    """
    _id = scrapy.Field()
    data = scrapy.Field()


class GroupItem(XmqItem):
    pass


class TopicItem(XmqItem):
    group_name = scrapy.Field()


class TopicImagesItem(TopicItem):
    image_urls = scrapy.Field()
    images = scrapy.Field()


class TopicFilesItem(TopicItem):
    file_urls = scrapy.Field()
    files = scrapy.Field()


class XmqItemExporter(JsonItemExporter):
    """
    将data域内数据作为item导出
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('indent', 2)
        kwargs.setdefault('ensure_ascii', False)
        super(XmqItemExporter, self).__init__(*args, **kwargs)

    def export_item(self, item):
        super(XmqItemExporter, self).export_item(item['data'])
