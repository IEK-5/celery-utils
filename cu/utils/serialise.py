import json
import pickle
import logging
import msgpack

from functools import wraps

from cu.utils.files \
    import remove_file, move_file, get_tempfile


SUPPORTED = {
    'pickle': (pickle, 'b'),
    'msgpack': (msgpack, 'b'),
    'json': (json, '')
}


def _srl_mode(how, mode='w'):
    if how not in SUPPORTED:
        raise RuntimeError\
            (f"{how} serialisation is not supported")

    return SUPPORTED[how][0], mode + SUPPORTED[how][1]


def serialise(how):
    """A decorator to serialise function return

    :fun: function

    :how: string, how to serialise the return value

    """
    def wrapper(fun):
        @wraps(fun)
        def wrap(*args, **kwargs):
            res = fun(*args, **kwargs)

            ofn = get_tempfile()
            try:
                srl, mode = _srl_mode(how, mode='w')
                with open(ofn, mode) as f:
                    srl.dump(res, f)
                return ofn
            except Exception as e:
                remove_file(ofn)
                raise e
        return wrap
    return wrapper


def _determine_serialisation(fn, failed):
    for how in SUPPORTED.keys():
        if failed == how:
            continue

        try:
            return how, _deserialise(fn, how)
        except:
            continue

    raise RuntimeError\
        ("Cannot deserialise {} with any supported "
         "serialisers!".format(fn))


def _deserialise(fn, how):
    """Deserialise filename

    :fn: string, path to a local file

    :how: string, how to deserialise

    :return: whatever was in the file

    """
    srl, mode = _srl_mode(how, mode='r')

    with open(fn, mode) as f:
        return srl.load(f)


def _upload(data, fn):
    return data


def deserialise(fn, how):
    try:
        return _deserialise(fn, how)
    except Exception as e:
        logging.error\
            ("""Cannot deserialise with default method!
            how = {}
            fn = {}
            exception: {}: {}
            """.format(how, fn, type(e), e))

    newhow, data = _determine_serialisation(fn, how)
    from cu.cache.cache import cache_fn
    cache_fn(return_type = newhow, ofn_arg = 'fn')\
        (_upload)(data=data, fn=fn)
    return data
