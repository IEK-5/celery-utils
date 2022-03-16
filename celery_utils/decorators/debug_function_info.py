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


def debug_decorator(level = 'debug', **info):
    """Print function calls and extra info

    :level: level of messages: 'debug', 'info', 'warning',
    'error', or 'critical'

    :info: whatever info to be printed

    """
    def wrapper(fun):
        @wraps(fun)
        def wrap(*args, **kwargs):
            loghow = _logging_level(level)
            loghow("""function call: {}
            args: {}
            kwargs: {}
            {}
            """.format(fun.__name__, args, kwargs, _format_dictionary(info)))
            return fun(*args, **kwargs)
        return wrap
    return wrapper
