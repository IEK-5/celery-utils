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
