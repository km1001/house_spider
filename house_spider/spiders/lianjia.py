# -*- coding: utf-8 -*-
import time
from datetime import datetime

import scrapy
from scrapy import Selector
import json
import re
import pymongo
from house_spider.items import LianjiaVillageItem, LianjiaHouseItem


class LianjiaSpider(scrapy.Spider):
    name = 'lianjia'
    allowed_domains = ['cq.lianjia.com']
    start_urls = ['cq.lianjia.com']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = 'https://cq.lianjia.com'
        self.client = pymongo.MongoClient(host='127.0.0.1', port=27017)

    def start_requests(self):
        request_url = 'https://cq.lianjia.com/xiaoqu/'
        yield scrapy.Request(url=request_url, callback=self.parse_district_links)

    def parse_district_links(self, response):
        """提取地区链接"""
        sel = Selector(response)
        links = sel.css("div[data-role='ershoufang'] div:first-child a::attr(href)").extract()
        for link in links:
            url = self.base_url + link
            yield scrapy.Request(url=url, callback=self.parse_bizcircle_links)

    def parse_bizcircle_links(self, response):
        """提取商圈链接"""
        sel = Selector(response)
        links = sel.css("div[data-role='ershoufang'] div:nth-child(2) a::attr(href)").extract()
        for link in links:
            url = self.base_url + link
            yield scrapy.Request(url=url, callback=self.parse_village_list, meta={"ref": url})

    def parse_village_list(self, response):
        """提取小区链接"""
        sel = Selector(response)
        links = sel.css(".listContent .xiaoquListItem .img::attr(href)").extract()
        for link in links:
            village_id = link.replace(self.base_url + '/xiaoqu/', '').replace('/', '')
            db = self.client['house']
            coll = db['lianjia_village']
            village = coll.find_one({'id': village_id})
            if village is None:
                yield scrapy.Request(url=link, callback=self.parse_village_detail)
            else:
                # 小区房源 https://cq.lianjia.com/ershoufang/c3620038190566370/
                url = self.base_url + "/ershoufang/c" + village_id + "/"
                yield scrapy.Request(url=url, callback=self.parse_house_list, meta={"ref": url})
                # 成交房源
                url = self.base_url + "/chengjiao/c" + village_id + "/"
                yield scrapy.Request(url=url, callback=self.parse_chouse_list, meta={"ref": url})

        # page
        page_data = sel.css(".house-lst-page-box::attr(page-data)").extract_first()
        page_data = json.loads(page_data)
        if page_data['curPage'] < page_data['totalPage']:
            url = response.meta["ref"] + 'pg' + str(page_data['curPage'] + 1)
            yield scrapy.Request(url=url, callback=self.parse_village_list, meta=response.meta)

    def parse_village_detail(self, response):
        """提取小区详情"""
        village_url = response.url
        sel = Selector(response)
        zone = sel.css('.xiaoquDetailbreadCrumbs .l-txt a::text').extract()
        latitude = 0
        longitude = 0
        try:
            html = response.body.decode().replace('\r', '')
            local = html[html.find('resblockPosition:'):html.find('resblockName') - 1]
            m = re.search('(\d.*\d),(\d.*\d)', local)
            longitude = m.group(1)
            latitude = m.group(2)
        except Exception:
            pass

        item = LianjiaVillageItem()
        item['id'] = village_url.replace(self.base_url + '/xiaoqu/', '').replace('/', '')
        item['name'] = sel.css('.detailHeader .detailTitle::text').extract_first()
        item['address'] = sel.css('.detailHeader .detailDesc::text').extract_first()
        item['latitude'] = latitude
        item['longitude'] = longitude
        item['zone'] = ','.join(zone)
        item['year'] = sel.css('.xiaoquInfo .xiaoquInfoItem:nth-child(1) .xiaoquInfoContent::text').extract_first()
        item['build_type'] = sel.css('.xiaoquInfo .xiaoquInfoItem:nth-child(2) .xiaoquInfoContent::text').extract_first()
        item['property_costs'] = sel.css('.xiaoquInfo .xiaoquInfoItem:nth-child(3) .xiaoquInfoContent::text').extract_first()
        item['property_company'] = sel.css('.xiaoquInfo .xiaoquInfoItem:nth-child(4) .xiaoquInfoContent::text').extract_first()
        item['developers'] = sel.css('.xiaoquInfo .xiaoquInfoItem:nth-child(5) .xiaoquInfoContent::text').extract_first()
        item['buildings'] = sel.css('.xiaoquInfo .xiaoquInfoItem:nth-child(6) .xiaoquInfoContent::text').extract_first()
        item['total_house'] = sel.css('.xiaoquInfo .xiaoquInfoItem:nth-child(7) .xiaoquInfoContent::text').extract_first()
        item['采集时间'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        print(item['name'])
        yield item

        # 小区房源 https://cq.lianjia.com/ershoufang/c3620038190566370/
        url = self.base_url + "/ershoufang/c" + item['id'] + "/"
        yield scrapy.Request(url=url, callback=self.parse_house_list, meta={"ref": url})
        # 成交房源
        url = self.base_url + "/chengjiao/c" + item['id'] + "/"
        yield scrapy.Request(url=url, callback=self.parse_chouse_list, meta={"ref": url})

    def parse_house_list(self, response):
        """提取房源链接"""
        sel = Selector(response)
        # 链家有时小区查询不到数据
        total = sel.css('.resultDes .total span::text').extract_first()
        total = int(total)
        if total > 0:
            # 提取房源链接
            links = sel.css(".sellListContent li .info .title a::attr(href)").extract()
            for link in links:
                yield scrapy.Request(url=link, callback=self.parse_house_detail)
            # 链接分页
            page_data = sel.css(".house-lst-page-box::attr(page-data)").extract_first()
            page_data = json.loads(page_data)
            if page_data['curPage'] == 1 and page_data['totalPage'] > 1:
                price = response.url.replace(self.base_url + '/ershoufang/', '')
                for x in range(2, page_data['totalPage'] + 1, 1):
                    url = self.base_url + '/ershoufang/' + 'pg' + str(x) + price
                    yield scrapy.Request(url=url, callback=self.parse_house_list)

    def parse_house_detail(self, response):
        """提取房源信息"""
        sel = Selector(response)

        item = LianjiaHouseItem()
        item['房屋Id'] = response.url.replace(self.base_url + '/ershoufang/', '').replace('.html', '')
        item['标题'] = sel.css('.title-wrapper .title .main::text').extract_first()
        item['售价'] = sel.css('.overview .content .price .total::text').extract_first()
        item['小区'] = sel.css('.overview .content .aroundInfo .communityName a.info::text').extract_first()
        item['小区ID'] = sel.css('.overview .content .aroundInfo .communityName a.info::attr(href)').extract_first().replace('/xiaoqu/', '').replace('/', '')
        item['房屋户型'] = sel.css('#introduction .base .content ul li:nth-child(1)::text').extract_first()
        item['所在楼层'] = sel.css('#introduction .base .content ul li:nth-child(2)::text').extract_first()
        item['建筑面积'] = sel.css('#introduction .base .content ul li:nth-child(3)::text').extract_first()
        item['户型结构'] = sel.css('#introduction .base .content ul li:nth-child(4)::text').extract_first()
        item['套内面积'] = sel.css('#introduction .base .content ul li:nth-child(5)::text').extract_first()
        item['建筑类型'] = sel.css('#introduction .base .content ul li:nth-child(6)::text').extract_first()
        item['房屋朝向'] = sel.css('#introduction .base .content ul li:nth-child(7)::text').extract_first()
        item['建筑结构'] = sel.css('#introduction .base .content ul li:nth-child(8)::text').extract_first()
        item['装修情况'] = sel.css('#introduction .base .content ul li:nth-child(9)::text').extract_first()
        item['梯户比例'] = sel.css('#introduction .base .content ul li:nth-child(10)::text').extract_first()
        item['配备电梯'] = sel.css('#introduction .base .content ul li:nth-child(11)::text').extract_first()
        item['产权年限'] = sel.css('#introduction .base .content ul li:nth-child(12)::text').extract_first()
        item['挂牌时间'] = sel.css('#introduction .transaction .content ul li:nth-child(1) span:nth-child(2)::text').extract_first()
        item['交易权属'] = sel.css('#introduction .transaction .content ul li:nth-child(2) span:nth-child(2)::text').extract_first()
        item['上次交易'] = sel.css('#introduction .transaction .content ul li:nth-child(3) span:nth-child(2)::text').extract_first()
        item['房屋用途'] = sel.css('#introduction .transaction .content ul li:nth-child(4) span:nth-child(2)::text').extract_first()
        item['房屋年限'] = sel.css('#introduction .transaction .content ul li:nth-child(5) span:nth-child(2)::text').extract_first()
        item['产权所属'] = sel.css('#introduction .transaction .content ul li:nth-child(6) span:nth-child(2)::text').extract_first()
        item['抵押信息'] = sel.css('#introduction .transaction .content ul li:nth-child(7) span:nth-child(2)::attr(title)').extract_first()
        item['房本备件'] = sel.css('#introduction .transaction .content ul li:nth-child(8) span:nth-child(2)::text').extract_first()
        item['状态'] = '在售'
        item['采集时间'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        yield item

    def parse_chouse_list(self, response):
        """提取成交房源链接"""
        sel = Selector(response)
        # 链家有时小区查询不到数据
        total = sel.css('.resultDes .total span::text').extract_first()
        total = int(total)
        if total > 0:
            # 提取房源链接
            links = sel.css(".listContent li .info .title a::attr(href)").extract()
            for link in links:
                yield scrapy.Request(url=link, callback=self.parse_chouse_detail)
            # 链接分页
            page_data = sel.css(".house-lst-page-box::attr(page-data)").extract_first()
            page_data = json.loads(page_data)
            if page_data['curPage'] == 1 and page_data['totalPage'] > 1:
                price = response.url.replace(self.base_url + '/chengjiao/', '')
                for x in range(2, page_data['totalPage'] + 1, 1):
                    url = self.base_url + '/chengjiao/' + 'pg' + str(x) + price
                    yield scrapy.Request(url=url, callback=self.parse_chouse_list)

    def parse_chouse_detail(self, response):
        """提取成交房源信息"""
        sel = Selector(response)
        house_id = response.url.replace(self.base_url + '/chengjiao/', '').replace('.html', '')
        db = self.client['house']
        coll = db['lianjia_House']
        house = coll.find_one({'房屋Id': house_id, '状态': '成交'})
        if house is None:

            house = coll.find_one({'房屋Id': house_id})
            item = LianjiaHouseItem()
            item['房屋Id'] = house_id
            item['售价'] = sel.css('.wrapper .overview .info.fr .msg span:nth-child(1) label::text').extract_first()
            item['成交价'] = sel.css('.wrapper .overview .info.fr .price .dealTotalPrice i::text').extract_first()

            if house is None:
                item['标题'] = sel.css('.house-title .wrapper::text').extract_first()
                item['小区'] = sel.css('.wrapper .deal-bread a:nth-child(9)::text').extract_first().replace('二手房成交', '')
                item['小区ID'] = sel.css('.house-title::attr(data-lj_action_housedel_id)').extract_first()
                item['房屋户型'] = sel.css('#introduction .base .content ul li:nth-child(1)::text').extract_first()
                item['所在楼层'] = sel.css('#introduction .base .content ul li:nth-child(2)::text').extract_first()
                item['建筑面积'] = sel.css('#introduction .base .content ul li:nth-child(3)::text').extract_first()
                item['户型结构'] = sel.css('#introduction .base .content ul li:nth-child(4)::text').extract_first()
                item['套内面积'] = sel.css('#introduction .base .content ul li:nth-child(5)::text').extract_first()
                item['建筑类型'] = sel.css('#introduction .base .content ul li:nth-child(6)::text').extract_first()
                item['房屋朝向'] = sel.css('#introduction .base .content ul li:nth-child(7)::text').extract_first()
                item['装修情况'] = sel.css('#introduction .base .content ul li:nth-child(9)::text').extract_first()
                item['建筑结构'] = sel.css('#introduction .base .content ul li:nth-child(10)::text').extract_first()
                item['梯户比例'] = sel.css('#introduction .base .content ul li:nth-child(12)::text').extract_first()
                item['产权年限'] = sel.css('#introduction .base .content ul li:nth-child(13)::text').extract_first()
                item['配备电梯'] = sel.css('#introduction .base .content ul li:nth-child(14)::text').extract_first()
                item['交易权属'] = sel.css('#introduction .transaction .content ul li:nth-child(2)::text').extract_first()
                item['挂牌时间'] = sel.css('#introduction .transaction .content ul li:nth-child(3)::text').extract_first()
                item['房屋用途'] = sel.css('#introduction .transaction .content ul li:nth-child(4)::text').extract_first()
                item['房屋年限'] = sel.css('#introduction .transaction .content ul li:nth-child(5)::text').extract_first()
                item['产权所属'] = sel.css('#introduction .transaction .content ul li:nth-child(6)::text').extract_first()
            else:
                item['标题'] = house['标题']
                item['小区'] = house['小区']
                item['小区ID'] = house['小区ID']
                item['房屋户型'] = house['房屋户型']
                item['所在楼层'] = house['所在楼层']
                item['建筑面积'] = house['建筑面积']
                item['户型结构'] = house['户型结构']
                item['套内面积'] = house['套内面积']
                item['建筑类型'] = house['建筑类型']
                item['房屋朝向'] = house['房屋朝向']
                item['建筑结构'] = house['建筑结构']
                item['装修情况'] = house['装修情况']
                item['梯户比例'] = house['梯户比例']
                item['配备电梯'] = house['配备电梯']
                item['产权年限'] = house['产权年限']
                item['挂牌时间'] = house['挂牌时间']
                item['交易权属'] = house['交易权属']
                item['上次交易'] = house['上次交易']
                item['房屋用途'] = house['房屋用途']
                item['房屋年限'] = house['房屋年限']
                item['产权所属'] = house['产权所属']
                item['抵押信息'] = house['抵押信息']
                item['房本备件'] = house['房本备件']

            item['状态'] = '成交'
            item['成交时间'] = datetime.strptime(sel.css('.house-title div span::text').extract_first().replace(' 成交', ''), '%Y.%m.%d').strftime('%Y-%m-%d')
            item['采集时间'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            yield item
