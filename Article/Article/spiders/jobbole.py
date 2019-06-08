# -*- coding: utf-8 -*-
import scrapy
import re
from urlparse import urljoin
from scrapy import Request
from Article.sites.jobbole.jobbole_item import JobboleArticleItem
from Article.util.common import get_md5
import datetime
from Article.sites.jobbole.jobbole_item import JobboleArticleItemLoader
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from scrapy_redis.spiders import RedisSpider


class SspiderSpider(scrapy.Spider):
    name = 'jobbole'
    start_urls = [
        'http://blog.jobbole.com/all-posts',
    ]
    allowed_domins = ['blog.jobbole']
    custom_settings = {
        "DOWNLOAD_DELAY" : 5,
    }
   
    #tiqu all article
    def parse(self,response):
        post_nodes = response.css("div#archive .post.floated-thumb .post-thumb a")
        for post_node in post_nodes: 
            post_url = post_node.css("::attr(href)").extract()[0]
            image_urls = post_node.css("img::attr(src)").extract()[0]
            exact_url = urljoin(response.url,post_url)
            yield Request(url=exact_url,callback=self.parse_detail,meta={'image_urls':image_urls})

        next_url = response.css("a.next.page-numbers::attr(href)").extract()[0]
        next_url_extract =  urljoin(response.url,next_url)
        if next_url:
            yield Request(url=next_url_extract,callback=self.parse)    
        
    def parse_detail(self, response):
        #tiqu article cotent
        image_urls = response.meta.get("image_urls","")
        item_loader = JobboleArticleItemLoader(item=JobboleArticleItem(), response = response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url_obj_id", get_md5(response.url))
        item_loader.add_value("url",response.url)
        item_loader.add_value("image_urls",image_urls)
        item_loader.add_xpath("praisenum", "//div[@class='post-adds']/span[1]/h10/text()")
        item_loader.add_xpath("colectnum","//span[contains(@class,'bookmark-btn')]/text()")
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_xpath("content", "//div[@class='entry']")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        article_item = item_loader.load_item() 
        yield article_item


