# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from scrapy.conf import settings


class HouseSpiderPipeline(object):
    def process_item(self, item, spider):
        return item


class LianjiaVillageSavePipeline(object):
    def __init__(self):
        pass

    def process_item(self, item, spider):
        if spider.name == 'lianjia':
            client = pymongo.MongoClient(host=settings['MONGO_HOST'], port=settings['MONGO_PORT'])
            db = client['house']
            coll = db[item.collection]
            coll.insert(dict(item))
