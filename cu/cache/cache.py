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


import os
import celery
import inspect
import logging

from functools import wraps

from cu.exceptions \
    import FILE_DISAPPEARED

from cu.storage.remotestorage_path \
    import RemoteStoragePath, is_remote_path

from cu.utils.files \
    import remove_file, move_file, get_tempfile
from cu.utils.matchargs \
    import matchargs
from cu.utils.serialise \
    import serialise, deserialise

from cu.cache.tasks \
    import call_fn_cache
from cu.cache.compute_ofn \
    import compute_ofn
from cu.cache.ifpass_minage \
    import ifpass_minage


def _function_defaults(fun, **kwargs):
    res = {}

    for k, v in inspect.signature(fun).parameters.items():
        if k in kwargs:
            res[k] = kwargs[k]
            continue

        if v.default is inspect._empty:
            continue

        res[k] = v.default

    return res


def _check_in_storage(fun, args, kwargs,
                      minage = None, update_timestamp = True,
                      **ofn_kwargs):
    """Check function call present in the storage

    :fun, args, kwargs: function and arguments

    :minage: see ?cu.cache.ifpass_minage.ifpass_minage

    :update_timestamp: if update timestamp on cache hit

    :keys, ofn_arg, path_prefix, path_prefix_arg: see ?cu.cache.compute_ofn.compute_ofn

    :remotetype, serialise: see ?cu.storage.remotestorage_path.RemoteStoragePath

    """
    ofn = matchargs(compute_ofn)\
        (fun = fun, args = args, kwargs = kwargs, **ofn_kwargs)
    ofn_rpath = matchargs(RemoteStoragePath)\
        (path = ofn, **ofn_kwargs)

    if ofn_rpath.in_storage() and \
       ifpass_minage(minage = minage,
                     fntime = ofn_rpath.get_timestamp(),
                     kwargs = kwargs):
        if update_timestamp:
            ofn_rpath.update_timestamp()
        return True, ofn_rpath

    return False, ofn_rpath


def cache_fn(return_type = 'path', remove_return = True,
             ignore = lambda x: False, **cache_kwargs):
    """Cache results of a function that returns a file

    :return_type: what to expect from the function
          - 'path' expects a path
          - 'pickle' expects a pickle-serialisable object
          - 'json' expects a json-serialisable object
          - 'msgpack' expects a msgpack-serialisable object

    :remove_return: if True, then return filename from the function is
    considered to be temporary and removed. if 'path' != return_type,
    then True value is implied.

    :ignore: a boolean function that is computed if result of a
    function should be ignored.

    :cache_kwargs: see ?cu.cache.cache._check_in_storage

    """
    def wrapper(fun):
        if 'path' != return_type:
            fun = serialise(how = return_type)(fun)

        @wraps(fun)
        def wrap(*args, **kwargs):
            isin, ofn_rpath = \
                matchargs(_check_in_storage)\
                (fun = fun, args = args, kwargs = kwargs,
                 serialise = return_type, **cache_kwargs)

            if isin:
                return str(ofn_rpath)

            tfn = fun(*args, **kwargs)

            if ignore(tfn):
                return tfn

            tfn_rpath = RemoteStoragePath(tfn)

            if is_remote_path(tfn):
                ofn_rpath.link(tfn_rpath.path)
                return str(ofn_rpath)

            if not os.path.exists(tfn_rpath.path):
                raise FILE_DISAPPEARED\
                    (f"{tfn_rpath.path} is not remote "
                     "and not locally present!")

            # linking file does not remove it!
            if_link = not (('path' != return_type) or remove_return)
            move_file(tfn_rpath.path, ofn_rpath.path, if_link)
            ofn_rpath.upload()
            return str(ofn_rpath)

        wrap._cache_args = \
            {'return_type': return_type,
             'remove_return': remove_return}
        wrap._cache_args.update\
            (_function_defaults\
             (_check_in_storage, **cache_kwargs))
        wrap._cache_args.update\
            (_function_defaults\
             (RemoteStoragePath, serialise = return_type,
              **cache_kwargs))
        return wrap
    return wrapper


class _CALL_NOT_IN_CACHE(Exception):
    pass


def _save_call(calls, ofn):
    if calls is not None:
        return calls

    # explanation: _save_call is wraped with cache_fn, hence if ofn
    # exists in a remote storage it will be get locally and, the
    # following line should not be reached. If calls is not None, then
    # _save_call has been called to actually save the call.
    raise _CALL_NOT_IN_CACHE(f"ofn = {ofn}")


def cache_call(call_serialiser = 'msgpack', cache_result = True, **cache_kwargs):
    """Wraps tasks generation calls (*/calls.py)

    :call_serialiser: how to serialise the celery call

    :cache_result: if True an additional task to the queue, that sets
    the result of the call to the cache

    :cache_kwargs: see ?cu.cache.cache._check_in_storage

    """
    def wrapper(fun):
        sc = cache_fn\
            (return_type=call_serialiser, ofn_arg='ofn',
             **cache_kwargs)(_save_call)

        @wraps(fun)
        def wrap(*args, **kwargs):
            isin, ofn_rpath = \
                matchargs(_check_in_storage)\
                (fun = fun, args = args, kwargs = kwargs,
                 **cache_kwargs)

            # '*_meta' contains some meta information about the call:
            # how to serialise the result.
            meta_fn = matchargs(RemoteStoragePath)\
                (path = ofn_rpath.path + '_meta',
                 serialise = call_serialiser, **cache_kwargs)
            if cache_result and isin and meta_fn.in_storage():
                # at this point meta_fn must exist!
                return call_fn_cache.signature\
                    (kwargs = {'result': None,
                               'call_serialiser': call_serialiser,
                               'cache_kwargs': cache_kwargs,
                               'ofn': str(ofn_rpath)})

            # '*_call' file contains the serialised task tree (below
            # 'calls'). 'calls' can be pretty big, and hence
            # serialised on one worker and not send over broker
            call_fn = matchargs(RemoteStoragePath)\
                (path = ofn_rpath.path + '_call',
                 serialise = call_serialiser, **cache_kwargs)
            try:
                return celery.signature\
                    (RemoteStoragePath\
                     (sc(calls = None, ofn = call_fn.path))\
                     .get_locally(True))
            except _CALL_NOT_IN_CACHE as e:
                pass

            calls = fun(*args, **kwargs) # this can be long

            if cache_result:
                calls |= call_fn_cache.signature\
                    (kwargs = {'call_serialiser': call_serialiser,
                               'cache_kwargs': cache_kwargs,
                               'ofn': str(ofn_rpath)})

            # call_fn_cache is actually run after the "sc"
            sc(calls = calls, ofn = call_fn.path)
            return calls

        wrap._cache_args = \
            {'call_serialiser': call_serialiser,
             '_save_call': sc._cache_args}
        wrap._cache_args.update\
            (_function_defaults\
             (_check_in_storage, **cache_kwargs))
        return wrap
    return wrapper
