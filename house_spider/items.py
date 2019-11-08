# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HouseSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class LianjiaVillageItem(scrapy.Item):
    # 链家小区
    collection = 'lianjia_village'
    id = scrapy.Field()
    name = scrapy.Field()
    zone = scrapy.Field()
    address = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()
    year = scrapy.Field()
    build_type = scrapy.Field()
    property_costs = scrapy.Field()
    property_company = scrapy.Field()
    developers = scrapy.Field()
    buildings = scrapy.Field()
    total_house = scrapy.Field()
