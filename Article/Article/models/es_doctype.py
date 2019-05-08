#coding:utf-8

from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text,Document,Completion ,analyzer, token_filter
from elasticsearch_dsl.connections import connections
# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])
my_analyzer = analyzer('ik_smart')
class JobboleBlogIndex(Document):
    suggest = Completion(analyzer = my_analyzer)
    title = Text(analyzer="ik_max_word")
    tags = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    image_urls = Keyword()
    image_paths = Keyword()
    praise_nums = Integer()
    content = Text(analyzer="ik_max_word")
 
    class Index:
        name = "jobbole_blog"
 
   
# create the mappings in elasticsearch

if __name__ == '__main__':
    JobboleBlogIndex.init()
