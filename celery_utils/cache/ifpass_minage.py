import logging


def _warning(wtype, **kwargs):
    if 'format' == wtype:
        w = """minage argument has invalid format!
        ignoring the minage value"""
    elif 'keys' == wtype:
        w = "minage argument contains irrelevant keys!"
    else:
        raise RuntimeError("invalid wtype = {}".format(wtype))

    for k,v in kwargs.items():
        w += """
        {} = {}
        """.format(k,v)
    logging.warning(w)


def ifpass_minage(minage, fntime, kwargs):
    """Check if fntime passes the

    :minage: unix timestamp (int or float) or a dictionary allowing to
    determine the mininimum allowed age for the file.

    if minage is a dictionary it can contain:
    {'one of kwargs key': [('kwargs value', unix time stamp), ...]}

    :fntime: filename timestamp

    :kwargs: task kwargs. Only used it minage is dict.

    :return: boolean. True if filename passes the minage check

    """
    if not minage:
        return True

    if isinstance(minage, (int, float)):
        return fntime > minage

    if not isinstance(minage, dict):
        _warning('format', minage = minage, fntime = fntime, kwargs = kwargs)
        return False

    for k,item in minage.items():
        if k not in kwargs:
            _warning('keys', minage = minage, fntime = fntime, kwargs = kwargs)
            return False

        if not isinstance(item, list):
            _warning('format', minage = minage, fntime = fntime, kwargs = kwargs)
            return False

        for x in item:
            if kwargs[k] == x[0] \
               and fntime < x[1]:
                return False

    return True
