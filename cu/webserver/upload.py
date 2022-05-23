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

from cu.app \
    import UPLOADS_DIR

from cu.cache.cache \
    import cache_fn

from cu.utils.files \
    import remove_file, get_tempfile


def _hash_file(fn, chunk_size = 4096):
    h = hashlib.md5()

    with open(fn, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)

    return h.hexdigest()


@cache_fn(keys = ['name'], link = True, ofn_arg = 'name')
def _upload_file(fn, name):
    return fn


def upload_request_data(request_data):
    ofn = get_tempfile()

    try:
        request_data.save(ofn, overwrite = True)
        name = os.path.join\
            (UPLOADS_DIR, _hash_file(ofn))
        return _upload_file(fn = ofn, name = name)
    finally:
        remove_file(ofn)


def upload(fn = 'NA'):
    """Upload a file to a storage

    The prefix for the storage is specified in CONFIGS['webserver']['uploads_dir']

    :fn: filename path. With curl, say 'curl -F fn=@local_file ...'

    """
    return {'storage_fn': fn}


def download(fn = 'NA'):
    """Download a file from a storage

    :fn: remote storage path

    """
    return fn
