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


import logging

from functools \
    import wraps

from celery_utils.app import CONFIGS

from celery_utils.utils.float_hash \
    import float_hash

from celery_utils.utils.redis.lock \
    import RedisLock, Locked

from celery_utils.exceptions \
    import TASK_RUNNING


def one_instance(expire=60):
    """Introduce and iter-machine lock for a function

    :expire: number of seconds after which the lock expires

    """
    def wrapper(fun):
        @wraps(fun)
        def wrap(*args, **kwargs):
            key = float_hash\
                (("one_instance_lock",
                  fun.__name__, args, kwargs))
            try:
                with RedisLock\
                     (redis_url = CONFIGS['broker_url'],
                      key = key,
                      timeout = expire):
                    return fun(*args, **kwargs)
            except Locked:
                logging.debug("one_instance: {} is locked!"\
                              .format(key))
            raise TASK_RUNNING()
        return wrap
    return wrapper
