#
# This file is part of the celery-utils (https://github.com/e.sovetkin/celery-utils).
# Copyright (c) 2022 Jenya Sovetkin.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import time
import redis

from celery_utils.utils.redis.parse_url \
    import parse_url


class Locked(Exception):
    pass


class RedisLock:
    """Distributed lock

    """

    def __init__(self, redis_url, key, sleep=-1, timeout=None):
        """init

        :redis_url: how to connect to redis

        :key: a name for the lock

        :sleep: if positive locks sleeps before another attempt

        :timeout: expire time for the lock

        """
        self.key = key
        self.sleep = sleep
        self._redis = redis.StrictRedis\
            (**parse_url(redis_url))
        self._lock = redis.lock.Lock\
            (self._redis, self.key, timeout = timeout,
             blocking = 1,
             blocking_timeout = False)



    def __enter__(self):
        while not self._lock.acquire():
            if self.sleep < 0:
                raise Locked()

            time.sleep(self.sleep)
        return True


    def __exit__(self, type, value, traceback):
        self._redis.delete(self.key)
