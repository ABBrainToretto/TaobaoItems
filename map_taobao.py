# -*- coding: UTF-8 -*-
import csv
import re
import urllib2
from pymongo import MongoClient

##--------链接数据库----------##
conn=MongoClient('localhost')
db=conn.taobao #链接数据库
db=db.taobao #连接库中的taobao表

##--------获取mongo中每条记录的'location'----------##
def get_list():
    f=db.find()
    for tea in f:
        yield str(tea['location'].replace(' ','').encode("utf-8"))

#调用百度api获取经纬度，注意在地名后添加"市"，因为有些时候单纯的地名会返回空值，比如"上海"，这是百度的bug
def getLocation(name):
    url= 'http://api.map.baidu.com/geocoder?address=%s%s&output=html'%(name,'市')
    html = urllib2.urlopen(urllib2.Request(url)).read()
    sub = re.compile(r'"location":\{"lat":(\d+),"lng":(\d+)\}',re.S)
    lat_lng = re.findall(sub,html)
    # print lat_lng[0][0],lat_lng[0][1]
    return lat_lng[0]

##---------输出csv文件，方便导入地图中----------##
def main():
    i=0
    with open('tea.csv', 'w') as csvfile:
        fieldnames=['name','longitude','latitude']
        writer=csv.DictWriter(csvfile,fieldnames=fieldnames)
        writer.writeheader()

        for place in get_list():
            a=getLocation(place)
            if a[0]:   #为了排除一些空值，因为记录中有些是"日本"，"英国"等地名，无法正常返回
                writer.writerow({'name':place,'longitude':str(a[1]),'latitude':str(a[0])})
                i+=1
                print i
            else:
                print (place)
                i+=1

if __name__=='__main__':
    main()
