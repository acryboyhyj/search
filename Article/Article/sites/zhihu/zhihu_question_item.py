#-*- coding:utf-8
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
from Article.sites.zhihu.es_zhihu import ZhiHuQuestionIndex
from Article.util.common import extract_num, extract_num_include_dot, real_time_count
from Article.util.es_util import gen_suggests
from Article.util.common import exclude_none


ZHIHU_QUESTION_COUNT_INIT = 0
es_zhihu_question = connections.create_connection(ZhiHuQuestionIndex)
def get_nums(nums):
    nums = re.match('.*?(\d+).*',nums)
    if nums:
        num = int(nums.group(1))
    else:
        num = 0
    return num


class ZhihuQuestionItem(scrapy.Item, MysqlItem, EsItem):
    url_obj_id = scrapy.Field()
    title = scrapy.Field()
    question_id = scrapy.Field()
    url = scrapy.Field()
    topics= scrapy.Field()
    answer_num= scrapy.Field(
        input_processor=MapCompose(get_nums)
        )
    comments_num= scrapy.Field()
    watch_user_num= scrapy.Field()
    click_num= scrapy.Field()
    crawl_time= scrapy.Field()
    update_time= scrapy.Field()
    create_time= scrapy.Field()
    crawl_update_time= scrapy.Field()
    content= scrapy.Field(
            input_processor = MapCompose(exclude_none))
    
    def clean_data(self):
        self["question_id"] = self["question_id"]
        self["topics"] = ",".join(self["topics"])
        self["url"] = self["url"]
        self["title"] = "".join(self["title"])
        try:
            self["content"] = "".join(self["content"])
            self["content"] = remove_tags(self["content"])
        except BaseException:
            self["content"] = "无"
        try:
            self["answer_num"] = extract_num("".join(self["answer_num"]))
        except BaseException:
            self["answer_num"] = 0
        self["comments_num"] = extract_num("".join(self["comments_num"]))

        if len(self["watch_user_num"]) == 2:
            watch_user_num_click = self["watch_user_num"]
            self["watch_user_num"] = extract_num_include_dot(watch_user_num_click[0])
            self["click_num"] = extract_num_include_dot(watch_user_num_click[1])
        else:
            watch_user_num_click = self["watch_user_num"]
            self["watch_user_num"] = extract_num_include_dot(watch_user_num_click[0])
            self["click_num"] = 0

        self["crawl_time"] = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

    def save_to_es(self):
        self.clean_data()
        zhihu = ZhiHuQuestionIndex()
        zhihu.question_id = self["question_id"]
        zhihu.title = self["title"]
        zhihu.content = self["content"]
        zhihu.topics = self["topics"]

        zhihu.answer_num = self["answer_num"]
        zhihu.comments_num = self["comments_num"]
        zhihu.watch_user_num = self["watch_user_num"]
        zhihu.click_num = self["click_num"]
        zhihu.url = self["url"]

        zhihu.crawl_time = self["crawl_time"]

        # 在保存数据时便传入suggest
        zhihu.suggest = gen_suggests(es_zhihu_question,"zhihu_question",
                                          ((zhihu.title, 10), (zhihu.topics, 7), (zhihu.content, 5)))

        real_time_count('zhihu_question_count', ZHIHU_QUESTION_COUNT_INIT)
        zhihu.save()


    def save_to_mysql(self):
        insert_sql = """
                   insert into zhihu_questions(url_obj_id,question_id, title, content,topics,
                    answer_num, comments_num,watch_user_num, click_num, url,
                     crawl_time
                     )
                   VALUES (%s, %s, %s, %s, %s
                   , %s, %s, %s, %s, %s,
                   %s)
                   ON DUPLICATE KEY UPDATE
                   content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
                   watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
               """
        self.clean_data()
        sql_params = (
            self['url_obj_id'], self["question_id"], self["title"], self["content"], self["topics"],
            self["answer_num"], self["comments_num"], self["watch_user_num"], self["click_num"], self['url'],
            self["crawl_time"])

        return insert_sql, sql_params
    

class ZhihuQuestionItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


