import os
import json
import celery
import logging
import pickle

from functools import wraps

from celery_utils.app \
    import DEFAULT_REMOTE

from celery_utils.storage.remotestorage_path \
    import RemoteStoragePath, is_remote_path

from celery_utils.utils.files \
    import remove_file, move_file, get_tempfile

from celery_utils.cache.tasks \
    import call_fn_cache
from celery_utils.cache.compute_ofn \
    import compute_ofn
from celery_utils.cache.ifpass_minage \
    import ifpass_minage


def _logging(msg, how = logging.debug, **kwargs):
    for k,v in kwargs.items():
        msg += """
        {} = {}
        """.format(k,v)
    how(msg)


def _check_in_storage(fun, args, kwargs,
                      storage_type,
                      keys = None,
                      ofn_arg = None,
                      path_prefix = None,
                      path_prefix_arg = None,
                      minage = None,
                      update_timestamp = True):
    """Check call in storage

    :fun, args, kwargs: function and arguments

    :storage_type: type of remote storage.

    :keys: list of arguments name to use for computing the unique name
    for the cache item

    :ofn_arg: optional name of the kwargs that is intented to be used
    as a output filename

    :path_prefix, path_prefix_arg: how to prefix path of the file

    :minage: unixtime, minage of acceptable stored cached value. if
    None any cached value is accepted

    :update_timestamp: if update timestamp on cache hit

    """
    ofn = compute_ofn(fun = fun, args = args,
                      kwargs = kwargs, keys = keys,
                      ofn_arg = ofn_arg,
                      prefix = path_prefix,
                      prefix_arg = path_prefix_arg)
    ofn_rpath = RemoteStoragePath\
        (ofn, remotetype=storage_type)

    if ofn_rpath.in_storage() and \
       ifpass_minage(minage,
                     ofn_rpath.get_timestamp(),
                     kwargs):
        _logging("File is in cache!",
                 ofn = ofn, fun = fun.__name__,
                 args = args, kwargs = kwargs)
        if update_timestamp:
            ofn_rpath.update_timestamp()
        return True, ofn, ofn_rpath, minage

    _logging("File is NOT in cache!",
             ofn = ofn, fun = fun.__name__,
             args = args, kwargs = kwargs)
    return False, ofn, ofn_rpath, minage


def cache_fn_results(link = False,
                     ignore = lambda x: False,
                     storage_type = DEFAULT_REMOTE,
                     check_storage_kwargs = {}):
    """Cache results of a function that returns a file

    :link: if using a hardlink instead of moving file to local cache

    :ignore: a boolean function that is computed if result of a
    function should be ignored.

    :storage_type: type of remote storage.

    :check_storage_kwargs: see optional arguments of
    ?celery_utils.cache.cache._check_in_storage

    """
    def wrapper(fun):
        @wraps(fun)
        def wrap(*args, **kwargs):
            isin, ofn, ofn_rpath, _ = _check_in_storage\
                (fun = fun, args = args, kwargs = kwargs,
                 storage_type = storage_type,
                 **check_storage_kwargs)

            if isin:
                return str(ofn_rpath)

            tfn = fun(*args, **kwargs)

            if ignore(tfn):
                return tfn

            tfn_rpath = RemoteStoragePath(tfn, remotetype=storage_type)

            if os.path.exists(tfn_rpath.path):
                move_file(tfn_rpath.path, ofn, link)

            if is_remote_path(tfn):
                ofn_rpath.link(tfn_rpath.path)
                return str(ofn_rpath)

            ofn_rpath.upload()
            return str(ofn_rpath)
        return wrap
    return wrapper


@cache_fn_results(check_storage_kwargs = {'ofn_arg': 'ofn'})
def _save_calls(calls, ofn):
    try:
        with open(ofn, 'w') as f:
            json.dump(calls, f)
        return ofn
    except Exception as e:
        remove_file(ofn)
        raise e


def _results2pickle(fun):
    """Pickle results to a storage

    """
    @wraps(fun)
    def wrap(*args, **kwargs):
        res = fun(*args, **kwargs)

        ofn = get_tempfile()
        try:
            with open(ofn, 'wb') as f:
                pickle.dump(res, f)
        except Exception as e:
            remove_file(ofn)
            raise e

        return ofn
    return wrap


def _pickle2results(fun):
    """Get a pickled file and load it

    """
    @wraps(fun)
    def wrap(*args, **kwargs):
        ifn = fun(*args, **kwargs)

        ifn = RemoteStoragePath(ifn).get_locally()
        with open(ifn, 'rb') as f:
            return pickle.load(f)
    return wrap


def call_cache_fn_results(storage_type = DEFAULT_REMOTE,
                          check_storage_kwargs = {}):
    """Wraps tasks generation calls (*/calls.py)

    This adds an additional task to the queue, that sets the result of
    the call to the cache

    :storage_type: type of remote storage.

    :check_storage_kwargs: see optional arguments of
    ?celery_utils.cache.cache._check_in_storage

    """
    def wrapper(fun):
        @wraps(fun)
        def wrap(*args, **kwargs):
            isin, ofn, ofn_rpath, minage = _check_in_storage\
                (fun = fun, args = args, kwargs = kwargs,
                 storage_type = storage_type,
                 **check_storage_kwargs)

            if isin:
                return call_fn_cache.signature\
                    (kwargs = {'result': None,
                               'ofn': str(ofn_rpath),
                               'storage_type': storage_type})

            call_fn = RemoteStoragePath\
                (ofn + '_call.json',
                 remotetype=storage_type)
            if call_fn.in_storage() and \
               ifpass_minage(minage, call_fn.get_timestamp(),
                             kwargs):
                with open(call_fn.get_locally(), 'r') as f:
                    return celery.signature(json.load(f))

            calls = fun(*args, **kwargs) # this can be long
            calls |= call_fn_cache.signature\
                (kwargs = {'ofn': str(ofn_rpath),
                           'storage_type': storage_type})
            _save_calls(calls = calls, ofn = call_fn.path)
            return calls
        return wrap
    return wrapper


def cache_pickle_results(**kwargs):
    """Cache results of a function that returns a pickable object

    :kwargs: see ?celery_utils.cache.cache.cache_fn_results

    """
    def wrapper(fun):
        return _pickle2results(cache_fn_results(**kwargs)\
                               (_results2pickle(fun)))
    return wrapper


def cache(output = 'fn', **kwargs):
    """Wrapper for cache_fn_results, call_cache_fn_results,
    cache_pickle_results

    :output: either 'fn', 'call', 'pickle'
    'output' specifies what is expected from the function:
        - 'fn' expects a local path to be cached
        - 'call' expects celery.task
        - 'pickle' expects a pickable objects

    :kwargs: depending on the output, see
       - 'fn': ?celery_utils.cache.cache.cache_fn_results
       - 'call': ?celery_utils.cache.cache.call_cache_fn_results
       - 'pickle': ?celery_utils.cache.cache.cache_pickle_results

    """
    def wrapper(fun):
        if 'fn' == output:
            return cache_fn_results(**kwargs)(fun)
        elif 'call' == output:
            return call_cache_fn_results(**kwargs)(fun)
        elif 'pickle' == output:
            return cache_pickle_results(**kwargs)(fun)
        else:
            raise RuntimeError\
                ("cache: invalid argument output = {}"\
                 .format(output))
    return wrapper
