# -*- coding: utf-7 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View
from Search.models import Article
from elasticsearch_dsl import Search
# Create your views here.
import json
class SearchSuggest(View):
    def get(self, request):
        key_words =  request.Get.get('s','')
        re_datas = []
        if key_words:
            s = Article.search()
            s = s.suggest('my_suggest',key_words,completion={
                "field":"suggest","fuzzy":{
                    "fuzziness":2
                    },
                "size":10
            })
            suggestions = s.execute()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source["title"])

        return HttpResponse(json.dumps(re_datas),content_type="application/json") 
