# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text,Document,Completion ,analyzer, token_filter
from elasticsearch_dsl.connections import connections
# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])
my_analyzer = analyzer('ik_smart')
class JobboleBlogIndex(Document):
    suggest = Completion(analyzer=my_analyzer)
    title = Text(analyzer="ik_max_word")
    tags = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    image_urls = Keyword()
    image_paths = Keyword()
    praise_nums = Integer()
    content = Text(analyzer="ik_smart")

    class Index:
        name = "jobbole_blog"

class LagouJobIndex(Document):
    """拉勾网工作职位"""
    suggest = Completion(analyzer=my_analyzer)
    title = Text(analyzer="ik_max_word")
    url = Keyword()
    url_object_id = Keyword()
    salary_min = Integer()
    salary_max = Integer()
    job_city = Keyword()
    work_years_min = Integer()
    work_years_max = Integer()
    degree_need = Text(analyzer="ik_max_word")
    job_type = Keyword()
    publish_time = Date()
    job_advantage = Text(analyzer="ik_max_word")
    job_desc = Text(analyzer="ik_smart")
    job_addr = Text(analyzer="ik_max_word")
    company_name = Keyword()
    company_url = Keyword()
    tags = Text(analyzer="ik_max_word")
    crawl_time = Date()

    class Index:
        name = 'lagou'


class ZhiHuQuestionIndex(Document):
    """知乎问题"""
    suggest = Completion(analyzer=my_analyzer)

    question_id = Keyword()
    topics = Text(analyzer="ik_max_word")
    url = Keyword()
    title = Text(analyzer="ik_max_word")

    content = Text(analyzer="ik_max_word")
    answer_num = Integer()
    comments_num = Integer()
    watch_user_num = Integer()
    click_num = Integer()

    crawl_time = Date()

    class Index:
        name = 'zhihu_question'


class ZhiHuAnswerIndex(Document):
    """知乎回答"""
    suggest = Completion(analyzer=my_analyzer)

    answer_id = Keyword()
    question_id = Keyword()
    author_id = Keyword()
    author_name = Keyword()

    content = Text(analyzer="ik_smart")
    praise_num = Integer()
    comments_num = Integer()
    url = Keyword()
    create_time = Date()

    update_time = Date()
    crawl_time = Date()

    class Index:
        name = 'zhihu_answer'
# create the mappings in elasticsearch

if __name__ == '__main__':
    JobboleBlogIndex.init()
    ZhiHuQuestionIndex.init()
    ZhiHuAnswerIndex.init()
