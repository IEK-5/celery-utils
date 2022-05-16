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


import inspect

from functools import wraps


def matchargs(fun):
    """Match list of kwargs to the arguments a function

    :func: a function to call

    :kwargs: key word arguments

    """
    spec = inspect.getfullargspec(fun)

    if spec.varargs:
        raise RuntimeError\
            ("matchargs is not applicable for "
             "functions with positional arguments")

    @wraps(fun)
    def wrapper(*args, **kwargs):
        if len(args):
            raise RuntimeError\
            ("matchargs is not applicable for "
             "functions with positional arguments")

        if spec.varkw:
            return fun(**kwargs)

        return fun(**{k:v \
                      for k,v in kwargs.items() \
                      if k in spec.args})
    return wrapper
