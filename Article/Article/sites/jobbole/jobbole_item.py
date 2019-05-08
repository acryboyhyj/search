# -*- coding: utf-8 -*-
import scrapy
import os,sys

from scrapy.loader import ItemLoader
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Join,Identity
import re
import datetime
from w3lib.html import remove_tags
from Article.settings import  SQL_DATETIME_FORMAT,SQL_DATE_FORMAT
from Article.sites.jobbole.es_jobbole import JobboleBlogIndex
from elasticsearch_dsl.connections import connections
import redis
from Article.items import MysqlItem,EsItem
from Article.util.es_util import gen_suggests

from Article.util.common import extract_num

es = connections.create_connection(JobboleBlogIndex)

redis_cli = redis.StrictRedis()

JOBBOLE_COUNT_INIT=0

def remove_comment_tags(value):
    #去掉tag中提取的评论
    if u"评论" in value:
        return ""
    else:
        return value
def get_nums(nums):
    nums = re.match('.*?(\d+).*',nums)
    if nums:
        num = int(nums.group(1))
    else:
        num = 0
    return num

def convert_date(value):
#    date = date.strip()
#    date = re.sub(r'[^\x00-\x7f]',r'','2018/12/22 ·')
#    try:
#        date = datetime.datetime.strptime(create_date,"%Y/%m/%d").date()
#    except Exception as e:
#        date = datetime.datetime.now().date()
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


class JobboleArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

class JobboleArticleItem(scrapy.Item, MysqlItem, EsItem):
    url = scrapy.Field()
    image_urls = scrapy.Field()
    title = scrapy.Field()
    praisenum = scrapy.Field(
            input_processor=MapCompose(get_nums)
            )
    colectnum = scrapy.Field(
            input_processor=MapCompose(get_nums))
    create_date = scrapy.Field(
            input_processor=MapCompose(convert_date))
    content = scrapy.Field()
    image_paths= scrapy.Field(
            output_processor=Identity())
    url_obj_id = scrapy.Field()
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    
    def help_fields(self):
        for field in self.field_list:
            print(field, "= scrapy.Field()")
    def clean_data(self):
        if self["image_urls"]:
            self["image_urls"] = self["image_urls"][0]
        
    def save_to_mysql(self):
        self.clean_data()
        insert_sql = """
            insert into article(url_obj_id, title, url, create_date, praisenum)
            VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(praisenum)
        """
        params = (self['url_obj_id'],self["title"], self["url"], self["create_date"], self["praisenum"])

        return insert_sql, params

    def save_to_es(self):
        self.clean_data()
        article = JobboleBlogIndex()
        article.title = self['title']
        article.create_date = self["create_date"]
        article.content = remove_tags(self["content"])
        article.image_urls = self["image_urls"]
        if "image_paths" in self:
            article.image_paths = self["image_paths"]
        article.praise_nums = self["praisenum"]
        article.url = self["url"]
        article.meta.id = self["url_obj_id"]
        article.suggest = gen_suggests(es,"jobbole_blog" ,((article.title,10),(article.tags, 7)))
        article.save()
        redis_cli.incr("jobbole_blog_count")
        return

 

