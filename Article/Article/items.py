# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from util.common import extract_num
from scrapy.loader import ItemLoader
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Join,Identity
import re
import datetime
from w3lib.html import remove_tags
from settings import  SQL_DATETIME_FORMAT,SQL_DATE_FORMAT
from util.es_doctype import Article
from elasticsearch_dsl.connections import connections
es = connections.create_connection(hosts=['localhost'])
def remove_comment_tags(value):
    #去掉tag中提取的评论
    if u"评论" in value:
        return ""
    else:
        return value


def gen_suggests(index, info_tuple):
    #根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            words = es.indices.analyze(index=index,body={'text':text,'analyzer':"ik_max_word",'filter':["lowercase"]})
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words = anylyzed_words - used_words
        else:     
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words), "weight":weight})

    return suggests
class ArticleItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

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

class JobboleArticleItem(scrapy.Item):
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
    def get_insert_sql(self):
        insert_sql = """
            insert into article(url_obj_id, title, url, create_date, praisenum)
            VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content=VALUES(praisenum)
        """


        params = (self['url_obj_id'],self["title"], self["url"], self["create_date"], self["praisenum"])

        return insert_sql, params

    def save_to_es(self):
        article = Article()
        article.title = self['title']
        article.create_date = self["create_date"]
        article.content = remove_tags(self["content"])
        article.image_urls = self["image_urls"]
        if "image_paths" in self:
            article.image_paths = self["image_paths"]
        article.praise_nums = self["praisenum"]
        article.url = self["url"]
        article.meta.id = self["url_obj_id"]
        article.suggest = gen_suggests(Article.Index.name, ((article.title,10),(article.tags, 7)))
        article.save()


        return

def get_salary_min(value):
    match_re = '(\d+)\w-(\d+)\w'
    re_str = re.match(match_re,value)
    if re_str:
        return re_str.group(1)
    else:
        return ["none"]

def get_salary_max(value):
    match_re = '(\d+)\w-(\d+)\w'
    re_str = re.match(match_re,value) 
    if re_str:
        return re_str.group(2)
    else:
        return ["none"]


class LagouJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


def remove_splash(value):
    #去掉工作城市的斜线
    return value.replace("/","")

def get_workyears_min(value):
    match_year = ".*?(\d+)-(\d+).*?"
    result = re.match(match_year,value)
    if result:
        return result.group(1)
    else:
        return 0
def get_workyears_max(value):
    match_year = ".*?(\d+)-(\d+).*?"
    result = re.match(match_year,value)
    if result:
        return result.group(2)
    else:
        return 0

def get_degree(value):
    result = re.match("(.{2}).*?",value)
    if result:
        return result.group(1)
    else:
        return ["no forbiddeN"]


def get_publishtime(publish_time):
    if u"天" in publish_time:
        match_re =  "(\d+).*?"
        result = re.match(match_re,publish_time)
        days = result.group(1)
        date = datetime.datetime.now() - datetime.timedelta(int(days))
        return date.date()
    elif ":" in publish_time:
        return datetime.datetime.now().date()
    elif "-" in publish_time:
        return publish_time

def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip()!=u"查看地图"]
    return "".join(addr_list)
    



class LagouJobItem(scrapy.Item):
    url = scrapy.Field()
    url_obj_id = scrapy.Field()
    title = scrapy.Field()


    salary_min = scrapy.Field(
            input_processor = MapCompose(get_salary_min)
            )
    salary_max = scrapy.Field(
            input_processor = MapCompose(get_salary_max)
            )
    
    job_city = scrapy.Field(

            input_processor = MapCompose(remove_splash)
            )
    work_years_min = scrapy.Field(
            input_processor = MapCompose(remove_splash,get_workyears_min)
            )
    work_years_max = scrapy.Field(
            input_processor = MapCompose(remove_splash,get_workyears_max)

            )
    degree_need = scrapy.Field(

            input_processor=MapCompose(remove_splash,get_degree))
    tags = scrapy.Field(

            output_processor=Join()
            )
    publish_time = scrapy.Field(

            input_processor = MapCompose(get_publishtime)
            )
    job_addr = scrapy.Field(

           input_processor = MapCompose(remove_tags,handle_jobaddr) 
            )
    company_url = scrapy.Field(
 
            )

    company_name = scrapy.Field(
  
            )
    crawl_time = scrapy.Field(
   
            )
    crawl_update_time = scrapy.Field(
    
            )
    job_type = scrapy.Field(
     
            )
    job_advantage = scrapy.Field(
      
            )
    job_desc = scrapy.Field(
       
            )
    def get_insert_sql(self):
     
        insert_sql = """
            insert into lagou_job(title, url, url_obj_id, salary_min,salary_max, job_city, work_years_min,work_years_max, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_name, company_url,
            tags, crawl_time) VALUES (%s, %s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE salary_min=VALUES(salary_min), salary_max=VALUES(salary_max),job_desc=VALUES(job_desc)
        """
        params = (
            self["title"],self["url"], self["url_obj_id"], self["salary_min"],self["salary_max"], self["job_city"],
            self["work_years_min"],self["work_years_max"], self["degree_need"], self["job_type"],
            self["publish_time"], self["job_advantage"], self["job_desc"],
            self["job_addr"], self["company_name"], self["company_url"],
            self["tags"], self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )
       
        return insert_sql,params



class ZhihuQuestionItemLoader(ItemLoader):
    default_output_processor = TakeFirst()

class ZhihuAnswerItemLoader(ItemLoader):
    default_output_processor = TakeFirst()




class ZhihuQuestionItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    zhihu_id = scrapy.Field()
    
    topics= scrapy.Field()
    answer_num= scrapy.Field(
        input_processor=MapCompose(get_nums)
        )
    comments_num= scrapy.Field(
        input_processor=MapCompose(get_nums)    
            )
    watch_user_num= scrapy.Field(
            input_processor = MapCompose(lambda x : int(x.replace(',',"")))            
            )
    click_num= scrapy.Field(
            input_processor = MapCompose(lambda x : int(x.replace(',',"")))            
            )
    crawl_time= scrapy.Field()
    update_time= scrapy.Field()
    create_time= scrapy.Field()
    crawl_update_time= scrapy.Field()
    content= scrapy.Field()

    def get_insert_sql(self):
        #插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_questions(zhihu_id, topics, url, title, content, answer_num, comments_num,
              watch_user_num, click_num, crawl_time
              )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
              watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
        """
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))
        '''
        if len(self["watch_user_num"]) == 2:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = int(self["watch_user_num"][1])
        else:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = 0
        '''
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num,
                  self["watch_user_num"], self["click_num"], crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    zhihu_id= scrapy.Field()
    url= scrapy.Field()
    question_id= scrapy.Field()
    author_id= scrapy.Field()
    content= scrapy.Field()
    praise_num= scrapy.Field()
    comments_num= scrapy.Field()
    create_time= scrapy.Field()
    update_time= scrapy.Field()
    crawl_time= scrapy.Field()
    crawl_update_time= scrapy.Field()

    def get_insert_sql(self):
        #插入知乎question表的sql语句
        insert_sql = """
            insert into answer(zhihu_id, url, question_id, author_id, content, praise_num, comments_num,
              create_time, update_time, crawl_time
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), praise_num=VALUES(praise_num),
              update_time=VALUES(update_time)
        """

        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["praise_num"],
            self["comments_num"], create_time, update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql, params


