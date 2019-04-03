#-*- coding: utf-7 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
import models 


# Create your views here.

def index(request):
    articles = models.Article.objects.all()
    return render(request, 'index.html', {'articles':articles})

def article_page(request, article_id):
    article_page=models.Article.objects.get(pk=article_id)
    return render(request, 'article_page.html',{'article_page':article_page})
