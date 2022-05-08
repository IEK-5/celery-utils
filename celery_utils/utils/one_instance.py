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
