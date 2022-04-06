import celery

from functools import wraps

from celery_utils.app \
    import CELERY_APP
from celery_utils.storage.get_locally \
    import get_locally
from celery_utils.decorators.addretry \
    import AddRetry
from celery_utils.decorators.one_instance \
    import one_instance
from celery_utils.decorators.calldocs \
    import calldocs
from celery_utils.decorators.debug_function_info \
    import debug_decorator


def task_decorator(expire = 600,
                   retry_args = {},
                   cache = 'fn',
                   cache_args = {},
                   get_args_locally = True,
                   debug_info = True,
                   debug_loglevel = 'debug',
                   debug_info_kwargs = {}):
    """Make a function to be a celery task

    :expire: simultaneous execution lock expire (in seconds)

    :retry_args: arguments how to retry tasks see
                 ?celery_utils.decorators.addretry.AddRetry

    :cache: expected output type.
        - None do not cache anything
        - 'fn' expect local path with a file
        - 'pickle' except pickable python object
          that is stored in a cache as a pickle file

    :cache_args: arguments for cache.
    See ?celery_utils.cache.cache.cache

    :get_args_locally: if resolve obtain locally all remote paths in
    arguments

    :debug_info, debug_loglevel, debug_info_kwargs:
    print debug info for the called function. see kwargs in:
    ? celery_utils.decorators.debug_function_info.debug_decorator

    """
    def wrapper(fun):
        if debug_info:
            fun = debug_decorator(level=debug_loglevel,
                                  **debug_info_kwargs)(fun)

        if get_args_locally:
            fun = get_locally(fun)

        fun = one_instance(expire = expire)(fun)

        if cache is not None:
            from celery_utils.cache.cache \
                import cache as cache_decorator
            fun = cache_decorator\
                (output = cache, **cache_args)(fun)

        @CELERY_APP.task\
            (bind = True,
             base = AddRetry(**retry_args)(celery.Task))
        @wraps(fun)
        def wrap(self, *args, **kwargs):
            return fun(*args, **kwargs)

        return wrap
    return wrapper


def call_decorator(cache = True,
                   cache_args = {},
                   get_args_locally = False,
                   debug_info = True,
                   debug_loglevel = 'debug',
                   debug_info_kwargs = {},
                   add_calldocs = True,
                   calldocs_kwargs = {},
                   calldocs_others = []):
    """A decorator that produces chain of celery tasks

    :cache_args: arguments for cache.
    See ?celery_utils.cache.cache.cache

    :get_args_locally: if resolve obtain locally all remote paths in
    arguments

    :debug_info, debug_loglevel, debug_info_kwargs:
    print debug info for the called function. see kwargs in:
    ? celery_utils.decorators.debug_function_info.debug_decorator

    :docs, docs_kwargs, docs_others:
    sets ._call_docs attribute, allowing webserver to pass arguments,
    determine default values and generate help page
    ? celery_utils.decorators.call_docs.call_docs
    """
    def wrapper(fun):
        if debug_info:
            fun = debug_decorator(level=debug_loglevel,
                                  **debug_info_kwargs)(fun)

        if get_args_locally:
            fun = get_locally(fun)

        if cache:
            from celery_utils.cache.cache \
                import cache as cache_decorator
            fun = cache_decorator\
                (output = 'call', **cache_args)(fun)

        @wraps(fun)
        def wrap(*args, **kwargs):
            return fun(*args, **kwargs)

        if add_calldocs:
            wrap._calldocs = calldocs(wrap, calldocs_kwargs,
                                      calldocs_others)

        return wrap
    return wrapper
