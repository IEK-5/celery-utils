import celery

from functools import wraps

from celery_utils.app \
    import CELERY_APP
from celery_utils.storage.get_locally \
    import get_locally
from celery_utils.utils.addattr \
    import AddAttr
from celery_utils.utils.addretry \
    import AddRetry
from celery_utils.utils.one_instance \
    import one_instance
from celery_utils.utils.calldocs \
    import calldocs
from celery_utils.utils.debug_function_info \
    import debug_decorator
from celery_utils.utils.matchargs \
    import matchargs


def task(cache = 'fn', get_args_locally = True,
         debug_info = True, queue = 'celery', **kwargs):
    """Make a function to be a celery task

    :cache: expected output type.
        - None do not cache anything
        - 'fn' expect local path with a file
        - 'pickle' except pickable python object
          that is stored in a cache as a pickle file

    :get_args_locally: if resolve obtain locally all remote paths in
    arguments

    :link, ignore, storage_type:
    see ?celery_utils.cache.cache_fn_results

    :keys, storage_type, ofn_arg, path_prefix, path_prefix_arg, minage, update_timestamp:
    see ?celery_utils.cache.cache._check_in_storage

    :debug_info, debug_loglevel, debug_info_kwargs:
    see ?celery_utils.decorators.debug_function_info.debug_decorator

    :autoretry_for, max_retries, retry_backoff, retry_backoff_max, retry_jitter:
    see ?celery_utils.addretry.AddRetry

    :expire: simultaneous execution lock expire (in seconds) see
    ?celery_utils.utils.one_instance.one_instance

    :queue: name of the queue to use

    """
    def wrapper(fun):
        if debug_info:
            fun = matchargs(debug_decorator)(**kwargs)(fun)

        if get_args_locally:
            fun = get_locally(fun)

        fun = matchargs(one_instance)(**kwargs)(fun)

        if cache is not None:
            from celery_utils.cache.cache \
                import cache as cache_decorator
            fun = matchargs(cache_decorator)\
                (output = cache, **kwargs)(fun)

        attr = {'cache': cache,
                'get_args_locally': get_args_locally,
                'debug_info': debug_info}
        attr.update(**kwargs)
        if hasattr(fun, '_cache_args'):
            attr.update(fun._cache_args)

        bs_cls = AddAttr(**kwargs)(celery.Task)
        bs_cls = matchargs(AddRetry)(**kwargs)(bs_cls)

        @CELERY_APP.task(bind = True, queue = queue, base = bs_cls)
        @wraps(fun)
        def wrap(self, *a, **kw):
            return fun(*a, **kw)

        return wrap
    return wrapper


def call(cache = True, get_args_locally = False,
         debug_info = True, add_calldocs = True,
         autoretry_for = [], **kwargs):
    """A decorator that produces chain of celery tasks

    :cache: if cache call results

    :get_args_locally: if resolve obtain locally all remote paths in
    arguments

    :debug_info, debug_loglevel, debug_info_kwargs: see
    ?celery_utils.decorators.debug_function_info.debug_decorator

    :add_calldocs: if add docs attribute

    :autoretry_for: this specifies exceptions occurring during the
    call execution, that should trigger the autoretry

    :docs, docs_kwargs, docs_others:
    sets ._call_docs attribute, allowing webserver to pass arguments,
    determine default values and generate help page
    ? celery_utils.decorators.call_docs.call_docs

    """
    def wrapper(fun):
        if debug_info:
            fun = matchargs(debug_decorator)(**kwargs)(fun)

        if get_args_locally:
            fun = get_locally(fun)

        if cache:
            from celery_utils.cache.cache \
                import cache as cache_decorator
            fun = matchargs(cache)\
                (output = 'call', **kwargs)(fun)

        @wraps(fun)
        def wrap(*a, **kw):
            return fun(*a, **kw)

        attr = {'cache': cache,
                'get_args_locally': get_args_locally,
                'debug_info': debug_info,
                'autoretry_for': autoretry_for}
        attr.update(**kwargs)
        if hasattr(fun, '_cache_args'):
            attr.update(fun._cache_args)
        if add_calldocs:
            attr.update(
                {'calldocs': matchargs(calldocs)\
                 (fun=wrap, **kwargs)})
        wrap.cu_attr = attr

        return wrap
    return wrapper
