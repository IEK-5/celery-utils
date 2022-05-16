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


import json
import redis

from celery_utils.utils.float_hash \
    import float_hash

from celery_utils.utils.redis.parse_url \
    import parse_url


class Redis_Dictionary:


    def __init__(self, name, redis_url,
                 hash_function = float_hash,
                 expire_time = 7200):
        """A distributed dictionary with redis

        :name: name of the set in redis

        :redis_url: how to connect to redis

        :hash_function: function that produces a hash for keys

        :expire_time: time to expire for dictionary items
        """
        self._name = name
        self._client = redis.StrictRedis(**parse_url(redis_url))
        self._hash = hash_function
        self._expire = expire_time


    def __contains__(self, key):
        hkey = self._hash(key)
        return self._client.exists(self._name + hkey)


    def __setitem__(self, key, item):
        hkey = self._hash(key)
        sitem = json.dumps(item)
        self._client.set(self._name + hkey, sitem,
                         ex = self._expire)


    def __getitem__(self, key):
        hkey = self._hash(key)

        if not self._client.exists(self._name + hkey):
            raise KeyError\
                ("'{key}' is not in hset".format(key=key))

        sitem = self._client.get(self._name + hkey)
        return json.loads(sitem)


    def __delitem__(self, key):
        hkey = self._hash(key)
        self._client.delete(self._name + hkey)
