# -*- coding: utf-8 -*-


import datetime
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from Article.items import LagouJobItemLoader
from Article.items import LagouJobItem
from Article.util.common import get_md5
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['http://www.lagou.com/']

    rules = (
        Rule(LinkExtractor(allow=("zhaopin/.*",)), follow=True),
        Rule(LinkExtractor(allow=("gongsi/j\d+.html",)), follow=True),
        Rule(LinkExtractor(allow=r'/jobs/\d+.html'), callback='parse_job', follow=True),
    )

    def parse_job(self, response):
        jobitem_loader = LagouJobItemLoader(item=LagouJobItem(), response =response)
        jobitem_loader.add_css('title', 'div.job-name::attr(title)')
        jobitem_loader.add_value('url', response.url)
        jobitem_loader.add_value('url_obj_id', get_md5(response.url))

        jobitem_loader.add_css('salary_min',"dd.job_request p span.salary::text")
        jobitem_loader.add_css('salary_max',"dd.job_request p span.salary::text")
        jobitem_loader.add_xpath('job_city','//dd[@class="job_request"]/p/span[2]/text()')
        jobitem_loader.add_xpath('work_years_min', "//dd[@class='job_request']/p/span[3]/text()")
        jobitem_loader.add_xpath('work_years_max', "//dd[@class='job_request']/p/span[3]/text()")
        jobitem_loader.add_xpath('degree_need', "//dd[@class='job_request']/p/span[4]/text()")
        jobitem_loader.add_xpath("job_type", "//*[@class='job_request']/p/span[5]/text()")
        
        jobitem_loader.add_xpath('tags','//dd[@class="job_request"]/ul//li/text()')
        jobitem_loader.add_css('publish_time', ".publish_time::text")
        jobitem_loader.add_css("job_advantage", ".job-advantage p::text")
        jobitem_loader.add_css("job_desc", ".job_bt div")
        jobitem_loader.add_css("job_addr", ".work_addr")
        jobitem_loader.add_value("crawl_time", datetime.datetime.now())

        jobitem_loader.add_css("company_name", "#job_company dt a img::attr(alt)")
        jobitem_loader.add_css("company_url", "#job_company dt a::attr(href)") 

        return jobitem_loader.load_item()
