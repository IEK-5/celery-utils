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

from functools import wraps


def _format_dictionary(d):
    """Print dictionary

    :d: dictionary

    :return: string
    """
    res = ""
    for key, item in d.items():
        res += "{}: {}\n".format(key,item)
    return res


def _logging_level(level):
    if 'debug' == level:
        return logging.debug
    elif 'info' == level:
        return logging.info
    elif 'warning' == level:
        return logging.warning
    elif 'error' == level:
        return logging.error
    elif 'critical' == level:
        return logging.critical
    else:
        raise RuntimeError\
            ("debug_decorator: invalid argument level = {}"\
             .format(level))


def debug_decorator(debug_loglevel = 'debug', **info):
    """Print function calls and extra info

    :level: level of messages: 'debug', 'info', 'warning',
    'error', or 'critical'

    :info: whatever info to be printed

    """
    def wrapper(fun):
        @wraps(fun)
        def wrap(*args, **kwargs):
            loghow = _logging_level(debug_loglevel)
            loghow("""function call: {}
            args: {}
            kwargs: {}
            {}
            """.format(fun.__name__, args, kwargs, _format_dictionary(info)))
            return fun(*args, **kwargs)
        return wrap
    return wrapper
