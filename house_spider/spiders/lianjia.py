# -*- coding: utf-8 -*-
import scrapy
from scrapy import Selector
import json


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
            print('village:' + link)
            # yield scrapy.Request(url=link, callback=self.parse_village_list)

        # page
        page_data = sel.css(".house-lst-page-box::attr(page-data)").extract_first()
        page_data = json.loads(page_data)
        if page_data['curPage'] < page_data['totalPage']:
            url = response.meta["ref"] + 'pg' + str(page_data['curPage'] + 1)
            yield scrapy.Request(url=url, callback=self.parse_village_list, meta=response.meta)
