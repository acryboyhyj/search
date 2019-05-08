#encoding:utf-8
import datetime
import re
import scrapy
from elasticsearch_dsl import connections
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
from Article.items import MysqlItem, EsItem
from Article.settings import SQL_DATETIME_FORMAT
from Article.sites.lagou.es_lagou import LagouJobIndex
from Article.util.common import real_time_count
from Article.util.es_util import gen_suggests

es_lagou_job = connections.create_connection(LagouJobIndex)
JOB_COUNT_INIT = 0

def remove_splash(value):
    #去掉工作城市的斜线
    return value.replace("/","")


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
    

class LagouJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class LagouJobItem(scrapy.Item, MysqlItem, EsItem):
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
            input_processor = MapCompose(remove_splash)
            )
    work_years_max = scrapy.Field(
            input_processor = MapCompose(remove_splash)

            )
    degree_need = scrapy.Field(

            input_processor=MapCompose(remove_splash,get_degree))
    tags = scrapy.Field(

            output_processor=Join(",")
            )
    publish_time = scrapy.Field()
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

    def clean_data(self):
        try:
            self["tags"] = self["tags"]
        except KeyError:
            self["tags"] = ""

        match_obj1 = re.match("经验(\d+)-(\d+)年", self['work_years_min'])
        match_obj2 = re.match("经验应届毕业生", self['work_years_min'])
        match_obj3 = re.match("经验不限", self['work_years_min'])
        match_obj4 = re.match("经验(\d+)年以下", self['work_years_min'])
        match_obj5 = re.match("经验(\d+)年以上", self['work_years_min'])

        if match_obj1:
            self['work_years_min'] = match_obj1.group(1)
            self['work_years_max'] = match_obj1.group(2)
        elif match_obj2:
            self['work_years_min'] = 0.5
            self['work_years_max'] = 0.5
        elif match_obj3:
            self['work_years_min'] = 0
            self['work_years_max'] = 0
        elif match_obj4:
            self['work_years_min'] = 0
            self['work_years_max'] = match_obj4.group(1)
        elif match_obj5:
            self['work_years_min'] = match_obj4.group(1)
            self['work_years_max'] = match_obj4.group(1) + 100
        else:
            self['work_years_min'] = 999
            self['work_years_max'] = 999
    
        match_time1 = re.match("(\d+):(\d+).*", self["publish_time"])
        match_time2 = re.match("(\d+)天前.*", self["publish_time"])
        match_time3 = re.match("(\d+)-(\d+)-(\d+)", self["publish_time"])
        if match_time1:
            today = datetime.datetime.now()
            hour = int(match_time1.group(1))
            minutues = int(match_time1.group(2))
            time = datetime.datetime(
                today.year, today.month, today.day, hour, minutues)
            self["publish_time"] = time.strftime(SQL_DATETIME_FORMAT)
        elif match_time2:
            days_ago = int(match_time2.group(1))
            today = datetime.datetime.now() - datetime.timedelta(days=days_ago)
            self["publish_time"] = today.strftime(SQL_DATETIME_FORMAT)
        elif match_time3:
            year = int(match_time3.group(1))
            month = int(match_time3.group(2))
            day = int(match_time3.group(3))
            today = datetime.datetime(year, month, day)
            self["publish_time"] = today.strftime(SQL_DATETIME_FORMAT)
        else:
            self["publish_time"] = datetime.datetime.now(
            ).strftime(SQL_DATETIME_FORMAT)
    

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
    
    def save_to_es(self):
        self.clean_data()
        job = LagouJobIndex()
        job.title = self["title"]
        job.url = self["url"]
        job.meta.id = self["url_obj_id"]
        job.salary_min = self["salary_min"]
        job.salary_max = self["salary_max"]
        job.job_city = self["job_city"]
        job.work_years_min = self["work_years_min"]
        job.work_years_max = self["work_years_max"]
        job.degree_need = self["degree_need"]
        job.job_desc = remove_tags(self["job_desc"]).strip().replace("\r\n", "").replace("\t", "")
        job.job_advantage = self["job_advantage"]
        job.tags = self["tags"]
        job.job_type = self["job_type"]
        job.publish_time = self["publish_time"]
        job.job_addr = self["job_addr"]
        job.company_name = self["company_name"]
        job.company_url = self["company_url"]
        job.crawl_time = self['crawl_time']

        job.suggest = gen_suggests(es_lagou_job,"lagou",
                                        ((job.title, 10), (job.tags, 7), (job.job_advantage, 6), (job.job_desc, 3),
                                         (job.job_addr, 5), (job.company_name, 8), (job.degree_need, 4),
                                         (job.job_city, 9)))
        real_time_count('lagou_job_count', JOB_COUNT_INIT)
        job.save()



