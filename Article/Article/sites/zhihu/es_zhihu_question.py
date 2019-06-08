#encoding:utf-8

from elasticsearch_dsl import connections, Document, Keyword, Text, Integer, Date, Completion, analyzer

connections.create_connection(hosts=["localhost"])

my_analyzer = analyzer('ik_smart')
class ZhiHuQuestionIndex(Document):
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

if __name__ == "__main__":
    ZhiHuQuestionIndex.init()
 
