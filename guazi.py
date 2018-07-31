import math
import re
from concurrent.futures import ThreadPoolExecutor

import requests
import lxml
import lxml.etree


# 获取网页源代码
def getHtml(url, header):
    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()
        return response.content.decode('utf-8')
    except:
        return ''


# 获取翻页url
def getPageUrl(url, response):
    mytree = lxml.etree.HTML(response)
    # 页码
    carNum = mytree.xpath('//*[@id="post"]/p[3]/text()')[0]
    carNum = math.ceil(int(re.findall('(\d+)', carNum)[0]) / 40)
    urlList = url.rsplit('/', maxsplit=1)
    pageUrlList = []
    if carNum != 0:
        for i in range(1, carNum + 1):
            pageUrl = urlList[0] + "/o" + str(i) + "/" + urlList[1]
            pageUrlList.append(pageUrl)

    return pageUrlList


# 获取汽车品牌
def getCarBrand(response):
    mytree = lxml.etree.HTML(response)
    # 汽车品牌url
    carBrandUrl = mytree.xpath('//div[@class="dd-all clearfix js-brand js-option-hid-info"]/ul/li/p/a/@href')
    # 汽车品牌名
    carBrandName = mytree.xpath('//div[@class="dd-all clearfix js-brand js-option-hid-info"]/ul/li/p/a/text()')

    carBrandDict = {}
    for i in range(len(carBrandName)):
        carBrandDict[carBrandName[i]] = "https://www.carHome.com" + carBrandUrl[i]

    return carBrandDict


# 获取汽车信息
def getCarInfo(pageUrl, carBrandName):
    response = getHtml(pageUrl, header)
    mytree = lxml.etree.HTML(response)
    for i in range(40):
        # 汽车名称
        carName = mytree.xpath('//ul[@class="carlist clearfix js-top"]/li/a/h2/text()')[i]
        # 汽车图片
        carPic = mytree.xpath('//ul[@class="carlist clearfix js-top"]/li/a/img/@src')[i]
        carPic = carPic.rsplit("jpg", maxsplit=1)[0] + 'jpg'
        # 汽车出产年份、里程数
        carInfo = mytree.xpath('//ul[@class="carlist clearfix js-top"]/li/a/div[1]/text()')[i]
        # 现价
        carCurrentPrice = mytree.xpath('//ul[@class="carlist clearfix js-top"]/li/a/div[2]/p/text()')[i] + "万"
        # 原价
        carOriginPrice = mytree.xpath('//ul[@class="carlist clearfix js-top"]/li/a/div[2]/em/text()')[i]

        print(carName, carPic, carInfo, carCurrentPrice, carOriginPrice)

        # 写入文件
        path = carBrandName + '.txt'
        with open(path, 'a+') as f:
            f.write(str((carName, carPic, carInfo, carCurrentPrice, carOriginPrice)) + '\n')


if __name__ == '__main__':
    url = 'https://www.carHome.com/gz/buy/'

    header = {
        "Cookie": "uuid=1de574eb-9dc2-4ce1-aa01-c4d84a73cf85; ganji_uuid=1097844088671826665367; lg=1; antipas=26608iF85721yTr399P72947737y5; clueSourceCode=%2A%2300; sessionid=45e6a1e9-0211-410d-e52d-513387da7208; Hm_lvt_936a6d5df3f3d309bda39e92da3dd52f=1531224149,1531442065,1531528226; cainfo=%7B%22ca_s%22%3A%22seo_baidu%22%2C%22ca_n%22%3A%22default%22%2C%22ca_i%22%3A%22-%22%2C%22ca_medium%22%3A%22-%22%2C%22ca_term%22%3A%22-%22%2C%22ca_kw%22%3A%22-%22%2C%22keyword%22%3A%22-%22%2C%22ca_keywordid%22%3A%22-%22%2C%22scode%22%3A%22-%22%2C%22version%22%3A1%2C%22platform%22%3A%221%22%2C%22client_ab%22%3A%22-%22%2C%22guid%22%3A%221de574eb-9dc2-4ce1-aa01-c4d84a73cf85%22%2C%22sessionid%22%3A%2245e6a1e9-0211-410d-e52d-513387da7208%22%7D; close_finance_popup=2018-07-14; cityDomain=gz; preTime=%7B%22last%22%3A1531528425%2C%22this%22%3A1531224147%2C%22pre%22%3A1531224147%7D; Hm_lpvt_936a6d5df3f3d309bda39e92da3dd52f=1531528427",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3423.2 Safari/537.36",
    }
    # 获得初始页源代码
    html = getHtml(url, header)

    # 获取汽车品牌信息字典
    carBrandDict = getCarBrand(html)

    # 多线程(10条的线程池)
    with ThreadPoolExecutor(10) as exT:
        # 程序执行流程
        # 根据汽车品牌进行爬取
        for carBrandName, carBrandUrl in carBrandDict.items():
            # 获取不同品牌页面源代码
            html = getHtml(carBrandUrl, header)
            # 获取当前品牌页面的页码url
            pageUrlList = getPageUrl(carBrandUrl, html)
            # 翻页
            for pageUrl in pageUrlList:
                # 获取汽车信息并写入文件
                exT.submit(getCarInfo, pageUrl, carBrandName)
