#!/usr/bin/env python
# coding: utf-8

# In[23]:


import requests
from bs4 import BeautifulSoup
import numpy as np
import time
import re
import pickle
import os
import pandas as pd
import logging
import datetime


# In[ ]:


#抓出現在日期
date_time=str(datetime.datetime.now()).split(' ')[0]


# In[ ]:


path='C:/Users/1903026/Desktop/log_py/'+date_time+'.txt'
#建立log，紀錄資訊
if os.path.isfile(path):
    logging.basicConfig(level=logging.WARNING,#控制檯列印的日誌級別
                        filename=path,
                        filemode='a') #模式有w和a，w就是寫模式，每次都會重新寫日誌，覆蓋之前的日誌;a是append的意思
else:
    logging.basicConfig(level=logging.WARNING,#控制檯列印的日誌級別
                        filename=path,
                        filemode='w') #模式有w和a，w就是寫模式，每次都會重新寫日誌，覆蓋之前的日誌;a是append的意思


# In[ ]:


#讀取已有資料，找到最新資料時間
D_old=pd.read_csv('C:/Users/1903026/Desktop/apple_news.csv')


# In[121]:


#防爬機制 1
user_agent = [
"Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
"Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
"Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko",
"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
"Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
"Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)"
]


# In[ ]:


#來抓目前及時能抓到的資料
a=requests.get('https://tw.appledaily.com/new/realtime',headers={'User-Agent':np.random.choice(user_agent)})
if a.status_code !=200:
    print('Error QQ,can not access apple news')
else:
    soup=BeautifulSoup(a.text,'lxml')
    page=1
    #如果有下10頁，page=page+10
    #如果沒有，找最後一頁是多少，讓page等於他
    #蘋果不能直接抓到最大頁數，可惡QQ
    while ('下10頁' in re.sub(string=soup.find(class_='page_switch').text,repl='',pattern='\s+')):
        page=page+10
        a=requests.get('https://tw.appledaily.com/new/realtime/'+str(page),
                       headers={'User-Agent':np.random.choice(user_agent)})
        soup=BeautifulSoup(a.text,'lxml')
    temp=[p.get('title') for p in soup.find(class_='page_switch').find_all('a')]
    page=int(temp[len(temp)-1])


# In[ ]:


#收集報導網址
CATE=[]
A_URL=[]

#收集到舊資料X筆，代表開始重複，不繼續收集下去，以url為準(減少爬蟲時間與克服蘋果文章日期會改變的問題)
restricted=100
N=0


# In[ ]:


for i in range(0,page):
    #如果超過限制，代表後來資料皆已收集過，不在收集，跳出迴圈
    if N>restricted:
        print('Now page is {i} and old data contains {N}duplicated observations, Stop!.'.format(i=i,N=N))
        break
    else:
        print('Now page is {i} and old data contains {N}  duplicated observation.'.format(i=i,N=N))
    #收集資料
    a=requests.get('https://tw.appledaily.com/new/realtime/'+str(i+1),
                   headers={'User-Agent':np.random.choice(user_agent)})
    if a.status_code !=200:
        print('Error QQ,can not access apple news')
    else:
        a.encoding='UTF-8'
        soup=BeautifulSoup(a.text,'lxml')
        #抓每個新聞分類，和網址
        try:
            target=soup.find_all('li',class_='rtddt')
        except:
            print('Can not find article information for page '+str(i+1))
            continue
        #save category
        try:
            category=[re.sub(string=s.find('h2').text,pattern='\\u3000|\\xa0',repl='') for s in target]
        except:
            print('Page '+str(i+1)+' is wrong for crawl category,please check')
            category=[]
        #save article url
        try:
            article_url=[s.find('a').get('href') for s in target]
        except:
            print('Page '+str(i+1)+' is wrong for crawl article url,please check')
            article=[]
        if len(article_url) != len(category):
            raise RuntimeError('Big problem for unequal length for category & article_url')
        else:
            CATE.append(category)
            A_URL.append(article_url)
        #判斷現有資料是否已有此網址，紀錄文章次數，超過restricted即停止爬蟲
        N+=len([s for s in D_old.url.isin(article_url) if s==True])
    if i % 5 ==0:
        print(i)
        time.sleep(int(np.random.randint(1,10,1)))


# In[ ]:


