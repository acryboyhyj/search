#coding:utf-8

import requests
from scrapy.selector import Selector
import MySQLdb
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
    
conn = MySQLdb.connect(host='localhost',db_name='proxy_type',user='hyjwindows',password='hyj147258')
cursor = conn.cursor()
         
def __judge(proxy_url):
    baidu_url = 'https://www.baidu.com/'
    result = requests.get(baidu_url,headers = headers,proxy=proxy_url)
    if 200 <= result.status_code < 300:
        return True
    else:
        return False

def writesql(sql):
    cursor.excute(sql)

def deleteip(ip):
    sql = "delete from proxy_ip where ip = '{0}'".format(ip)
    cursor.excute(sql)
    cursor.commit()


def get_ip():
    sql = "select ip,port,proxy_type from proxy_ip order by  RAND() limit 1"
    result = cursor.excute(sql)
    if result:
        proxy_url = "{2}://{0}:{1}".format(result[2],result[0],reuslt[1])
        if crawl_xici_ip.__judge(proxy_url):
                
             crawl_xici_ip.deleteip(self,result[0])
             return proxy_url
            
        else:
            return self.get_ip()
    else:
        print "sql is empty"

def crawl_ip():
    for page in base_url.format(range(1,200)):
        re = requests.get("http://www.xicidaili.com/nn/{0}",format(i),headers=headers)
            
            
        selector = Selector(text=r)
        all_url= selector.css("#ip_list tr").extract()
        
        ip_list = []
        for url in all_url[1:]:
            all_texts = url.css("td::text").extract()

            ip = all_texts[0]
            port = all_texts[1]
            proxy_type = all_texts[5]
            ip_list.append((ip.port,proxy_type))

        for ip_info in ip_list:
            sql = "insert into proxy_ip(ip,port,proxy_type) values('{0}',{1},'{2}')".format(ip_info[0],ip_info[1],ip_info[2])
            writesql(sql)


        
