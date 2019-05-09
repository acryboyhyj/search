# -*- coding: utf-8 -*-
import scrapy
import re
from urlparse import urljoin
from scrapy import Request
from Article.util.common import get_md5
import datetime
from Article.sites.zhihu.zhihu_item import ZhihuQuestionItemLoader
from Article.sites.zhihu.zhihu_item import ZhihuAnswerItemLoader
from Article.sites.zhihu.zhihu_item import ZhihuQuestionItem
from Article.sites.zhihu.zhihu_item import ZhihuQuestionItem
from Article.sites.zhihu.zhihu_item import ZhihuAnswerItem

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pickle
import json


class SspiderSpider(scrapy.Spider):
    name = 'zhihu'
    start_urls = [
        'https://www.zhihu.com/',
    ]
    allowed_domins = ['www.zhihu.com']
    custom_settings = { 
        "COOKIES_ENABLED":True,
        "DOWNLOAD_DELAY" : 5,
    }
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B*%5D.topics&offset{1}=&limit={2}&sort_by=default&platform=desktop"
    
    @staticmethod
    def judge_login(browser):
        try:
    
            notify_ele = browser.find_element_by_class_name("PushNotifications-count")
            return True
        except:
            return False
    
    
    @staticmethod
    def writecookies(browser):
        import os,sys
        Cookies = browser.get_cookies()
        cookie_dict = {}
        cookie_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        cookie_dir = os.path.join(cookie_dir,"cookie")
        sys.path.insert(0,cookie_dir)
        for cookie in Cookies:
        # 写入文件
       
      
            file_path = os.path.join(cookie_dir,cookie['name']+ '.txt') 
     
            f = open(str(file_path), "wb")
                
            pickle.dump(cookie, f)
            f.close()
            cookie_dict[cookie['name']] = cookie['value']
        return cookie_dict
    
    
    @staticmethod
    def try_login(browser):
        browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(Keys.CONTROL + "a")
        browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys("17774014040")
        browser.find_element_by_css_selector(".SignFlow-password input").send_keys(Keys.CONTROL + "a")
        browser.find_element_by_css_selector(".SignFlow-password input").send_keys("huangyunjin")
        browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
        time.sleep(10)

    def start_requests(self):
        chrome_option = Options()
        chrome_option.add_argument("--disable-extensions")
        chrome_option.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        browser = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver",
                                   chrome_options=chrome_option)

        try:
            browser.maximize_window()
        except:
            pass
        browser.get("https://www.zhihu.com/signin")

        time.sleep(10)
        login_success = SspiderSpider.judge_login(browser)
        
        if not login_success:
   
            while not login_success:
                SspiderSpider.try_login(browser)
                login_success = SspiderSpider.judge_login(browser)
            
            
            cookie_dict = SspiderSpider.writecookies(browser)
            browser.close()
            return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict)]

        else:
            cookie_dict = SspiderSpider.writecookies(browser)
            browser.close()
            return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict)]


            
    def parse(self,response):
        

        all_url = response.css("a::attr(href)").extract()
        all_url = [urljoin(response.url,url) for url in all_url]
        all_url = filter(lambda x: True if x.startswith("https://www.zhihu.com") else False,all_url)
        match_re = "(.*zhihu.com/question/(\d+))(/|$).*"
        
        for url in all_url:
            result =  re.match(match_re,url)
            if result:
                #如果提取到question相关的页面则下载后交由提取函数进行提取
                request_url = result.group(1)
                yield scrapy.Request(request_url,  callback=self.parse_question)
            else:
                #如果不是question页面则直接进一步跟踪
                yield scrapy.Request(url, callback=self.parse)
     
    def parse_question(self, response):
      
     
        question_item_loader = ZhihuQuestionItemLoader(item = ZhihuQuestionItem(), response = response)
        question_item_loader.add_value("url_obj_id", get_md5(response.url))
        question_item_loader.add_value("url",response.url)
        question_item_loader.add_css("title",".QuestionHeader-title::text")
        match_re = "(.*zhihu.com/question/(\d+))(/|$).*"

        result = re.match(match_re,response.url)
        if result:
            question_id = result.group(2)

        question_item_loader.add_value("question_id",question_id)
        question_item_loader.add_css("answer_num",".QuestionMainAction ViewAll-QuestionMainAction::text")
        question_item_loader.add_css("content", ".QuestionHeader-detail")
        question_item_loader.add_css("comments_num",".QuestionHeader-Comment button::text")
        question_item_loader.add_css("watch_user_num",".NumberBoard-itemInner strong::text")
        question_item_loader.add_css("click_num",".NumberBoard-itemName strong::text")
        question_item_loader.add_css("topics", ".Popover div::text")
        question_item_loader.add_value("crawl_time", datetime.datetime.now())

        answer_url = response.xpath("//a[@class='UserLink-link']/@href")
        question_item = question_item_loader.load_item()
        yield question_item  
        yield scrapy.Request(self.start_answer_url.format(question_id, 0, 20), callback=self.parse_answer)

        
    def parse_answer(self, response):
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        #提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["url_obj_id"] = get_md5(url=answer["url"])
            answer_item["answer_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["author_name"] = answer["author"]["name"] if "name" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else ""
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, callback=self.parse_answer)

