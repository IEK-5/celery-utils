import os
import celery
import inspect

from celery_utils.app \
    import CACHE_ODIR

from celery_utils.utils.float_hash \
    import float_hash


def _full_fn_name(fun):
    res = inspect.getmodule(fun)
    return os.path.join(*res.__name__.split('.'), fun.__name__)


def compute_ofn(fun, args, kwargs, keys, ofn_arg,
                prefix = None, prefix_arg = None):
    """Compute ofn given function and arguments

    :fun, args, kwargs: function and arguments

    :keys: list of keys from kwargs. For computing filename do not use
           all kwargs, only with keys matching from this list

    :ofn_arg: key in kwargs. instead of computing filename use the
              provided in kwargs.

    :prefix: subdirectory to place the file

    :prefix_arg: key of kwargs. specify prefix via kwargs

    :return: filename

    """
    if ofn_arg is not None and ofn_arg in kwargs:
        ofn = kwargs[ofn_arg]
        os.makedirs(os.path.dirname(ofn), exist_ok = True)
        return ofn

    # in tasks with bind=True, the first argument is self,
    # which has a string representation dependent on the library version.
    # Hence, I ignore the first argument in that scenario
    if len(args) and isinstance(args[0], celery.Task):
            args = args[1:]

    if keys is not None:
        uniq = (args,)
        if kwargs:
            uniq = {k:v for k,v in kwargs.items()
                    if k in keys}
    else:
        uniq = (args, kwargs)
    fullfn = _full_fn_name(fun)
    key = float_hash(("cache_results", fullfn, uniq))

    prefix = '' if prefix is None else prefix
    if prefix_arg is not None and \
       prefix_arg in kwargs:
        prefix = os.path.join(prefix,kwargs[prefix_arg])

    ofn = os.path.join(CACHE_ODIR, prefix, fullfn)
    os.makedirs(ofn, exist_ok = True)

    return os.path.join(ofn, key)
