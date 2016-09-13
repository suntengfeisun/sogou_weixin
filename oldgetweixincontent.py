# -*- coding: utf-8 -*-


"""
写在优化之前
这次更新的目的在于之前的版本生产者大于消费者,导致了生产者的大量堆积
本次主要更新
解决多进程锁死
尝试使用python.queue替代redis,不使用分布式
多进程尝试
"""

import time
import random
import requests
import simplejson
from lxml import etree
from urllib import quote
import sys
import Queue
from mysqlpooldao import MysqlDao
import threading
from config import Config
from headers import Headers

reload(sys)
sys.setdefaultencoding('utf-8')


class Worker(threading.Thread):
    queue = None

    def __init__(self):
        threading.Thread.__init__(self)

    @classmethod
    def set_queue(self, queue):
        self.queue = queue
        return self

    def run(self):
        mysqlDao = MysqlDao()
        while True:
            print(self.getName())
            if self.queue.empty():
                break
            content = simplejson.loads(self.queue.get())
            id = content[0]
            category_id = content[1]
            url = content[2]
            img_main = content[3]
            self.getContent(id, category_id, url, img_main, mysqlDao)

        mysqlDao.close()

    def getContent(self, id, category_id, url, img_main, mysqlDao):
        try:
            # print(url)
            headers = Headers().getHeaders()
            req = requests.get(url, headers=headers, timeout=20)
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
                # print(sql)
                mysqlDao.execute(sql)
                url = 'http://mp.weixin.qq.com/mp/getrelatedmsg?url=' + quote(
                        url) + '&title=' + title + '&uin=&key=&pass_ticket=&wxtoken=&devicetype=&clientversion=0&x5=0'
                # print(url)
                req = requests.get(url, headers=headers, timeout=20)
                html = req.content
                # print(html)
                html_dict = simplejson.loads(html)
                for article in html_dict['article_list']:
                    img = ''
                    insert_value = '"' + str(category_id) + '","' + article[
                        'url'] + '","' + img + '",0,"' + time_now + '"'
                    sql = 'insert ignore into zmt_weixin_url (`category_id`,`url`,`img_main`,`status`,`created_at`) values (' + insert_value + ')'
                    # print(sql)
                    mysqlDao.execute(sql)
        except Exception, e:
            print Exception, ":", e
            print(sql)
        sql = 'update zmt_weixin_url set `status`=1 where `id`=' + str(id)
        # print(sql)
        mysqlDao.execute(sql)


if __name__ == '__main__':
    # 初始化一个队列 2016年7月22日 11:18:55新尝试
    queue = Queue.Queue()
    # 初始化mysql
    mysqlDao = MysqlDao()
    while True:
        day_now = time.strftime('%Y-%m-%d') + ' 00:00:00'
        # 从mysql为status为0的url入队列
        sql = 'select `id`,`category_id`,`url`,`img_main` from zmt_weixin_url WHERE `status`=0 AND `created_at` > "' + day_now + '" limit 0,500'
        print(sql)
        ret = mysqlDao.execute(sql)
        for r in ret:
            queue.put(simplejson.dumps(r))
        Worker.set_queue(queue)
        # 初始化并启动进程
        local_school = threading.local()
        threads = []
        for i in range(Config.clawler_num):
            worker = Worker()
            threads.append(worker)
        for t in threads:
            t.setDaemon(True)
            t.start()
        t.join()
    mysqlDao.close()
