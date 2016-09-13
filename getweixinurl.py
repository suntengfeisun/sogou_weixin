# -*- coding: utf-8 -*-

import sys
import time
import requests
import simplejson
from lxml import etree
from public.headers import Headers
from public.proxies import Proxies
from public.redispooldao import RedisDao

reload(sys)
sys.setdefaultencoding('utf-8')

category = [
    {  # http://weixin.sogou.com/pcindex/pc/pc_1/1.html
        'url': '/pc_1',
        'name': u'推荐',
        'category_id': 2
    },
    {
        'url': '/pc_2',
        'name': u'段子手',
        'category_id': 3
    },
    {
        'url': '/pc_3',
        'name': u'养生堂',
        'category_id': 4
    },
    {
        'url': '/pc_4',
        'name': u'私房话',
        'category_id': 5
    },
    {
        'url': '/pc_5',
        'name': u'八卦精',
        'category_id': 6
    },
    {
        'url': '/pc_6',
        'name': u'爱生活',
        'category_id': 7
    },
    {
        'url': '/pc_7',
        'name': u'财经迷',
        'category_id': 8
    },
    {
        'url': '/pc_8',
        'name': u'汽车迷',
        'category_id': 9
    },
    {
        'url': '/pc_9',
        'name': u'科技咖',
        'category_id': 10
    },
    {
        'url': '/pc_10',
        'name': u'潮人帮',
        'category_id': 11
    },
    {
        'url': '/pc_11',
        'name': u'辣妈帮',
        'category_id': 12
    },
    {
        'url': '/pc_12',
        'name': u'点赞党',
        'category_id': 13
    },
    {
        'url': '/pc_13',
        'name': u'旅行家',
        'category_id': 14
    },
    {
        'url': '/pc_14',
        'name': u'职场人',
        'category_id': 15
    },
    {
        'url': '/pc_15',
        'name': u'美食家',
        'category_id': 16
    },
    {
        'url': '/pc_16',
        'name': u'古今通',
        'category_id': 17
    },
    {
        'url': '/pc_17',
        'name': u'学霸族',
        'category_id': 18
    },
    {
        'url': '/pc_18',
        'name': u'星座控',
        'category_id': 19
    },
    {
        'url': '/pc_19',
        'name': u'体育迷',
        'category_id': 20
    }
]

url_main = 'http://weixin.sogou.com/pcindex/pc'


def doIt(url, category_id, i=0):
    if i == 0:
        url1 = url_main + url + url + '.html'
    else:
        url1 = url_main + url + '/' + str(i) + '.html'
    print(url1)
    req_status = True
    headers = Headers.get_headers()
    proxies = Proxies.get_proxies()
    try:
        req = requests.get(url1, headers=headers, timeout=10, proxies=proxies)
    except:
        req_status = False

    if req_status:
        if req.status_code != 404:
            html = req.content
            selector = etree.HTML(html)
            urls = selector.xpath('//a[contains(@uigs,"summary")]/@href')
            imgs = selector.xpath('//a[contains(@uigs,"img")]/img[1]/@src')
            c = 0
            redis_dao = RedisDao()
            while True:
                if c >= len(urls):
                    break
                url2 = urls[c]
                img = imgs[c]
                data = {
                    'category_id': category_id,
                    'url': url2,
                    'img_main': img
                }
                try:
                    date = time.strftime('%Y%m%d')
                    redis_dao.rpush('queue:weixin_%s' % date, simplejson.dumps(data))
                except:
                    redis_dao = RedisDao()
                c = c + 1
            i = i + 1
            doIt(url, category_id, i)


if __name__ == '__main__':
    print(time.strftime('%Y-%m-%d %H:%M:%S'))
    for c in category:
        url = c['url']
        category_id = c['category_id']
        doIt(url, category_id)
    print('game over')
