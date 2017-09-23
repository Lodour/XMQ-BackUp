# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader.processors import MapCompose

from xmq.api import XmqApi
from xmq.itemloaders import JsonItemLoader, FilterSameValue
from xmq.items import TopicItem
from xmq.spiders import XmqBaseSpider


class TopicsSpider(XmqBaseSpider):
    name = 'topics'
    export_name = 'topics[%s]'

    def __init__(self, group, *args, **kwargs):
        super(TopicsSpider, self).__init__(*args, **kwargs)
        self.group = group
        self.start_urls = [XmqApi.URL_TOPICS(group)]
        self.export_name = self.export_name % group
        self.last_create_time = None

    def parse(self, response):
        loader = JsonItemLoader(item=TopicItem(), response=response)
        filter_duplicate = MapCompose(FilterSameValue('create_time', self.last_create_time))
        loader.add_json('data', 'resp_data/topics', filter_duplicate)
        yield loader.load_item()

        self.last_create_time = create_time = XmqApi.find_latest_create_time(loader.json_data)
        if create_time is not None:
            url = XmqApi.URL_TOPICS(self.group, create_time)
            yield scrapy.Request(url, headers=self.headers, callback=self.parse)
