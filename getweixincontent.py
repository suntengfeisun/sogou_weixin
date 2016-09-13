# -*- coding: utf-8 -*-

import sys
import time
import random
import requests
import simplejson
import threading
from lxml import etree
from urllib import quote
from public.config import Config
from public.mysqlpooldao import MysqlDao
from public.redispooldao import RedisDao
from public.headers import Headers
from public.proxies import Proxies

reload(sys)
sys.setdefaultencoding('utf-8')


class Worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        mysql_dao = MysqlDao()
        redis_dao = RedisDao()
        while True:
            print(self.getName())
            date = time.strftime('%Y%m%d')
            data_json = redis_dao.lpop('queue:weixin_%s' % date)
            if data_json == None:
                break
            data = simplejson.loads(data_json)
            category_id = data['category_id']
            url = data['url']
            img_main = data['img_main']
            self.getContent(category_id, url, img_main, mysql_dao)
        mysql_dao.close()

    def getContent(self, category_id, url, img_main, mysql_dao):
        try:
            headers = Headers.get_headers()
            proxies = Proxies.get_proxies()
            req = requests.get(url, headers=headers, timeout=20, proxies=proxies)
            html = req.content
            selector = etree.HTML(html)
            titles = selector.xpath('//title/text()')
            contents = selector.xpath('//*[contains(@class,"rich_media_content")]/descendant::text()')
            imgs = selector.xpath('//*[contains(@class,"rich_media_content")]/descendant::img/@data-src')
            times = selector.xpath('//*[contains(@id,"post-date")]/text()')
            authors = selector.xpath('//*[contains(@id,"post-user")]/text()')
            if len(times) > 0:
                time_t = times[0]
            else:
                time_t = ''
            if len(authors) > 0:
                author = authors[0]
            else:
                author = ''
            if len(titles) > 0:
                title = titles[0].replace('"', '').replace(' ', '')
                ct = ''
                ig = ''
                for content in contents:
                    content = content.replace('"', '').replace('\n', '').replace('\t', '').replace('\r', '').replace(
                            ' ', '')
                    if content != '':
                        ct = ct + '{ycontent}' + content
                for img in imgs:
                    ig = ig + '{yimg}' + img
                time_now = time.strftime('%Y-%m-%d %H:%M:%S')
                insert_value = '"' + str(
                        category_id) + '","' + title + '","' + ct + '","' + url + '","' + img_main + '","","' + ig + '","","' + author + '","' + time_t + '","' + time_now + '","' + time_now + '"';
                sql = 'insert ignore into zmt_weixin_content (`category_id`,`title`,`content`,`url`,`img_main`,`img_main_oss`,`img`,`img_oss`,`author`,`time`,`created_at`,`updated_at`) values (' + insert_value + ')'
                mysql_dao.execute(sql)
                url = 'http://mp.weixin.qq.com/mp/getrelatedmsg?url=' + quote(
                        url) + '&title=' + title + '&uin=&key=&pass_ticket=&wxtoken=&devicetype=&clientversion=0&x5=0'
                req = requests.get(url, headers=headers, timeout=20)
                html = req.content
                html_dict = simplejson.loads(html)
                for article in html_dict['article_list']:
                    img = ''
                    insert_value = '"' + str(category_id) + '","' + article[
                        'url'] + '","' + img + '",0,"' + time_now + '"'
                    sql = 'insert ignore into zmt_weixin_url (`category_id`,`url`,`img_main`,`status`,`created_at`) values (' + insert_value + ')'
                    mysql_dao.execute(sql)
        except Exception, e:
            print Exception, ":", e
            print(sql)


if __name__ == '__main__':
    # 初始化并启动进程
    threads = []
    for i in xrange(Config.clawler_num):
        worker = Worker()
        threads.append(worker)
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()
    print('game over')
