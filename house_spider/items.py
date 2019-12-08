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
    采集时间 = scrapy.Field()

class LianjiaHouseItem(scrapy.Item):
    collection = 'lianjia_House'
    房屋Id = scrapy.Field()
    标题 = scrapy.Field()
    售价 = scrapy.Field()
    小区 = scrapy.Field()
    小区ID = scrapy.Field()
    房屋户型 = scrapy.Field()
    所在楼层 = scrapy.Field()
    建筑面积 = scrapy.Field()
    户型结构 = scrapy.Field()
    套内面积 = scrapy.Field()
    建筑类型 = scrapy.Field()
    房屋朝向 = scrapy.Field()
    建筑结构 = scrapy.Field()
    装修情况 = scrapy.Field()
    梯户比例 = scrapy.Field()
    配备电梯 = scrapy.Field()
    产权年限 = scrapy.Field()
    挂牌时间 = scrapy.Field()
    交易权属 = scrapy.Field()
    上次交易 = scrapy.Field()
    房屋用途 = scrapy.Field()
    房屋年限 = scrapy.Field()
    产权所属 = scrapy.Field()
    抵押信息 = scrapy.Field()
    房本备件 = scrapy.Field()
    成交价 = scrapy.Field()
    状态 = scrapy.Field()
    采集时间 = scrapy.Field()
    成交时间 = scrapy.Field()