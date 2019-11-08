# -*- coding: utf-8 -*-
import scrapy
from scrapy import Selector
import json
import re

from house_spider.items import LianjiaVillageItem


class LianjiaSpider(scrapy.Spider):
    name = 'lianjia'
    allowed_domains = ['cq.lianjia.com']
    start_urls = ['cq.lianjia.com']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = 'https://cq.lianjia.com'

    def start_requests(self):
        request_url = 'https://cq.lianjia.com/xiaoqu/'
        yield scrapy.Request(url=request_url, callback=self.parse_district_links)

    def parse_district_links(self, response):
        sel = Selector(response)
        links = sel.css("div[data-role='ershoufang'] div:first-child a::attr(href)").extract()
        for link in links:
            url = self.base_url + link
            yield scrapy.Request(url=url, callback=self.parse_bizcircle_links)

    def parse_bizcircle_links(self, response):
        sel = Selector(response)
        links = sel.css("div[data-role='ershoufang'] div:nth-child(2) a::attr(href)").extract()
        for link in links:
            url = self.base_url + link
            yield scrapy.Request(url=url, callback=self.parse_village_list, meta={"ref": url})

    def parse_village_list(self, response):
        sel = Selector(response)
        links = sel.css(".listContent .xiaoquListItem .img::attr(href)").extract()
        for link in links:
            yield scrapy.Request(url=link, callback=self.parse_village_detail)

        # page
        page_data = sel.css(".house-lst-page-box::attr(page-data)").extract_first()
        page_data = json.loads(page_data)
        if page_data['curPage'] < page_data['totalPage']:
            url = response.meta["ref"] + 'pg' + str(page_data['curPage'] + 1)
            yield scrapy.Request(url=url, callback=self.parse_village_list, meta=response.meta)

    def parse_village_detail(self, response):
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
        item['id'] = village_url.replace('https://cq.lianjia.com/xiaoqu/', '').replace('/', '')
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
        yield item
