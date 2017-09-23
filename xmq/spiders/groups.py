# -*- coding: utf-8 -*-

from xmq.api import XmqApi
from xmq.itemloaders import JsonItemLoader
from xmq.items import GroupItem
from xmq.spiders import XmqBaseSpider


class GroupsSpider(XmqBaseSpider):
    name = 'groups'
    export_name = 'groups'

    start_urls = [XmqApi.URL_GROUPS]

    def parse(self, response):
        loader = JsonItemLoader(item=GroupItem(), response=response)
        loader.add_json('data', 'resp_data/groups')
        return loader.load_item()
