# -*- coding: utf-8 -*-

import sys
import redis
from time import sleep
from config import Config


class RedisDao():
    def __init__(self):
        self._init_redis()

    def _init_redis(self):
        n = 0
        while n < 5:
            try:
                # pool = redis.ConnectionPool(host=Config.redis_host, password=Config.redis_auth, port=6379, db=0)
                pool = redis.ConnectionPool(host=Config.redis_host, password=Config.redis_auth, port=6379, db=0)
                self._conn = redis.Redis(connection_pool=pool)
                self._pool = pool
                break
            except Exception, e:
                print Exception, ":", e
                if n >= Config.redis_retry_times:
                    print ('Redis Connect Error,exit!')
                    sys.exit()
                else:
                    n = n + 1
                    print ('Redis Connect Error,sleep!')
                    sleep(100)

    def set(self, key, value):
        return self._conn.set(key, value)

    def get(self, key):
        return self._conn.get(key)

    def rpush(self, key, value):
        return self._conn.rpush(key, value)

    def lpop(self, key):
        return self._conn.lpop(key)

    def lpop(self, key):
        return self._conn.lpop(key)
