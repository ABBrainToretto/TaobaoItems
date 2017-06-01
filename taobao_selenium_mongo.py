# -*- coding: UTF-8 -*-
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import re
import sys
import pymongo
from config import *

reload(sys) # Python2.5 初始化后会删除 sys.setdefaultencoding 这个方法，我们需要重新载入
sys.setdefaultencoding('utf-8')

browser = webdriver.Firefox()#使用Chrome浏览器
wait=WebDriverWait(browser, 10)
client= pymongo.MongoClient(MONGO_URL,connect=False)#申明一个mongo对象，需要传入MONGO_URL,False表明每个进程在执行的时候启动mongodb的连接
db=client[MONGO_DB]

#用来打开网页
def search():
    try:
        browser.get('http://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))#'#J_TSearchForm > div.search-button > button'这些需要根据具体的网页具体分析
        input.send_keys(KEYWORD)
        submit.click()
        total=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()

#自动将下一页的页码填入空格，自动进行翻页
def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)

#获取该商品的所有信息
def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))#'#'代表id
    html = browser.page_source
    doc=pq(html)
    items=doc('#mainsrp-itemlist .items .item').items()

    for item in items:
        if item.find('.pic .img').attr('src'):
            product={
                'image':item.find('.pic .img').attr('src'),#获取商品照片
                'id':re.findall(r"(\d+)",item.find('.pic .img').attr('id'),re.S)[0],#获取商品在淘宝上的（唯一）编号
                'price':float(re.findall(r"(\d+\.\d+)",item.find('.price').text(), re.S)[0]),#获取商品单价
                'deal':float(item.find('.deal-cnt').text()[:-3]),#获取商品成交量
                'title':item.find('.title').text().replace(' ',''),#获取商品标题
                'shop':item.find('.shop').text(),#获取商品所属的店铺信息
                'location':item.find('.location').text()#获取店铺的位置信息
            }
            save_to_mongo(product)

#将爬取的商品信息存入本地mongo数据库中
def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print(u'存储到MongoDB成功')
        print (result)
        return True
    return False

def main():
    total=search()
    total=int(re.compile('(\d+)').search(total).group(1))
    for i in range(2,total+1):
        next_page(i)#显示当前爬取网页的页数
        print ('搞定%d'%i)

if __name__=='__main__':
    main()