#更新實際所需頁面
page=i
#資料格式
D=pd.DataFrame(columns=['url','category','title','publish_time','content','additional'])
#index
n=0


# In[ ]:


#抓取所有內容，轉成結構化資料
for j in range(0,page):
    cate=CATE[j]
    target_url=A_URL[j]
    if len(cate) != len(target_url):
        raise RuntimeError('Big problem for length of category is not equal to article url')
    else:
        for i in range(0,len(cate)):
            n=n+1
            b=requests.get(target_url[i],
                           headers={'User-Agent':np.random.choice(user_agent)})
            if b.status_code !=200:
                print('Problem for url: '+target_url[i])
                continue
            soup2=BeautifulSoup(b.text,'lxml')
            #抓標題
            try:
                title=re.sub(string=soup2.find('h1').text,pattern='\\u3000|\\xa0',repl='')
            except:
                print('Title can not find.Check url: '+target_url[i])
                title=' '
            #抓時間
            try:
                tt=soup2.find(class_='ndArticle_creat').text.split('：')[1]
            except:
                tt=' '
            #抓內文
            try:
                txt=''
                temp=soup2.find('div',class_='ndArticle_margin').select('p,div')
                index1=[i for i,s in enumerate(temp) if (('改寫、轉貼分享，違者必究' in s.text) and i!=0)]
                index1=index1[0]
                temp=temp[0:index1:1]
                #編按可用內容為0，所以不要抓取開頭為編按的文章
                if re.search(string=temp[0].text,pattern='^編按：|^【編者按】') is not None:
                    txt=' '
                else:
                    for s in temp:
                        txt=txt+s.text
                    #防止後來讀取產生NaN
                    if txt == '':
                        txt=' '
                    else:
                        txt=txt
                    #如果有【即時論壇徵稿】後面為無意義雜訊，去除
                    if '【即時論壇徵稿】' in txt:
                        txt=txt[:(txt.find('【即時論壇徵稿】'))]
                    else:
                        txt=txt
                    #去除空格、UTF-16編碼
                    txt=txt.strip()
                    txt=re.sub(string=txt,pattern='\\xa0|\\u3000',repl='')
                    if '報導' in txt:
                        txt=re.search(string=txt,pattern='.+（.+報導）|.+報導|.+\(.+報導\)').group(0)
                    else:
                        #雜訊混進資料
                        if 'Frameborder，' in txt:
                            txt=txt[:txt.find('Frameborder，')]
                        else:
                            txt=txt
            except:
                txt=' '
            #抓額外圖片
            add=''
            #標題圖片
            try:
                additional=soup2.find(class_='ndAritcle_headPic').find('img').get('src')
                add=add+additional+'，'
            except:
                add=add
            #預防抓到很多不要的圖片，例如:編按內文藏了很多不該有的圖片
            if txt == ' ':
                if add=='':
                    add=' '
                else:
                    add=re.sub(string=add,pattern='，',repl='')
            else:
                try:
                    additional=soup2.find('div',class_='ndArticle_margin').find_all('img')
                    additional=[s.get('src') for s in additional]
                    if len(additional)>0:
                        for k in range(0,len(additional)):
                            if k != (len(additional)-1):
                                add=add+additional[k]+'，'
                            else:
                                add=add+additional[k]
                    else:
                        add=re.sub(string=add,pattern='，',repl='')
                except:
                    add=re.sub(string=add,pattern='，',repl='')
                #預防下次讀取NaN產生
                if add == '':
                    add=' '
                else:
                    add=add
            #合併資料
            dd={
               'url':target_url[i],
                'category':cate[i],
                'title':title,
                'publish_time':tt,
                'content':txt,
                'additional':add 
            }
            d=pd.DataFrame(dd,columns=['url','category','title','publish_time','content','additional'],
                           index=[n])
            D=pd.concat([D,d],axis=0)
            time.sleep(int(np.random.randint(1,8,1)))
    print('Current page is '+str(j+1))


# In[ ]:


D_temp=pd.concat([D,D_old],axis=0)
D_temp=D_temp[~D_temp.duplicated(subset=['url','category'])]


# In[ ]:


#神奇編碼，如果僅存utf-8就會變亂碼....
D_temp.to_csv('C:/Users/jaesm14774/Desktop/apple_news.csv',index=0,encoding='utf_8_sig')

