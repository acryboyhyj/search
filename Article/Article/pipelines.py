# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.http import Request
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy.exporters import JsonItemExporter
import json
import jsonpickle
import codecs
import MySQLdb
from twisted.enterprise import adbapi
import MySQLdb.cursors
class ArticlePipeline(object):
    def process_item(self, item, spider):
        return item


class DefaultValuesPipeline(object):

    def process_item(self, item, spider):
        for k in item.fields:
            item.setdefault(k,"default")
        
        return item


class JobboleArticleImagePipeline(ImagesPipeline):
        
    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        item['image_paths'] = image_paths
        return item
#custion own json file to store result 
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('Article.json','w',encoding='utf-8')
    
    def process_item(self, item, spider):
        lines = jsonpickle.encode(item) + "\n"
        
        self.file.write(lines)
        return item
    
    def spider_closed(self, spider):
        self.file.close()

#use scrapy's jsonexpoter
class JsonExpoterPipeline(object):
    def __init__ (self):
        self.file = open('Articleexport.json','wb',)
        self.exporter = JsonItemExporter(self.file,encoding='utf-8',ensure_ascii=False)
        self.exporter.start_exporting()
    def spider_closed(self,spider):
        self.exporter.finish_exporting()

class MysqlPipeline(object):
    """ write data to mysql"""
    def __init__(self):
       self.conn = MySQLdb.connect('localhost','hyjwindows','hyj147258','Article', charset='utf8')
       self.cursor = self.conn.cursor()

    def process_item(self,item, spider):
        insert_sql = "insert into article(url_obj_id,title,url,create_date) VALUES('{0}','{1}','{2}','{3}')"\
                .format(item['url_obj_id'], item['title'].encode('utf8'), item['url'].encode('utf8'), item['create_date'])
                
        self.cursor.execute(insert_sql)
        self.conn.commit()

class MysqlTwistedPipline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) #处理异常

    def handle_error(self, failure, item, spider):
        #处理异步插入的异常
        print (failure)
    def do_insert(self, cursor, item):
        #执行具体的插入
        #根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)


class EsPipeline():
    def process_item(self, item, spider):
        #将item转换为es的数据
        item.save_to_es()

        return item
