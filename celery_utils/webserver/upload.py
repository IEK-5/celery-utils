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
import hashlib

from celery_utils.app \
    import CACHE_ODIR

from celery_utils.cache.cache \
    import cache

from cu.utils.files \
    import remove_file, get_tempfile


def _hash_file(fn, chunk_size = 4096):
    h = hashlib.md5()

    with open(fn, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)

    return h.hexdigest()


@cache(keys = ['name'], link = True, ofn_arg = 'name')
def _upload_file(fn, name):
    return fn


def upload(request_data):
    # TODO: this does not exposes /api/cu/upload correctly
    ofn = get_tempfile()

    try:
        request_data.save(ofn, overwrite = True)
        # TODO: this needs to be done via CONFIGS?
        # use full_fn_name
        name = os.path.join\
            (CACHE_ODIR, "cu", "upload", _hash_file(ofn))
        name = _upload_file(fn = ofn, name = name)
        return {'storage_fn': name}
    finally:
        remote_file(ofn)


def download(fn):
    return fn
