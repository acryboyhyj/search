#encoding:utf-8

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
from Article.sites.zhihu.es_zhihu import ZhiHuQuestionIndex, ZhiHuAnswerIndex
from Article.util.common import extract_num, extract_num_include_dot, real_time_count
from Article.util.es_util import gen_suggests
from Article.util.common import exclude_none

es_zhihu_question = connections.create_connection(ZhiHuQuestionIndex)
es_zhihu_answer = connections.create_connection(ZhiHuAnswerIndex)
ZHIHU_QUESTION_COUNT_INIT = 0
ZHIHU_ANSWER_COUNT_INIT = 0


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
        self["question_id"] = self["question_id"][0]
        self["topics"] = ",".join(self["topics"])
        self["url"] = self["url"][0]
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



        def sava_to_mysql(self):
            #插入知乎question表的sql语句
            insert_sql = """
                insert into zhihu_questions(url_obj_id,question_id, topics, url, title, content, answer_num, comments_num,
              watch_user_num, click_num, crawl_time
              )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
              watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
        """
            self.clean_data()
            params = (self['url_obj_id'],self['question_id'], self['topics'], self['url'], self['title'], self['content'],self['answer_num'], self['comments_num'],
                  self["watch_user_num"], self["click_num"],self['crawl_time'])

            return insert_sql, params

        def save_to_es(self):
            self.clean_data()
            zhihu = ZhiHuQuestionIndex()
            zhihu.meta.id = self["url_ob_id"]
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
    
    def clean_data(self):
        try:
            self["praise_num"] = extract_num("".join(self["praise_num"]))
        except BaseException:
            self["praise_num"] = 0
        self["comments_num"] = extract_num("".join(self["comments_num"]))

        self["create_time"] = datetime.datetime.fromtimestamp(
            self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        try:
            self["update_time"] = datetime.datetime.fromtimestamp(
                self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        except:
            self["update_time"] = self["create_time"]

        self["crawl_time"] = self["crawl_time"].strftime(SQL_DATETIME_FORMAT)
        self["content"] = remove_tags(self["content"])

    def save_to_es(self):
        self.clean_data()
        zhihu = ZhiHuAnswerIndex()

        zhihu.meta.id = self["url_obj_id"]
        zhihu.answer_id = self["answer_id"]
        zhihu.question_id = self["question_id"]
        zhihu.author_id = self["author_id"]

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
        real_time_count("zhihu_answer_count", ZHIHU_QUESTION_COUNT_INIT)
        zhihu.save()


class ZhihuQuestionItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

class ZhihuAnswerItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

