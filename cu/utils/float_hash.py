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
import types
import hashlib


def float_hash(key, digits = 8):
    h = hashlib.md5()
    if isinstance(key, (tuple, list)):
        for x in key:
            h.update(float_hash(x, digits).encode('utf-8'))
        return h.hexdigest()

    if isinstance(key, dict):
        for k,v in key.items():
            h.update(float_hash(k, digits).encode('utf-8'))
            h.update(float_hash(v, digits).encode('utf-8'))
        return h.hexdigest()

    if isinstance(key, float):
        key = ('%.' + str(digits) + 'f') % key

    if isinstance(key, types.FunctionType):
        key = key.__name__

    h.update(str(key).encode('utf-8'))
    return h.hexdigest()
