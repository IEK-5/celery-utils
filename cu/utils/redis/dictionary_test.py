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

from cu.utils.redis_dictionary \
    import Redis_Dictionary

from cu \
    import REDIS_IP


def test_one():
    d = Redis_Dictionary(name = 'test_one',
                         host = REDIS_IP,
                         port = 6379,
                         db = 0)

    assert 'one' not in d
    d['one'] = 1
    assert 'one' in d
    assert d['one'] == 1
    d['one'] = 2
    assert d['one'] == 2
    del d['one']
    assert 'one' not in d

    d[(1.2,'two')] = 2
    assert (1.2,'two') in d
    del d[(1.2,'two')]


def test_timeout():
    d = Redis_Dictionary(name = 'test_timeout',
                         host = REDIS_IP,
                         port = 6379,
                         db = 0,
                         expire_time = 5)

    d['one'] = 1
    assert 'one' in d
    time.sleep(6)
    assert 'one' not in d
