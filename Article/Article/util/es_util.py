#encoding:utf-8

def gen_suggests(es_con,index, info_tuple):
    #根据字符串生成搜索建议数组
    es = es_con
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

