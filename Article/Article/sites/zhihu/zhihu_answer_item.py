#-*- coding:utf-8 -*-
import datetime
import re
import scrapy
from elasticsearch_dsl import connections
from scrapy.loader.processors import MapCompose
from w3lib.html import remove_tags
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Join,Identity
from scrapy.loader import ItemLoader
from Article.items import MysqlItem, EsItem
from Article.settings import SQL_DATETIME_FORMAT
from Article.sites.zhihu.es_zhihu import ZhiHuAnswerIndex
from Article.util.common import extract_num, extract_num_include_dot, real_time_count
from Article.util.es_util import gen_suggests
from Article.util.common import exclude_none

es_zhihu_answer = connections.create_connection(ZhiHuAnswerIndex)


ZHIHU_ANSWER_COUNT_INIT = 0
def get_nums(nums):
    nums = re.match('.*?(\d+).*',nums)
    if nums:
        num = int(nums.group(1))
    else:
        num = 0
    return num


class ZhihuAnswerItem(scrapy.Item, MysqlItem, EsItem):
    url_obj_id= scrapy.Field()
    url= scrapy.Field()
    question_id= scrapy.Field()
    author_id= scrapy.Field()
    answer_id = scrapy.Field()
    content= scrapy.Field()
    praise_num= scrapy.Field()
    comments_num= scrapy.Field()
    create_time= scrapy.Field()
    update_time= scrapy.Field()
    crawl_time= scrapy.Field()
    author_name = scrapy.Field()    
    def clean_data(self):
        try:
            self["praise_num"] = extract_num("".join(self["praise_num"]))
        except BaseException:
            self["praise_num"] = 0
        try: 
            self["comments_num"] = extract_num("".join(self["comments_num"]))
        except BaseException:
            self["comments_num"] = 0
        self["create_time"] = datetime.datetime.fromtimestamp(
            self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        try:
            self["update_time"] = datetime.datetime.fromtimestamp(
                self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        except:
            self["update_time"] = self["create_time"]

        self["crawl_time"] = self["crawl_time"].strftime(SQL_DATETIME_FORMAT)
        self["content"] = remove_tags(self["content"])
    
    def save_to_mysql(self):

        self.clean_data()
        # 插入知乎answer表的sql语句
        insert_sql = """
                   insert into answer(url_obj_id, answer_id, question_id, author_id, author_name,
                   content, praise_num, comments_num,url,create_time,
                   update_time, crawl_time)
                   VALUES (%s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s,
                      %s, %s)
                     ON DUPLICATE KEY UPDATE
                     content=VALUES(content), comments_num=VALUES(comments_num), praise_num=VALUES(praise_num),
                     update_time=VALUES(update_time), author_name=VALUES(author_name)
               """
        sql_params = (
            self["url_obj_id"], self["answer_id"], self["question_id"], self["author_id"], self["author_name"],
            self["content"], self["praise_num"], self["comments_num"], self["url"], self["create_time"],
            self["update_time"], self["crawl_time"]
        )

        return insert_sql, sql_params
    
    def save_to_es(self):
        self.clean_data()
        zhihu = ZhiHuAnswerIndex()

        zhihu.meta.id = self["url_obj_id"]
        zhihu.answer_id = self["answer_id"]
        zhihu.question_id = self["question_id"]
        zhihu.author_id = self["author_id"]
        zhihu.author_name = self["author_name"]
        zhihu.content = self["content"]
        zhihu.praise_num = self["praise_num"]
        zhihu.comments_num = self["comments_num"]
        zhihu.url = self["url"]
        zhihu.create_time = self["create_time"]

        zhihu.update_time = self["update_time"]
        zhihu.crawl_time = self["crawl_time"]

        # 在保存数据时便传入suggest
        zhihu.suggest = gen_suggests(es_zhihu_answer,"zhihu_answer",
                                          ((zhihu.author_name, 10), (zhihu.content, 7)))
        real_time_count("zhihu_answer_count", ZHIHU_ANSWER_COUNT_INIT)
        zhihu.save()


class ZhihuAnswerItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

