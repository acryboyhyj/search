#encoding:utf-8

import scrapy
from abc import ABCMeta, abstractmethod

class ArticleItem(scrapy.Item):                                            
    pass

class BaseItem(object):

    field_list= []

    @abstractmethod
    def clean_data(self):
        pass
    @staticmethod
    @abstractmethod 
    def help_fields(fields):

        pass


class MysqlItem(BaseItem):
    table_name = ""
    duplicate_update = []

    @abstractmethod 
    def save_to_mysql(self):
        pass

class EsItem(BaseItem):
    @abstractmethod
    def save_to_es(self):
        pass
