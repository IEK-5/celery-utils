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

from cu.app \
    import CACHE_ODIR

from cu.utils.float_hash \
    import float_hash


# _full_fn_name is only applicable for true function, and not
# decorated celery tasks
def _full_fn_name(fun):
    res = inspect.getmodule(fun)
    return os.path.join(*res.__name__.split('.'), fun.__name__)


def compute_ofn(fun, args, kwargs,
                keys = None, ofn_arg = None,
                path_prefix = None, path_prefix_arg = None):
    """Compute ofn given function and arguments

    :fun, args, kwargs: function and arguments

    :keys: list of keys from kwargs. For computing filename do not use
           all kwargs, only with keys matching from this list

    :ofn_arg: key in kwargs. instead of computing filename use the
              provided in kwargs.

    :path_prefix: subdirectory to place the file

    :path_prefix_arg: key of kwargs. specify prefix via kwargs

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

    path_prefix = '' if path_prefix is None else path_prefix
    if path_prefix_arg is not None and \
       path_prefix_arg in kwargs:
        path_prefix = os.path.join\
            (path_prefix,kwargs[path_prefix_arg])

    ofn = os.path.join(CACHE_ODIR, path_prefix, fullfn)
    os.makedirs(ofn, exist_ok = True)

    return os.path.join(ofn, key)
