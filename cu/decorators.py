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


import celery

from functools import wraps

from cu.app \
    import CELERY_APP
from cu.storage.get_locally \
    import get_locally
from cu.utils.addattr \
    import AddAttr
from cu.utils.addretry \
    import AddRetry
from cu.utils.one_instance \
    import one_instance
from cu.utils.calldocs \
    import calldocs
from cu.utils.debug_function_info \
    import debug_decorator
from cu.utils.matchargs \
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
    see ?cu.cache.cache_fn_results

    :keys, storage_type, ofn_arg, path_prefix, path_prefix_arg, minage, update_timestamp:
    see ?cu.cache.cache._check_in_storage

    :debug_info, debug_loglevel, debug_info_kwargs:
    see ?cu.decorators.debug_function_info.debug_decorator

    :autoretry_for, max_retries, retry_backoff, retry_backoff_max, retry_jitter:
    see ?cu.addretry.AddRetry

    :expire: simultaneous execution lock expire (in seconds) see
    ?cu.utils.one_instance.one_instance

    :queue: name of the queue to use

    """
    def wrapper(fun):
        if debug_info:
            fun = matchargs(debug_decorator)(**kwargs)(fun)

        if get_args_locally:
            fun = get_locally(fun)

        fun = matchargs(one_instance)(**kwargs)(fun)

        if cache is not None:
            from cu.cache.cache \
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
    ?cu.decorators.debug_function_info.debug_decorator

    :add_calldocs: if add docs attribute

    :autoretry_for: this specifies exceptions occurring during the
    call execution, that should trigger the autoretry

    :docs, docs_kwargs, docs_others:
    sets ._call_docs attribute, allowing webserver to pass arguments,
    determine default values and generate help page
    ? cu.decorators.call_docs.call_docs

    """
    def wrapper(fun):
        if debug_info:
            fun = matchargs(debug_decorator)(**kwargs)(fun)

        if get_args_locally:
            fun = get_locally(fun)

        if cache:
            from cu.cache.cache \
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
